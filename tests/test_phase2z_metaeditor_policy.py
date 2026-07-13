import unittest
from lab.phase2z_metaeditor_policy import evaluate
class MetaEditorPolicy(unittest.TestCase):
 def record(self,**changes):
  value={"exit":1,"metaeditor_version":"5.0.0.5836","checks":{k:True for k in ("version","source","log_complete","zero_errors","zero_warnings","fresh_ex5","expected_ex5_path","hashes_match")}};value.update(changes);return value
 def test_exit_one_clean_fresh_is_accepted(self):self.assertEqual(evaluate(self.record()),(True,"accepted_metaeditor_5836_one"))
 def test_exit_one_failure_matrix(self):
  for key in ("zero_errors","zero_warnings","fresh_ex5","expected_ex5_path","log_complete","source","hashes_match"):
   r=self.record();r["checks"][key]=False;self.assertFalse(evaluate(r)[0],key)
 def test_unexpected_exit_and_contradiction_fail(self):
  self.assertFalse(evaluate(self.record(exit=2))[0]);r=self.record();r["checks"]["zero_errors"]=False;self.assertFalse(evaluate(r)[0])
