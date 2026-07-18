"""Typed-target local readiness for the frozen ten-strategy parity suite."""
from __future__ import annotations
import copy,csv,json,shutil,tempfile
from datetime import datetime
from pathlib import Path
from lab.mql5gen.ten_strategy import CSV,PACKAGE,RUNTIME,TESTER,generate
from lab.native_target import BUILD,EDITOR,POLICY,COMPILER_LOG_REDACTION_POLICY_IDENTITY,DEPENDENCY_GRAPH,atomic_publish,compiler_output_identity,file_sha,identified,inventory_identity,manifest_identity,raw_sha,safe_relative,validate_compiler_envelope,validate_compiler_log_redaction,validate_dependency_graph
from lab.native_targets import TEN_STRATEGY_TARGET as TARGET
from lab.phase2_execution import canon,sha
from lab.phase2_ten_strategy import FIX,EXECUTION_IDENTITY,TIME_IDENTITY,strategy_suite

ROOT=Path(__file__).resolve().parents[1];GENERATED=FIX/'generated';MANIFEST=FIX/'precompile_batch.json';READINESS=FIX/'local_readiness.json'
SOURCE_NAMES=('strategy_suite.json','fixture_suite.json','coverage_matrix.json','rust_task.json','rust_evidence.json','experiment_bundle.json','replay_record.json','reconciliation_protocol.json','budget_map.json','failure_vocabulary.json','measurement_schema.json')
SCRIPTS=tuple(ROOT/x for x in (TARGET.compiler_script,TARGET.execution_script,TARGET.collection_script))
REQUIRED=('compile.json','execution.json','compile.log','tester-journal.log','tester.htm','completion-marker.json','failure-marker.json',CSV)
STRUCTURAL=('strategy_identity','trade_ordinal','direction','signal_index','signal_timestamp','entry_index','entry_timestamp','exit_index','exit_timestamp','exit_reason','no_trade_reason','terminal_source_disposition')
NUMERIC=('entry_price','initial_stop','initial_target','exit_price','holding_bars','gross_price_return')
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def budget_map():
 exact=sha({'schema':'nora.exact_embedded_price_arithmetic_v1','operations':['embedded OHLC read','integer offset add/subtract','same-side subtract']})
 value={'schema_version':'nora.ten_strategy_applicable_budget_map_v1','scope':'frozen suite/fixtures/runtime/tester only','fields':{x:{'kind':'exact_zero','absolute':0.0,'relative':0.0,'ulp':0,'governing_identity':exact} for x in NUMERIC},'dependency_evidence':{'ema_highest_lowest': '3fe6ce82622ad0a0fa01e887e4745a02bfcb8e1ff5e0899f37e3108e50687cdb','execution':EXECUTION_IDENTITY},'atr_distance_numeric_emission':'not_emitted; signal decisions only','broad_tolerance_created':False}
 return identified(value,'applicable_budget_map_identity')
def reconciliation_protocol():
 value={'schema_version':'nora.ten_strategy_reconciliation_protocol_v1','structural_exact':list(STRUCTURAL)+['strategy_order','trade_count','ledger_order','null_state','marker_states'],'numeric_fields':list(NUMERIC),'measurement':['rust','mql5','absolute_error','relative_error','ulp_distance','governing_accepted_budget_identity'],'budget_map_identity':budget_map()['applicable_budget_map_identity'],'structural_tolerance_forbidden':True}
 return identified(value,'strategy_reconciliation_protocol_identity')
def failure_vocabulary():
 value={'schema_version':'nora.ten_strategy_failure_vocabulary_v1','codes':['ROW_COUNT_MISMATCH','MISSING_TRADE','EXTRA_TRADE','DUPLICATE_TRADE','TRADE_REORDERED','WRONG_DIRECTION','WRONG_ENTRY_INDEX','WRONG_EXIT_INDEX','WRONG_EXIT_REASON','FRIDAY_CLOSE_MISMATCH','COMPLETED_LEVEL_SHIFT_MISMATCH','NEXT_OPEN_MISMATCH','DUAL_TOUCH_MISMATCH','NULL_WARMUP_MISMATCH','TERMINAL_SOURCE_EXECUTED','NUMERIC_BUDGET_EXCEEDED','STRATEGY_IDENTITY_MISMATCH','SUITE_IDENTITY_MISMATCH','EXECUTION_CONTRACT_MISMATCH','TIME_CONTRACT_MISMATCH','MARKER_FAILURE','COMPILER_FAILURE','INTERRUPTED_PUBLICATION','CROSS_TARGET_EVIDENCE']}
 return identified(value,'failure_vocabulary_identity')
def measurement_schema():return identified({'schema_version':'nora.ten_strategy_ledger_numeric_measurement_v1','fields':['rust_value','mql5_value','absolute_error','relative_error','ulp_distance','governing_accepted_budget_identity']},'ledger_numeric_measurement_schema_identity')
def generated():
 with tempfile.TemporaryDirectory(dir=ROOT) as d:
  p=generate(Path(d));return p,{n:(Path(d)/n).read_bytes() for n in (RUNTIME,TESTER,PACKAGE)}
def build_compile_input():
 p,data=generated();suite=load(FIX/'strategy_suite.json');rust=load(FIX/'rust_evidence.json');protocol=reconciliation_protocol();budgets=budget_map()
 value={'schema_version':TARGET.compile_input_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'compiler_output_schema':TARGET.compiler_output_schema,'compile_evidence_schema':TARGET.compile_evidence_schema,'suite_identity':suite['suite_identity'],'strategy_identities':[x['strategy_identity'] for x in suite['strategies']],'fixture_identity':load(FIX/'fixture_suite.json')['input_fixture_identity'],'coverage_matrix_identity':load(FIX/'coverage_matrix.json')['coverage_matrix_identity'],'rust_evidence_identity':rust['combined_rust_evidence_identity'],'expected_ledger_vector_identities':rust['expected_ledger_vector_identities'],'execution_contract_identity':EXECUTION_IDENTITY,'time_rule_contract_identity':TIME_IDENTITY,'reconciliation_protocol_identity':protocol['strategy_reconciliation_protocol_identity'],'budget_map_identity':budgets['applicable_budget_map_identity'],'runtime_identity':p['runtime_identity'],'runtime_sha256':raw_sha(data[RUNTIME]),'tester_identity':p['tester_identity'],'tester_sha256':raw_sha(data[TESTER]),'package_identity':p['package_identity'],'expected_metaeditor_executable':EDITOR,'expected_metaeditor_build':BUILD,'compiler_policy':POLICY,'redaction_policy_identity':COMPILER_LOG_REDACTION_POLICY_IDENTITY,'runtime_source_path':f'generated/{RUNTIME}','tester_source_path':f'generated/{TESTER}','expected_ex5_path':f'compile/{TARGET.ex5_filename}','compile_command_template':f'{EDITOR} /compile:"{{tester_source}}" /log:"{{compiler_log}}"','required_warning_count':0,'required_error_count':0,'grammar_admitted':False,'searchable':False}
 return identified(value,'compile_input_identity')
def build_precompile():
 ci=build_compile_input();p,data=generated();items=[]
 for n in SOURCE_NAMES:items.append({'path':str((FIX/n).relative_to(ROOT)),'role':n.removesuffix('.json'),'sha256':file_sha(FIX/n)})
 for n,r in ((RUNTIME,'mql5_runtime'),(TESTER,'mql5_tester'),(PACKAGE,'executable_package')):items.append({'path':f'generated/{n}','role':r,'sha256':raw_sha(data[n])})
 items.append({'path':f'generated/{TARGET.compile_input_filename}','role':'compile_input','sha256':raw_sha((canon(ci)+'\n').encode())})
 for path,role in zip(SCRIPTS,('compiler_script','execution_script','package_builder_script')):items.append({'path':str(path.relative_to(ROOT)),'role':role,'sha256':file_sha(path)})
 value={'schema_version':TARGET.precompile_batch_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'suite_identity':ci['suite_identity'],'strategy_identities':ci['strategy_identities'],'compile_input_identity':ci['compile_input_identity'],'files':items,'staged_inventory_identity':inventory_identity(items),'host_context_matrix':list(TARGET.host_contexts),'precompile_ready':True,'compile_evidence_pending':True,'compile_evidence_imported':False,'final_packet_ready':False,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False,'complete_phase2_gate':False}
 return identified(value,'precompile_batch_identity')
def preflight(value=None):
 value=value or load(MANIFEST);expected=build_precompile();return {'status':'PASS' if value==expected else 'FAIL','precompile_ready':value.get('precompile_ready'),'compile_evidence_pending':value.get('compile_evidence_pending'),'compile_evidence_imported':value.get('compile_evidence_imported'),'final_packet_ready':value.get('final_packet_ready'),'native_execution_attempted':value.get('native_execution_attempted'),'native_parity_accepted':value.get('native_parity_accepted'),'searchable':value.get('searchable')}
def stage(destination):
 batch=load(MANIFEST);assert preflight(batch)['status']=='PASS';_,data=generated();data[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  for x in batch['files']:
   dst=tmp/x['path'];dst.parent.mkdir(parents=True,exist_ok=True)
   if x['path'].startswith('generated/'):dst.write_bytes(data[dst.name])
   else:shutil.copy2(ROOT/x['path'],dst)
   if file_sha(dst)!=x['sha256']:raise ValueError('staging hash')
  return {'precompile_batch_identity':batch['precompile_batch_identity'],'staged_inventory_identity':batch['staged_inventory_identity']}
 return atomic_publish(Path(destination),'.ten-strategy-stage-',write)
def expected_rows():return [t for x in load(FIX/'rust_evidence.json')['rust_output']['strategy_outputs'] for t in x['trades']]
def reconcile_rows(rows):
 expected=expected_rows()
 if len(rows)!=len(expected):raise ValueError('ROW_COUNT_MISMATCH')
 measurements=[]
 for got,want in zip(rows,expected):
  for key in STRUCTURAL:
   if got.get(key)!=want.get(key):raise ValueError('STRATEGY_IDENTITY_MISMATCH' if key=='strategy_identity' else 'TRADE_REORDERED')
  for key in NUMERIC:
   if got.get(key)!=want.get(key):raise ValueError('NUMERIC_BUDGET_EXCEEDED')
   if want.get(key) is not None:measurements.append({'field':key,'rust_value':want[key],'mql5_value':got[key],'absolute_error':0.0,'relative_error':0.0,'ulp_distance':0,'governing_accepted_budget_identity':budget_map()['fields'][key]['governing_identity']})
 value={'schema_version':TARGET.reconciliation_implementation,'classification':'PASS_EXACT','strategy_count':10,'row_count':len(rows),'measurements':measurements,'budget_map_identity':budget_map()['applicable_budget_map_identity']};return identified(value,'reconciliation_identity')
def create_synthetic_compiler_evidence(destination,failure=False):
 ci=build_compile_input();log=b'synthetic ten strategy compile\nResult: 0 errors, 0 warnings\n';ex5=b'synthetic-ten-strategy-ex5'
 def write(tmp):
  (tmp/'compile.log').write_bytes(log);(tmp/TARGET.ex5_filename).write_bytes(ex5);record={'schema_version':TARGET.compiler_output_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'compile_input_identity':ci['compile_input_identity'],'runtime_sha256':ci['runtime_sha256'],'tester_sha256':ci['tester_sha256'],'package_identity':ci['package_identity'],'metaeditor_executable':EDITOR,'observed_metaeditor_build':BUILD,'exact_command':'synthetic protocol fixture','raw_process_exit':1,'normalized_result':'failure' if failure else 'success','compiler_policy':POLICY,'policy_decision':'rejected' if failure else 'accepted_metaeditor_5836_one','log_path':'compile.log','log_size':len(log),'log_sha256':raw_sha(log),'warning_count':0,'warnings':[],'error_count':1 if failure else 0,'errors':['synthetic'] if failure else [],'ex5_path':TARGET.ex5_filename,'ex5_size':len(ex5),'ex5_sha256':raw_sha(ex5),'freshness_proof':{'preexisting_ex5_removed_or_isolated':True,'produced_after_invocation_start':True,'single_unambiguous_ex5':True},'completion_state':'failed' if failure else 'completed','failure_reason':'synthetic' if failure else None,'synthetic_protocol_fixture':True};record['compiler_output_identity']=compiler_output_identity(record);(tmp/'compiler_record.json').write_text(canon(record)+'\n');return record
 return atomic_publish(Path(destination),'.ten-strategy-compile-',write)
def import_evidence(evidence,destination,inject_failure=False):
 evidence=Path(evidence);record=load(evidence/'compiler_record.json');ci=build_compile_input()
 if record.get('target_identifier')!=TARGET.target_identifier or record.get('normalized_result')!='success' or record.get('error_count')!=0:raise ValueError('COMPILER_FAILURE')
 packet=identified({'schema_version':TARGET.packet_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'compile_input_identity':ci['compile_input_identity'],'compiler_output_identity':record['compiler_output_identity'],'suite_identity':ci['suite_identity'],'strategy_identities':ci['strategy_identities'],'runtime_identity':ci['runtime_identity'],'tester_identity':ci['tester_identity'],'package_identity':ci['package_identity'],'host_context_matrix':list(TARGET.host_contexts)},'execution_packet_identity')
 batch=identified({'schema_version':TARGET.final_batch_schema,'target_identifier':TARGET.target_identifier,'dependency_graph':DEPENDENCY_GRAPH,'compile_input_identity':ci['compile_input_identity'],'compiler_output_identity':record['compiler_output_identity'],'execution_packet_identity':packet['execution_packet_identity'],'staged_inventory_identity':build_precompile()['staged_inventory_identity'],'synthetic_protocol_fixture':True},'final_batch_identity')
 def write(tmp):(tmp/'execution_packet.json').write_text(canon(packet)+'\n');(tmp/'final_batch.json').write_text(canon(batch)+'\n');return {'synthetic_compiler_output_identity':record['compiler_output_identity'],'synthetic_execution_packet_identity':packet['execution_packet_identity'],'synthetic_final_batch_identity':batch['final_batch_identity']}
 return atomic_publish(Path(destination),'.ten-strategy-final-',write,inject_failure=inject_failure)

# Genuine compiler evidence uses the same non-circular target chain as the
# accepted Layer-1 target.  It intentionally lives beside the synthetic
# helpers above: those helpers remain protocol fixtures and are never accepted
# by this importer.
def build_packet(record,record_sha):
 ci=build_compile_input(); p,_=generated(); scripts={x.name:{'path':str(x.relative_to(ROOT)),'sha256':file_sha(x)} for x in SCRIPTS[1:]}
 value={'schema_version':TARGET.packet_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,
  'compile_input_identity':ci['compile_input_identity'],'compiler_output_identity':record.get('compiler_output_identity') or compiler_output_identity(record),'compiler_output_record_sha256':record_sha,
  'compiler_log_sha256':record['log_sha256'],'raw_compiler_log_sha256':record['raw_log_sha256'],'raw_compiler_log_size':record['raw_log_size'],'redaction_policy_identity':record['redaction_policy_identity'],'ex5_path':record['ex5_path'],'ex5_size':record['ex5_size'],'ex5_sha256':record['ex5_sha256'],
  **{k:ci[k] for k in ('suite_identity','strategy_identities','fixture_identity','coverage_matrix_identity','rust_evidence_identity','expected_ledger_vector_identities','execution_contract_identity','time_rule_contract_identity','reconciliation_protocol_identity','budget_map_identity','runtime_identity','runtime_sha256','tester_identity','tester_sha256','package_identity')},
  'scripts':scripts,'host_context_matrix':list(TARGET.host_contexts),'completion_marker':TARGET.completion_marker,'failure_marker':TARGET.failure_marker,'result_filename':CSV,'reconciliation_implementation':TARGET.reconciliation_implementation}
 return identified(value,'execution_packet_identity')

def import_genuine_evidence(evidence_dir,destination,raw_log_path=None,inject_failure=False):
 evidence_dir=Path(evidence_dir); allowed={'compiler_record.json','compile.redacted.log',TARGET.ex5_filename,'compile_evidence_manifest.json','inventory.json'}
 if not evidence_dir.is_dir() or {x.name for x in evidence_dir.iterdir()}!=allowed: raise ValueError('compiler evidence file set')
 record=load(evidence_dir/'compiler_record.json')
 if record.get('synthetic_protocol_fixture') is True: raise ValueError('synthetic compiler evidence')
 errors=validate_compiler_envelope(record,build_compile_input(),evidence_dir,TARGET)+validate_compiler_log_redaction(record,evidence_dir,raw_log_path)
 if errors: raise ValueError(', '.join(errors))
 manifest=load(evidence_dir/'compile_evidence_manifest.json'); expected={'schema_version':TARGET.compile_evidence_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'compile_input_identity':build_compile_input()['compile_input_identity']}
 if manifest!=expected: raise ValueError('compile evidence manifest')
 declared=load(evidence_dir/'inventory.json')
 if len(declared)!=4 or {x.get('path') for x in declared}!={'compiler_record.json','compile.redacted.log',TARGET.ex5_filename,'compile_evidence_manifest.json'}: raise ValueError('inventory allowlist')
 for x in declared:
  if not safe_relative(x['path']) or file_sha(evidence_dir/x['path'])!=x['sha256']: raise ValueError('inventory binding')
 packet=build_packet(record,file_sha(evidence_dir/'compiler_record.json')); pre=build_precompile()
 items=pre['files']+[{'path':'compile/'+x['path'],'role':x['role'],'sha256':x['sha256']} for x in declared]+[{'path':'execution_packet.json','role':'execution_packet','sha256':'generated'}]
 batch={'schema_version':TARGET.final_batch_schema,'target_identifier':TARGET.target_identifier,'dependency_graph':DEPENDENCY_GRAPH,'target_descriptor_identity':TARGET.identity,
  'compile_input_identity':packet['compile_input_identity'],'compiler_output_identity':record.get('compiler_output_identity') or compiler_output_identity(record),'execution_packet_identity':packet['execution_packet_identity'],
  'frozen_identities':{k:packet[k] for k in ('suite_identity','strategy_identities','fixture_identity','coverage_matrix_identity','rust_evidence_identity','expected_ledger_vector_identities','execution_contract_identity','time_rule_contract_identity','reconciliation_protocol_identity','budget_map_identity','runtime_identity','tester_identity','package_identity')},
  'ex5_sha256':record['ex5_sha256'],'compiler_log_sha256':record['log_sha256'],'raw_compiler_log_sha256':record['raw_log_sha256'],'raw_compiler_log_size':record['raw_log_size'],'redaction_policy_identity':record['redaction_policy_identity'],'staged_files':items,'staged_inventory_identity':inventory_identity(items),
  'precompile_ready':True,'compile_evidence_pending':False,'compile_evidence_imported':True,'final_packet_ready':True,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False,'complete_phase2_gate':False}
 if validate_dependency_graph(batch['dependency_graph']): raise ValueError('dependency graph')
 batch=identified(batch,'final_batch_identity'); _,data=generated(); data[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  shutil.copytree(evidence_dir,tmp/'compile'); (tmp/'compile_input.json').write_text(canon(build_compile_input())+'\n'); (tmp/'execution_packet.json').write_text(canon(packet)+'\n'); (tmp/'final_batch.json').write_text(canon(batch)+'\n')
  for item in pre['files']:
   target=tmp/item['path']; target.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('generated/'): target.write_bytes(data[target.name])
   else: shutil.copy2(ROOT/item['path'],target)
  return {'compiler_output_identity':record.get('compiler_output_identity') or compiler_output_identity(record),'execution_packet_identity':packet['execution_packet_identity'],'final_batch_identity':batch['final_batch_identity'],'staged_inventory_identity':batch['staged_inventory_identity']}
 return atomic_publish(Path(destination),'.ten-strategy-import-',write,inject_failure=inject_failure)

def stage_final(final_dir,destination):
 final_dir=Path(final_dir); packet=load(final_dir/'execution_packet.json'); batch=load(final_dir/'final_batch.json')
 if batch.get('target_identifier')!=TARGET.target_identifier or packet.get('target_descriptor_identity')!=TARGET.identity or batch.get('execution_packet_identity')!=packet.get('execution_packet_identity'): raise ValueError('final preflight')
 _,data=generated(); data[TARGET.compile_input_filename]=(canon(build_compile_input())+'\n').encode()
 def write(tmp):
  for item in batch['staged_files']:
   target=tmp/item['path']; target.parent.mkdir(parents=True,exist_ok=True)
   if item['path'].startswith('compile/'): shutil.copy2(final_dir/item['path'],target)
   elif item['path']=='execution_packet.json': target.write_text(canon(packet)+'\n')
   elif item['path'].startswith('generated/'): target.write_bytes(data[target.name])
   else: shutil.copy2(ROOT/item['path'],target)
   if item['sha256']!='generated' and file_sha(target)!=item['sha256']: raise ValueError('final staging hash')
  for name in ('compile_input.json','final_batch.json'): shutil.copy2(final_dir/name,tmp/name)
  return {'final_batch_identity':batch['final_batch_identity'],'execution_packet_identity':packet['execution_packet_identity'],'staged_inventory_identity':batch['staged_inventory_identity']}
 return atomic_publish(Path(destination),'.ten-strategy-final-stage-',write)
def build_synthetic_returned(destination,mutate=None):
 rows=copy.deepcopy(expected_rows());mutate=mutate or (lambda x:None);mutate(rows)
 def write(tmp):
  (tmp/'rows.json').write_text(canon(rows)+'\n');(tmp/'completion-marker.json').write_text(canon({'marker':TARGET.completion_marker,'present':True})+'\n');(tmp/'failure-marker.json').write_text(canon({'marker':TARGET.failure_marker,'present':False})+'\n');return reconcile_rows(rows)
 return atomic_publish(Path(destination),'.ten-strategy-returned-',write)
def local_readiness():
 with tempfile.TemporaryDirectory(dir=ROOT) as d:
  r=Path(d);create_synthetic_compiler_evidence(r/'compile');ids=import_evidence(r/'compile',r/'final');rec=build_synthetic_returned(r/'returned')
 value={'schema_version':'nora.ten_strategy_local_readiness_v1','target_descriptor_identity':TARGET.identity,'compile_input_identity':build_compile_input()['compile_input_identity'],'precompile_batch_identity':build_precompile()['precompile_batch_identity'],'staged_inventory_identity':build_precompile()['staged_inventory_identity'],**ids,'synthetic_reconciliation_identity':rec['reconciliation_identity'],'synthetic_protocol_fixture_only':True,'precompile_ready':True,'compile_evidence_pending':True,'compile_evidence_imported':False,'final_packet_ready':False,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False,'complete_phase2_gate':False,'production_data_required':False}
 return identified(value,'local_readiness_identity')
def freeze():
 GENERATED.mkdir(parents=True,exist_ok=True);generate(GENERATED)
 values={'reconciliation_protocol.json':reconciliation_protocol(),'budget_map.json':budget_map(),'failure_vocabulary.json':failure_vocabulary(),'measurement_schema.json':measurement_schema()}
 for name,value in values.items():(FIX/name).write_text(canon(value)+'\n')
 values.update({'target_descriptor.json':identified(TARGET.value(),'target_descriptor_identity'),'compile_input.json':build_compile_input(),'precompile_batch.json':build_precompile()})
 for name in ('target_descriptor.json','compile_input.json','precompile_batch.json'):(FIX/name).write_text(canon(values[name])+'\n')
 values['local_readiness.json']=local_readiness();(FIX/'local_readiness.json').write_text(canon(values['local_readiness.json'])+'\n')
 return values
