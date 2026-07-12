import json,tempfile,unittest
from pathlib import Path
from lab.phase2x_batch import ROOT,MANIFEST,load,preflight,stage
class BatchV2(unittest.TestCase):
 def copy_manifest(self,d):
  p=Path(d)/'manifest.json';p.write_bytes((ROOT/MANIFEST).read_bytes());return p.relative_to(ROOT) if p.is_relative_to(ROOT) else None
 def test_valid_frozen_preflight_and_two_directory_staging(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as d:
   p=Path(d);r=preflight(p/'report.json');self.assertEqual(r['status'],'PASS');a=stage(p/'a');b=stage(p/'b');self.assertEqual(a,b);self.assertEqual((p/'a'/MANIFEST).read_bytes(),(p/'b'/MANIFEST).read_bytes())
 def test_vector_bindings_and_closed_states(self):
  v=load();self.assertEqual(v['historical_batch_identity'],'97d223ac2e217da907094b07fcc77e8ae97b6c713380c1aa47bf5e475779b23f')
  for t in v['targets']:
   self.assertEqual(len(t['expected_vectors']['expected_vector_identity']),64);self.assertFalse(t['native_execution_attempted']);self.assertFalse(t['native_parity']);self.assertFalse(t['grammar_admitted']);self.assertFalse(t['searchable'])
 def test_existing_and_injected_failure_cleanup(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as d:
   p=Path(d);(p/'x').mkdir();
   with self.assertRaises(ValueError):stage(p/'x')
   with self.assertRaises(RuntimeError):stage(p/'fail',inject_failure=True)
   self.assertFalse((p/'fail').exists());self.assertFalse(list(p.glob('.phase2xv2-*')))
   with self.assertRaises(RuntimeError):preflight(p/'no.json',fail_publish=True)
   self.assertFalse((p/'no.tmp').exists())
