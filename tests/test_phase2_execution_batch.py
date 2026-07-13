import unittest
from lab.phase2_execution_batch import load,preflight_batch,FAILURES,classify_synthetic
class ExecutionBatch(unittest.TestCase):
 def test_preflight_and_inert_states(self):
  b=load();self.assertEqual(preflight_batch(b),'ok');self.assertEqual(b['execution']['host_contexts'],['GDAXI/M1','AUDCAD/M1']);self.assertFalse(b['execution']['native_execution_attempted']);self.assertFalse(b['execution']['native_parity_accepted'])
 def test_all_synthetic_failure_classes_are_sealed(self):
  self.assertEqual(classify_synthetic('unknown'),'exact_pass')
  for kind in FAILURES:self.assertEqual(classify_synthetic(kind),kind)
