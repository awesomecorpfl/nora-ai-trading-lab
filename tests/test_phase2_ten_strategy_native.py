import copy,json
from pathlib import Path
import pytest
from lab.native_targets import TEN_STRATEGY_TARGET as T
from lab.phase2_ten_strategy import FIX,strategy_suite
from lab.phase2_ten_strategy_native import *

def test_frozen_target_compile_precompile_and_readiness_are_current():
 assert load(FIX/'target_descriptor.json')['target_descriptor_identity']==T.identity
 assert load(FIX/'compile_input.json')==build_compile_input()
 assert load(MANIFEST)==build_precompile() and preflight()['status']=='PASS'
 state=load(READINESS);assert state==local_readiness()
 assert state['precompile_ready'] and state['compile_evidence_pending'] and not state['compile_evidence_imported']
 assert not state['final_packet_ready'] and not state['native_execution_attempted'] and not state['native_parity_accepted']
 assert not state['grammar_admitted'] and not state['searchable'] and not state['complete_phase2_gate'] and not state['production_data_required']

def test_exact_ten_five_per_family_and_accepted_dependencies():
 suite=strategy_suite();assert len(suite['strategies'])==10
 assert sum(x['family']=='trend-pullback' for x in suite['strategies'])==5 and sum(x['family']=='close-confirmed breakout' for x in suite['strategies'])==5
 assert all(not x['searchable'] and not x['grammar_admitted'] for x in suite['strategies'])

def test_deterministic_generation_and_staging(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';assert stage(a)==stage(b)
 for p in a.rglob('*'):
  if p.is_file():assert p.read_bytes()==(b/p.relative_to(a)).read_bytes()

def test_synthetic_compiler_packet_batch_chain_and_failures(tmp_path):
 create_synthetic_compiler_evidence(tmp_path/'compile');ids=import_evidence(tmp_path/'compile',tmp_path/'final')
 assert set(ids)=={'synthetic_compiler_output_identity','synthetic_execution_packet_identity','synthetic_final_batch_identity'}
 with pytest.raises(ValueError):import_evidence(tmp_path/'compile',tmp_path/'final')
 create_synthetic_compiler_evidence(tmp_path/'bad',failure=True)
 with pytest.raises(ValueError,match='COMPILER_FAILURE'):import_evidence(tmp_path/'bad',tmp_path/'bad-final')
 create_synthetic_compiler_evidence(tmp_path/'interrupt')
 with pytest.raises(RuntimeError):import_evidence(tmp_path/'interrupt',tmp_path/'interrupted',inject_failure=True)
 assert not (tmp_path/'interrupted').exists()
 record=load(tmp_path/'compile/compiler_record.json');record['target_identifier']='layer1_first_batch';(tmp_path/'compile/compiler_record.json').write_text(json.dumps(record))
 with pytest.raises(ValueError):import_evidence(tmp_path/'compile',tmp_path/'cross')

def test_exact_reconciliation_and_all_structural_failure_classes():
 rows=expected_rows();assert reconcile_rows(rows)['classification']=='PASS_EXACT'
 for changed in (rows[:-1],rows+[rows[-1]],rows[:1]+rows[:1]+rows[1:],list(reversed(rows))):
  with pytest.raises(ValueError):reconcile_rows(changed)
 mutations=[('strategy_identity','wrong'),('direction','short' if rows[0]['direction']=='long' else 'long'),('entry_index',999),('exit_index',999),('exit_reason','friday_close'),('signal_index',999),('terminal_source_disposition','executed')]
 for key,value in mutations:
  changed=copy.deepcopy(rows);changed[0][key]=value
  with pytest.raises(ValueError):reconcile_rows(changed)
 changed=copy.deepcopy(rows);row=next(x for x in changed if x['entry_price'] is not None);row['entry_price']+=1e-9
 with pytest.raises(ValueError,match='NUMERIC'):reconcile_rows(changed)

def test_budget_map_is_exact_scoped_and_does_not_invent_atr_tolerance():
 value=budget_map();assert not value['broad_tolerance_created'] and value['atr_distance_numeric_emission'].startswith('not_emitted')
 assert all(x['kind']=='exact_zero' and x['absolute']==0 and x['ulp']==0 for x in value['fields'].values())

def test_returned_publication_is_atomic_and_marker_vocabulary_is_bound(tmp_path):
 rec=build_synthetic_returned(tmp_path/'returned');assert rec['classification']=='PASS_EXACT'
 assert load(tmp_path/'returned/completion-marker.json')=={'marker':T.completion_marker,'present':True}
 assert load(tmp_path/'returned/failure-marker.json')=={'marker':T.failure_marker,'present':False}

def test_preflight_rejects_suite_strategy_contract_and_state_mutations():
 base=build_precompile()
 for key,value in [('suite_identity','wrong'),('strategy_identities',[]),('target_descriptor_identity','wrong'),('native_execution_attempted',True),('native_parity_accepted',True),('searchable',True),('grammar_admitted',True)]:
  changed=copy.deepcopy(base);changed[key]=value;assert preflight(changed)['status']=='FAIL'
