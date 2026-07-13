"""Strict local returned-result reconciliation for the execution canary."""
import json
from pathlib import Path
from lab.phase2_execution import SCHEMA,PRECEDENCE,sha
REQUIRED={"compile.json","execution.json","compile.log","tester-journal.log","tester.htm","nora_phase2_execution_tester_v1.csv"}
def reconcile(rows,expected):
 if len(rows)!=len(expected): return 'ledger_row_count'
 seen=[]
 for actual,want in zip(rows,expected):
  for key in ('scenario_id','ledger_row_index','entry_bar_index','exit_bar_index','direction','exit_reason','expected_state','pass'):
   if actual.get(key)!=want.get(key): return key
  for key in ('entry_price','exit_price','stop_price','target_price'):
   if actual.get(key)!=want.get(key): return key
  seen.append(actual['scenario_id'])
 return 'ok' if len(seen)==len(set(seen)) else 'duplicate_scenario'
def preflight(package):
 required={'target_identifier','execution_plan_identity','runtime_identity','tester_identity','package_identity','expected_execution_vector_identity','execution_csv_schema_identity','precedence_contract','native_execution_attempted','native_parity_accepted','grammar_admitted','searchable'}
 if set(package)<required:return 'missing_binding'
 if package['target_identifier']!='execution' or package['precedence_contract']!=PRECEDENCE:return 'contract_failure'
 if any(package[x] for x in ('native_execution_attempted','native_parity_accepted','grammar_admitted','searchable')):return 'state_failure'
 return 'ok'
