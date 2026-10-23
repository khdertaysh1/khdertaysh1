import json
from pathlib import Path
import tempfile
import unittest
from logsentinel.cli import analyze, parse_line, main
BASE=Path(__file__).resolve().parents[1]

def failed(second, ip='192.0.2.10'):
    return f'2026-10-23T10:{second//60:02d}:{second%60:02d}+00:00 lab sshd[1]: Failed password for demo from {ip} port 22 ssh2'

class LogTests(unittest.TestCase):
    def test_failure_then_success(self):
        result=analyze((BASE/'examples/auth.log').read_text().splitlines(),'ssh')
        self.assertEqual([a['rule'] for a in result['alerts']],['ssh_failure_burst','ssh_success_after_failures'])

    def test_window_expiration(self):
        result=analyze([failed(i*61) for i in range(5)],'ssh',window=60)
        self.assertFalse(result['alerts'])

    def test_threshold_boundary_inclusive(self):
        result=analyze([failed(i) for i in range(5)],'ssh',window=4)
        self.assertEqual(len(result['alerts']),1)

    def test_sources_not_merged(self):
        self.assertFalse(analyze([failed(i, f'192.0.2.{i+1}') for i in range(5)],'ssh')['alerts'])

    def test_nginx_distinct_paths(self):
        result=analyze((BASE/'examples/access.log').read_text().splitlines(),'nginx')
        self.assertEqual(result['alerts'][0]['count'],10)
        self.assertNotIn('CANARY',json.dumps(result))

    def test_repeated_same_path_not_scan(self):
        line='192.0.2.1 - - [23/Oct/2026:10:00:00 +0000] "GET /missing HTTP/1.1" 404 0'
        self.assertFalse(analyze([line]*20,'nginx')['alerts'])

    def test_successful_navigation_excluded(self):
        lines=(BASE/'examples/access.log').read_text().replace(' 404 ',' 200 ').splitlines()
        self.assertFalse(analyze(lines,'nginx')['alerts'])

    def test_out_of_order_fails(self):
        with self.assertRaises(ValueError): analyze([failed(2),failed(1)],'ssh')

    def test_syslog_requires_year(self):
        line='Oct 23 10:00:00 lab sshd[1]: Failed password for demo from 192.0.2.1 port 22 ssh2'
        with self.assertRaises(ValueError): parse_line(line,'ssh')
        self.assertEqual(parse_line(line,'ssh',2026)['kind'],'ssh_failure')

    def test_unparsed_lines_counted(self):
        result=analyze(['irrelevant line'],'ssh')
        self.assertEqual(result['skipped_lines'],1); self.assertEqual(result['parsed_lines'],0)

    def test_source_limit(self):
        with self.assertRaises(ValueError): analyze([failed(0),failed(1,'192.0.2.2')],'ssh',max_sources=1)

    def test_no_repeated_burst_in_same_window(self):
        result=analyze([failed(i) for i in range(20)],'ssh')
        self.assertEqual(len(result['alerts']),1)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as raw:
            out=Path(raw)/'report.json'
            self.assertEqual(main([str(BASE/'examples/auth.log'),'--format','ssh','-o',str(out)]),0)
            self.assertEqual(len(json.loads(out.read_text())['alerts']),2)
