import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from lab.mql5gen import TESTER_MANIFEST_FILENAME, TESTER_SOURCE_FILENAME, generate_tester_canary

ROOT=Path(__file__).resolve().parents[1]
CONDITION=ROOT/'tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.manifest.json'
EVIDENCE=ROOT/'tests/fixtures/phase2g_translation_evidence.json'
SCRIPT_FIXTURE=ROOT/'tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.manifest.json'
FROZEN=ROOT/'tests/fixtures/phase2j_mql5_condition_tester'

class TesterCanary(unittest.TestCase):
 def test_repeatable_frozen_and_no_trading(self):
  with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
   one=generate_tester_canary(CONDITION,EVIDENCE,SCRIPT_FIXTURE,a);two=generate_tester_canary(CONDITION,EVIDENCE,SCRIPT_FIXTURE,b)
   src=Path(a,TESTER_SOURCE_FILENAME).read_bytes();self.assertEqual(src,Path(b,TESTER_SOURCE_FILENAME).read_bytes());self.assertEqual(src,(FROZEN/TESTER_SOURCE_FILENAME).read_bytes());self.assertEqual(one['tester_fixture_identity'],two['tester_fixture_identity']);self.assertEqual(json.loads(Path(a,TESTER_MANIFEST_FILENAME).read_text()),json.loads((FROZEN/TESTER_MANIFEST_FILENAME).read_text()))
   low=src.decode().lower()
   for token in ('ordersend','ctrade','buy','sell','positionopen','positionclose','copybuffer','symbolinfotick','_symbol','_period','bid','ask','spread','account','indicator','copyrates'):
    self.assertIsNone(re.search(r'\\b'+re.escape(token)+r'\\b',low))
   self.assertIn('fileflush',low);self.assertIn('file_common',low);self.assertIn('testerstop',low)
 def test_input_mutation_changes_source_and_identity(self):
  value=json.loads(EVIDENCE.read_text());value=copy.deepcopy(value);value['rows'][2]['bindings']['sma3']=1.1007
  with tempfile.TemporaryDirectory() as d:
   p=Path(d); altered=p/'e.json';altered.write_text(json.dumps(value));(p/'one').mkdir();(p/'two').mkdir();a=generate_tester_canary(CONDITION,EVIDENCE,SCRIPT_FIXTURE,p/'one');b=generate_tester_canary(CONDITION,altered,SCRIPT_FIXTURE,p/'two');self.assertNotEqual(a['source_sha256'],b['source_sha256']);self.assertNotEqual(a['tester_fixture_identity'],b['tester_fixture_identity'])
