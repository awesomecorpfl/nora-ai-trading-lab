"""Local native-contract support for the fixed Phase-2 time-rule canary."""
from __future__ import annotations
import argparse,csv,json,shutil,tempfile
from datetime import datetime
from pathlib import Path
from lab.mql5gen.time_rules import generate,RUNTIME,TESTER,PACKAGE,CSV,SCHEMA
from lab.native_target import (BUILD,EDITOR,POLICY,DEPENDENCY_GRAPH,atomic_publish,
 compiler_output_identity,file_sha,identified,inventory_identity,raw_sha,safe_relative,
 validate_compiler_envelope,validate_dependency_graph,manifest_identity)
from lab.native_targets import TIME_RULE_TARGET as TARGET
from lab.phase2_execution import canon,sha

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'tests/fixtures/phase2_time_rule_rust_evidence.json'
CONTRACTS=ROOT/'tests/fixtures/phase2_time_rule_contracts.json'
MQL5=ROOT/'tests/fixtures/phase2_time_rule_mql5'
MANIFEST=ROOT/'tests/fixtures/phase2_time_rule_precompile_batch.json'
SCRIPTS=tuple(ROOT/x for x in (TARGET.compiler_script,TARGET.execution_script,TARGET.collection_script))
FAILURES=("wrong_winter_offset","wrong_summer_offset","spring_transition_error","autumn_fold_collapse","friday_cutoff_error","rollover_boundary_error","monday_boundary_error","orb_boundary_error","m5_anchor_error","h1_anchor_error","double_conversion","source_clock_mismatch","missing_row","extra_row","duplicate_row","scenario_reordering","wrong_reason_code","marker_failure","identity_failure","compiler_failure","interrupted_package")
REQUIRED=("compile.json","execution.json","compile.log","tester-journal.log","tester.htm","completion-marker.json","failure-marker.json",CSV)

def generated_sources():
 with tempfile.TemporaryDirectory(dir=ROOT) as d:
  out=Path(d)/'g';out.mkdir();p=generate(EVIDENCE,out)
  return p,{n:(out/n).read_bytes() for n in (RUNTIME,TESTER,PACKAGE)}

def frozen():
 e=json.loads(EVIDENCE.read_text());c=json.loads(CONTRACTS.read_text());p,_=generated_sources()
 return e,c,p

def build_compile_input():
 e,c,p=frozen();_,files=generated_sources();script_sha=file_sha(SCRIPTS[0])
 value={"schema_version":TARGET.compile_input_schema,"target_identifier":TARGET.target_identifier,"target_descriptor_identity":TARGET.identity,
  "clock_contract_identities":{"dataset":c['dataset']['dataset_clock_identity'],"strategy":c['strategy']['strategy_clock_identity'],"session":c['session']['session_clock_identity'],"dst":c['dst_regime']['identity'],"anchoring":c['anchoring']['anchoring_identity'],"reasons":c['reasons']['reason_code_identity']},
  "scenario_identities":e['scenario_identities'],"rust_task_output_identity":e['task_output_identity'],"rust_plan_identity":e['time_rule_plan_identity'],"expected_vector_identity":e['expected_vector_identity'],"csv_schema_identity":p['csv_schema_identity'],
  "runtime_identity":p['runtime_identity'],"runtime_sha256":raw_sha(files[RUNTIME]),"tester_identity":p['tester_identity'],"tester_sha256":raw_sha(files[TESTER]),"package_identity":p['package_identity'],
  "compiler_script_identity":sha({"target":"time_rules","sha256":script_sha}),"compiler_script_sha256":script_sha,"compiler_policy":POLICY,"expected_metaeditor_executable":EDITOR,"expected_metaeditor_build":BUILD,
  "runtime_source_path":f"generated/phase2_time_rules/{RUNTIME}","tester_source_path":f"generated/phase2_time_rules/{TESTER}","expected_ex5_path":f"compile/{TARGET.ex5_filename}","compile_command_template":f'{EDITOR} /compile:"{{tester_source}}" /log:"{{compiler_log}}"',"required_warning_count":0,"required_error_count":0}
 return identified(value,'compile_input_identity')

def validate_output(record,evidence_dir): return validate_compiler_envelope(record,build_compile_input(),evidence_dir,TARGET)

def create_synthetic_compiler_evidence(destination):
 destination=Path(destination);ci=build_compile_input();log=b"synthetic time-rule compile\nResult: 0 errors, 0 warnings\n";ex5=b"synthetic-time-rule-ex5-not-native"
 def write(tmp):
  (tmp/'compile.log').write_bytes(log);(tmp/TARGET.ex5_filename).write_bytes(ex5)
  record={"schema_version":TARGET.compiler_output_schema,"target_identifier":"time_rules","target_descriptor_identity":TARGET.identity,"compile_input_identity":ci['compile_input_identity'],"runtime_sha256":ci['runtime_sha256'],"tester_sha256":ci['tester_sha256'],"package_identity":ci['package_identity'],"metaeditor_executable":EDITOR,"observed_metaeditor_build":BUILD,"exact_command":"synthetic protocol fixture","invocation_start_utc":"2040-01-01T00:00:00Z","invocation_completion_utc":"2040-01-01T00:00:01Z","raw_process_exit":1,"normalized_result":"success","compiler_policy":POLICY,"policy_decision":"accepted_metaeditor_5836_one","log_path":"compile.log","log_size":len(log),"log_sha256":raw_sha(log),"warning_count":0,"warnings":[],"error_count":0,"errors":[],"ex5_path":TARGET.ex5_filename,"ex5_size":len(ex5),"ex5_modification_utc":"2040-01-01T00:00:01Z","ex5_sha256":raw_sha(ex5),"stale_ex5_disposition":"none_present","freshness_proof":{"preexisting_ex5_removed_or_isolated":True,"produced_after_invocation_start":True,"single_unambiguous_ex5":True},"completion_state":"completed","failure_reason":None,"synthetic_protocol_fixture":True};record['compiler_output_identity']=compiler_output_identity(record);(tmp/'compiler_record.json').write_text(canon(record)+'\n')
  manifest={"schema_version":TARGET.compile_evidence_schema,"target_identifier":"time_rules","target_descriptor_identity":TARGET.identity,"compile_input_identity":ci['compile_input_identity']};(tmp/'compile_evidence_manifest.json').write_text(canon(manifest)+'\n')
  inventory=[{"path":p,"role":role,"sha256":file_sha(tmp/p)} for p,role in (("compiler_record.json","compiler_record"),("compile.log","compiler_log"),(TARGET.ex5_filename,"ex5"),("compile_evidence_manifest.json","compile_evidence_manifest"))];(tmp/'inventory.json').write_text(canon(inventory)+'\n');return record
 return atomic_publish(destination,'.synthetic-time-compile-',write)

def local_readiness_evidence():
 with tempfile.TemporaryDirectory(dir=ROOT) as d:
  root=Path(d);create_synthetic_compiler_evidence(root/'e');synthetic=import_evidence(root/'e',root/'final')
 value={"schema_version":"nora.time_rule_local_readiness_v1","target_descriptor_identity":TARGET.identity,"compile_input_identity":build_compile_input()['compile_input_identity'],"precompile_batch_identity":build_precompile()['precompile_batch_identity'],"precompile_staged_inventory_identity":build_precompile()['staged_inventory_identity'],"synthetic_compiler_output_identity":synthetic['compiler_output_identity'],"synthetic_execution_packet_identity":synthetic['execution_packet_identity'],"synthetic_final_batch_identity":synthetic['final_batch_identity'],"synthetic_final_staged_inventory_identity":synthetic['staged_inventory_identity'],"synthetic_protocol_fixture_only":True,"genuine_native_compiler_evidence":False,"final_native_packet_present":False,"compile_evidence_pending":True,"compile_evidence_imported":False,"final_packet_ready":False,"native_execution_attempted":False,"native_parity_accepted":False,"grammar_admitted":False,"searchable":False,"complete_phase2_gate":False}
 return identified(value,'local_readiness_identity')

def build_packet(record,record_sha):
 ci=build_compile_input();e,c,p=frozen();scripts={x.name:{"path":str(x.relative_to(ROOT)),"sha256":file_sha(x)} for x in SCRIPTS[1:]}
 value={"schema_version":TARGET.packet_schema,"target_identifier":"time_rules","target_descriptor_identity":TARGET.identity,"compile_input_identity":ci['compile_input_identity'],"compiler_output_identity":record['compiler_output_identity'],"compiler_output_record_sha256":record_sha,"compiler_log_sha256":record['log_sha256'],"ex5_path":record['ex5_path'],"ex5_size":record['ex5_size'],"ex5_sha256":record['ex5_sha256'],
  "clock_contract_identities":ci['clock_contract_identities'],"scenario_identities":e['scenario_identities'],"rust_task_output_identity":e['task_output_identity'],"rust_plan_identity":e['time_rule_plan_identity'],"expected_vector_identity":e['expected_vector_identity'],"csv_schema_identity":p['csv_schema_identity'],"runtime_identity":p['runtime_identity'],"runtime_sha256":p['runtime_sha256'],"tester_identity":p['tester_identity'],"tester_sha256":p['tester_sha256'],"package_identity":p['package_identity'],"scripts":scripts,"host_context_matrix":list(TARGET.host_contexts),"completion_marker":TARGET.completion_marker,"failure_marker":TARGET.failure_marker,"result_filename":TARGET.result_csv_filename,"reconciliation_implementation":TARGET.reconciliation_implementation}
 return identified(value,'execution_packet_identity')

def build_final_batch(packet,record,items):
 value={"schema_version":TARGET.final_batch_schema,"target_identifier":"time_rules","dependency_graph":DEPENDENCY_GRAPH,"target_descriptor_identity":TARGET.identity,"compile_input_identity":packet['compile_input_identity'],"compiler_output_identity":record['compiler_output_identity'],"execution_packet_identity":packet['execution_packet_identity'],"ex5_sha256":record['ex5_sha256'],"compiler_log_sha256":record['log_sha256'],"frozen_time_rule_identities":{"clocks":packet['clock_contract_identities'],"scenarios":packet['scenario_identities'],"task":packet['rust_task_output_identity'],"plan":packet['rust_plan_identity'],"vectors":packet['expected_vector_identity'],"csv_schema":packet['csv_schema_identity'],"runtime":packet['runtime_identity'],"tester":packet['tester_identity'],"package":packet['package_identity']},"staged_files":items,"staged_inventory_identity":inventory_identity(items),"precompile_ready":True,"compile_evidence_pending":False,"compile_evidence_imported":True,"final_packet_ready":True,"native_execution_attempted":False,"native_parity_accepted":False,"grammar_admitted":False,"searchable":False,"complete_phase2_gate":False}
 if validate_dependency_graph(value['dependency_graph']):raise ValueError('dependency graph')
 return identified(value,'final_batch_identity')

def import_evidence(evidence_dir,destination,inject_failure=False):
 evidence_dir=Path(evidence_dir);destination=Path(destination);ex5=TARGET.ex5_filename
 allowed={'compiler_record.json','compile.log',ex5,'compile_evidence_manifest.json','inventory.json'}
 if not evidence_dir.is_dir() or {p.name for p in evidence_dir.iterdir()}!=allowed:raise ValueError('unexpected or missing file')
 record=json.loads((evidence_dir/'compiler_record.json').read_text(encoding='utf-8-sig'));errors=validate_output(record,evidence_dir)
 if errors:raise ValueError(', '.join(errors))
 record['compiler_output_identity']=compiler_output_identity(record)
 manifest=json.loads((evidence_dir/'compile_evidence_manifest.json').read_text(encoding='utf-8-sig'))
 if manifest!={"schema_version":TARGET.compile_evidence_schema,"target_identifier":"time_rules","target_descriptor_identity":TARGET.identity,"compile_input_identity":build_compile_input()['compile_input_identity']}:raise ValueError('compile evidence manifest')
 declared=json.loads((evidence_dir/'inventory.json').read_text(encoding='utf-8-sig'))
 expected={'compiler_record.json','compile.log',ex5,'compile_evidence_manifest.json'}
 if len(declared)!=4 or {x.get('path') for x in declared}!=expected:raise ValueError('inventory allowlist')
 for x in declared:
  if not safe_relative(x['path']) or file_sha(evidence_dir/x['path'])!=x['sha256']:raise ValueError('inventory binding')
 packet=build_packet(record,file_sha(evidence_dir/'compiler_record.json'))
 precompile=build_precompile()
 items=precompile['files']+[{"path":"compile/"+x['path'],"role":x['role'],"sha256":x['sha256']} for x in declared]+[{"path":"execution_packet.json","role":"execution_packet","sha256":"generated"}]
 batch=build_final_batch(packet,record,items)
 _,generated=generated_sources();generated[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  shutil.copytree(evidence_dir,tmp/'compile');(tmp/'compile_input.json').write_text(canon(build_compile_input())+'\n');(tmp/'execution_packet.json').write_text(canon(packet)+'\n');(tmp/'final_batch.json').write_text(canon(batch)+'\n')
  for item in precompile['files']:
   destination=tmp/item['path'];destination.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('generated/phase2_time_rules/'):destination.write_bytes(generated[destination.name])
   else:shutil.copy2(ROOT/item['path'],destination)
  return {"compile_input_identity":build_compile_input()['compile_input_identity'],"compiler_output_identity":record['compiler_output_identity'],"execution_packet_identity":packet['execution_packet_identity'],"final_batch_identity":batch['final_batch_identity'],"staged_inventory_identity":batch['staged_inventory_identity']}
 return atomic_publish(destination,'.time-rule-import-',write,inject_failure=inject_failure)

def build_precompile():
 e,c,p=frozen();ci=build_compile_input();_,generated=generated_sources()
 files=[{"path":"tests/fixtures/phase2_time_rule_rust_evidence.json","role":"rust_time_rule_evidence","sha256":file_sha(EVIDENCE)},{"path":"tests/fixtures/phase2_time_rule_contracts.json","role":"clock_contracts","sha256":file_sha(CONTRACTS)}]
 for name,role in ((RUNTIME,'mql5_runtime'),(TESTER,'mql5_tester'),(PACKAGE,'executable_package')):files.append({"path":f"generated/phase2_time_rules/{name}","role":role,"sha256":raw_sha(generated[name])})
 files.append({"path":f"generated/phase2_time_rules/{TARGET.compile_input_filename}","role":"compile_input_manifest","sha256":raw_sha((canon(ci)+'\n').encode())})
 for path,role in zip(SCRIPTS,('compiler_script','execution_script','package_builder_script')):files.append({"path":str(path.relative_to(ROOT)),"role":role,"sha256":file_sha(path)})
 value={"schema_version":TARGET.precompile_batch_schema,"target_identifier":"time_rules","target_descriptor_identity":TARGET.identity,"clock_contract_identities":ci['clock_contract_identities'],"scenario_identities":e['scenario_identities'],"rust_task_output_identity":e['task_output_identity'],"rust_plan_identity":e['time_rule_plan_identity'],"expected_vector_identity":e['expected_vector_identity'],"csv_schema_identity":p['csv_schema_identity'],"runtime_identity":p['runtime_identity'],"tester_identity":p['tester_identity'],"package_identity":p['package_identity'],"compile_input_identity":ci['compile_input_identity'],"files":files,"host_context_matrix":list(TARGET.host_contexts),"staged_inventory_identity":inventory_identity(files),"precompile_ready":True,"compile_evidence_pending":True,"compile_evidence_imported":False,"final_packet_ready":False,"native_execution_attempted":False,"native_parity_accepted":False,"grammar_admitted":False,"searchable":False,"complete_phase2_gate":False}
 return identified(value,'precompile_batch_identity')

def preflight(value=None):
 value=value or json.loads(MANIFEST.read_text());expected=build_precompile()
 return {"status":"PASS" if value==expected else "FAIL","classification":"ok" if value==expected else "stale_or_mixed_identity_chain","compile_input_identity":value.get('compile_input_identity'),"precompile_batch_identity":value.get('precompile_batch_identity'),"staged_inventory_identity":value.get('staged_inventory_identity')}

def stage(destination):
 destination=Path(destination);value=json.loads(MANIFEST.read_text());
 if preflight(value)['status']!='PASS':raise ValueError('preflight')
 _,generated=generated_sources();generated[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  for item in value['files']:
   target=tmp/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('generated/phase2_time_rules/'):target.write_bytes(generated[target.name])
   else:shutil.copy2(ROOT/item['path'],target)
   if file_sha(target)!=item['sha256']:raise ValueError('staging hash')
  dst=tmp/MANIFEST.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(MANIFEST,dst)
  return {"precompile_batch_identity":value['precompile_batch_identity'],"staged_inventory_identity":value['staged_inventory_identity']}
 return atomic_publish(destination,'.time-rule-stage-',write)

def stage_final(final_dir,destination):
 final_dir=Path(final_dir);batch=load_json(final_dir/'final_batch.json');packet=load_json(final_dir/'execution_packet.json')
 if batch.get('target_identifier')!='time_rules' or packet.get('target_descriptor_identity')!=TARGET.identity or batch.get('execution_packet_identity')!=packet.get('execution_packet_identity'):raise ValueError('final preflight')
 _,generated=generated_sources();generated[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  for item in batch['staged_files']:
   target=tmp/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('compile/'):shutil.copy2(final_dir/item['path'],target)
   elif item['path']=='execution_packet.json':target.write_text(canon(packet)+'\n')
   elif item['path'].startswith('generated/phase2_time_rules/'):target.write_bytes(generated[target.name])
   else:shutil.copy2(ROOT/item['path'],target)
   if item['sha256']!='generated' and file_sha(target)!=item['sha256']:raise ValueError('final staging hash')
  for name in ('compile_input.json','final_batch.json'):(tmp/name).write_bytes((final_dir/name).read_bytes())
  return {"final_batch_identity":batch['final_batch_identity'],"execution_packet_identity":packet['execution_packet_identity'],"staged_inventory_identity":batch['staged_inventory_identity']}
 return atomic_publish(Path(destination),'.time-rule-final-stage-',write)

def actual_rows(path):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:raw=list(csv.DictReader(f,delimiter='\t'))
 integers={'source_epoch','utc_offset_seconds','m5_anchor_epoch','h1_anchor_epoch'};booleans={'dst','session_member','friday_close','rollover','monday_delay','orb'}
 return [{k:(int(v) if k in integers else v=='true' if k in booleans else v) for k,v in row.items()} for row in raw]

def reconcile_rows(rows,evidence=None):
 expected=(evidence or json.loads(EVIDENCE.read_text()))['expected_vectors'];fields=[x for x in SCHEMA if x!='pass']
 if len(rows)!=len(expected):raise ValueError('row count')
 seen=[]
 for got,want in zip(rows,expected):
  if got.get('pass')!='true':raise ValueError('pass state')
  if any(got.get(k)!=want.get(k) for k in fields):raise ValueError('time-rule field mismatch')
  seen.append(got['scenario_id'])
 if len(seen)!=len(set(seen)):raise ValueError('duplicate row')
 return {"classification":"PASS_EXACT","semantic_time_rule_identity":sha(rows)}

def load_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def ingest(package_dir,packet,batch,expected_run,expected_symbol):
 package_dir=Path(package_dir);expected_files=set(REQUIRED)|{'returned_inventory.json','returned_result_manifest.json'}
 if {p.name for p in package_dir.iterdir() if p.is_file()}!=expected_files:raise ValueError('package file set')
 manifest=load_json(package_dir/'returned_result_manifest.json');claimed=manifest.get('returned_package_identity')
 normalized=dict(manifest);normalized.pop('returned_package_identity',None)
 windows_ordered=raw_sha(json.dumps(normalized,separators=(',',':'),ensure_ascii=False).encode())
 if manifest.get('schema_version')!=TARGET.returned_package_schema or manifest.get('target_identifier')!='time_rules' or claimed not in (manifest_identity(manifest,'returned_package_identity'),windows_ordered):raise ValueError('returned manifest')
 inventory_path=package_dir/'returned_inventory.json'
 if file_sha(inventory_path)!=manifest.get('returned_inventory_sha256'):raise ValueError('returned inventory hash')
 inventory=load_json(inventory_path)
 if [x.get('path') for x in inventory]!=list(REQUIRED):raise ValueError('inventory order')
 for x in inventory:
  p=package_dir/x['path']
  if not p.is_file() or p.stat().st_size!=x.get('size') or file_sha(p)!=x.get('sha256'):raise ValueError('inventory binding')
 record=load_json(package_dir/'execution.json');required={"run_identifier":expected_run,"target_identifier":"time_rules","host_symbol":expected_symbol,"timeframe":"M1","final_batch_identity":batch['final_batch_identity'],"compile_input_identity":packet['compile_input_identity'],"compiler_output_identity":packet['compiler_output_identity'],"execution_packet_identity":packet['execution_packet_identity'],"ex5_sha256":packet['ex5_sha256'],"runtime_identity":packet['runtime_identity'],"tester_identity":packet['tester_identity'],"package_identity":packet['package_identity'],"rust_plan_identity":packet['rust_plan_identity'],"expected_vector_identity":packet['expected_vector_identity'],"csv_schema_identity":packet['csv_schema_identity'],"clock_contract_identities":packet['clock_contract_identities'],"scenario_identities":packet['scenario_identities'],"completion_marker_present":True,"failure_marker_present":False,"no_trading_operations":True,"collection_state":"complete"}
 if any(record.get(k)!=v for k,v in required.items()):raise ValueError('execution binding')
 if datetime.fromisoformat(record['requested_start_utc'].replace('Z','+00:00'))>=datetime.fromisoformat(record['observed_completion_utc'].replace('Z','+00:00')):raise ValueError('chronology')
 if record.get('result_csv_sha256')!=file_sha(package_dir/CSV) or record.get('journal_segment_sha256')!=file_sha(package_dir/'tester-journal.log'):raise ValueError('fresh file binding')
 if load_json(package_dir/'completion-marker.json')!={"marker":TARGET.completion_marker,"present":True} or load_json(package_dir/'failure-marker.json')!={"marker":TARGET.failure_marker,"present":False}:raise ValueError('marker state')
 report=load_json(package_dir/'tester.htm')
 for k,v in {"run_identifier":expected_run,"symbol":expected_symbol,"timeframe":"M1","ex5_sha256":packet['ex5_sha256'],"csv_sha256":record['result_csv_sha256'],"journal_sha256":record['journal_segment_sha256'],"completion_marker_present":True,"failure_marker_present":False,"no_trading_operations":True}.items():
  if report.get(k)!=v:raise ValueError('report substitute')
 compiler=load_json(package_dir/'compile.json')
 if compiler_output_identity(compiler)!=packet['compiler_output_identity'] or compiler.get('ex5_sha256')!=packet['ex5_sha256']:raise ValueError('compiler binding')
 row_result=reconcile_rows(actual_rows(package_dir/CSV))
 result={"schema_version":TARGET.reconciliation_implementation,"run_identifier":expected_run,"host_context":f"{expected_symbol}/M1","returned_package_identity":claimed,"returned_inventory_identity":file_sha(inventory_path),"execution_record_identity":sha(record),"csv_sha256":file_sha(package_dir/CSV),"journal_identity":file_sha(package_dir/'tester-journal.log'),"report_substitute_identity":file_sha(package_dir/'tester.htm'),**row_result}
 result['reconciliation_identity']=sha(result);return result

def build_synthetic_returned(destination,final_dir,run_identifier,symbol):
 """Build a clearly synthetic filesystem package for contract tests only."""
 final_dir=Path(final_dir);packet=load_json(final_dir/'execution_packet.json');batch=load_json(final_dir/'final_batch.json');e=load_json(EVIDENCE)
 def write(tmp):
  compiler=load_json(final_dir/'compile/compiler_record.json');(tmp/'compile.json').write_text(canon(compiler)+'\n');shutil.copy2(final_dir/'compile/compile.log',tmp/'compile.log')
  journal=(f"synthetic bounded journal {run_identifier} {symbol}\n").encode();(tmp/'tester-journal.log').write_bytes(journal)
  with (tmp/CSV).open('w',newline='',encoding='utf-8') as f:
   writer=csv.DictWriter(f,fieldnames=SCHEMA,delimiter='\t',lineterminator='\n');writer.writeheader()
   for row in e['expected_vectors']:writer.writerow({**row,'dst':str(row['dst']).lower(),'session_member':str(row['session_member']).lower(),'friday_close':str(row['friday_close']).lower(),'rollover':str(row['rollover']).lower(),'monday_delay':str(row['monday_delay']).lower(),'orb':str(row['orb']).lower(),'pass':'true'})
  csv_sha=file_sha(tmp/CSV);journal_sha=file_sha(tmp/'tester-journal.log')
  (tmp/'completion-marker.json').write_text(canon({"marker":TARGET.completion_marker,"present":True})+'\n');(tmp/'failure-marker.json').write_text(canon({"marker":TARGET.failure_marker,"present":False})+'\n')
  report={"schema_version":"nora.time_rule_tester_evidence_v1","run_identifier":run_identifier,"symbol":symbol,"timeframe":"M1","ex5_sha256":packet['ex5_sha256'],"csv_sha256":csv_sha,"journal_sha256":journal_sha,"completion_marker_present":True,"failure_marker_present":False,"no_trading_operations":True,"synthetic_protocol_fixture":True};(tmp/'tester.htm').write_text(canon(report)+'\n')
  record={"schema_version":"nora.time_rule_run_record_v1","run_identifier":run_identifier,"target_identifier":"time_rules","host_symbol":symbol,"timeframe":"M1","requested_start_utc":"2040-01-01T00:00:00Z","observed_completion_utc":"2040-01-01T00:00:01Z","final_batch_identity":batch['final_batch_identity'],"compile_input_identity":packet['compile_input_identity'],"compiler_output_identity":packet['compiler_output_identity'],"execution_packet_identity":packet['execution_packet_identity'],"ex5_sha256":packet['ex5_sha256'],"runtime_identity":packet['runtime_identity'],"tester_identity":packet['tester_identity'],"package_identity":packet['package_identity'],"rust_plan_identity":packet['rust_plan_identity'],"expected_vector_identity":packet['expected_vector_identity'],"csv_schema_identity":packet['csv_schema_identity'],"clock_contract_identities":packet['clock_contract_identities'],"scenario_identities":packet['scenario_identities'],"result_csv_sha256":csv_sha,"journal_segment_sha256":journal_sha,"completion_marker_present":True,"failure_marker_present":False,"no_trading_operations":True,"collection_state":"complete","synthetic_protocol_fixture":True};(tmp/'execution.json').write_text(canon(record)+'\n')
  inventory=[{"path":name,"role":name,"size":(tmp/name).stat().st_size,"sha256":file_sha(tmp/name)} for name in REQUIRED];(tmp/'returned_inventory.json').write_text(canon(inventory)+'\n')
  manifest={"schema_version":TARGET.returned_package_schema,"target_identifier":"time_rules","batch_identity":batch['final_batch_identity'],"run_identifier":run_identifier,"host_symbol":symbol,"timeframe":"M1","execution_packet_identity":packet['execution_packet_identity'],"compiler_output_identity":packet['compiler_output_identity'],"ex5_sha256":packet['ex5_sha256'],"completion_marker_present":True,"failure_marker_present":False,"returned_inventory_sha256":file_sha(tmp/'returned_inventory.json'),"synthetic_protocol_fixture":True};manifest['returned_package_identity']=manifest_identity(manifest,'returned_package_identity');(tmp/'returned_result_manifest.json').write_text(canon(manifest)+'\n')
  return manifest
 return atomic_publish(Path(destination),'.time-rule-returned-',write)

def classify_failure(name):return name if name in FAILURES else 'exact_success'

def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True);s.add_parser('preflight');s.add_parser('write-precompile');s.add_parser('write-readiness');st=s.add_parser('stage');st.add_argument('--destination',required=True);fs=s.add_parser('stage-final');fs.add_argument('--final-dir',required=True);fs.add_argument('--destination',required=True);im=s.add_parser('import');im.add_argument('--evidence-dir',required=True);im.add_argument('--destination',required=True);a=p.parse_args()
 if a.command=='preflight':result=preflight()
 elif a.command=='write-precompile':
  value=build_precompile();temporary=MANIFEST.with_suffix('.json.tmp');temporary.write_text(canon(value)+'\n');temporary.replace(MANIFEST);result={"precompile_batch_identity":value['precompile_batch_identity'],"compile_input_identity":value['compile_input_identity'],"staged_inventory_identity":value['staged_inventory_identity']}
 elif a.command=='write-readiness':
  target=ROOT/'tests/fixtures/phase2_time_rule_local_readiness.json';result=local_readiness_evidence();temporary=target.with_suffix('.json.tmp');temporary.write_text(canon(result)+'\n');temporary.replace(target)
 elif a.command=='stage':result=stage(Path(a.destination))
 elif a.command=='stage-final':result=stage_final(Path(a.final_dir),Path(a.destination))
 else:result=import_evidence(Path(a.evidence_dir),Path(a.destination))
 print(canon(result))
if __name__=='__main__':main()
