import json,unittest
from pathlib import Path
from lab.phase2_execution import SCENARIOS,SCHEMA,PRECEDENCE,evidence,plan_identity,scenario_identity

ROOT=Path(__file__).resolve().parents[1]; BINARY=ROOT/'engine/target/debug/labengine'; COMMITTED=ROOT/'tests/fixtures/phase2_execution_rust_evidence.json'
class ExecutionRustEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.value=evidence(BINARY)
 def test_all_scenarios_run_through_real_cli(self):
  self.assertEqual(self.value['scenario_order'],[s['id'] for s in SCENARIOS]);self.assertEqual(len(self.value['scenarios']),12)
  self.assertEqual(self.value['execution_plan_identity'],plan_identity())
  self.assertEqual(self.value['execution_csv_schema'],SCHEMA);self.assertEqual(self.value['precedence_contract'],PRECEDENCE)
  self.assertEqual(self.value,json.loads(COMMITTED.read_text()))
 def test_expected_fixed_outcomes(self):
  actual={x['scenario_id']:x for x in self.value['scenarios']}
  self.assertEqual(actual['gap_stop_over_signal_time']['exit_reason'],'initial_stop_gap')
  self.assertEqual(actual['signal_over_time_intrabar']['exit_reason'],'signal')
  self.assertEqual(actual['time_over_intrabar']['exit_reason'],'max_bars_held')
  self.assertTrue(actual['entry_row_excluded_terminal']['expected_null_no_trade'])
 def test_identity_mutations_fail_closed(self):
  original=SCENARIOS[0]; baseline=scenario_identity(original)
  for field,value in [('bars',[[99,99,99]]),('entry',[True]),('exit',[True]),('stop_offset',2.),('target_offset',3.),('time_exit',1),('expected_reason','initial_stop')]:
   changed=dict(original);changed[field]=value;self.assertNotEqual(scenario_identity(changed),baseline,field)
  self.assertNotEqual(plan_identity(),__import__('lab.phase2_execution',fromlist=['sha']).sha({'precedence':['signal','gap','time','intrabar']}))
