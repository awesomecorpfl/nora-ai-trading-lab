"""Deterministic embedded-vector MQL5 generator for the ten-strategy canary."""
from __future__ import annotations
from pathlib import Path
from lab.native_target import raw_sha
from lab.phase2_execution import sha,canon
from lab.phase2_ten_strategy import fixture_suite,strategy_suite

RUNTIME="NoraPhase2TenStrategyRuntimeV1.mqh";TESTER="NoraPhase2TenStrategyTesterCanaryV1.mq5";PACKAGE="phase2_ten_strategy_executable_package.json";CSV="nora_phase2_ten_strategy_v1.csv"

def _runtime()->str:
 return r'''#ifndef NORA_PHASE2_TEN_STRATEGY_RUNTIME_V1
#define NORA_PHASE2_TEN_STRATEGY_RUNTIME_V1
#define NORA_NULL DBL_MAX
struct NoraBar { string ts; double o; double h; double l; double c; bool session; bool friday; bool rollover; bool monday; };
bool Available(double x){return x!=NORA_NULL;}
void Ema(const double &x[],int n,double &out[]){int z=ArraySize(x);ArrayResize(out,z);double seed=0.0,e=0.0;for(int i=0;i<z;i++){out[i]=NORA_NULL;if(i<n)seed+=x[i];if(i==n-1){e=seed/n;out[i]=e;}else if(i>=n){e=e+2.0/(n+1.0)*(x[i]-e);out[i]=e;}}}
void Atr(const NoraBar &b[],double &out[]){int z=ArraySize(b);ArrayResize(out,z);double tr[];ArrayResize(tr,z);for(int i=0;i<z;i++)tr[i]=(i==0?b[i].h-b[i].l:MathMax(b[i].h-b[i].l,MathMax(MathAbs(b[i].h-b[i-1].c),MathAbs(b[i].l-b[i-1].c))));Ema(tr,3,out);}
void ShiftedLevel(const NoraBar &b[],int n,bool highest,double &out[]){int z=ArraySize(b);ArrayResize(out,z);for(int i=0;i<z;i++){out[i]=NORA_NULL;if(i<n)continue;double v=highest?-DBL_MAX:DBL_MAX;for(int j=i-n;j<i;j++)v=highest?MathMax(v,b[j].h):MathMin(v,b[j].l);out[i]=v;}}
bool Cross(double x,double y,double px,double py,bool above){if(!Available(y)||!Available(py))return false;return above?(px<=py&&x>y):(px>=py&&x<y);}
void WriteNoTrade(int f,string sid,string direction,string reason){FileWrite(f,sid,"NULL",direction,"NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL",reason,"none");}
void RunCase(int f,string sid,string family,string direction,int period,double limit,int maxhold,bool filterroll,bool filtermon,const NoraBar &b[]){
 int z=ArraySize(b);double close[],ref[],atr[];ArrayResize(close,z);for(int i=0;i<z;i++)close[i]=b[i].c;Atr(b,atr);if(family=="trend-pullback")Ema(close,period,ref);else ShiftedLevel(b,period,direction=="long",ref);
 bool signal[],opposite[];ArrayResize(signal,z);ArrayResize(opposite,z);for(int i=0;i<z;i++){signal[i]=false;opposite[i]=false;if(i==0)continue;bool up=Cross(close[i],ref[i],close[i-1],ref[i-1],true),down=Cross(close[i],ref[i],close[i-1],ref[i-1],false);if(family=="trend-pullback"&&Available(atr[i])){double slope=Available(ref[i-1])?ref[i]-ref[i-1]:NORA_NULL;double dist=Available(ref[i])?(close[i]-ref[i])/atr[i]:NORA_NULL;signal[i]=(direction=="long"?up:down)&&Available(slope)&&Available(dist)&&(direction=="long"?slope>0:slope<0)&&MathAbs(dist)<=limit;opposite[i]=(direction=="long"?down:up);}else if(family!="trend-pullback"){signal[i]=(direction=="long"?up:down);opposite[i]=(direction=="long"?down:up);}}
 bool open=false,pending=false;int source=-1,entry=-1,ordinal=0;double ep=0,stop=0,target=0;for(int i=0;i<z;i++){if(pending){entry=i;ep=b[i].o;stop=direction=="long"?ep-4.0:ep+4.0;target=direction=="long"?ep+6.0:ep-6.0;open=true;pending=false;}if(open&&i>entry){bool gs=direction=="long"?b[i].o<=stop:b[i].o>=stop,gt=direction=="long"?b[i].o>=target:b[i].o<=target,sh=direction=="long"?b[i].l<=stop:b[i].h>=stop,th=direction=="long"?b[i].h>=target:b[i].l<=target;double xp=0;string reason="";if(gs){xp=b[i].o;reason="gap_stop";}else if(gt){xp=b[i].o;reason="gap_target";}else if(opposite[i]){xp=b[i].c;reason="signal_exit";}else if(b[i].friday||i-entry>=maxhold){xp=b[i].c;reason=b[i].friday?"friday_close":"time_exit";}else if(sh&&th){xp=stop;reason="pessimistic_dual_touch";}else if(sh){xp=stop;reason="stop";}else if(th){xp=target;reason="target";}if(reason!=""){ordinal++;FileWrite(f,sid,ordinal,direction,source,b[source].ts,entry,b[entry].ts,DoubleToString(ep,16),DoubleToString(stop,16),DoubleToString(target,16),i,b[i].ts,DoubleToString(xp,16),reason,i-entry,DoubleToString(direction=="long"?xp-ep:ep-xp,16),"NULL","not_executed");open=false;}}
 if(!open&&!pending&&signal[i]&&b[i].session&&!(filterroll&&b[i].rollover)&&!(filtermon&&b[i].monday)&&i+1<z){pending=true;source=i;}}
 if(ordinal==0)WriteNoTrade(f,sid,direction,"none");}
#endif
'''

def _bars(segment:dict,index:int)->str:
 lines=[f"NoraBar b{index}[]={{"]
 for b in segment['bars']:
  bools=','.join('true' if b[k] else 'false' for k in ('session_member','friday_close','rollover','monday_delay'))
  lines.append('{"%s",%.17g,%.17g,%.17g,%.17g,%s},'%(b['timestamp'],b['open'],b['high'],b['low'],b['close'],bools))
 lines.append('};');return '\n'.join(lines)

def _tester()->str:
 suite=strategy_suite();segments=fixture_suite()['segments'];decl=[];calls=[]
 for i,(s,g) in enumerate(zip(suite['strategies'],segments)):
  decl.append(_bars(g,i));p=s['parameters'];limit=p.get('distance_atr_limit',0.0);t=s['time_session_rule'];calls.append(f'RunCase(f,"{s["strategy_identity"]}","{s["family"]}","{s["direction_support"][0]}",{p["period"]},{limit:.17g},{s["exit_rule"]["maximum_holding_bars"]},{str(t["rollover_filter"]).lower()},{str(t["monday_delay"]).lower()},b{i});')
 return '#property strict\n#include "'+RUNTIME+'"\n'+'\n'.join(decl)+f'''\nint OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_COMMON,'\\t');if(f==INVALID_HANDLE)return INIT_FAILED;FileWrite(f,"strategy_identity","trade_ordinal","direction","signal_index","signal_timestamp","entry_index","entry_timestamp","entry_price","initial_stop","initial_target","exit_index","exit_timestamp","exit_price","exit_reason","holding_bars","gross_price_return","no_trade_reason","terminal_source_disposition");'''+''.join(calls)+'''FileFlush(f);FileClose(f);Print("NORA_PHASE2_TEN_STRATEGY_COMPLETE_V1");ExpertRemove();return INIT_SUCCEEDED;}\nvoid OnTick(){}\n'''

def generate(destination:Path)->dict:
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=True);runtime=_runtime().encode();tester=_tester().encode()
 r=sha({'schema':'nora.phase2_ten_strategy_runtime_v1','source_sha256':raw_sha(runtime)});t=sha({'schema':'nora.phase2_ten_strategy_tester_v1','source_sha256':raw_sha(tester),'runtime_identity':r})
 package={'schema_version':'nora.phase2_ten_strategy_executable_package_v1','suite_identity':strategy_suite()['suite_identity'],'runtime_identity':r,'tester_identity':t,'runtime_sha256':raw_sha(runtime),'tester_sha256':raw_sha(tester),'result_csv':CSV,'expected_ledgers_are_resolver_inputs':False}
 package['package_identity']=sha(package);(destination/RUNTIME).write_bytes(runtime);(destination/TESTER).write_bytes(tester);(destination/PACKAGE).write_text(canon(package)+'\n');return package
