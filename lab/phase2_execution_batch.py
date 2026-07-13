"""Execution target preflight and synthetic returned-package failure taxonomy."""
import json
from pathlib import Path
from lab.phase2_execution_native import preflight
FAILURES=['wrong_entry_bar','wrong_entry_price','wrong_exit_bar','wrong_exit_price','wrong_exit_reason','precedence_failure','ambiguous_bar_optimism','same_bar_entry_exit','missing_ledger_row','extra_ledger_row','duplicate_scenario','scenario_reordering','incomplete_result','compiler_failure','runtime_failure','interrupted_result','identity_failure','contract_failure']
def load(path='tests/fixtures/phase2x_native_batch_v4.json'):return json.loads(Path(path).read_text())
def preflight_batch(value):
 e=value['execution']
 if not all(k in e for k in ('execution_plan_identity','runtime_identity','tester_identity','package_identity','expected_execution_vector_identity','execution_csv_schema_identity')): return 'contract_failure'
 if e['native_execution_attempted'] or e['native_parity_accepted'] or e['grammar_admitted'] or e['searchable']:return 'state_failure'
 if e['host_contexts']!=['GDAXI/M1','AUDCAD/M1'] or len(e['required_native_matrix'])!=5:return 'matrix_failure'
 return 'ok'
def classify_synthetic(kind): return kind if kind in FAILURES else 'exact_pass'
