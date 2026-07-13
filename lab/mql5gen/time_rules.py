"""Deterministic fixed-epoch MQL5 generator for the Phase-2 time-rule canary.

This generator only emits source; it never consults a terminal, chart, clock or market
series.  Expected rows are compared after the resolver has calculated its inputs.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from lab.phase2_time_contracts import canon, identity

VERSION="nora.phase2.time_rule_mql5_v1"
RUNTIME="NoraPhase2TimeRuleRuntimeV1.mqh"; TESTER="NoraPhase2TimeRuleTesterCanaryV1.mq5"
PACKAGE="phase2_time_rule_executable_package.json"; CSV="nora_phase2_time_rule_tester_v1.csv"
MARKER="NORA_PHASE2_TIME_RULE_COMPLETE_V1"; FAIL="NORA_PHASE2_TIME_RULE_FAIL_V1"
SCHEMA=["scenario_id","source_epoch","source_clock","new_york","broker","utc_offset_seconds","dst","session_member","friday_close","rollover","monday_delay","orb","m5_anchor_epoch","h1_anchor_epoch","conversion_state","reason_code","pass"]

def sha(x):
 b=x if isinstance(x,bytes) else canon(x).encode(); return hashlib.sha256(b).hexdigest()
def _id(*x): return sha(list(x))

def _runtime(): return b'''#ifndef NORA_PHASE2_TIME_RULE_RUNTIME_V1_MQH
#define NORA_PHASE2_TIME_RULE_RUNTIME_V1_MQH
bool NoraLeap(const int y){return (y%4==0 && (y%100!=0 || y%400==0));}
int NoraDays(const int y,const int m){int d[12]={31,28,31,30,31,30,31,31,30,31,30,31};return m==2&&NoraLeap(y)?29:d[m-1];}
int NoraSunday(const int y,const int m,const int nth){MqlDateTime q;ZeroMemory(q);q.year=y;q.mon=m;q.day=1;datetime t=StructToTime(q);TimeToStruct(t,q);return 1+((7-q.day_of_week)%7)+7*(nth-1);}
bool NoraDst(const long epoch){MqlDateTime u;TimeToStruct((datetime)epoch,u);int start=NoraSunday(u.year,3,2),end=NoraSunday(u.year,11,1);MqlDateTime q;ZeroMemory(q);q.year=u.year;q.mon=3;q.day=start;q.hour=7;long a=(long)StructToTime(q);ZeroMemory(q);q.year=u.year;q.mon=11;q.day=end;q.hour=6;long b=(long)StructToTime(q);return epoch>=a&&epoch<b;}
void NoraCivil(const long epoch,const int offset,MqlDateTime &o){TimeToStruct((datetime)(epoch+offset),o);}
bool NoraWindow(const MqlDateTime &x,const int sh,const int sm,const int eh,const int em){int z=x.hour*60+x.min,a=sh*60+sm,b=eh*60+em;return a<=b?(z>=a&&z<b):(z>=a||z<b);}
string NoraStamp(const MqlDateTime &x){return StringFormat("%04d-%02d-%02d %02d:%02d",x.year,x.mon,x.day,x.hour,x.min);}
#endif
'''

def _tester(rows):
 data=','.join('{"%s",%d,"%s","%s"}'%(r['scenario_id'],r['source_epoch'],r['source_clock'],r['conversion_state']) for r in rows)
 expected=','.join('"%s"'%r['reason_code'] for r in rows)
 return ('''#property strict
#include "%s"
struct NoraTimeCaseV1{string id;long epoch;string source;string conversion;};
NoraTimeCaseV1 NoraCases[%d]={%s}; string NoraExpected[%d]={%s};
int OnInit(){int f=FileOpen("%s",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,'\\t');if(f==INVALID_HANDLE){Print("%s");return INIT_FAILED;}FileWrite(f,"%s");for(int i=0;i<ArraySize(NoraCases);i++){NoraTimeCaseV1 c=NoraCases[i];bool rejected=(c.conversion!="declared_not_converted" && c.conversion!="broker_declared");bool dst=NoraDst(c.epoch);int off=dst?10800:7200;MqlDateTime ny,b;NoraCivil(c.epoch,dst?-14400:-18000,ny);NoraCivil(c.epoch,off,b);bool fri=!rejected && ny.day_of_week==5 && (ny.hour>16 || (ny.hour==16&&ny.min>=25));bool roll=!rejected&&NoraWindow(b,23,50,0,10);bool mon=!rejected&&b.day_of_week==1&&NoraWindow(b,0,0,0,15);bool orb=!rejected&&NoraWindow(b,9,30,10,0);bool session=!rejected&&b.day_of_week>0&&b.day_of_week<6&&NoraWindow(b,9,30,16,0);string reason=rejected?"conversion_rejected":(fri?"friday_close":(roll?"rollover":(mon?"monday_delay":(orb?"orb_active":(session?"session_member":"outside_session")))));bool pass=(reason==NoraExpected[i]);FileWrite(f,c.id,c.epoch,c.source,NoraStamp(ny),NoraStamp(b),off,dst?"true":"false",session?"true":"false",fri?"true":"false",roll?"true":"false",mon?"true":"false",orb?"true":"false",c.epoch-c.epoch%%300,c.epoch-c.epoch%%3600,c.conversion,reason,pass?"true":"false");if(!pass){FileClose(f);Print("%s");return INIT_FAILED;}}FileClose(f);Print("%s");return INIT_SUCCEEDED;}void OnDeinit(const int reason){}
'''%(RUNTIME,len(rows),data,len(rows),expected,CSV,FAIL,'","'.join(SCHEMA),FAIL,MARKER)).encode()

def generate(evidence_path,out_dir):
 ev=json.loads(Path(evidence_path).read_text()); out=Path(out_dir); names=[RUNTIME,TESTER,PACKAGE]
 if not out.is_dir() or any((out/n).exists() for n in names): raise ValueError("time-rule output target invalid")
 runtime=_runtime(); rs=sha(runtime); ri=_id("runtime",VERSION,rs)
 tester=_tester(ev['expected_vectors']); ts=sha(tester); ti=_id("tester",VERSION,ri,ev['time_rule_plan_identity'],ts)
 p={"version":VERSION,"target":"time_rules","runtime_identity":ri,"runtime_sha256":rs,"tester_identity":ti,"tester_sha256":ts,"time_rule_plan_identity":ev['time_rule_plan_identity'],"expected_vector_identity":ev['expected_vector_identity'],"csv_schema":SCHEMA,"csv_schema_identity":sha(SCHEMA),"scenario_identities":ev['scenario_identities'],"completion_marker":MARKER,"failure_marker":FAIL,"native_execution_attempted":False,"native_parity_accepted":False,"grammar_admitted":False,"searchable":False};p['package_identity']=_id("package",p)
 files={RUNTIME:runtime,TESTER:tester,PACKAGE:(canon(p)+'\n').encode()}; written=[]
 try:
  for n in names:(out/n).write_bytes(files[n]);written.append(n)
 except Exception:
  for n in written:(out/n).unlink(missing_ok=True)
  raise
 return p
