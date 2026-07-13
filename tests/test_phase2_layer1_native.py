import copy,json
from pathlib import Path
import pytest

from lab.native_target import compiler_output_identity,file_sha,manifest_identity
from lab.native_targets import LAYER1_BATCH_TARGET as T
from lab.phase2_execution import canon
from lab.phase2_layer1_native import *

def test_frozen_compile_precompile_descriptor_and_readiness_are_current():
 assert load(FIX/'target_descriptor.json')['target_descriptor_identity']==T.identity
 assert load(FIX/'compile_input.json')==build_compile_input();assert load(MANIFEST)==build_precompile();assert preflight()['status']=='PASS'
 readiness=load(READINESS);assert readiness==local_readiness() and readiness['synthetic_protocol_fixture_only']
 assert not readiness['genuine_native_compiler_evidence'] and not readiness['native_execution_attempted'] and not readiness['native_parity_accepted'] and not readiness['searchable']

def test_preflight_rejects_every_bound_mutation_and_state_change():
 base=build_precompile()
 mutations=[('selected_node_identities','wrong'),('scenario_identities',{}),('expected_vector_identity','0'*64),('reference_modes',{}),('parity_protocol_identity','0'*64),('native_parity_accepted',True),('native_execution_attempted',True),('searchable',True),('grammar_admitted',True)]
 for key,value in mutations:
  changed=copy.deepcopy(base);changed[key]=value;assert preflight(changed)['status']=='FAIL'

def test_two_directory_staging_is_deterministic(tmp_path):
 a=stage(tmp_path/'a');b=stage(tmp_path/'b');assert a==b
 for left in (tmp_path/'a').rglob('*'):
  if left.is_file():assert left.read_bytes()==(tmp_path/'b'/left.relative_to(tmp_path/'a')).read_bytes()

def test_two_directory_final_staging_is_deterministic(tmp_path):
 create_synthetic_compiler_evidence(tmp_path/'e');import_evidence(tmp_path/'e',tmp_path/'final')
 assert stage_final(tmp_path/'final',tmp_path/'a')==stage_final(tmp_path/'final',tmp_path/'b')
 for left in (tmp_path/'a').rglob('*'):
  if left.is_file():assert left.read_bytes()==(tmp_path/'b'/left.relative_to(tmp_path/'a')).read_bytes()

def test_synthetic_compiler_import_atomic_chain_and_cross_target_rejection(tmp_path):
 create_synthetic_compiler_evidence(tmp_path/'e');a=import_evidence(tmp_path/'e',tmp_path/'a');b=import_evidence(tmp_path/'e',tmp_path/'b');assert a==b
 with pytest.raises(ValueError):import_evidence(tmp_path/'e',tmp_path/'a')
 with pytest.raises(RuntimeError):import_evidence(tmp_path/'e',tmp_path/'interrupted',inject_failure=True)
 assert not (tmp_path/'interrupted').exists()
 for target in ('time_rules','execution','macd','percentile'):
  bad=tmp_path/target;create_synthetic_compiler_evidence(bad);record=load(bad/'compiler_record.json');record['target_identifier']=target;record['compiler_output_identity']=compiler_output_identity(record);(bad/'compiler_record.json').write_text(canon(record)+'\n')
  with pytest.raises(ValueError):import_evidence(bad,tmp_path/(target+'-out'))
 failed=tmp_path/'failed';create_synthetic_compiler_evidence(failed,failure=True)
 with pytest.raises(ValueError):import_evidence(failed,tmp_path/'failed-out')

def test_exact_and_explicit_test_budget_reconciliation():
 rows=expected_rows();assert reconcile_rows(rows)['classification']=='PASS_EXACT'
 changed=copy.deepcopy(rows);next(x for x in changed if x['value'] is not None)['value']+=1e-13
 budget={x:{'value':{'absolute':1e-12,'relative':0.0,'ulp':2**64}} for x in ('EMA','Highest','Lowest')}
 assert reconcile_rows(changed,budget)['classification']=='PASS_WITHIN_TEST_BUDGET'
 with pytest.raises(ValueError,match='BUDGET'):reconcile_rows(changed)
 with pytest.raises(ValueError,match='BUDGET'):reconcile_rows(changed,{x:{'value':{'absolute':1e-15,'relative':0.0,'ulp':1}} for x in ('EMA','Highest','Lowest')})

def test_exact_contract_failures_cover_rows_null_warmup_order_and_reasons():
 rows=expected_rows()
 for changed in (rows[:-1],rows+[rows[-1]],rows[:1]+rows[:1]+rows[1:]):
  with pytest.raises(ValueError):reconcile_rows(changed)
 for key,value in (('timestamp','wrong'),('null',True),('classification','wrong'),('reason_code','wrong'),('node','MACD'),('output','wrong')):
  changed=copy.deepcopy(rows);changed[3][key]=value
  with pytest.raises(ValueError):reconcile_rows(changed)
 changed=copy.deepcopy(rows);changed[0],changed[1]=changed[1],changed[0]
 with pytest.raises(ValueError):reconcile_rows(changed)

def _refresh_returned(root):
 inv=load(root/'returned_inventory.json')
 for item in inv:
  p=root/item['path'];item['size']=p.stat().st_size;item['sha256']=file_sha(p)
 (root/'returned_inventory.json').write_text(canon(inv)+'\n');m=load(root/'returned_result_manifest.json');m['returned_inventory_sha256']=file_sha(root/'returned_inventory.json');m['returned_package_identity']=manifest_identity(m,'returned_package_identity');(root/'returned_result_manifest.json').write_text(canon(m)+'\n')

def test_returned_package_exact_numeric_marker_and_cross_target_paths(tmp_path):
 create_synthetic_compiler_evidence(tmp_path/'e');import_evidence(tmp_path/'e',tmp_path/'final');packet=load(tmp_path/'final/execution_packet.json');batch=load(tmp_path/'final/final_batch.json')
 build_synthetic_returned(tmp_path/'exact',tmp_path/'final');assert ingest(tmp_path/'exact',packet,batch,'A1','GDAXI')['classification']=='PASS_EXACT'
 build_synthetic_returned(tmp_path/'numeric',tmp_path/'final',delta=1e-13);budget={x:{'value':{'absolute':1e-12,'relative':0.0,'ulp':2**64}} for x in ('EMA','Highest','Lowest')};assert ingest(tmp_path/'numeric',packet,batch,'A1','GDAXI',budget)['classification']=='PASS_WITHIN_TEST_BUDGET'
 build_synthetic_returned(tmp_path/'marker',tmp_path/'final');(tmp_path/'marker/completion-marker.json').write_text(canon({'marker':T.completion_marker,'present':False})+'\n');_refresh_returned(tmp_path/'marker')
 with pytest.raises(ValueError):ingest(tmp_path/'marker',packet,batch,'A1','GDAXI')
 build_synthetic_returned(tmp_path/'cross',tmp_path/'final');record=load(tmp_path/'cross/execution.json');record['target_identifier']='execution';(tmp_path/'cross/execution.json').write_text(canon(record)+'\n');_refresh_returned(tmp_path/'cross')
 with pytest.raises(ValueError):ingest(tmp_path/'cross',packet,batch,'A1','GDAXI')
