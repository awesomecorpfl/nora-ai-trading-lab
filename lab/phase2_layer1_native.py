"""Typed-target native readiness and synthetic reconciliation for Layer-1 batch one."""
from __future__ import annotations

import copy,csv,json,shutil,tempfile
from datetime import datetime
from pathlib import Path

from lab.mql5gen.layer1_batch import CSV,PACKAGE,RUNTIME,TESTER,generate
from lab.native_target import (BUILD,EDITOR,POLICY,DEPENDENCY_GRAPH,atomic_publish,compiler_output_identity,
 file_sha,identified,inventory_identity,manifest_identity,raw_sha,safe_relative,validate_compiler_envelope,validate_dependency_graph)
from lab.native_targets import LAYER1_BATCH_TARGET as TARGET
from lab.numeric_parity import measure,within_budget
from lab.phase2_execution import canon,sha

ROOT=Path(__file__).resolve().parents[1];FIX=ROOT/'tests/fixtures/phase2_layer1_first_batch'
FILES={x:FIX/x for x in ('authoritative_matrix.json','dependency_map.json','batch_plan.json','numeric_protocol.json','failure_vocabulary.json','rust_evidence.json')}
MQL=FIX/'generated';MANIFEST=FIX/'precompile_batch.json';READINESS=FIX/'local_readiness.json'
FINAL=FIX/'native_final'
SCRIPTS=tuple(ROOT/x for x in (TARGET.compiler_script,TARGET.execution_script,TARGET.collection_script))
REQUIRED=('compile.json','execution.json','compile.log','tester-journal.log','tester.htm','completion-marker.json','failure-marker.json',CSV)

def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def frozen():return {k:load(v) for k,v in FILES.items()}
def generated():
 f=frozen();
 with tempfile.TemporaryDirectory(dir=ROOT) as d:
  out=Path(d);p=generate(out,f['rust_evidence.json'],f['batch_plan.json'],f['numeric_protocol.json'])
  return p,{n:(out/n).read_bytes() for n in (RUNTIME,TESTER,PACKAGE)}

def build_compile_input():
 f=frozen();p,data=generated();plan=f['batch_plan.json'];protocol=f['numeric_protocol.json'];e=f['rust_evidence.json'];script=file_sha(SCRIPTS[0])
 value={'schema_version':TARGET.compile_input_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,
  'selected_node_identities':plan['selected_node_identities'],'scenario_identities':e['scenario_identities'],'rust_task_output_identity':e['rust_task_output_identity'],
  'expected_vector_identity':e['expected_vector_identity'],'output_schema_identity':e['output_schema_identity'],'batch_plan_identity':plan['batch_plan_identity'],
  'parity_protocol_identity':protocol['parity_protocol_identity'],'reference_modes':plan['reference_modes'],'runtime_identity':p['runtime_identity'],'runtime_sha256':raw_sha(data[RUNTIME]),
  'tester_identity':p['tester_identity'],'tester_sha256':raw_sha(data[TESTER]),'package_identity':p['package_identity'],'compiler_script_identity':sha({'target':TARGET.target_identifier,'sha256':script}),
  'compiler_script_sha256':script,'compiler_policy':POLICY,'expected_metaeditor_executable':EDITOR,'expected_metaeditor_build':BUILD,
  'runtime_source_path':f'generated/{RUNTIME}','tester_source_path':f'generated/{TESTER}','expected_ex5_path':f'compile/{TARGET.ex5_filename}',
  'compile_command_template':f'{EDITOR} /compile:"{{tester_source}}" /log:"{{compiler_log}}"','required_warning_count':0,'required_error_count':0}
 return identified(value,'compile_input_identity')

def build_precompile():
 f=frozen();p,data=generated();ci=build_compile_input();items=[]
 for key,path in FILES.items():items.append({'path':str(path.relative_to(ROOT)),'role':key.removesuffix('.json'),'sha256':file_sha(path)})
 for name,role in ((RUNTIME,'mql5_runtime'),(TESTER,'mql5_tester'),(PACKAGE,'executable_package')):items.append({'path':f'generated/{name}','role':role,'sha256':raw_sha(data[name])})
 items.append({'path':f'generated/{TARGET.compile_input_filename}','role':'compile_input_manifest','sha256':raw_sha((canon(ci)+'\n').encode())})
 for path,role in zip(SCRIPTS,('compiler_script','execution_script','package_builder_script')):items.append({'path':str(path.relative_to(ROOT)),'role':role,'sha256':file_sha(path)})
 value={'schema_version':TARGET.precompile_batch_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,
  'selected_node_identities':ci['selected_node_identities'],'scenario_identities':ci['scenario_identities'],'rust_task_output_identity':ci['rust_task_output_identity'],
  'expected_vector_identity':ci['expected_vector_identity'],'output_schema_identity':ci['output_schema_identity'],'batch_plan_identity':ci['batch_plan_identity'],
  'parity_protocol_identity':ci['parity_protocol_identity'],'reference_modes':ci['reference_modes'],'runtime_identity':p['runtime_identity'],'tester_identity':p['tester_identity'],
  'package_identity':p['package_identity'],'compile_input_identity':ci['compile_input_identity'],'files':items,'host_context_matrix':list(TARGET.host_contexts),
  'staged_inventory_identity':inventory_identity(items),'precompile_ready':True,'compile_evidence_pending':True,'compile_evidence_imported':False,
  'final_packet_ready':False,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False,'complete_phase2_gate':False}
 return identified(value,'precompile_batch_identity')

def preflight(value=None):
 value=value or load(MANIFEST);expected=build_precompile();forbidden=any(value.get(k) for k in ('native_execution_attempted','native_parity_accepted','grammar_admitted','searchable'))
 return {'status':'PASS' if value==expected and not forbidden else 'FAIL','classification':'ok' if value==expected and not forbidden else 'stale_mutated_or_cross_target',
         'compile_input_identity':value.get('compile_input_identity'),'precompile_batch_identity':value.get('precompile_batch_identity'),'staged_inventory_identity':value.get('staged_inventory_identity')}

def stage(destination):
 value=load(MANIFEST)
 if preflight(value)['status']!='PASS':raise ValueError('preflight')
 _,data=generated();data[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  for item in value['files']:
   target=tmp/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('generated/'):target.write_bytes(data[target.name])
   else:shutil.copy2(ROOT/item['path'],target)
   if file_sha(target)!=item['sha256']:raise ValueError('staging hash')
  dst=tmp/MANIFEST.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(MANIFEST,dst)
  return {'precompile_batch_identity':value['precompile_batch_identity'],'staged_inventory_identity':value['staged_inventory_identity']}
 return atomic_publish(Path(destination),'.layer1-stage-',write)

def stage_final(final_dir,destination):
 final_dir=Path(final_dir);packet=load(final_dir/'execution_packet.json');batch=load(final_dir/'final_batch.json')
 if batch.get('target_identifier')!=TARGET.target_identifier or packet.get('target_descriptor_identity')!=TARGET.identity or batch.get('execution_packet_identity')!=packet.get('execution_packet_identity'):raise ValueError('final preflight')
 _,data=generated();data[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  for item in batch['staged_files']:
   target=tmp/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('compile/'):shutil.copy2(final_dir/item['path'],target)
   elif item['path']=='execution_packet.json':target.write_text(canon(packet)+'\n')
   elif item['path'].startswith('generated/'):target.write_bytes(data[target.name])
   else:shutil.copy2(ROOT/item['path'],target)
   if item['sha256']!='generated' and file_sha(target)!=item['sha256']:raise ValueError('final staging hash')
  for name in ('compile_input.json','final_batch.json'):shutil.copy2(final_dir/name,tmp/name)
  return {'final_batch_identity':batch['final_batch_identity'],'execution_packet_identity':packet['execution_packet_identity'],'staged_inventory_identity':batch['staged_inventory_identity']}
 return atomic_publish(Path(destination),'.layer1-final-stage-',write)

def create_synthetic_compiler_evidence(destination, *, failure=False):
 ci=build_compile_input();log=b'synthetic layer1 compile\nResult: 0 errors, 0 warnings\n';ex5=b'synthetic-layer1-ex5-not-native'
 def write(tmp):
  (tmp/'compile.log').write_bytes(log);(tmp/TARGET.ex5_filename).write_bytes(ex5)
  record={'schema_version':TARGET.compiler_output_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,
   'compile_input_identity':ci['compile_input_identity'],'runtime_sha256':ci['runtime_sha256'],'tester_sha256':ci['tester_sha256'],'package_identity':ci['package_identity'],
   'metaeditor_executable':EDITOR,'observed_metaeditor_build':BUILD,'exact_command':'synthetic protocol fixture','invocation_start_utc':'2040-01-01T00:00:00Z',
   'invocation_completion_utc':'2040-01-01T00:00:01Z','raw_process_exit':1,'normalized_result':'failure' if failure else 'success','compiler_policy':POLICY,
   'policy_decision':'rejected' if failure else 'accepted_metaeditor_5836_one','log_path':'compile.log','log_size':len(log),'log_sha256':raw_sha(log),'warning_count':0,'warnings':[],
   'error_count':1 if failure else 0,'errors':['synthetic'] if failure else [],'ex5_path':TARGET.ex5_filename,'ex5_size':len(ex5),'ex5_modification_utc':'2040-01-01T00:00:01Z',
   'ex5_sha256':raw_sha(ex5),'stale_ex5_disposition':'none_present','freshness_proof':{'preexisting_ex5_removed_or_isolated':True,'produced_after_invocation_start':True,'single_unambiguous_ex5':True},
   'completion_state':'failed' if failure else 'completed','failure_reason':'synthetic' if failure else None,'synthetic_protocol_fixture':True}
  record['compiler_output_identity']=compiler_output_identity(record);(tmp/'compiler_record.json').write_text(canon(record)+'\n')
  manifest={'schema_version':TARGET.compile_evidence_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'compile_input_identity':ci['compile_input_identity']};(tmp/'compile_evidence_manifest.json').write_text(canon(manifest)+'\n')
  inv=[{'path':n,'role':r,'sha256':file_sha(tmp/n)} for n,r in (('compiler_record.json','compiler_record'),('compile.log','compiler_log'),(TARGET.ex5_filename,'ex5'),('compile_evidence_manifest.json','compile_evidence_manifest'))];(tmp/'inventory.json').write_text(canon(inv)+'\n');return record
 return atomic_publish(Path(destination),'.synthetic-layer1-compile-',write)

def build_packet(record,record_sha):
 ci=build_compile_input();p,_=generated();scripts={x.name:{'path':str(x.relative_to(ROOT)),'sha256':file_sha(x)} for x in SCRIPTS[1:]}
 value={'schema_version':TARGET.packet_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'compile_input_identity':ci['compile_input_identity'],
  'compiler_output_identity':record['compiler_output_identity'],'compiler_output_record_sha256':record_sha,'compiler_log_sha256':record['log_sha256'],'ex5_path':record['ex5_path'],'ex5_size':record['ex5_size'],'ex5_sha256':record['ex5_sha256'],
  **{k:ci[k] for k in ('selected_node_identities','scenario_identities','rust_task_output_identity','expected_vector_identity','output_schema_identity','batch_plan_identity','parity_protocol_identity','reference_modes','runtime_identity','runtime_sha256','tester_identity','tester_sha256','package_identity')},
  'scripts':scripts,'host_context_matrix':list(TARGET.host_contexts),'completion_marker':TARGET.completion_marker,'failure_marker':TARGET.failure_marker,'result_filename':CSV,'reconciliation_implementation':TARGET.reconciliation_implementation}
 return identified(value,'execution_packet_identity')

def import_evidence(evidence_dir,destination,inject_failure=False):
 evidence_dir=Path(evidence_dir);allowed={'compiler_record.json','compile.log',TARGET.ex5_filename,'compile_evidence_manifest.json','inventory.json'}
 if not evidence_dir.is_dir() or {x.name for x in evidence_dir.iterdir()}!=allowed:raise ValueError('compiler evidence file set')
 record=load(evidence_dir/'compiler_record.json');errors=validate_compiler_envelope(record,build_compile_input(),evidence_dir,TARGET)
 if errors:raise ValueError(', '.join(errors))
 manifest=load(evidence_dir/'compile_evidence_manifest.json');expected={'schema_version':TARGET.compile_evidence_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'compile_input_identity':build_compile_input()['compile_input_identity']}
 if manifest!=expected:raise ValueError('compile evidence manifest')
 declared=load(evidence_dir/'inventory.json')
 if len(declared)!=4 or {x.get('path') for x in declared}!={'compiler_record.json','compile.log',TARGET.ex5_filename,'compile_evidence_manifest.json'}:raise ValueError('inventory allowlist')
 for x in declared:
  if not safe_relative(x['path']) or file_sha(evidence_dir/x['path'])!=x['sha256']:raise ValueError('inventory binding')
 packet=build_packet(record,file_sha(evidence_dir/'compiler_record.json'));pre=build_precompile();items=pre['files']+[{'path':'compile/'+x['path'],'role':x['role'],'sha256':x['sha256']} for x in declared]+[{'path':'execution_packet.json','role':'execution_packet','sha256':'generated'}]
 batch={'schema_version':TARGET.final_batch_schema,'target_identifier':TARGET.target_identifier,'dependency_graph':DEPENDENCY_GRAPH,'target_descriptor_identity':TARGET.identity,
        'compile_input_identity':packet['compile_input_identity'],'compiler_output_identity':record['compiler_output_identity'],'execution_packet_identity':packet['execution_packet_identity'],
        'frozen_identities':{k:packet[k] for k in ('selected_node_identities','scenario_identities','rust_task_output_identity','expected_vector_identity','output_schema_identity','batch_plan_identity','parity_protocol_identity','reference_modes','runtime_identity','tester_identity','package_identity')},
        'ex5_sha256':record['ex5_sha256'],'compiler_log_sha256':record['log_sha256'],'staged_files':items,'staged_inventory_identity':inventory_identity(items),'precompile_ready':True,
        'compile_evidence_pending':False,'compile_evidence_imported':True,'final_packet_ready':True,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False,'complete_phase2_gate':False}
 if validate_dependency_graph(batch['dependency_graph']):raise ValueError('dependency graph')
 batch=identified(batch,'final_batch_identity');_,data=generated();data[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  shutil.copytree(evidence_dir,tmp/'compile');(tmp/'compile_input.json').write_text(canon(build_compile_input())+'\n');(tmp/'execution_packet.json').write_text(canon(packet)+'\n');(tmp/'final_batch.json').write_text(canon(batch)+'\n')
  for item in pre['files']:
   target=tmp/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('generated/'):target.write_bytes(data[target.name])
   else:shutil.copy2(ROOT/item['path'],target)
  return {'compiler_output_identity':record['compiler_output_identity'],'execution_packet_identity':packet['execution_packet_identity'],'final_batch_identity':batch['final_batch_identity'],'staged_inventory_identity':batch['staged_inventory_identity']}
 return atomic_publish(Path(destination),'.layer1-import-',write,inject_failure=inject_failure)

def expected_rows():return frozen()['rust_evidence.json']['rust_output']['rows']
def reconcile_rows(rows,budgets=None):
 expected=expected_rows()
 if len(rows)!=len(expected):raise ValueError('ROW_COUNT_MISMATCH')
 exact=('scenario_id','node','output','row','timestamp','null','classification','reason_code');groups={};exact_numeric=True
 for got,want in zip(rows,expected):
  for key in exact:
   if got.get(key)!=want.get(key):raise ValueError({'scenario_id':'SCENARIO_ORDER_MISMATCH','timestamp':'TIMESTAMP_MISMATCH','null':'NULL_MISMATCH','reason_code':'REASON_CODE_MISMATCH'}.get(key,'OUTPUT_REORDERED'))
  if want['value'] is None:
   if got.get('value') is not None:raise ValueError('NULL_MISMATCH')
  else:
   if got.get('value') is None:raise ValueError('NULL_MISMATCH')
   groups.setdefault((want['node'],want['output']),([],[],[]));groups[(want['node'],want['output'])][0].append(want['value']);groups[(want['node'],want['output'])][1].append(got['value']);groups[(want['node'],want['output'])][2].append(want['classification'])
 measurements={};
 for (node,output),(rust,mql,phases) in groups.items():
  m=measure(rust,mql,phases);measurements[f'{node}.{output}']=m;exact_numeric &= m['exact']
  if not m['exact']:
   budget=(budgets or {}).get(node,{}).get(output)
   if budget is None or not within_budget(m,budget):raise ValueError('NUMERIC_BUDGET_EXCEEDED')
 result={'schema_version':TARGET.reconciliation_implementation,'classification':'PASS_EXACT' if exact_numeric else 'PASS_WITHIN_TEST_BUDGET','measurements':measurements,'budget_identity':sha(budgets) if budgets else None,'empirical_native_budget_accepted':False}
 result['semantic_result_identity']=sha(rows);result['reconciliation_identity']=sha(result);return result

def build_synthetic_returned(destination,final_dir,run_identifier='A1',symbol='GDAXI',delta=0.0):
 final_dir=Path(final_dir);packet=load(final_dir/'execution_packet.json');batch=load(final_dir/'final_batch.json')
 def write(tmp):
  compiler=load(final_dir/'compile/compiler_record.json');(tmp/'compile.json').write_text(canon(compiler)+'\n');shutil.copy2(final_dir/'compile/compile.log',tmp/'compile.log');(tmp/'tester-journal.log').write_text('synthetic bounded journal\n')
  fields=frozen()['rust_evidence.json']['output_schema']
  with (tmp/CSV).open('w',newline='') as stream:
   writer=csv.DictWriter(stream,fieldnames=fields,delimiter='\t',lineterminator='\n');writer.writeheader()
   for source in expected_rows():
    row=dict(source)
    if row['value'] is not None:row['value']+=delta
    for key in ('row','timestamp','value'):row[key]='NULL' if row[key] is None else row[key]
    row['null']=str(row['null']).lower();writer.writerow(row)
  csv_sha=file_sha(tmp/CSV);journal=file_sha(tmp/'tester-journal.log');(tmp/'completion-marker.json').write_text(canon({'marker':TARGET.completion_marker,'present':True})+'\n');(tmp/'failure-marker.json').write_text(canon({'marker':TARGET.failure_marker,'present':False})+'\n')
  report={'run_identifier':run_identifier,'symbol':symbol,'timeframe':'M1','ex5_sha256':packet['ex5_sha256'],'csv_sha256':csv_sha,'journal_sha256':journal,'completion_marker_present':True,'failure_marker_present':False,'no_trading_operations':True,'synthetic_protocol_fixture':True};(tmp/'tester.htm').write_text(canon(report)+'\n')
  record={'schema_version':'nora.layer1_run_record_v1','run_identifier':run_identifier,'target_identifier':TARGET.target_identifier,'host_symbol':symbol,'timeframe':'M1','requested_start_utc':'2040-01-01T00:00:00Z','observed_completion_utc':'2040-01-01T00:00:01Z','final_batch_identity':batch['final_batch_identity'],'execution_packet_identity':packet['execution_packet_identity'],'compile_input_identity':packet['compile_input_identity'],'compiler_output_identity':packet['compiler_output_identity'],'ex5_sha256':packet['ex5_sha256'],'runtime_identity':packet['runtime_identity'],'tester_identity':packet['tester_identity'],'package_identity':packet['package_identity'],'batch_plan_identity':packet['batch_plan_identity'],'parity_protocol_identity':packet['parity_protocol_identity'],'expected_vector_identity':packet['expected_vector_identity'],'scenario_identities':packet['scenario_identities'],'selected_node_identities':packet['selected_node_identities'],'reference_modes':packet['reference_modes'],'result_csv_sha256':csv_sha,'journal_segment_sha256':journal,'completion_marker_present':True,'failure_marker_present':False,'no_trading_operations':True,'collection_state':'complete','synthetic_protocol_fixture':True};(tmp/'execution.json').write_text(canon(record)+'\n')
  inv=[{'path':n,'role':n,'size':(tmp/n).stat().st_size,'sha256':file_sha(tmp/n)} for n in REQUIRED];(tmp/'returned_inventory.json').write_text(canon(inv)+'\n')
  manifest={'schema_version':TARGET.returned_package_schema,'target_identifier':TARGET.target_identifier,'final_batch_identity':batch['final_batch_identity'],'run_identifier':run_identifier,'host_symbol':symbol,'timeframe':'M1','execution_packet_identity':packet['execution_packet_identity'],'compiler_output_identity':packet['compiler_output_identity'],'ex5_sha256':packet['ex5_sha256'],'completion_marker_present':True,'failure_marker_present':False,'returned_inventory_sha256':file_sha(tmp/'returned_inventory.json'),'synthetic_protocol_fixture':True};manifest['returned_package_identity']=manifest_identity(manifest,'returned_package_identity');(tmp/'returned_result_manifest.json').write_text(canon(manifest)+'\n');return manifest
 return atomic_publish(Path(destination),'.layer1-returned-',write)

def actual_rows(path):
 with Path(path).open(newline='') as f:raw=list(csv.DictReader(f,delimiter='\t'))
 out=[]
 for row in raw:
  out.append({**row,'row':None if row['row']=='NULL' else int(row['row']),'timestamp':None if row['timestamp']=='NULL' else row['timestamp'],'value':None if row['value']=='NULL' else float(row['value']),'null':row['null']=='true'})
 return out

def ingest(package_dir,packet,batch,run_identifier,symbol,budgets=None):
 package_dir=Path(package_dir);expected=set(REQUIRED)|{'returned_inventory.json','returned_result_manifest.json'}
 if {x.name for x in package_dir.iterdir() if x.is_file()}!=expected:raise ValueError('package file set')
 manifest=load(package_dir/'returned_result_manifest.json')
 if manifest.get('returned_package_identity')!=manifest_identity(manifest,'returned_package_identity') or manifest.get('target_identifier')!=TARGET.target_identifier:raise ValueError('returned manifest')
 inventory=load(package_dir/'returned_inventory.json')
 if [x.get('path') for x in inventory]!=list(REQUIRED) or file_sha(package_dir/'returned_inventory.json')!=manifest['returned_inventory_sha256']:raise ValueError('inventory order')
 for x in inventory:
  p=package_dir/x['path']
  if p.stat().st_size!=x['size'] or file_sha(p)!=x['sha256']:raise ValueError('inventory binding')
 record=load(package_dir/'execution.json');bindings={'run_identifier':run_identifier,'target_identifier':TARGET.target_identifier,'host_symbol':symbol,'timeframe':'M1','final_batch_identity':batch['final_batch_identity'],'execution_packet_identity':packet['execution_packet_identity'],'compile_input_identity':packet['compile_input_identity'],'compiler_output_identity':packet['compiler_output_identity'],'ex5_sha256':packet['ex5_sha256'],'runtime_identity':packet['runtime_identity'],'tester_identity':packet['tester_identity'],'package_identity':packet['package_identity'],'batch_plan_identity':packet['batch_plan_identity'],'parity_protocol_identity':packet['parity_protocol_identity'],'expected_vector_identity':packet['expected_vector_identity'],'scenario_identities':packet['scenario_identities'],'selected_node_identities':packet['selected_node_identities'],'reference_modes':packet['reference_modes'],'completion_marker_present':True,'failure_marker_present':False,'no_trading_operations':True,'collection_state':'complete'}
 if any(record.get(k)!=v for k,v in bindings.items()):raise ValueError('execution binding')
 if datetime.fromisoformat(record['requested_start_utc'].replace('Z','+00:00'))>=datetime.fromisoformat(record['observed_completion_utc'].replace('Z','+00:00')):raise ValueError('chronology')
 if record['result_csv_sha256']!=file_sha(package_dir/CSV) or record['journal_segment_sha256']!=file_sha(package_dir/'tester-journal.log'):raise ValueError('fresh files')
 if load(package_dir/'completion-marker.json')!={'marker':TARGET.completion_marker,'present':True} or load(package_dir/'failure-marker.json')!={'marker':TARGET.failure_marker,'present':False}:raise ValueError('MARKER_FAILURE')
 report=load(package_dir/'tester.htm');report_bindings={'run_identifier':run_identifier,'symbol':symbol,'timeframe':'M1','ex5_sha256':packet['ex5_sha256'],'csv_sha256':record['result_csv_sha256'],'journal_sha256':record['journal_segment_sha256'],'completion_marker_present':True,'failure_marker_present':False,'no_trading_operations':True}
 if any(report.get(k)!=v for k,v in report_bindings.items()):raise ValueError('tester report substitute')
 compiler=load(package_dir/'compile.json')
 if compiler_output_identity(compiler)!=packet['compiler_output_identity']:raise ValueError('compiler binding')
 result=reconcile_rows(actual_rows(package_dir/CSV),budgets);result.update({'run_identifier':run_identifier,'host_context':f'{symbol}/M1','returned_package_identity':manifest['returned_package_identity'],'execution_record_identity':sha(record),'csv_sha256':file_sha(package_dir/CSV),'journal_identity':file_sha(package_dir/'tester-journal.log'),'report_substitute_identity':file_sha(package_dir/'tester.htm')});result['reconciliation_identity']=sha({k:v for k,v in result.items() if k!='reconciliation_identity'});return result

def local_readiness():
 with tempfile.TemporaryDirectory(dir=ROOT) as d:
  root=Path(d);create_synthetic_compiler_evidence(root/'e');ids=import_evidence(root/'e',root/'final');build_synthetic_returned(root/'returned',root/'final');rec=ingest(root/'returned',load(root/'final/execution_packet.json'),load(root/'final/final_batch.json'),'A1','GDAXI')
 value={'schema_version':'nora.layer1_local_readiness_v1','target_descriptor_identity':TARGET.identity,'compile_input_identity':build_compile_input()['compile_input_identity'],'precompile_batch_identity':build_precompile()['precompile_batch_identity'],'precompile_staged_inventory_identity':build_precompile()['staged_inventory_identity'],
        'synthetic_compiler_output_identity':ids['compiler_output_identity'],'synthetic_execution_packet_identity':ids['execution_packet_identity'],'synthetic_final_batch_identity':ids['final_batch_identity'],'synthetic_final_staged_inventory_identity':ids['staged_inventory_identity'],'synthetic_reconciliation_identity':rec['reconciliation_identity'],
        'synthetic_protocol_fixture_only':True,'genuine_native_compiler_evidence':False,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False,'phase2_complete':False}
 return identified(value,'local_readiness_identity')

def freeze_native():
 values={FIX/'target_descriptor.json':identified(TARGET.value(),'target_descriptor_identity'),FIX/'compile_input.json':build_compile_input(),MANIFEST:build_precompile(),READINESS:local_readiness()}
 for path,value in values.items():
  temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(canon(value)+'\n');temporary.replace(path)
 return {path.name:next((value[k] for k in ('target_descriptor_identity','compile_input_identity','precompile_batch_identity','local_readiness_identity') if k in value),None) for path,value in values.items()}
