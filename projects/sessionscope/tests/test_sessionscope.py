import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
from sessionscope.cli import analyze, main
from sessionscope._support import har_entries, output

BASE = Path(__file__).resolve().parents[1]

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.before = har_entries(BASE / 'examples/before.har')
        self.after = har_entries(BASE / 'examples/after.har')

    def test_denial(self):
        self.assertEqual(analyze(self.before, self.after)['routes'][0]['assessment'], 'access_denied_observed')

    def test_http_success_is_not_proof(self):
        result = analyze(self.before, self.before)
        self.assertEqual(result['routes'][0]['assessment'], 'successful_http_requires_content_review')

    def test_marker_persistence(self):
        result = analyze(self.before, self.before, 'LAB_PROTECTED_MARKER')
        self.assertEqual(result['routes'][0]['assessment'], 'protected_marker_persists_review_capture_and_cache')

    def test_base64_marker(self):
        entries = copy.deepcopy(self.before)
        content = entries[0]['response']['content']
        content['text'] = base64.b64encode(content['text'].encode()).decode()
        content['encoding'] = 'base64'
        self.assertEqual(analyze(self.before, entries, 'LAB_PROTECTED_MARKER')['routes'][0]['marker_presence']['after'], [True])

    def test_unmatched(self):
        self.assertEqual(analyze(self.before, [])['routes'][0]['assessment'], 'unmatched_capture')

    def test_duplicates_are_preserved(self):
        self.assertEqual(len(analyze(self.before * 2, self.after)['routes'][0]['before']), 2)

    def test_secret_values_never_exported(self):
        text = json.dumps(analyze(self.before, self.before))
        for secret in ('CANARY_AUTH', 'CANARY_COOKIE', 'CANARY_QUERY', 'LAB_PROTECTED_MARKER'):
            self.assertNotIn(secret, text)

    def test_cookie_attributes(self):
        cookie = analyze(self.before, self.after)['routes'][0]['before'][0]['set_cookie_attributes'][0]
        self.assertTrue(cookie['http_only']); self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['same_site'], 'lax')

    def test_bad_har_has_readable_error(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / 'bad.json'; path.write_text('{}')
            with self.assertRaises(ValueError): har_entries(path)

    def test_report_escapes_html(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / 'report.html'
            output({'tool':'SessionScope','value':'</pre><script>alert(1)</script>'}, path)
            text = path.read_text()
            self.assertNotIn('<script>', text); self.assertIn('&lt;script&gt;', text)

    def test_no_input_overwrite(self):
        with self.assertRaises(ValueError): output({'tool':'test'}, BASE / 'examples/before.har', [BASE / 'examples/before.har'])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / 'report.json'
            self.assertEqual(main([str(BASE / 'examples/before.har'), str(BASE / 'examples/after.har'), '-o', str(path)]), 0)
            self.assertEqual(json.loads(path.read_text())['tool'], 'SessionScope')

    def test_malformed_headers_rejected(self):
        entries = copy.deepcopy(self.before)
        entries[0]['response']['headers'] = ['bad']
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / 'bad.har'
            path.write_text(json.dumps({'log': {'entries': entries}}))
            with self.assertRaises(ValueError): har_entries(path)

    def test_malformed_post_body_rejected(self):
        entries = copy.deepcopy(self.before)
        entries[0]['request']['postData'] = {'text': 12, 'mimeType': 'application/json'}
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / 'bad.har'
            path.write_text(json.dumps({'log': {'entries': entries}}))
            with self.assertRaises(ValueError): har_entries(path)
