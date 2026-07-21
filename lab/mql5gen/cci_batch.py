from __future__ import annotations
import hashlib,json
from pathlib import Path
from lab.mql5gen.layer1_batch import _array,_strings
from lab.phase2_execution import canon,sha
from lab.phase2_layer1 import CSV_SCHEMA
RUNTIME='NoraPhase2CCIRuntimeV1.mqh';TESTER='NoraPhase2CCITesterV1.mq5';PACKAGE='phase2_cci_executable_package.json';CSV='nora_phase2_cci_v1.csv';MARKER='NORA_PHASE2_CCI_COMPLETE_V1';FAIL='NORA_PHASE2_CCI_FAIL_V1';ROOT=Path(__file__).resolve().parents[2];SCENARIOS=ROOT/'tests/fixtures/phase2_cci_scenarios.json'
def runtime(): return '''#ifndef NORA_PHASE2_CCI_RUNTIME_V1_MQH
#define NORA_PHASE2_CCI_RUNTIME_V1_MQH
bool NoraCCICompute(const double &high[],const double &low[],const double &close[],const int count,const int period,double &value[],bool &valid[]){if(period<=0)return false;ArrayResize(value,count);ArrayResize(valid,count);for(int i=0;i<count;i++){value[i]=0.0;valid[i]=false;}for(int i=period-1;i<count;i++){double sum=0.0;for(int j=0;j<period;j++)sum+=(high[i-period+1+j]+low[i-period+1+j]+close[i-period+1+j])/3.0;double mean=sum/period;double dev=0.0;for(int j=0;j<period;j++){double tp=(high[i-period+1+j]+low[i-period+1+j]+close[i-period+1+j])/3.0;dev+=MathAbs(tp-mean);}dev/=period;double tp=(high[i]+low[i]+close[i])/3.0;value[i]=(dev==0.0)?0.0:(tp-mean)/(0.015*dev);valid[i]=true;}return true;}
#endif
'''
def tester():
 blocks=[]
 for i,s in enumerate(json.loads(SCENARIOS.read_text())['scenarios']):
  n=len(s['high']);p=s['period'];o=s['output']
  if p<=0: blocks.append(f'FileWrite(f,"{s["id"]}","CCI","{o}","NULL","NULL","NULL","true","invalid_input","invalid_period");');continue
  blocks.append(f'''double h{i}[{n}]={{{_array(s["high"])}}};double l{i}[{n}]={{{_array(s["low"])}}};double c{i}[{n}]={{{_array(s["close"])}}};string t{i}[{n}]={{{_strings(s["timestamps"])}}};double v{i}[];bool ok{i}[];if(!NoraCCICompute(h{i},l{i},c{i},{n},{p},v{i},ok{i})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}for(int j=0;j<{n};j++){{FileWrite(f,"{s["id"]}","CCI","{o}",j,t{i}[j],ok{i}[j]?DoubleToString(v{i}[j],17):"NULL",ok{i}[j]?"false":"true",ok{i}[j]?"steady_state":"warmup_or_null",ok{i}[j]?"ok":"warmup");}}''')
 return f'''#property strict
#include "{RUNTIME}"
int OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});{''.join(blocks)}FileClose(f);Print("{MARKER}");return INIT_SUCCEEDED;}}
void OnDeinit(const int reason){{}}
'''
def generate(out:Path,evidence:dict)->dict:
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rb=runtime().encode();tb=tester().encode();rh=hashlib.sha256(rb).hexdigest();th=hashlib.sha256(tb).hexdigest();ri=sha({'role':'runtime','content_sha256':rh});ti=sha({'role':'tester','runtime_identity':ri,'content_sha256':th});p={'schema_version':'nora.phase2_cci_executable_package_v1','target_identifier':'layer1_cci','rust_evidence_identity':evidence['rust_evidence_identity'],'expected_vector_identity':evidence['expected_vector_identity'],'output_schema':CSV_SCHEMA,'output_schema_identity':sha(CSV_SCHEMA),'runtime_identity':ri,'tester_identity':ti,'runtime_sha256':rh,'tester_sha256':th,'result_filename':CSV,'completion_marker':MARKER,'failure_marker':FAIL,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False};p['package_identity']=sha(p);(out/RUNTIME).write_bytes(rb);(out/TESTER).write_bytes(tb);(out/PACKAGE).write_text(canon(p)+'\n');return p
if __name__=='__main__':
 e=json.loads((ROOT/'tests/fixtures/phase2_cci_local_evidence/rust_evidence.json').read_text());print(json.dumps(generate(ROOT/'tests/fixtures/phase2_cci_native',e),indent=2,sort_keys=True))
