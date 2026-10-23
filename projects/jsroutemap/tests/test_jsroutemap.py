import json
from pathlib import Path
import tempfile
import unittest
from jsroutemap.cli import extract, sanitize, analyze, main
BASE=Path(__file__).resolve().parents[1]

class RouteTests(unittest.TestCase):
    def test_fetch(self):
        row=extract("fetch('/api/users?token=CANARY');",'app.js')[0]
        self.assertEqual(row['route'],'/api/users?token'); self.assertEqual(row['method'],'UNKNOWN')
        self.assertEqual(row['context'],'fetch')

    def test_axios_method(self):
        self.assertEqual(extract("axios.post('/api/users')",'x.js')[0]['method'],'POST')

    def test_xhr_method(self):
        self.assertEqual(extract("xhr.open('DELETE', '/api/users/1')",'x.js')[0]['method'],'DELETE')

    def test_dynamic_placeholder(self):
        row=extract('fetch(`/api/${userId}/profile`)', 'app.js')[0]
        self.assertTrue(row['dynamic']); self.assertEqual(row['route'],'/api/{dynamic}/profile')

    def test_url_credentials_query_fragment_omitted(self):
        self.assertEqual(sanitize('https://user:secret@example.test:8443/x?a=secret#fragment'),'https://example.test:8443/x?a')

    def test_protocol_relative_rejected(self):
        self.assertIsNone(sanitize('//example.test/api'))

    def test_control_and_spaces_rejected(self):
        self.assertIsNone(sanitize('/a b')); self.assertIsNone(sanitize('/a\n'))

    def test_source_line(self):
        self.assertEqual(extract("\n\nfetch('/x')",'app.js')[0]['line'],3)

    def test_no_network_canaries_omitted(self):
        text=json.dumps(analyze([BASE/'examples/app.js']))
        self.assertNotIn('CANARY_',text)

    def test_missing_input(self):
        with self.assertRaises(ValueError): analyze([BASE/'does-not-exist.js'])

    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'link.js'; p.symlink_to(BASE/'examples/app.js')
            with self.assertRaises(ValueError): analyze([p])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'routes.json'
            self.assertEqual(main([str(BASE/'examples/app.js'),'-o',str(p)]),0)
            self.assertEqual(json.loads(p.read_text())['files_scanned'],1)
