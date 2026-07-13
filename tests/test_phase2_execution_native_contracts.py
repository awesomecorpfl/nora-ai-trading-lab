import unittest
from pathlib import Path
from lab.mql5gen.execution import generate
from lab.phase2_execution_native import REQUIRED,preflight,reconcile
from lab.phase2_execution import SCHEMA
ROOT=Path(__file__).resolve().parents[1]
class ExecutionNativeContracts(unittest.TestCase):
 def test_scripts_are_target_specific_and_no_deployment(self):
  paths=[ROOT/'phase-0a-h/windows'/x for x in ('compile-execution-tester-canary.ps1','execute-execution-tester-canary.ps1','build-execution-returned-package.ps1')]
  text='\n'.join(x.read_text().lower() for x in paths)
  self.assertIn('execution',text);self.assertNotIn('ordersend',text);self.assertNotIn('macd',text);self.assertNotIn('percentile',text)
 def test_preflight_and_exact_ledger_reconciliation(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   p=generate(ROOT/'tests/fixtures/phase2_execution_rust_evidence.json',d);p['target_identifier']='execution';self.assertEqual(preflight(p),'ok')
   row={'scenario_id':'a','ledger_row_index':0,'entry_bar_index':0,'entry_price':1.,'exit_bar_index':1,'exit_price':2.,'direction':'long','stop_price':0.,'target_price':3.,'exit_reason':'signal','expected_state':'trade','pass':'true'}
   self.assertEqual(reconcile([row],[dict(row)]),'ok');bad=dict(row);bad['exit_reason']='initial_target';self.assertEqual(reconcile([bad],[row]),'exit_reason')
   p['native_execution_attempted']=True;self.assertEqual(preflight(p),'state_failure')
