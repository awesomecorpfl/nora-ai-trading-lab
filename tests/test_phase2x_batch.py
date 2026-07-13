import json,tempfile,unittest
from pathlib import Path
from lab.phase2x_batch import ROOT,MANIFEST,load,preflight,stage
class BatchV2(unittest.TestCase):
 def mutated(self,d,fn):
  p=Path(d)/'mut.json';v=load();fn(v);p.write_text(json.dumps(v));return p.relative_to(ROOT)
 def copy_manifest(self,d):
  p=Path(d)/'manifest.json';p.write_bytes((ROOT/MANIFEST).read_bytes());return p.relative_to(ROOT) if p.is_relative_to(ROOT) else None
 def test_valid_frozen_preflight_and_two_directory_staging(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as d:
   p=Path(d);r=preflight(p/'report.json');self.assertEqual(r['status'],'PASS');a=stage(p/'a');b=stage(p/'b');self.assertEqual(a,b);self.assertEqual((p/'a'/MANIFEST).read_bytes(),(p/'b'/MANIFEST).read_bytes())
 def test_vector_bindings_and_closed_states(self):
  v=load();self.assertIn('46329192b3fa4dedf6d3f1f007cc45e7e9cb035b56f06d50097c42d51dbfb9d6',v['historical_batch_identities'])
  for t in v['targets']:
   self.assertEqual(len(t['expected_vectors']['expected_vector_identity']),64);self.assertTrue(t['native_execution_attempted']);self.assertTrue(t['native_result_returned']);self.assertTrue(t['native_reconciliation_passed']);self.assertTrue(t['native_parity_evidence_available']);self.assertFalse(t['native_parity']);self.assertFalse(t['grammar_admitted']);self.assertFalse(t['searchable'])
 def test_existing_and_injected_failure_cleanup(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as d:
   p=Path(d);(p/'x').mkdir();
   with self.assertRaises(ValueError):stage(p/'x')
   with self.assertRaises(RuntimeError):stage(p/'fail',inject_failure=True)
   self.assertFalse((p/'fail').exists());self.assertFalse(list(p.glob('.phase2xv3-*')))
   with self.assertRaises(RuntimeError):preflight(p/'no.json',fail_publish=True)
   self.assertFalse((p/'no.tmp').exists())
 def test_manifest_vector_identity_schema_and_state_tampering(self):
  cases=(
   lambda v:v['targets'][0]['expected_vectors']['vectors']['macd'].__setitem__(3,0.0),
   lambda v:v['targets'][0]['expected_vectors']['vectors']['null_masks']['macd'].__setitem__(3,True),
   lambda v:v['targets'][0]['expected_vectors']['rows'].reverse(),
   lambda v:v['targets'][0]['expected_vectors']['columns'].__setitem__(1,'renamed'),
   lambda v:v['targets'][0].__setitem__('rust_task_identity','0'*64),
   lambda v:v['targets'][0].__setitem__('runtime_identity','0'*64),
   lambda v:v['targets'][0].__setitem__('tester_identity','0'*64),
   lambda v:v['targets'][0].__setitem__('package_identity','0'*64),
   lambda v:v['targets'][0].__setitem__('completion_marker','wrong'),
   lambda v:v['targets'][0].__setitem__('searchable',True),
   lambda v:v['targets'].__setitem__(1,dict(v['targets'][0])),
   lambda v:v['allowlisted_paths'].append(v['allowlisted_paths'][1]),
  )
  with tempfile.TemporaryDirectory(dir=ROOT) as d:
   for fn in cases:
    rel=self.mutated(d,fn);self.assertEqual(preflight(Path(d)/'r.json',rel)['status'],'FAIL')
