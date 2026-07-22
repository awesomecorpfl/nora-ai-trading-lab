from __future__ import annotations
import hashlib,json
from pathlib import Path
from lab.mql5gen.layer1_batch import _array,_strings
from lab.phase2_execution import canon,sha
from lab.phase2_layer1 import CSV_SCHEMA
ROOT=Path(__file__).resolve().parents[2];SCENARIOS=ROOT/'tests/fixtures/phase2_session_ohlc_scenarios.json';RUNTIME='NoraPhase2SessionOH LCRuntimeV1.mqh'.replace(' ','');TESTER='NoraPhase2SessionOHLCTesterV1.mq5';PACKAGE='phase2_session_ohlc_executable_package.json';CSV='nora_phase2_session_ohlc_v1.csv';MARKER='NORA_PHASE2_SESSION_OHLC_COMPLETE_V1';FAIL='NORA_PHASE2_SESSION_OHLC_FAIL_V1'
def runtime(): return '''#ifndef NORA_SESSION_OHLC_RUNTIME_V1_MQH
#define NORA_SESSION_OHLC_RUNTIME_V1_MQH
bool NoraSessionOHLCCompute(const string &sid[],const double &o[],const double &h[],const double &l[],const double &c[],const int n,const int which,double &v[]){ArrayResize(v,n);string cur="";double so=0,sh=0,sl=0;for(int i=0;i<n;i++){if(i==0||sid[i]!=cur){cur=sid[i];so=o[i];sh=h[i];sl=l[i];}else{sh=MathMax(sh,h[i]);sl=MathMin(sl,l[i]);}if(which==0)v[i]=so;else if(which==1)v[i]=sh;else if(which==2)v[i]=sl;else v[i]=c[i];}return true;}
#endif
'''
def tester():
 blocks=[]
 for i,s in enumerate(json.loads(SCENARIOS.read_text())['scenarios']):
  n=len(s['open']);w={'open':0,'high':1,'low':2,'close':3}[s['output']]
  blocks.append(f'''string sid{i}[{n}]={{{_strings(s['session_id'])}}};string t{i}[{n}]={{{_strings(s['timestamps'])}}};double o{i}[{n}]={{{_array(s['open'])}}};double h{i}[{n}]={{{_array(s['high'])}}};double l{i}[{n}]={{{_array(s['low'])}}};double c{i}[{n}]={{{_array(s['close'])}}};double v{i}[];if(!NoraSessionOHLCCompute(sid{i},o{i},h{i},l{i},c{i},{n},{w},v{i})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}for(int j=0;j<{n};j++)FileWrite(f,"{s['id']}","SessionOHLC","{s['output']}",j,t{i}[j],DoubleToString(v{i}[j],17),"false","steady_state","ok");''')
 return f'''#property strict
#include "{RUNTIME}"
int OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});{''.join(blocks)}FileClose(f);Print("{MARKER}");return INIT_SUCCEEDED;}}
void OnDeinit(const int reason){{}}
'''
def generate(out,evidence):
 out.mkdir(parents=True,exist_ok=True);rb=runtime().encode();tb=tester().encode();rh=hashlib.sha256(rb).hexdigest();th=hashlib.sha256(tb).hexdigest();ri=sha({'role':'runtime','content_sha256':rh});ti=sha({'role':'tester','runtime_identity':ri,'content_sha256':th});p={'schema_version':'nora.phase2_session_ohlc_executable_package_v1','target_identifier':'layer1_session_ohlc','rust_evidence_identity':evidence['rust_evidence_identity'],'expected_vector_identity':evidence['expected_vector_identity'],'output_schema':CSV_SCHEMA,'output_schema_identity':sha(CSV_SCHEMA),'runtime_identity':ri,'tester_identity':ti,'runtime_sha256':rh,'tester_sha256':th,'result_filename':CSV,'completion_marker':MARKER,'failure_marker':FAIL,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False};p['package_identity']=sha(p);(out/RUNTIME).write_bytes(rb);(out/TESTER).write_bytes(tb);(out/PACKAGE).write_text(canon(p)+'\n');return p
if __name__=='__main__':
 e=json.loads((ROOT/'tests/fixtures/phase2_session_ohlc_local_evidence/manifest.json').read_text());print(json.dumps(generate(ROOT/'tests/fixtures/phase2_session_ohlc_native',e),indent=2,sort_keys=True))
