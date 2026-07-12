import tempfile,unittest
from pathlib import Path
from lab.phase2x_batch import load
from lab.phase2y_reconcile import reconcile,publish
class Reconcile(unittest.TestCase):
 def fixture(self):
  b=load();v={'batch_identity':b['batch_identity'],'targets':{}}
  for t in b['targets']:
   e=t['expected_vectors'];rows=[]
   for i in e['rows']:
    row={'row':i}
    for k,x in e['vectors'].items():
     if k not in ('row','close','source','null_masks'):row[k]=x[i]
    rows.append(row)
   v['targets'][t['id']]={k:t[k] for k in ('rust_component_identity','runtime_identity','tester_identity','package_identity')};v['targets'][t['id']].update({'expected_vector_identity':e['expected_vector_identity'],'compile':'compiled','runtime':'completed','completion_marker':t['completion_marker'],'rows':rows})
  return v
 def test_exact_and_within_tolerance(self):
  v=self.fixture();self.assertEqual(reconcile(v)['classification'],'PASS_EXACT');v['targets']['macd']['rows'][3]['macd']+=1e-13;self.assertEqual(reconcile(v)['classification'],'PASS_WITHIN_TOLERANCE')
 def test_identity_compile_interrupt_row_null_value_and_nonfinite_failures(self):
  for mutate,expected in ((lambda v:v.update(batch_identity='0'*64),'FAIL_IDENTITY'),(lambda v:v['targets']['macd'].update(compile='failed'),'FAIL_COMPILE'),(lambda v:v['targets']['macd'].update(runtime='interrupted'),'FAIL_INTERRUPTED'),(lambda v:v['targets']['macd'].update(rows=[]),'FAIL_ROW_ALIGNMENT'),(lambda v:v['targets']['macd']['rows'][3].update(macd=None),'FAIL_NULL_ALIGNMENT'),(lambda v:v['targets']['macd']['rows'][3].update(macd=1.0),'FAIL_VALUE_MISMATCH'),(lambda v:v['targets']['macd']['rows'][3].update(macd=float('nan')),'FAIL_CONTRACT')):
   v=self.fixture();mutate(v);self.assertEqual(reconcile(v)['classification'],expected)
 def test_atomic_immutable_evidence_publication(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);v=self.fixture();one=publish(v,p/'one.json');two=publish(v,p/'two.json');self.assertEqual(one,two);self.assertEqual((p/'one.json').read_bytes(),(p/'two.json').read_bytes())
   with self.assertRaises(ValueError):publish(v,p/'one.json')
   with self.assertRaises(RuntimeError):publish(v,p/'bad.json',True)
   self.assertFalse((p/'bad.tmp').exists());self.assertFalse((p/'bad.json').exists())
