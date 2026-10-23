import copy
import json
from pathlib import Path
import tempfile
import unittest
from flowdiff.cli import analyze, compare_shapes, shape, main
from flowdiff._support import har_entries
BASE = Path(__file__).resolve().parents[1]

class FlowTests(unittest.TestCase):
    def setUp(self):
        self.left = har_entries(BASE / 'examples/before.har')
        self.right = har_entries(BASE / 'examples/after.har')

    def test_field_changes(self):
        diff = analyze(self.left, self.right)['comparisons'][0]['difference']
        self.assertEqual(diff['status'], {'left':200,'right':401})
        self.assertIn('/error', diff['response']['json_structure']['added'])
        self.assertIn('/account/id', diff['response']['json_structure']['removed'])

    def test_rfc6901(self):
        self.assertIn('/a~1b/~0key', shape({'a/b':{'~key':False}}))

    def test_boolean_is_not_number(self):
        self.assertEqual(shape([False, 1, None]), {'':'array','/0':'boolean','/1':'number','/2':'null'})

    def test_type_change(self):
        diff = compare_shapes({'state':'parsed_json','shape':shape({'id':1})}, {'state':'parsed_json','shape':shape({'id':'1'})})
        self.assertEqual(diff['type_changed'][0]['pointer'], '/id')

    def test_scalar_changes_intentionally_omitted(self):
        left = {'state':'parsed_json','shape':shape({'id':1})}
        right = {'state':'parsed_json','shape':shape({'id':2})}
        self.assertFalse(compare_shapes(left,right)['type_changed'])

    def test_different_routes_unmatched_by_default(self):
        right = copy.deepcopy(self.right); right[0]['request']['url'] = 'https://lab.example.test/other'
        self.assertEqual(len(analyze(self.left,right)['comparisons']), 2)
        self.assertEqual(analyze(self.left,right,True)['comparisons'][0]['difference']['status']['right'],401)

    def test_empty_capture(self):
        self.assertEqual(analyze([],[])['comparisons'],[])

    def test_duplicate_occurrences(self):
        self.assertEqual(len(analyze(self.left*2,self.right)['comparisons']),2)
        self.assertEqual(analyze(self.left*2,self.right)['comparisons'][1]['difference']['state'],'unmatched')

    def test_body_and_header_secrets_absent(self):
        text=json.dumps(analyze(self.left,self.right))
        for token in ('CANARY_AUTH','CANARY_COOKIE','CANARY_QUERY','LAB_PROTECTED_MARKER'): self.assertNotIn(token,text)

    def test_invalid_json_is_reported(self):
        right=copy.deepcopy(self.right); right[0]['response']['content']['text']='{'
        diff=analyze(self.left,right)['comparisons'][0]['difference']['response']['json_structure']
        self.assertEqual(diff['right_state'],'invalid_json')

    def test_missing_body_is_not_empty_server_data(self):
        right=copy.deepcopy(self.right); right[0]['response']['content'].pop('text')
        diff=analyze(self.left,right)['comparisons'][0]['difference']['response']['json_structure']
        self.assertEqual(diff['right_state'],'not_captured_or_empty')

    def test_cli_html(self):
        with tempfile.TemporaryDirectory() as raw:
            out=Path(raw)/'report.html'
            self.assertEqual(main([str(BASE/'examples/before.har'),str(BASE/'examples/after.har'),'-o',str(out)]),0)
            self.assertIn('FlowDiff',out.read_text())
