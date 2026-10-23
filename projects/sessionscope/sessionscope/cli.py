"""Compare recorded HAR evidence; never replay a session."""
import argparse
from collections import defaultdict
import json
import re
from ._support import har_entries, names, output, response_text, route


def inventory(entry):
    request, response = entry['request'], entry['response']
    headers = names(request.get('headers', []))
    cookies = names(request.get('cookies', []))
    set_cookies = []
    for header in response.get('headers', []):
        if header.get('name', '').lower() == 'set-cookie':
            value = header.get('value', '')
            parts = [part.strip() for part in value.split(';')]
            if parts and '=' in parts[0]:
                cookie_name, cookie_value = parts[0].split('=', 1)
                attrs = {p.split('=', 1)[0].lower(): p.split('=', 1)[1] if '=' in p else True for p in parts[1:]}
                set_cookies.append({'name': cookie_name, 'secure': 'secure' in attrs,
                                    'http_only': 'httponly' in attrs,
                                    'same_site': str(attrs.get('samesite', 'unspecified')).lower()
                                    if str(attrs.get('samesite', '')).lower() in ('lax', 'strict', 'none') else 'unspecified',
                                    'empty_value': cookie_value == '',
                                    'max_age_zero': attrs.get('max-age') == '0'})
    return {'status': response['status'], 'authorization_header_present': 'authorization' in headers,
            'cookie_names': sorted(cookies), 'cookie_header_present': 'cookie' in headers,
            'set_cookie_attributes': set_cookies}


def analyze(before, after, marker=None, path_pattern=None):
    groups = [defaultdict(list), defaultdict(list)]
    for entries, group in zip((before, after), groups):
        for entry in entries:
            if path_pattern and not path_pattern.search(entry['request']['url']):
                continue
            group[route(entry['request'])].append(entry)
    results = []
    for key in sorted(set(groups[0]) | set(groups[1])):
        left, right = groups[0].get(key, []), groups[1].get(key, [])
        row = {'route': key, 'before': [inventory(e) for e in left], 'after': [inventory(e) for e in right]}
        if not left or not right:
            row['assessment'] = 'unmatched_capture'
        elif any(200 <= e['response']['status'] < 300 for e in right):
            row['assessment'] = 'successful_http_requires_content_review'
        elif all(e['response']['status'] in (401, 403) for e in right):
            row['assessment'] = 'access_denied_observed'
        elif any(300 <= e['response']['status'] < 400 for e in right):
            row['assessment'] = 'redirect_requires_review'
        else:
            row['assessment'] = 'inconclusive'
        if marker is not None:
            before_matches = [marker in response_text(e['response']) for e in left]
            after_matches = [marker in response_text(e['response']) for e in right]
            row['marker_presence'] = {'before': before_matches, 'after': after_matches}
            if any(before_matches) and any(found and 200 <= e['response']['status'] < 300 for found, e in zip(after_matches, right)):
                row['assessment'] = 'protected_marker_persists_review_capture_and_cache'
        results.append(row)
    return {'tool': 'SessionScope', 'version': '0.1.0', 'routes': results,
            'limits': ['Captures do not prove request timing, logout completion or server-side revocation.',
                       'A 2xx response alone does not establish authenticated access.',
                       'Markers can occur in cached/public/error responses. Verify freshness and identity manually.',
                       'Cookie values, header values and response bodies are omitted. Paths and names are retained.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', help='HAR captured before logout')
    parser.add_argument('after', help='HAR captured after logout')
    parser.add_argument('--marker', help='Exact non-secret marker expected only in protected response content')
    parser.add_argument('--path-regex', help='Only inspect matching recorded request URLs')
    parser.add_argument('-o', '--output', help='JSON or .html report (default: stdout JSON)')
    args = parser.parse_args(argv)
    try:
        if args.marker == '':
            raise ValueError('marker must not be empty')
        pattern = re.compile(args.path_regex) if args.path_regex else None
        result = analyze(har_entries(args.before), har_entries(args.after), args.marker, pattern)
        output(result, args.output, (args.before, args.after))
        return 0
    except (OSError, ValueError, TypeError, KeyError, re.error) as exc:
        parser.exit(2, f'error: {exc}\n')
