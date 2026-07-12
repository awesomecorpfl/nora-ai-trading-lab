import json,tempfile,unittest
from pathlib import Path
from lab.phase2x_batch import manifest,preflight,stage

class Phase2XBatch(unittest.TestCase):
 def test_preflight_and_deterministic_atomic_staging(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a=stage(p/'a');b=stage(p/'b');self.assertEqual(a['batch_identity'],b['batch_identity']);self.assertEqual((p/'a'/'batch.json').read_bytes(),(p/'b'/'batch.json').read_bytes());self.assertEqual(preflight(p/'report.json')['status'],'PASS')
   self.assertFalse(any(x['native_parity'] or x['grammar_admitted'] or x['searchable'] for x in a['targets']))
 def test_existing_and_injected_failure_leave_no_package(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'exists').mkdir();
   with self.assertRaises(ValueError):stage(p/'exists')
   with self.assertRaises(RuntimeError):stage(p/'failed',True)
   self.assertFalse((p/'failed').exists())
 def test_bindings_are_distinct_and_complete(self):
  value=manifest();self.assertEqual(value['target_order'],['macd','percentile']);self.assertNotEqual(value['targets'][0]['runtime_identity'],value['targets'][1]['runtime_identity'])
  for target in value['targets']:self.assertEqual(len(target['package_identity']),64);self.assertTrue(target['csv_filename'].endswith('.csv'))
