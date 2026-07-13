import copy,json,unittest
from pathlib import Path
from lab.mql5gen.execution import resolver_inputs,generate,TESTER

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=json.loads((ROOT/'tests/fixtures/phase2_execution_rust_evidence.json').read_text())
def resolve(q):
 if q is None:return 'no_trade'
 if q['gap_stop']:return 'initial_stop_gap'
 if q['gap_target']:return 'initial_target_gap'
 if q['signal']:return 'signal'
 if q['time_due']:return 'max_bars_held'
 if q['stop_touch'] and q['target_touch']:return 'initial_stop_pessimistic'
 if q['stop_touch']:return 'initial_stop'
 if q['target_touch']:return 'initial_target'
 return 'no_trade'
class DecisionInputs(unittest.TestCase):
 def test_all_frozen_decisions_and_order(self):
  self.assertEqual([x['scenario_id'] for x in EVIDENCE['scenarios']],['completed_next_open','entry_row_excluded_terminal','gap_stop_over_signal_time','gap_target','signal_over_time_intrabar','time_over_intrabar','pessimistic_dual_touch','nonambiguous_stop','nonambiguous_target','signal_exit','time_exit','terminal_no_trade'])
  for r in EVIDENCE['scenarios']:self.assertEqual(resolve(resolver_inputs(r)),r['exit_reason'])
 def test_expected_outputs_are_not_inputs(self):
  r=copy.deepcopy(EVIDENCE['scenarios'][2]);base=resolver_inputs(r)
  r['task_fixture']['expected_reason']='initial_target';r['task_fixture']['expected']['exit_price']=999.;self.assertEqual(resolver_inputs(r),base)
 def test_geometry_vectors_and_simultaneity(self):
  x={r['scenario_id']:resolver_inputs(r) for r in EVIDENCE['scenarios']}
  self.assertTrue(x['gap_stop_over_signal_time']['gap_stop'] and x['gap_stop_over_signal_time']['signal'] and x['gap_stop_over_signal_time']['time_due'])
  self.assertTrue(x['gap_target']['gap_target']);self.assertTrue(x['signal_over_time_intrabar']['signal'] and x['signal_over_time_intrabar']['time_due'] and x['signal_over_time_intrabar']['stop_touch'] and x['signal_over_time_intrabar']['target_touch'])
  self.assertTrue(x['pessimistic_dual_touch']['stop_touch'] and x['pessimistic_dual_touch']['target_touch']);self.assertTrue(x['nonambiguous_stop']['stop_touch'] and not x['nonambiguous_stop']['target_touch']);self.assertTrue(x['nonambiguous_target']['target_touch'] and not x['nonambiguous_target']['stop_touch'])
 def test_generated_call_has_no_expected_field_arguments(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   generate(ROOT/'tests/fixtures/phase2_execution_rust_evidence.json',d);src=(Path(d)/TESTER).read_text()
   self.assertNotIn('e.reason==',src);self.assertNotIn('e.exit_price,e.exit_price',src);self.assertIn('NoraExecutionResolveV1(10,0,8.5,10,8,true,false,true,true,true,false)',src)
