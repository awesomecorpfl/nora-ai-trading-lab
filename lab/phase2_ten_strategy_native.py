"""Typed-target local readiness for the frozen ten-strategy parity suite."""
from __future__ import annotations
import copy,csv,json,shutil,tempfile
from pathlib import Path
from lab.mql5gen.ten_strategy import CSV,PACKAGE,RUNTIME,TESTER,generate
from lab.native_target import BUILD,EDITOR,POLICY,DEPENDENCY_GRAPH,atomic_publish,compiler_output_identity,file_sha,identified,inventory_identity,manifest_identity,raw_sha,safe_relative,validate_compiler_envelope
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
 value={'schema_version':TARGET.compile_input_schema,'target_identifier':TARGET.target_identifier,'target_descriptor_identity':TARGET.identity,'suite_identity':suite['suite_identity'],'strategy_identities':[x['strategy_identity'] for x in suite['strategies']],'fixture_identity':load(FIX/'fixture_suite.json')['input_fixture_identity'],'coverage_matrix_identity':load(FIX/'coverage_matrix.json')['coverage_matrix_identity'],'rust_evidence_identity':rust['combined_rust_evidence_identity'],'expected_ledger_vector_identities':rust['expected_ledger_vector_identities'],'execution_contract_identity':EXECUTION_IDENTITY,'time_rule_contract_identity':TIME_IDENTITY,'reconciliation_protocol_identity':protocol['strategy_reconciliation_protocol_identity'],'budget_map_identity':budgets['applicable_budget_map_identity'],'runtime_identity':p['runtime_identity'],'runtime_sha256':raw_sha(data[RUNTIME]),'tester_identity':p['tester_identity'],'tester_sha256':raw_sha(data[TESTER]),'package_identity':p['package_identity'],'expected_metaeditor_executable':EDITOR,'expected_metaeditor_build':BUILD,'compiler_policy':POLICY,'runtime_source_path':f'generated/{RUNTIME}','tester_source_path':f'generated/{TESTER}','expected_ex5_path':f'compile/{TARGET.ex5_filename}','compile_command_template':f'{EDITOR} /compile:"{{tester_source}}" /log:"{{compiler_log}}"','required_warning_count':0,'required_error_count':0,'grammar_admitted':False,'searchable':False}
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
