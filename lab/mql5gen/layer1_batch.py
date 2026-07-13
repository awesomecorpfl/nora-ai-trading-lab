"""Deterministic chart-independent MQL5 source for the first Layer-1 batch."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab.phase2_execution import canon, sha
from lab.phase2_layer1 import CSV_SCHEMA, load_scenarios

RUNTIME="NoraPhase2Layer1BatchRuntimeV1.mqh"
TESTER="NoraPhase2Layer1BatchTesterCanaryV1.mq5"
PACKAGE="phase2_layer1_batch_executable_package.json"
CSV="nora_phase2_layer1_batch_v1.csv"
MARKER="NORA_PHASE2_LAYER1_BATCH_COMPLETE_V1"
FAIL="NORA_PHASE2_LAYER1_BATCH_FAIL_V1"

def translate_feature_node(node:dict)->dict:
    if not isinstance(node,dict) or set(node)!={"type","input","period"}:raise ValueError("strict layer1 feature schema")
    if node["type"] not in ("ema","highest","lowest"):raise ValueError("unsupported layer1 feature")
    source=node["input"]
    if not isinstance(source,dict) or source.get("type")!="series" or not isinstance(source.get("name"),str) or not source["name"] or set(source)!={"type","name"}:raise ValueError("typed numeric input required")
    if not isinstance(node["period"],int) or isinstance(node["period"],bool) or node["period"]<1:raise ValueError("positive period required")
    canonical=json.dumps(node,sort_keys=True,separators=(",",":"))
    value={"schema_version":"nora.layer1_ast_mql5_binding_v1","canonical_node":canonical,"node_identity":sha(canonical),
           "input_type":"numeric","output_type":"numeric","output_name":"value","runtime_function":"NoraLayer1Compute",
           "kind":{"ema":0,"highest":1,"lowest":2}[node["type"]],"period":node["period"],"reference_mode":"independent_generated","grammar_admitted":False,"searchable":False}
    value["translation_identity"]=sha(value);return value


def _array(values): return ",".join("0.0" if x is None else format(x,".17g") for x in values)
def _nulls(values): return ",".join("true" if x is None else "false" for x in values)
def _strings(values): return ",".join('"'+x+'"' for x in values)


def runtime()->str:
    return '''#ifndef NORA_PHASE2_LAYER1_BATCH_RUNTIME_V1_MQH
#define NORA_PHASE2_LAYER1_BATCH_RUNTIME_V1_MQH
bool NoraLayer1Compute(const int kind,const double &source[],const bool &source_null[],const int count,const int period,double &out[],bool &out_null[]){
 if(period<1)return false;ArrayResize(out,count);ArrayResize(out_null,count);for(int i=0;i<count;i++){out[i]=0.0;out_null[i]=true;}
 if(kind==0){double seed=0.0,state=0.0;int seeded=0;bool ready=false;double alpha=2.0/(period+1.0);for(int i=0;i<count;i++){if(source_null[i]){seed=0.0;seeded=0;ready=false;continue;}if(ready){state=state+alpha*(source[i]-state);out[i]=state;out_null[i]=false;}else{seed+=source[i];seeded++;if(seeded==period){state=seed/period;ready=true;out[i]=state;out_null[i]=false;}}}return true;}
 for(int i=period-1;i<count;i++){bool missing=false;double value=(kind==1?-DBL_MAX:DBL_MAX);for(int j=i+1-period;j<=i;j++){if(source_null[j]){missing=true;break;}if(kind==1)value=MathMax(value,source[j]);else value=MathMin(value,source[j]);}if(!missing){out[i]=value;out_null[i]=false;}}return true;}
#endif
'''


def tester()->str:
    blocks=[]
    for index,s in enumerate(load_scenarios()["scenarios"]):
        kind={"EMA":0,"Highest":1,"Lowest":2}[s["node"]];n=len(s["values"])
        if s["period"]==0:
            blocks.append(f'FileWrite(f,"{s["id"]}","{s["node"]}","{s["output"]}","NULL","NULL","NULL","true","invalid_input","invalid_period");')
            continue
        blocks.append(f'''double v{index}[{n}]={{{_array(s["values"])}}};bool n{index}[{n}]={{{_nulls(s["values"])}}};string t{index}[{n}]={{{_strings(s["timestamps"])}}};double o{index}[];bool z{index}[];
if(!NoraLayer1Compute({kind},v{index},n{index},{n},{s["period"]},o{index},z{index})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}
for(int i=0;i<{n};i++){{string reason=!z{index}[i]?"ok":(n{index}[i]?"null_input":"warmup");string phase=!z{index}[i]?"steady_state":"warmup_or_null";FileWrite(f,"{s["id"]}","{s["node"]}","{s["output"]}",i,t{index}[i],z{index}[i]?"NULL":DoubleToString(o{index}[i],17),z{index}[i]?"true":"false",phase,reason);}}''')
    return f'''#property strict
#include "{RUNTIME}"
int OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});
{''.join(blocks)}
FileClose(f);Print("{MARKER}");return INIT_SUCCEEDED;}}
void OnDeinit(const int reason){{}}
'''


def generate(out:Path,evidence:dict,batch_plan:dict,protocol:dict)->dict:
    out=Path(out);names=(RUNTIME,TESTER,PACKAGE)
    if not out.is_dir() or any((out/x).exists() for x in names):raise ValueError("layer1 output target invalid")
    rt=runtime().encode();ts=tester().encode();rsha=hashlib.sha256(rt).hexdigest();tsha=hashlib.sha256(ts).hexdigest();rid=sha({"role":"runtime","content_sha256":rsha});tid=sha({"role":"tester","runtime_identity":rid,"content_sha256":tsha})
    package={"schema_version":"nora.layer1_batch_executable_package_v1","target_identifier":"layer1_first_batch",
             "selected_node_identities":evidence["selected_node_identities"],"scenario_identities":evidence["scenario_identities"],
             "rust_task_output_identity":evidence["rust_task_output_identity"],"expected_vector_identity":evidence["expected_vector_identity"],
             "batch_plan_identity":batch_plan["batch_plan_identity"],"parity_protocol_identity":protocol["parity_protocol_identity"],
             "reference_modes":batch_plan["reference_modes"],"runtime_identity":rid,"tester_identity":tid,
             "runtime_sha256":rsha,"tester_sha256":tsha,"csv_schema":CSV_SCHEMA,
             "csv_schema_identity":sha(CSV_SCHEMA),"result_filename":CSV,"completion_marker":MARKER,"failure_marker":FAIL,
             "native_execution_attempted":False,"native_parity_accepted":False,"grammar_admitted":False,"searchable":False}
    package["package_identity"]=sha(package)
    (out/RUNTIME).write_bytes(rt);(out/TESTER).write_bytes(ts);(out/PACKAGE).write_text(canon(package)+"\n")
    return package
