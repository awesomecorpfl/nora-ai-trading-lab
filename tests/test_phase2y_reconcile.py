import json,tempfile,unittest
from pathlib import Path
from lab.phase2x_batch import manifest
from lab.phase2y_reconcile import reconcile
class Reconcile(unittest.TestCase):
 def _fixture(self,path,**changes):
  batch=manifest();value={'batch_identity':batch['batch_identity'],'targets':{}}
  for target in batch['targets']:value['targets'][target['id']]={'target_identity':target['package_identity'],'compile':'compiled','runtime':'completed','completion_marker':target['completion_marker'],'rows':[{'row':i,'values':[0.0]} for i in range(target['expected_vectors']['row_count'])]}
  value.update(changes);(path/'result.json').write_text(json.dumps(value));return value
 def test_exact_synthetic_protocol_match(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self._fixture(p);r=reconcile(p);self.assertEqual(r['classification'],'PASS_EXACT');self.assertTrue(r['synthetic_protocol_fixture']);self.assertFalse(r['native_parity_updated'])
 def test_identity_compile_runtime_row_and_nonfinite_failures(self):
  cases=(('identity',lambda x:x.update(batch_identity='0'*64),'FAIL_IDENTITY'),('compile',lambda x:x['targets']['macd'].update(compile='failed'),'FAIL_COMPILE'),('runtime',lambda x:x['targets']['macd'].update(runtime='interrupted'),'FAIL_INTERRUPTED'),('row',lambda x:x['targets']['macd'].update(rows=[]),'FAIL_ROW_ALIGNMENT'),('nan',lambda x:x['targets']['macd']['rows'][0].update(values=[float('nan')]),'FAIL_CONTRACT'))
  for _,mut,expected in cases:
   with tempfile.TemporaryDirectory() as d:
    p=Path(d);value=self._fixture(p);mut(value);(p/'result.json').write_text(json.dumps(value));self.assertEqual(reconcile(p)['classification'],expected)
