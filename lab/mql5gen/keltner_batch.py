from __future__ import annotations
import hashlib,json
from pathlib import Path
from lab.mql5gen.layer1_batch import _array,_strings
from lab.phase2_execution import canon,sha
from lab.phase2_layer1 import CSV_SCHEMA
ROOT=Path(__file__).resolve().parents[2];SC=ROOT/'tests/fixtures/phase2_keltner_scenarios.json';R='NoraPhase2KeltnerRuntimeV1.mqh';T='NoraPhase2KeltnerTesterV1.mq5';P='phase2_keltner_executable_package.json';CSV='nora_phase2_keltner_v1.csv';MARK='NORA_PHASE2_KELTNER_COMPLETE_V1';FAIL='NORA_PHASE2_KELTNER_FAIL_V1'
def runtime():return '''#ifndef NORA_PHASE2_KELTNER_RUNTIME_V1_MQH
#define NORA_PHASE2_KELTNER_RUNTIME_V1_MQH
bool NoraKeltner(const double &h[],const double &l[],const double &c[],int n,int p,double k,int which,double &v[],bool &ok[]){if(p<=0)return false;ArrayResize(v,n);ArrayResize(ok,n);for(int i=0;i<n;i++){v[i]=0;ok[i]=false;}double tr[],ee[],aa[];ArrayResize(tr,n);ArrayResize(ee,n);ArrayResize(aa,n);for(int i=0;i<n;i++){tr[i]=(i==0)?h[i]-l[i]:MathMax(h[i]-l[i],MathMax(MathAbs(h[i]-c[i-1]),MathAbs(l[i]-c[i-1])));ee[i]=0;aa[i]=0;}for(int i=p-1;i<n;i++){if(i==p-1){for(int j=0;j<p;j++){ee[i]+=c[j];aa[i]+=tr[j];}ee[i]/=p;aa[i]/=p;}else{ee[i]=ee[i-1]+(2.0/(p+1.0))*(c[i]-ee[i-1]);aa[i]=((aa[i-1]*(p-1))+tr[i])/p;}v[i]=(which==0)?ee[i]:((which==1)?ee[i]+k*aa[i]:ee[i]-k*aa[i]);ok[i]=true;}return true;}
#endif
'''
def tester():
 b=[]
 for i,s in enumerate(json.loads(SC.read_text())['scenarios']):
  n=len(s['close']);p=s['period'];w={'middle':0,'upper':1,'lower':2}[s['output']]
  if p<=0:b.append(f'FileWrite(f,"{s["id"]}","Keltner","{s["output"]}","NULL","NULL","NULL","true","invalid_input","invalid_period");');continue
  b.append(f'''double h{i}[{n}]={{{_array(s["high"])}}};double l{i}[{n}]={{{_array(s["low"])}}};double c{i}[{n}]={{{_array(s["close"])}}};string t{i}[{n}]={{{_strings(s["timestamps"])}}};double v{i}[];bool q{i}[];if(!NoraKeltner(h{i},l{i},c{i},{n},{p},{s["k"]},{w},v{i},q{i})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}for(int j=0;j<{n};j++)FileWrite(f,"{s["id"]}","Keltner","{s["output"]}",j,t{i}[j],q{i}[j]?DoubleToString(v{i}[j],17):"NULL",q{i}[j]?"false":"true",q{i}[j]?"steady_state":"warmup_or_null",q{i}[j]?"ok":"warmup");''')
 return f'''#property strict
#include "{R}"
int OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});{''.join(b)}FileClose(f);Print("{MARK}");return INIT_SUCCEEDED;}}void OnDeinit(const int reason){{}}
'''
def generate(out,e):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rb=runtime().encode();tb=tester().encode();rh=hashlib.sha256(rb).hexdigest();th=hashlib.sha256(tb).hexdigest();ri=sha({'role':'runtime','content_sha256':rh});ti=sha({'role':'tester','runtime_identity':ri,'content_sha256':th});p={'schema_version':'nora.phase2_keltner_executable_package_v1','target_identifier':'layer1_keltner','rust_evidence_identity':e['rust_evidence_identity'],'expected_vector_identity':e['expected_vector_identity'],'output_schema':CSV_SCHEMA,'output_schema_identity':sha(CSV_SCHEMA),'runtime_identity':ri,'tester_identity':ti,'runtime_sha256':rh,'tester_sha256':th,'result_filename':CSV,'completion_marker':MARK,'failure_marker':FAIL,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False};p['package_identity']=sha(p);(out/R).write_bytes(rb);(out/T).write_bytes(tb);(out/P).write_text(canon(p)+'\n');return p
if __name__=='__main__':
 e=json.loads((ROOT/'tests/fixtures/phase2_keltner_local_evidence.json').read_text());print(json.dumps(generate(ROOT/'tests/fixtures/phase2_keltner_native',e),indent=2))
