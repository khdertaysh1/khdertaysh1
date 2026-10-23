"""Analyze ordered SSH or Nginx logs with bounded correlation windows."""
import argparse
from collections import deque
from datetime import datetime, timezone
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlsplit
from ._support import output

NGINX = re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^]]+)\] "(?P<method>[A-Z]+) (?P<url>\S+) [^"]+" (?P<status>\d{3})\b')
SSH = re.compile(r'(?P<result>Failed password|Accepted password|Accepted publickey) for (?:invalid user )?\S+ from (?P<ip>\S+) port \d+')
SYSLOG = re.compile(r'^(?P<time>[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d)\s+')
ISO = re.compile(r'^\S+')


def address(value):
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        raise ValueError('log contains an invalid source IP') from None


def parse_line(line, kind, year=None):
    if kind == 'nginx':
        match = NGINX.search(line)
        if not match:
            return None
        time = datetime.strptime(match['time'], '%d/%b/%Y:%H:%M:%S %z')
        status = int(match['status'])
        if not 100 <= status <= 599:
            raise ValueError('invalid HTTP status in Nginx log')
        return {'time': time.timestamp(), 'ip': address(match['ip']), 'kind': 'web',
                'path': urlsplit(match['url']).path, 'status': status}
    match = SSH.search(line)
    if not match:
        return None
    syslog = SYSLOG.search(line)
    if syslog:
        if year is None:
            raise ValueError('RFC3164 SSH timestamps need --year; timezone is interpreted as UTC')
        time = datetime.strptime(f"{year} {syslog['time']}", '%Y %b %d %H:%M:%S').replace(tzinfo=timezone.utc)
    else:
        stamp = ISO.search(line)
        if stamp is None:
            return None
        time = datetime.fromisoformat(stamp[0].replace('Z', '+00:00'))
        if time.tzinfo is None:
            raise ValueError('ISO SSH timestamps must include a timezone')
    return {'time': time.timestamp(), 'ip': address(match['ip']),
            'kind': 'ssh_failure' if match['result'].startswith('Failed') else 'ssh_success'}


def analyze(lines, kind, window=300, failures=5, paths=10, year=None, max_sources=10000):
    states, alerts = {}, []
    parsed = skipped = 0
    previous = None
    def emit(rule, event, count):
        alerts.append({'rule': rule, 'source_ip': event['ip'],
                       'timestamp': datetime.fromtimestamp(event['time'], timezone.utc).isoformat(),
                       'window_seconds': window, 'count': count,
                       'severity': 'review', 'evidence_line': line_number})
    for line_number, line in enumerate(lines, 1):
        if len(line) > 65536:
            raise ValueError(f'line {line_number}: exceeds 64 KiB')
        event = parse_line(line, kind, year)
        if event is None:
            skipped += 1
            continue
        parsed += 1
        now = event['time']
        if previous is not None and now < previous:
            raise ValueError(f'line {line_number}: events must be ordered by timestamp; split year-boundary logs')
        previous = now
        # Remove idle sources before allocating a new one; memory is capped explicitly.
        if event['ip'] not in states:
            for key in [key for key, state in states.items() if now - state['last_seen'] > window]:
                del states[key]
            if len(states) >= max_sources:
                raise ValueError('active-source limit reached; split logs or increase --max-sources')
            states[event['ip']] = {'failures': deque(), 'web': deque(), 'last_seen': now, 'last_alert': {}}
        state = states[event['ip']]
        state['last_seen'] = now
        for queue in ('failures', 'web'):
            while state[queue] and now - state[queue][0][0] > window:
                state[queue].popleft()
        def ready(rule):
            return now - state['last_alert'].get(rule, float('-inf')) > window
        if event['kind'] == 'ssh_failure':
            state['failures'].append((now, None))
            if len(state['failures']) >= failures and ready('ssh_failure_burst'):
                emit('ssh_failure_burst', event, len(state['failures']))
                state['last_alert']['ssh_failure_burst'] = now
        elif event['kind'] == 'ssh_success':
            if len(state['failures']) >= failures and ready('ssh_success_after_failures'):
                emit('ssh_success_after_failures', event, len(state['failures']))
                state['last_alert']['ssh_success_after_failures'] = now
            state['failures'].clear()
        else:
            # Only failed paths count; ordinary successful navigation is excluded.
            if event['status'] in (400, 401, 403, 404, 405):
                state['web'].append((now, event['path']))
            distinct = len({item[1] for item in state['web']})
            if distinct >= paths and ready('web_failed_path_sweep'):
                emit('web_failed_path_sweep', event, distinct)
                state['last_alert']['web_failed_path_sweep'] = now
        if len(state['failures']) + len(state['web']) > 100000:
            raise ValueError('per-source event limit reached; reduce the time window or split input')
    return {'tool': 'LogSentinel', 'version': '0.1.0', 'parsed_lines': parsed, 'skipped_lines': skipped,
            'alerts': alerts, 'configuration': {'window_seconds': window, 'failure_threshold': failures, 'path_threshold': paths},
            'limits': ['Alerts are triage signals, not confirmed attacks; NAT, automation and stale credentials can trigger them.',
                       'Nginx requires the standard combined/common request prefix; custom JSON logs are not supported.',
                       'SSH supports password failures and password/publickey successes; other events are skipped.',
                       'Source IPs and line references are retained; usernames, raw lines and URL query values are omitted.',
                       'Inputs must be chronological; RFC3164 requires an explicit year and assumes UTC.']}


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log')
    parser.add_argument('--format', required=True, choices=('ssh', 'nginx'))
    parser.add_argument('--window', type=positive, default=300)
    parser.add_argument('--failures', type=positive, default=5)
    parser.add_argument('--paths', type=positive, default=10)
    parser.add_argument('--year', type=int)
    parser.add_argument('--max-sources', type=positive, default=10000)
    parser.add_argument('-o', '--output')
    args = parser.parse_args(argv)
    try:
        with Path(args.log).open(encoding='utf-8', errors='strict') as stream:
            result = analyze(stream, args.format, args.window, args.failures, args.paths, args.year, args.max_sources)
        output(result, args.output, (args.log,))
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(2, f'error: {exc}\n')
