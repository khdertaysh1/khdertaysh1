"""Extract route candidates from local JavaScript without executing it."""
import argparse
from bisect import bisect_right
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qsl
from ._support import MAX_BYTES, output

# A lexical heuristic, not a JavaScript parser. Dynamic expressions are not evaluated.
LITERAL = re.compile(r'''(?P<quote>["'`])(?P<value>(?:\\.|[^\\])*?)(?P=quote)''', re.DOTALL)
CALL = re.compile(r'''(?P<call>fetch|axios\.(?:get|post|put|patch|delete|head|options)|\bopen)\s*\(\s*$''')
OPEN = re.compile(r'''\bopen\s*\(\s*["'](?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)["']\s*,\s*$''', re.I)


def sanitize(value):
    value = value.replace('\\/', '/')
    if not (value.startswith('/') and not value.startswith('//') or value.startswith(('https://', 'http://'))):
        return None
    # Reject whitespace, control characters and common non-route literals.
    if any(c.isspace() or ord(c) < 32 for c in value) or len(value) > 2048:
        return None
    # Keep template placeholders but do not let URL parsing treat their ?/# as separators.
    value = re.sub(r'\$\{[^}]*\}', '{dynamic}', value)
    parts = urlsplit(value)
    host = parts.hostname or ''
    if ':' in host:
        host = '[' + host + ']'
    try:
        port = parts.port
    except ValueError:
        return None
    if port:
        host += ':' + str(port)
    prefix = parts.scheme + '://' + host if parts.scheme else ''
    query_names = sorted(set(k for k, _ in parse_qsl(parts.query, keep_blank_values=True)))
    query = '?' + '&'.join(query_names) if query_names else ''
    return prefix + (parts.path or '/') + query


def extract(text, source):
    rows, seen = [], set()
    newlines = [i for i, char in enumerate(text) if char == "\n"]
    for match in LITERAL.finditer(text):
        value = match.group('value')
        candidate = sanitize(value)
        if candidate is None:
            continue
        prefix = text[max(0, match.start() - 100):match.start()]
        call = CALL.search(prefix)
        xhr = OPEN.search(prefix)
        method, context = 'UNKNOWN', 'string_literal'
        if xhr:
            method, context = xhr.group('method').upper(), 'xhr.open'
        elif call:
            context = call.group('call')
            if context.startswith('axios.'):
                method = context.split('.')[1].upper()
            # fetch may specify a method in a later options object: do not assume GET.
        line = bisect_right(newlines, match.start()) + 1
        signature = (candidate, method, line)
        if signature in seen:
            continue
        seen.add(signature)
        rows.append({'source': source, 'line': line, 'route': candidate, 'method': method,
                     'context': context, 'dynamic': '${' in value})
    return rows


def analyze(paths):
    rows, files = [], []
    for raw in paths:
        path = Path(raw)
        if path.is_symlink():
            raise ValueError('symlink inputs are not followed')
        if path.is_dir():
            files.extend(p for p in path.rglob('*') if p.suffix.lower() in ('.js', '.mjs', '.cjs') and not p.is_symlink() and not any(x.is_symlink() for x in p.parents))
        elif path.is_file():
            files.append(path)
        else:
            raise ValueError(f'input does not exist: {path}')
    unique = sorted(set(files), key=str)
    if not unique:
        raise ValueError('no JavaScript files found')
    total = 0
    for path in unique:
        total += path.stat().st_size
        if total > MAX_BYTES:
            raise ValueError('combined JavaScript input exceeds 50 MiB')
        rows.extend(extract(path.read_text(encoding='utf-8'), str(path)))
    return {'tool': 'JSRouteMap', 'version': '0.1.0', 'files_scanned': len(unique), 'candidates': rows,
            'limits': ['Lexical heuristic: comments, embedded strings and regular expressions can cause false positives.',
                       'Concatenated paths, escaped quotes and dynamic expressions may be missed.',
                       'A candidate does not prove route existence, accessibility or a vulnerability.',
                       'Query values and URL credentials are removed. Source paths and route path segments are retained.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', help='Local JavaScript files or directories')
    parser.add_argument('-o', '--output')
    args = parser.parse_args(argv)
    try:
        if args.output:
            target = Path(args.output).resolve()
            if any(target == Path(p).resolve() or Path(p).is_dir() and Path(p).resolve() in target.parents for p in args.paths):
                raise ValueError('output must be outside input files/directories')
        output(analyze(args.paths), args.output, args.paths)
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(2, f'error: {exc}\n')
