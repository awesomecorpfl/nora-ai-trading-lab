import unittest
from lab.phase2x_batch import load
from lab.phase2y_return_contract import VERSION,validate
class ReturnContract(unittest.TestCase):
 def fixture(self):
  b=load();return {'schema_version':VERSION,'batch_identity':b['batch_identity'],'run_identifier':'synthetic','declared_target_count':2,'batch_completion_state':'completed','interrupted':False,'timeout':False,'targets':[{'target_identifier':t['id'],'rust_task_identity':t['rust_task_identity'],'rust_component_identity':t['rust_component_identity'],'expected_vector_identity':t['expected_vectors']['expected_vector_identity'],'runtime_identity':t['runtime_identity'],'tester_identity':t['tester_identity'],'package_identity':t['package_identity'],'expected_result_filename':t['result_filename'],'actual_result_filename':t['result_filename'],'references':['result.csv','journal.log','report.json']} for t in b['targets']]}
 def test_valid_two_target_contract(self):self.assertTrue(validate(self.fixture())['valid'])
 def test_schema_identity_duplicate_unknown_missing_and_path_rejected(self):
  cases=(lambda x:x.update(schema_version='bad'),lambda x:x.update(batch_identity='0'*64),lambda x:x['targets'].append(x['targets'][0]),lambda x:x['targets'].__setitem__(0,{**x['targets'][0],'target_identifier':'unknown'}),lambda x:x['targets'][0]['references'].__setitem__(0,'../escape'))
  for f in cases:
   v=self.fixture();f(v);self.assertFalse(validate(v)['valid'])
