"""Compare HAR structures with JSON Pointer evidence and no raw values."""
import argparse
from collections import defaultdict
import json
from ._support import har_entries, names, output, response_text, route


def pointer(parent, key):
    return parent + '/' + str(key).replace('~', '~0').replace('/', '~1')


def shape(value, parent='', depth=0):
    if depth > 64:
        raise ValueError('JSON nesting exceeds 64 levels')
    if isinstance(value, dict):
        result = {parent: 'object'}
        for key, child in value.items():
            result.update(shape(child, pointer(parent, key), depth + 1))
        return result
    if isinstance(value, list):
        result = {parent: 'array'}
        for index, child in enumerate(value):
            result.update(shape(child, pointer(parent, index), depth + 1))
        return result
    kind = 'null' if value is None else 'boolean' if isinstance(value, bool) else 'number' if isinstance(value, (int, float)) else 'string'
    return {parent: kind}


def structures(entry, side):
    message = entry[side]
    if side == 'request':
        post = message.get('postData', {})
        raw = post.get('text', '')
        mime = post.get('mimeType', '')
    else:
        raw = response_text(message)
        mime = message.get('content', {}).get('mimeType', '')
    if not raw:
        return {'state': 'not_captured_or_empty', 'shape': {}}
    if 'json' not in mime.lower():
        return {'state': 'non_json_omitted', 'shape': {}}
    try:
        return {'state': 'parsed_json', 'shape': shape(json.loads(raw))}
    except (json.JSONDecodeError, RecursionError):
        return {'state': 'invalid_json', 'shape': {}}


def compare_shapes(left, right):
    a, b = left['shape'], right['shape']
    return {'left_state': left['state'], 'right_state': right['state'],
            'added': sorted(set(b) - set(a)), 'removed': sorted(set(a) - set(b)),
            'type_changed': [{'pointer': key, 'left_type': a[key], 'right_type': b[key]} for key in sorted(set(a) & set(b)) if a[key] != b[key]]}


def compare_entry(left, right):
    result = {'status': {'left': left['response']['status'], 'right': right['response']['status']}}
    for side in ('request', 'response'):
        a = names(left[side].get('headers', []))
        b = names(right[side].get('headers', []))
        result[side] = {'headers_added': sorted(b - a), 'headers_removed': sorted(a - b),
                        'json_structure': compare_shapes(structures(left, side), structures(right, side))}
    return result


def analyze(left, right, pair_by_index=False):
    rows = []
    if pair_by_index:
        for index in range(max(len(left), len(right))):
            a = left[index] if index < len(left) else None
            b = right[index] if index < len(right) else None
            row = {'occurrence': index, 'left_route': route(a['request']) if a else None, 'right_route': route(b['request']) if b else None}
            row['difference'] = compare_entry(a, b) if a and b else {'state': 'unmatched'}
            rows.append(row)
    else:
        a, b = defaultdict(list), defaultdict(list)
        for entries, group in ((left, a), (right, b)):
            for entry in entries:
                group[route(entry['request'])].append(entry)
        for key in sorted(set(a) | set(b)):
            for index in range(max(len(a[key]), len(b[key]))):
                row = {'route': key, 'occurrence': index}
                row['difference'] = compare_entry(a[key][index], b[key][index]) if index < min(len(a[key]), len(b[key])) else {'state': 'unmatched', 'side': 'left' if index < len(a[key]) else 'right'}
                rows.append(row)
    return {'tool': 'FlowDiff', 'version': '0.1.0', 'pairing': 'index' if pair_by_index else 'method_url_then_occurrence', 'comparisons': rows,
            'limits': ['Scalar value changes are intentionally omitted, including booleans and numbers.',
                       'Different routes require --pair-by-index and analyst-verified ordering.',
                       'Arrays compare by index; absent HAR content is not evidence of an empty server response.',
                       'Paths and JSON property names remain visible; query values and body values are omitted.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left'); parser.add_argument('right')
    parser.add_argument('--pair-by-index', action='store_true', help='Pair by capture order, even across different URLs')
    parser.add_argument('-o', '--output')
    args = parser.parse_args(argv)
    try:
        output(analyze(har_entries(args.left), har_entries(args.right), args.pair_by_index), args.output, (args.left, args.right))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        parser.exit(2, f'error: {exc}\n')
