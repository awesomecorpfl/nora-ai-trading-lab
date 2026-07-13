import copy,csv,json,tempfile
from pathlib import Path
import pytest
from lab.phase2_execution import canon
from lab.native_target import BUILD,EDITOR,POLICY,compiler_output_identity,raw_sha
from lab.native_targets import TIME_RULE_TARGET as T
from lab.phase2_time_native import *

def synthetic(root):
 ci=build_compile_input();log=b'time compile\nResult: 0 errors, 0 warnings\n';ex5=b'synthetic-time-rule-ex5-not-native'
 (root/'compile.log').write_bytes(log);(root/T.ex5_filename).write_bytes(ex5)
 r={"schema_version":T.compiler_output_schema,"target_identifier":"time_rules","target_descriptor_identity":T.identity,"compile_input_identity":ci['compile_input_identity'],"runtime_sha256":ci['runtime_sha256'],"tester_sha256":ci['tester_sha256'],"package_identity":ci['package_identity'],"metaeditor_executable":EDITOR,"observed_metaeditor_build":BUILD,"exact_command":"synthetic","invocation_start_utc":"2040-01-01T00:00:00Z","invocation_completion_utc":"2040-01-01T00:00:01Z","raw_process_exit":1,"normalized_result":"success","compiler_policy":POLICY,"policy_decision":"accepted_metaeditor_5836_one","log_path":"compile.log","log_size":len(log),"log_sha256":raw_sha(log),"warning_count":0,"warnings":[],"error_count":0,"errors":[],"ex5_path":T.ex5_filename,"ex5_size":len(ex5),"ex5_modification_utc":"2040-01-01T00:00:01Z","ex5_sha256":raw_sha(ex5),"stale_ex5_disposition":"none_present","freshness_proof":{"preexisting_ex5_removed_or_isolated":True,"produced_after_invocation_start":True,"single_unambiguous_ex5":True},"completion_state":"completed","failure_reason":None};r['compiler_output_identity']=compiler_output_identity(r)
 (root/'compiler_record.json').write_text(canon(r)+'\n');(root/'compile_evidence_manifest.json').write_text(canon({"schema_version":T.compile_evidence_schema,"target_identifier":"time_rules","target_descriptor_identity":T.identity,"compile_input_identity":ci['compile_input_identity']})+'\n')
 inv=[{"path":p,"role":role,"sha256":raw_sha((root/p).read_bytes())} for p,role in (("compiler_record.json","compiler_record"),("compile.log","compiler_log"),(T.ex5_filename,"ex5"),("compile_evidence_manifest.json","compile_evidence_manifest"))];(root/'inventory.json').write_text(canon(inv)+'\n');return r

def test_compile_input_is_frozen_acyclic_and_mutation_sensitive():
 x=build_compile_input();assert x==build_compile_input();assert T.identity==x['target_descriptor_identity']
 for forbidden in ('ex5_sha256','compiler_output_identity','final_batch_identity'):assert forbidden not in x
 for k in x:
  if k=='compile_input_identity':continue
  y=copy.deepcopy(x);y[k]=str(y[k])+'x';y.pop('compile_input_identity');assert sha(y)!=x['compile_input_identity']

def test_synthetic_import_is_typed_atomic_and_deterministic(tmp_path):
 e=tmp_path/'e';create_synthetic_compiler_evidence(e);a=import_evidence(e,tmp_path/'a');b=import_evidence(e,tmp_path/'b');assert a==b
 assert not json.loads((tmp_path/'a/final_batch.json').read_text())['native_execution_attempted']
 with pytest.raises(ValueError):import_evidence(e,tmp_path/'a')
 with pytest.raises(RuntimeError):import_evidence(e,tmp_path/'interrupted',inject_failure=True)
 assert not (tmp_path/'interrupted').exists()
 packets=[]
 for run,symbol in (("A1","GDAXI"),("A2","GDAXI"),("B1","AUDCAD"),("B2","AUDCAD")):
  build_synthetic_returned(tmp_path/run,tmp_path/'a',run,symbol);packets.append(ingest(tmp_path/run,load_json(tmp_path/'a/execution_packet.json'),load_json(tmp_path/'a/final_batch.json'),run,symbol))
 assert {x['classification'] for x in packets}=={'PASS_EXACT'}
 assert len({x['returned_package_identity'] for x in packets})==4
 assert len({x['execution_record_identity'] for x in packets})==4
 assert len({x['journal_identity'] for x in packets})==4
 assert len({x['semantic_time_rule_identity'] for x in packets})==1
 x=stage_final(tmp_path/'a',tmp_path/'final-a');y=stage_final(tmp_path/'b',tmp_path/'final-b');assert x==y
 assert (tmp_path/'final-a'/TARGET.execution_script).is_file()

def test_importer_accepts_only_the_declared_windows_ordered_manifest_form(tmp_path):
 e=tmp_path/'e';create_synthetic_compiler_evidence(e);import_evidence(e,tmp_path/'final')
 build_synthetic_returned(tmp_path/'run',tmp_path/'final','A1','GDAXI')
 packet=load_json(tmp_path/'final/execution_packet.json');batch=load_json(tmp_path/'final/final_batch.json')
 manifest=load_json(tmp_path/'run/returned_result_manifest.json');value=dict(manifest);value.pop('returned_package_identity');manifest['returned_package_identity']=raw_sha(json.dumps(value,separators=(',',':'),ensure_ascii=False).encode());(tmp_path/'run/returned_result_manifest.json').write_text(json.dumps(manifest,separators=(',',':')))
 assert ingest(tmp_path/'run',packet,batch,'A1','GDAXI')['classification']=='PASS_EXACT'

def test_import_rejects_cross_target_warnings_stale_hash_and_paths(tmp_path):
 for name,mutate in [('target',lambda r:r.update(target_identifier='execution')),('warning',lambda r:r.update(warning_count=1,warnings=['w'])),('fresh',lambda r:r.update(freshness_proof={})),('hash',lambda r:r.update(ex5_sha256='0'*64)),('path',lambda r:r.update(log_path='../x'))]:
  e=tmp_path/name;e.mkdir();r=synthetic(e);mutate(r);r['compiler_output_identity']=compiler_output_identity(r);(e/'compiler_record.json').write_text(canon(r)+'\n')
  with pytest.raises(ValueError):import_evidence(e,tmp_path/(name+'-out'))

def test_exact_reconciliation_and_named_failures(tmp_path):
 e=json.loads(EVIDENCE.read_text());rows=[]
 for x in e['expected_vectors']: rows.append({**x,'pass':'true'})
 assert reconcile_rows(rows)['classification']=='PASS_EXACT'
 for field in ('utc_offset_seconds','new_york','broker','dst','friday_close','rollover','monday_delay','orb','m5_anchor_epoch','h1_anchor_epoch','conversion_state','reason_code'):
  bad=copy.deepcopy(rows);bad[0][field]='changed'
  with pytest.raises(ValueError):reconcile_rows(bad)
 assert set(FAILURES)=={classify_failure(x) for x in FAILURES}

def test_precompile_generation_staging_and_scripts_are_safe(tmp_path):
 value=build_precompile();assert value['compile_evidence_pending'] and not value['native_execution_attempted'] and not value['native_parity_accepted']
 assert value['clock_contract_identities']['dataset']=='902f8a4aef17ee6abfe899a4017dfd751f0c1aa3c4f78aca070121e9f6540c6a'
 for p in SCRIPTS:
  text=p.read_text();assert 'time_rules' in text or 'TimeRule' in text
 for forbidden in ('TimeCurrent','TimeTradeServer','CopyRates','OrderSend','CTrade','MathRand'):assert forbidden not in (MQL5/RUNTIME).read_text()+(MQL5/TESTER).read_text()
 if MANIFEST.exists():
  assert preflight()['status']=='PASS';a=stage(tmp_path/'a');b=stage(tmp_path/'b');assert a==b
  for left in (tmp_path/'a').rglob('*'):
   if left.is_file():assert left.read_bytes()==(tmp_path/'b'/left.relative_to(tmp_path/'a')).read_bytes()
 readiness=local_readiness_evidence();assert readiness['synthetic_protocol_fixture_only'] and not readiness['genuine_native_compiler_evidence'] and not readiness['native_parity_accepted']

def test_native_acceptance_stays_narrow_when_raw_evidence_is_committed():
 p=Path(__file__).resolve().parents[1]/'tests/fixtures/phase2_time_rule_native_accepted/native_acceptance.json'
 assert p.is_file()
 value=json.loads(p.read_text())
 assert value['native_parity_accepted']
 assert not value['grammar_admitted']
 assert not value['searchable']
 assert not value['complete_phase2_gate']
