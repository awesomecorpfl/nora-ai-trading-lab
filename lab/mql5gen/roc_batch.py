from __future__ import annotations
import hashlib,json
from pathlib import Path
from lab.mql5gen.layer1_batch import _array,_nulls,_strings
from lab.phase2_execution import canon,sha
from lab.phase2_layer1 import CSV_SCHEMA
RUNTIME='NoraPhase2RocRuntimeV1.mqh'; TESTER='NoraPhase2RocTesterV1.mq5'; PACKAGE='phase2_roc_executable_package.json'; CSV='nora_phase2_roc_v1.csv'; MARKER='NORA_PHASE2_ROC_COMPLETE_V1'; FAIL='NORA_PHASE2_ROC_FAIL_V1'
ROOT=Path(__file__).resolve().parents[2]; SCENARIOS=ROOT/'tests/fixtures/phase2_roc_scenarios.json'
def runtime(): return '''#ifndef NORA_PHASE2_ROC_RUNTIME_V1_MQH\n#define NORA_PHASE2_ROC_RUNTIME_V1_MQH\nbool NoraRocCompute(const double &s[],const bool &n[],const int c,const int p,double &o[],bool &z[]){if(p<=0)return false;ArrayResize(o,c);ArrayResize(z,c);for(int i=0;i<c;i++){z[i]=true;o[i]=0.0;if(i<p||n[i]||n[i-p]||s[i-p]==0.0)continue;o[i]=(s[i]/s[i-p]-1.0)*100.0;z[i]=false;}return true;}\n#endif\n'''
def tester():
 blocks=[]
 for i,s in enumerate(json.loads(SCENARIOS.read_text())['scenarios']):
  n=len(s['values']); p=s['period']
  if p==0: blocks.append(f'FileWrite(f,"{s["id"]}","ROC","value","NULL","NULL","NULL","true","invalid_input","invalid_period");'); continue
  blocks.append(f'''double v{i}[{n}]={{{_array(s["values"])}}};bool n{i}[{n}]={{{_nulls(s["values"])}}};string t{i}[{n}]={{{_strings(s["timestamps"])}}};double o{i}[];bool z{i}[];if(!NoraRocCompute(v{i},n{i},{n},{p},o{i},z{i})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}for(int j=0;j<{n};j++){{string reason=z{i}[j]?(n{i}[j]?"null_input":(j<{p}?"warmup":"zero_baseline")):"ok";string phase=z{i}[j]?"warmup_or_null":"steady_state";FileWrite(f,"{s["id"]}","ROC","value",j,t{i}[j],z{i}[j]?"NULL":DoubleToString(o{i}[j],17),z{i}[j]?"true":"false",phase,reason);}}''')
 return f'''#property strict\n#include "{RUNTIME}"\nint OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});{''.join(blocks)}FileClose(f);Print("{MARKER}");return INIT_SUCCEEDED;}}\nvoid OnDeinit(const int reason){{}}\n'''
def generate(out:Path,evidence:dict):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 rt=runtime().encode();ts=tester().encode();rsha=hashlib.sha256(rt).hexdigest();tsha=hashlib.sha256(ts).hexdigest();rid=sha({'role':'runtime','content_sha256':rsha});tid=sha({'role':'tester','runtime_identity':rid,'content_sha256':tsha})
 package={'schema_version':'nora.phase2_roc_executable_package_v1','target_identifier':'layer1_roc','rust_evidence_identity':evidence['rust_evidence_identity'],'output_schema':CSV_SCHEMA,'runtime_identity':rid,'tester_identity':tid,'runtime_sha256':rsha,'tester_sha256':tsha,'result_filename':CSV,'completion_marker':MARKER,'failure_marker':FAIL,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False};package['package_identity']=sha(package)
 (out/RUNTIME).write_bytes(rt);(out/TESTER).write_bytes(ts);(out/PACKAGE).write_text(canon(package)+'\n');return package
