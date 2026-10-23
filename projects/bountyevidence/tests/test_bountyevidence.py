import copy
import json
from pathlib import Path
import tempfile
import unittest
from bountyevidence.cli import TEMPLATE, validate, redact, markdown, main

class EvidenceTests(unittest.TestCase):
    def test_valid_template(self):
        self.assertEqual(validate(TEMPLATE)['title'],TEMPLATE['title'])

    def test_missing_impact_rejected(self):
        data=copy.deepcopy(TEMPLATE); del data['impact']
        with self.assertRaises(ValueError): validate(data)

    def test_empty_steps_rejected(self):
        data=copy.deepcopy(TEMPLATE); data['steps']=[]
        with self.assertRaises(ValueError): validate(data)

    def test_unknown_field_rejected(self):
        data=copy.deepcopy(TEMPLATE); data['cookies']='secret'
        with self.assertRaises(ValueError): validate(data)

    def test_evidence_requires_three_fields(self):
        data=copy.deepcopy(TEMPLATE); data['evidence']=[{'label':'x'}]
        with self.assertRaises(ValueError): validate(data)

    def test_labeled_secret_redaction(self):
        for value in ('Authorization: Bearer CANARY','password=CANARY','api_key: CANARY','Cookie: sid=CANARY'):
            self.assertNotIn('CANARY',redact(value))

    def test_inline_bearer_and_jwt(self):
        self.assertNotIn('CANARY',redact('example Bearer CANARY'))
        self.assertEqual(redact('eyJabc.def.ghi'),'[REDACTED_JWT]')

    def test_url_query_removed(self):
        self.assertNotIn('CANARY',redact('https://example.test/a?key=CANARY'))

    def test_markdown_escapes_active_content(self):
        data=copy.deepcopy(TEMPLATE); data['summary']='<script>x</script>\n![image](https://evil.test/)'
        rendered=markdown(validate(data))
        self.assertNotIn('<script>',rendered); self.assertIn('&lt;script&gt;',rendered)
        self.assertNotIn('![image]',rendered)

    def test_init_refuses_existing_file(self):
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/'finding.json'; path.write_text('keep')
            with self.assertRaises(SystemExit): main(['init',str(path)])
            self.assertEqual(path.read_text(),'keep')

    def test_init_and_build_all_formats(self):
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/'finding.json'; self.assertEqual(main(['init',str(path)]),0)
            for ext in ('md','json','html'):
                out=Path(raw)/('report.'+ext)
                self.assertEqual(main(['build',str(path),'-o',str(out)]),0)
                self.assertTrue(out.is_file())

    def test_prevent_input_overwrite(self):
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/'finding.json'; path.write_text(json.dumps(TEMPLATE))
            with self.assertRaises(SystemExit): main(['build',str(path),'-o',str(path)])
