import copy,json
from pathlib import Path
import pytest
from lab.native_targets import TEN_STRATEGY_TARGET as T
from lab.native_target import (COMPILER_LOG_REDACTION_POLICY,
 COMPILER_LOG_REDACTION_POLICY_IDENTITY, redact_compiler_log,
 validate_compiler_log_redaction)
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

def test_stale_historical_compiler_evidence_is_rejected_after_source_correction(tmp_path):
 # native_final/compile is the preserved genuine evidence compiled from the
 # defective EMA-ATR source. After the Wilder correction its compile input,
 # runtime hash, and package identities are stale and the importer must reject
 # it so the historical compilation can never be reused for acceptance.
 historical=FIX/'native_final'/'compile'
 if not historical.is_dir():return
 with pytest.raises(ValueError):import_genuine_evidence(historical,tmp_path/'rejected')

def test_compiler_envelope_rejects_runtime_hash_identity_mismatch(tmp_path):
 # A compiler record whose runtime source hash disagrees with the frozen compile
 # input must be rejected by the envelope validator (identity mismatch).
 ci=build_compile_input();record={'schema_version':T.compiler_output_schema,'target_identifier':T.target_identifier,'target_descriptor_identity':T.identity,'compile_input_identity':ci['compile_input_identity'],'runtime_sha256':'deadbeef','tester_sha256':ci['tester_sha256'],'package_identity':ci['package_identity'],'metaeditor_executable':EDITOR,'observed_metaeditor_build':BUILD,'raw_process_exit':1,'normalized_result':'success','compiler_policy':POLICY,'policy_decision':'accepted_metaeditor_5836_one','log_path':'compile.log','log_size':0,'log_sha256':raw_sha(b''),'warning_count':0,'warnings':[],'error_count':0,'errors':[],'ex5_path':T.ex5_filename,'ex5_size':0,'ex5_sha256':raw_sha(b''),'freshness_proof':{'preexisting_ex5_removed_or_isolated':True,'produced_after_invocation_start':True,'single_unambiguous_ex5':True},'completion_state':'completed','failure_reason':None}
 errors=validate_compiler_envelope(record,ci,tmp_path,T)
 assert 'runtime hash' in errors

def _redaction_fixture(tmp_path):
 user_root="C:"+"\\Users\\"+"FixtureUser"
 raw=((user_root+"\\Nora\\Tester.mq5 : information: compiling Tester.mq5\r\n")+
      "Result: 0 errors, 0 warnings, 550 ms elapsed\r\n").encode('utf-16')
 raw_path=tmp_path/'raw.log';raw_path.write_bytes(raw)
 derivative,count=redact_compiler_log(raw);path=tmp_path/'compile.redacted.log';path.write_bytes(derivative)
 record={'log_path':path.name,'log_size':len(derivative),'log_sha256':raw_sha(derivative),
  'raw_log_size':len(raw),'raw_log_sha256':raw_sha(raw),'redacted_log_size':len(derivative),
  'redacted_log_sha256':raw_sha(derivative),'redacted_path_occurrences':count,
  'redaction_policy_version':COMPILER_LOG_REDACTION_POLICY['schema_version'],
  'redaction_policy_identity':COMPILER_LOG_REDACTION_POLICY_IDENTITY,
  'redaction_placeholder':COMPILER_LOG_REDACTION_POLICY['replacement'],
  'raw_log_preservation':'external_isolated_windows_evidence'}
 return record,raw_path,path

def _rebind_derivative(record,path):
 data=path.read_bytes();record['log_size']=record['redacted_log_size']=len(data);record['log_sha256']=record['redacted_log_sha256']=raw_sha(data)

def test_valid_path_only_compiler_log_redaction_is_raw_bound(tmp_path):
 record,raw,path=_redaction_fixture(tmp_path)
 assert validate_compiler_log_redaction(record,tmp_path,raw)==[]
 text=path.read_bytes().decode('utf-16')
 assert '<WINDOWS_USER_PATH>\\Nora\\Tester.mq5' in text
 assert ("C:"+"\\Users\\") not in text
 assert record['raw_log_sha256']!=record['redacted_log_sha256']

@pytest.mark.parametrize('field,reason', [('raw_log_sha256','raw log hash'),('raw_log_size','raw log size')])
def test_compiler_log_redaction_rejects_raw_binding_mismatch(tmp_path,field,reason):
 record,raw,_=_redaction_fixture(tmp_path);record[field]='0'*64 if 'sha' in field else record[field]+1
 assert reason in validate_compiler_log_redaction(record,tmp_path,raw)

def test_compiler_log_redaction_rejects_derivative_mismatch(tmp_path):
 record,raw,path=_redaction_fixture(tmp_path);path.write_bytes(path.read_bytes()+b'x')
 assert validate_compiler_log_redaction(record,tmp_path,raw)

@pytest.mark.parametrize('old,new', [('0 errors','1 errors'),('0 warnings','notices'),('information','<REDACTED>')])
def test_compiler_log_redaction_rejects_diagnostic_removal_or_extra_redaction(tmp_path,old,new):
 record,raw,path=_redaction_fixture(tmp_path);text=path.read_bytes().decode('utf-16').replace(old,new);path.write_bytes(text.encode('utf-16'));_rebind_derivative(record,path)
 errors=validate_compiler_log_redaction(record,tmp_path,raw)
 assert 'redacted log regeneration' in errors

def test_compiler_log_redaction_rejects_missing_raw_log(tmp_path):
 record,_,_=_redaction_fixture(tmp_path)
 assert 'missing raw log' in validate_compiler_log_redaction(record,tmp_path,tmp_path/'missing.log')

def test_corrected_genuine_compiler_packet_is_raw_bound_and_sealed():
 final=FIX/'native_corrected_final';record=load(final/'compile/compiler_record.json')
 packet=load(final/'execution_packet.json');batch=load(final/'final_batch.json')
 assert record['synthetic_protocol_fixture'] is False
 assert record['raw_log_sha256']=='f2f5a3be43c66736db98e3a161ac74849a301a9ecd4bfc818dc9137a3dbbe62f'
 assert record['raw_log_size']==3698 and record['redaction_policy_identity']==COMPILER_LOG_REDACTION_POLICY_IDENTITY
 assert record['compiler_output_identity']==compiler_output_identity(record)=='87a48eb8bf0297b46e438f7f5f692dde7b918a66eeca530f384bd6fc6fabfe26'
 assert packet['execution_packet_identity']=='1cb34d101d83bf1811d8b78a116740e6d2586cb7f598b50cb90b56a3833549c4'
 assert batch['final_batch_identity']=='cf9e9fd19c9fb19ea50be7094bd5eaa706288486186e7bf1ca7fb6c04f1b3018'
 assert packet['raw_compiler_log_sha256']==batch['raw_compiler_log_sha256']==record['raw_log_sha256']
 assert file_sha(final/'compile'/T.ex5_filename)==record['ex5_sha256']=='fd736e5b7a4984e1fd703f881cbe0fed5baaec9b98a7cc4abcecbfb875cd116d'
 text=(final/'compile/compile.redacted.log').read_bytes().decode('utf-16')
 assert '<WINDOWS_USER_PATH>' in text and ("C:"+"\\Users\\") not in text
 assert 'Result: 0 errors, 0 warnings' in text
 assert not batch['native_execution_attempted'] and not batch['native_parity_accepted'] and not batch['searchable']
