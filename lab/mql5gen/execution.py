"""Deterministic fixed-path MQL5 execution-canary generator; never invokes MQL5."""
import hashlib,json,os
from pathlib import Path
from lab.phase2_execution import SCHEMA,PRECEDENCE,canon,sha
VERSION="nora.phase2.execution_mql5_v1"; RUNTIME="NoraPhase2ExecutionRuntimeV1.mqh"; TESTER="NoraPhase2ExecutionTesterCanaryV1.mq5"; PACKAGE="phase2_execution_executable_package.json"; CSV="nora_phase2_execution_tester_v1.csv"; MARKER="NORA_PHASE2_EXECUTION_COMPLETE_V1"; FAIL="NORA_PHASE2_EXECUTION_FAIL"
def _id(*x): return sha(list(x))
def _runtime(): return b'''#ifndef NORA_PHASE2_EXECUTION_RUNTIME_V1_MQH\n#define NORA_PHASE2_EXECUTION_RUNTIME_V1_MQH\nstruct NoraExecutionResultV1 { bool has_trade; int entry_index; double entry_price; int exit_index; double exit_price; string reason; };\nNoraExecutionResultV1 NoraExecutionResolveV1(const double entry_price,const int entry_index,const double bar_open,const double bar_high,const double bar_low,const bool gap_stop,const bool gap_target,const bool signal,const bool time_due,const bool stop_touch,const bool target_touch)\n{ NoraExecutionResultV1 r; r.has_trade=true;r.entry_index=entry_index;r.entry_price=entry_price;r.exit_index=entry_index+1;r.exit_price=bar_open;r.reason=""; if(gap_stop){r.reason="initial_stop_gap";return r;} if(gap_target){r.reason="initial_target_gap";return r;} if(signal){r.reason="signal";return r;} if(time_due){r.reason="max_bars_held";return r;} if(stop_touch && target_touch){r.exit_price=entry_price-1.0;r.reason="initial_stop_pessimistic";return r;} if(stop_touch){r.exit_price=entry_price-1.0;r.reason="initial_stop";return r;} if(target_touch){r.exit_price=entry_price+2.0;r.reason="initial_target";return r;} r.has_trade=false;r.reason="no_trade";return r;}\n#endif\n'''
def resolver_inputs(record):
 s=record['task_fixture']; entry_index=next((i for i,x in enumerate(s['entry']) if x),-1)
 if entry_index<0 or entry_index+1>=len(s['bars']): return None
 entry=s['bars'][entry_index][0]; bar=s['bars'][entry_index+1]; stop=entry-s['stop_offset'];target=entry+s['target_offset']; signal=s['exit'][entry_index+1] is True; time=s['time_exit'] is not None and 1>=s['time_exit']
 return {'entry_index':entry_index,'exit_index':entry_index+1,'entry_price':entry,'bar_open':bar[0],'bar_high':bar[1],'bar_low':bar[2],'stop':stop,'target':target,'gap_stop':bar[0]<=stop,'gap_target':bar[0]>=target,'signal':signal,'time_due':time,'stop_touch':bar[2]<=stop,'target_touch':bar[1]>=target}
def _tester(records):
 rows=[]; calls=[]
 for i,r in enumerate(records):
  ledger=r['expected_trade_ledger_rows']; x=ledger[0] if ledger else None
  if x: rows.append('{"%s",%d,%d,%.16g,%d,%.16g,"%s",%.16g,%.16g,"%s","trade"}'%(r['scenario_id'],i,x['entry_index'],x['entry_price'],x['exit_index'],x['exit_price'],x['side'],x['entry_price']-1,x['entry_price']+2,r['exit_reason']))
  else: rows.append('{"%s",%d,-1,0.0,-1,0.0,"long",0.0,0.0,"no_trade","no_trade"}'%(r['scenario_id'],i))
  q=resolver_inputs(r)
  calls.append('NoraExecutionResultV1 actual; if(i==%d){%s}'%(i,('actual=NoraExecutionResolveV1(%.16g,%d,%.16g,%.16g,%.16g,%s,%s,%s,%s,%s,%s);'%(q['entry_price'],q['entry_index'],q['bar_open'],q['bar_high'],q['bar_low'],str(q['gap_stop']).lower(),str(q['gap_target']).lower(),str(q['signal']).lower(),str(q['time_due']).lower(),str(q['stop_touch']).lower(),str(q['target_touch']).lower()) if q else 'actual.has_trade=false;actual.reason="no_trade";')))
 return ('''#property strict\n#include "NoraPhase2ExecutionRuntimeV1.mqh"\nstruct NoraExpectedExecutionV1 { string id; int row; int entry_index; double entry_price; int exit_index; double exit_price; string side; double stop; double target; string reason; string state; };\nNoraExpectedExecutionV1 NoraExpected[%d]={%s};\nstring NoraExecutionCsv(const double v,const bool null_value){return null_value?"NULL":DoubleToString(v,16);}\nint OnInit(){int f=FileOpen("%s",FILE_WRITE|FILE_CSV|FILE_ANSI,'\\t');if(f==INVALID_HANDLE){Print("%s");return INIT_FAILED;}FileWrite(f,"scenario_id","ledger_row_index","entry_bar_index","entry_price","exit_bar_index","exit_price","direction","stop_price","target_price","exit_reason","expected_state","pass");for(int i=0;i<ArraySize(NoraExpected);i++){NoraExpectedExecutionV1 e=NoraExpected[i];%s bool pass=(actual.reason==e.reason && (e.state=="no_trade" ? !actual.has_trade : actual.has_trade));FileWrite(f,e.id,e.row,actual.has_trade?IntegerToString(actual.entry_index):"NULL",NoraExecutionCsv(actual.entry_price,!actual.has_trade),actual.has_trade?IntegerToString(actual.exit_index):"NULL",NoraExecutionCsv(actual.exit_price,!actual.has_trade),e.side,NoraExecutionCsv(e.stop,!actual.has_trade),NoraExecutionCsv(e.target,!actual.has_trade),actual.reason,e.state,pass?"true":"false");if(!pass){FileClose(f);Print("%s");return INIT_FAILED;}}FileClose(f);Print("%s");return INIT_SUCCEEDED;}void OnDeinit(const int reason){}\n'''%(len(rows),','.join(rows),CSV,FAIL,' '.join(calls),FAIL,MARKER)).encode()
def generate(evidence_path,out_dir):
 ev=json.loads(Path(evidence_path).read_text()); out=Path(out_dir); names=[RUNTIME,TESTER,PACKAGE]
 if not out.is_dir() or any((out/n).exists() for n in names): raise ValueError('execution output target invalid')
 runtime=_runtime(); rs=hashlib.sha256(runtime).hexdigest(); contract=ev['execution_plan_identity']; ri=_id('runtime',VERSION,contract,rs)
 tester=_tester(ev['scenarios']); ts=hashlib.sha256(tester).hexdigest(); ti=_id('tester',VERSION,ri,contract,ts)
 package={'version':VERSION,'execution_plan_identity':contract,'expected_execution_vector_identity':sha(ev['scenarios']),'execution_csv_schema_identity':sha(SCHEMA),'execution_csv_schema':SCHEMA,'precedence_contract':PRECEDENCE,'runtime_identity':ri,'tester_identity':ti,'runtime_sha256':rs,'tester_sha256':ts,'result_filename':CSV,'completion_marker':MARKER,'failure_marker':FAIL,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False};package['package_identity']=_id('package',package)
 data={RUNTIME:runtime,TESTER:tester,PACKAGE:(canon(package)+'\n').encode()}; done=[]
 try:
  for n in names:(out/n).write_bytes(data[n]);done.append(n)
 except Exception:
  for n in done:(out/n).unlink(missing_ok=True)
  raise
 return package
