"""Local input, validation and escaped, self-contained report output."""
import base64
import html
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit, parse_qsl

MAX_BYTES = 50 * 1024 * 1024

def load_json(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ValueError('JSON input exceeds the 50 MiB limit')
    with p.open(encoding='utf-8-sig') as stream:
        return json.load(stream)

def object_at(value, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label} must be an object')
    return value

def har_entries(path):
    data = object_at(load_json(path), 'HAR')
    log = object_at(data.get('log'), 'HAR.log')
    entries = log.get('entries')
    if not isinstance(entries, list):
        raise ValueError('HAR.log.entries must be an array')
    for index, entry in enumerate(entries):
        object_at(entry, f'entry {index}')
        request = object_at(entry.get('request'), f'entry {index}.request')
        response = object_at(entry.get('response'), f'entry {index}.response')
        if not isinstance(request.get('url'), str) or not isinstance(request.get('method'), str):
            raise ValueError(f'entry {index}: URL and method must be strings')
        for message in (request, response):
            names(message.get('headers', []))
            names(message.get('cookies', []))
            for header in message.get('headers', []):
                if not isinstance(header.get('value', ''), str):
                    raise ValueError('header values must be strings')
        content = object_at(response.get('content', {}), 'response.content')
        if not isinstance(content.get('mimeType', ''), str):
            raise ValueError('response content MIME type must be a string')
        if 'postData' in request:
            post = object_at(request['postData'], 'request.postData')
            if not isinstance(post.get('text', ''), str) or not isinstance(post.get('mimeType', ''), str):
                raise ValueError('request body text and MIME type must be strings')
        status = response.get('status')
        if type(status) is not int or not 0 <= status <= 599:
            raise ValueError(f'entry {index}: invalid HTTP status')
    return entries

def route(request):
    parts = urlsplit(request['url'])
    # Strip credentials, query values and fragments; names are useful for matching.
    host = (parts.hostname or '').lower()
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError('invalid URL port') from exc
    if ':' in host:
        host = '[' + host + ']'
    authority = host + (f':{port}' if port else '')
    query_names = sorted(set(key for key, _ in parse_qsl(parts.query, keep_blank_values=True)))
    query = '?' + '&'.join(query_names) if query_names else ''
    return f"{request['method'].upper()} {parts.scheme.lower()}://{authority}{parts.path or '/'}{query}"

def names(items):
    if items is None:
        return set()
    if not isinstance(items, list) or any(not isinstance(x, dict) or not isinstance(x.get('name'), str) for x in items):
        raise ValueError('header/cookie collection must contain named objects')
    return {item['name'].lower() for item in items}

def response_text(response):
    content = object_at(response.get('content', {}), 'response.content')
    value = content.get('text', '')
    if not isinstance(value, str):
        raise ValueError('response.content.text must be a string')
    if content.get('encoding') == 'base64':
        try:
            return base64.b64decode(value, validate=True).decode('utf-8', errors='replace')
        except (ValueError, UnicodeError) as exc:
            raise ValueError('invalid base64 response content') from exc
    return value

def output(data, destination=None, inputs=()):
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if destination is None:
        print(text, end='')
        return
    target = Path(destination)
    if any(target.resolve() == Path(p).resolve() for p in inputs):
        raise ValueError('output must not overwrite an input file')
    if target.suffix.lower() == '.html':
        title = html.escape(str(data.get('tool', 'Report')))
        text = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>{title} report</title><style>
:root{{color-scheme:dark}}body{{font:16px/1.6 system-ui;background:#0c1422;color:#dbe8f8;max-width:1100px;margin:40px auto;padding:0 24px}}
h1{{color:#65dbc6}}pre{{background:#142238;padding:24px;border:1px solid #304762;border-radius:16px;white-space:pre-wrap;overflow-wrap:anywhere}}
small{{color:#afc1d6}}</style><h1>{title}</h1><small>Local evidence • observations require analyst review</small><pre>{html.escape(text)}</pre></html>"""
    atomic_write(target, text)

def atomic_write(target, text):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.report-', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
        os.replace(temp, target)
    finally:
        Path(temp).unlink(missing_ok=True)
