"""Standalone RSI native package builder; does not mutate the accepted Layer-1 batch."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from lab.mql5gen.layer1_batch import rsi_runtime, _array, _nulls, _strings
from lab.phase2_execution import canon, sha
from lab.phase2_layer1 import CSV_SCHEMA

RUNTIME='NoraPhase2RsiRuntimeV1.mqh'
TESTER='NoraPhase2RsiTesterV1.mq5'
PACKAGE='phase2_rsi_executable_package.json'
CSV='nora_phase2_rsi_v1.csv'
MARKER='NORA_PHASE2_RSI_COMPLETE_V1'
FAIL='NORA_PHASE2_RSI_FAIL_V1'
ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=ROOT/'tests/fixtures/phase2_rsi_scenarios.json'

def tester():
 blocks=[]
 for index,s in enumerate(json.loads(SCENARIOS.read_text())['scenarios']):
  n=len(s['values'])
  if s['period']==0:
   blocks.append(f'FileWrite(f,"{s["id"]}","RSI","value","NULL","NULL","NULL","true","invalid_input","invalid_period");')
   continue
  blocks.append(f'''double v{index}[{n}]={{{_array(s["values"])}}};bool n{index}[{n}]={{{_nulls(s["values"])}}};string t{index}[{n}]={{{_strings(s["timestamps"])}}};double o{index}[];bool z{index}[];
if(!NoraRsiCompute(v{index},n{index},{n},{s["period"]},o{index},z{index})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}
for(int i=0;i<{n};i++){{string reason=!z{index}[i]?"ok":(n{index}[i]?"null_input":"warmup");string phase=!z{index}[i]?"steady_state":"warmup_or_null";FileWrite(f,"{s["id"]}","RSI","value",i,t{index}[i],z{index}[i]?"NULL":DoubleToString(o{index}[i],17),z{index}[i]?"true":"false",phase,reason);}}''')
 return f'''#property strict
#include "{RUNTIME}"
int OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});{''.join(blocks)}FileClose(f);Print("{MARKER}");return INIT_SUCCEEDED;}}
void OnDeinit(const int reason){{}}
'''

def generate(out:Path,evidence:dict):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if any((out/name).exists() for name in (RUNTIME,TESTER,PACKAGE)): raise ValueError('RSI output target occupied')
 rt=rsi_runtime().encode();ts=tester().encode();rsha=hashlib.sha256(rt).hexdigest();tsha=hashlib.sha256(ts).hexdigest()
 rid=sha({'role':'runtime','content_sha256':rsha});tid=sha({'role':'tester','runtime_identity':rid,'content_sha256':tsha})
 package={'schema_version':'nora.phase2_rsi_executable_package_v1','target_identifier':'layer1_rsi','rust_evidence_identity':evidence['rust_evidence_identity'],'expected_vector_identity':evidence['expected_vector_identity'],'output_schema':CSV_SCHEMA,'output_schema_identity':evidence['output_schema_identity'],'runtime_identity':rid,'tester_identity':tid,'runtime_sha256':rsha,'tester_sha256':tsha,'result_filename':CSV,'completion_marker':MARKER,'failure_marker':FAIL,'native_execution_attempted':False,'native_parity_accepted':False,'grammar_admitted':False,'searchable':False}
 package['package_identity']=sha(package)
 (out/RUNTIME).write_bytes(rt);(out/TESTER).write_bytes(ts);(out/PACKAGE).write_text(canon(package)+'\n')
 return package
