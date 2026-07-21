from __future__ import annotations
import hashlib,json
from pathlib import Path
from lab.mql5gen.layer1_batch import _array,_strings
from lab.phase2_execution import canon,sha
from lab.phase2_layer1 import CSV_SCHEMA
RUNTIME='NoraPhase2KamaRuntimeV1.mqh';TESTER='NoraPhase2KamaTesterV1.mq5';PACKAGE='phase2_kama_executable_package.json';CSV='nora_phase2_kama_v1.csv';MARKER='NORA_PHASE2_KAMA_COMPLETE_V1';FAIL='NORA_PHASE2_KAMA_FAIL_V1';ROOT=Path(__file__).resolve().parents[2];SCENARIOS=ROOT/'tests/fixtures/phase2_kama_scenarios.json'
def runtime():return '''#ifndef NORA_PHASE2_KAMA_RUNTIME_V1_MQH
#define NORA_PHASE2_KAMA_RUNTIME_V1_MQH
bool NoraKamaCompute(const double &x[],const int count,const int period,double &out[],bool &valid[]){if(period<1)return false;ArrayResize(out,count);ArrayResize(valid,count);for(int i=0;i<count;i++){out[i]=0.0;valid[i]=false;}if(count<=period)return true;double k=x[period];out[period]=k;valid[period]=true;double fc=2.0/(2.0+1.0),sc=2.0/(30.0+1.0);for(int i=period+1;i<count;i++){double path=0.0;for(int j=i-period+2;j<=i;j++)path+=MathAbs(x[j]-x[j-1]);double er=(path==0.0)?0.0:MathAbs(x[i]-x[i-period])/path;double a=MathPow(er*(fc-sc)+sc,2.0);k+=a*(x[i]-k);out[i]=k;valid[i]=true;}return true;}
#endif
'''
def tester():
 blocks=[]
 for i,s in enumerate(json.loads(SCENARIOS.read_text())['scenarios']):
  n=len(s['values']);p=s['period']
  if p==0:blocks.append(f'FileWrite(f,"{s["id"]}","KAMA","value","NULL","NULL","NULL","true","invalid_input","invalid_period");');continue
  blocks.append(f'''double x{i}[{n}]={{{_array(s["values"])}}};string t{i}[{n}]={{{_strings(s["timestamps"])}}};double k{i}[];bool v{i}[];if(!NoraKamaCompute(x{i},{n},{p},k{i},v{i})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}for(int j=0;j<{n};j++){{FileWrite(f,"{s["id"]}","KAMA","value",j,t{i}[j],v{i}[j]?DoubleToString(k{i}[j],17):"NULL",v{i}[j]?"false":"true",v{i}[j]?"steady_state":"warmup_or_null",v{i}[j]?"ok":"warmup");}}''')
 return f'''#property strict
#include "{RUNTIME}"
int OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});{''.join(blocks)}FileClose(f);Print("{MARKER}");return INIT_SUCCEEDED;}}
void OnDeinit(const int reason){{}}
'''
def generate(out:Path,evidence:dict)->dict:
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rb=runtime().encode();tb=tester().encode();rh=hashlib.sha256(rb).hexdigest();th=hashlib.sha256(tb).hexdigest();ri=sha({'role':'runtime','content_sha256':rh});ti=sha({'role':'tester','runtime_identity':ri,'content_sha256':th});p={'schema_version':'nora.phase2_kama_executable_package_v1','target_identifier':'layer1_kama','rust_evidence_identity':evidence['rust_evidence_identity'],'expected_vector_identity':evidence['expected_vector_identity'],'output_schema':CSV_SCHEMA,'output_schema_identity':sha(CSV_SCHEMA),'runtime_identity':ri,'tester_identity':ti,'runtime_sha256':rh,'tester_sha256':th,'result_filename':CSV,'completion_marker':MARKER,'failure_marker':FAIL,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False};p['package_identity']=sha(p);(out/RUNTIME).write_bytes(rb);(out/TESTER).write_bytes(tb);(out/PACKAGE).write_text(canon(p)+'\n');return p
