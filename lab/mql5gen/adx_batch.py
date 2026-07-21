from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab.mql5gen.layer1_batch import _array, _strings
from lab.phase2_execution import canon, sha
from lab.phase2_layer1 import CSV_SCHEMA

RUNTIME = "NoraPhase2AdxRuntimeV1.mqh"
TESTER = "NoraPhase2AdxTesterV1.mq5"
PACKAGE = "phase2_adx_executable_package.json"
CSV = "nora_phase2_adx_v1.csv"
MARKER = "NORA_PHASE2_ADX_COMPLETE_V1"
FAIL = "NORA_PHASE2_ADX_FAIL_V1"
ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "tests/fixtures/phase2_adx_scenarios.json"


def runtime() -> str:
    return '''#ifndef NORA_PHASE2_ADX_RUNTIME_V1_MQH
#define NORA_PHASE2_ADX_RUNTIME_V1_MQH
bool NoraAdxCompute(const double &h[],const double &l[],const double &c[],const int count,const int period,double &out[],bool &valid[]){
 if(period<1)return false;ArrayResize(out,count);ArrayResize(valid,count);double plus[],minus[],tr[],sp[],sm[],st[],dx[],dv[];ArrayResize(plus,count);ArrayResize(minus,count);ArrayResize(tr,count);ArrayResize(sp,count);ArrayResize(sm,count);ArrayResize(st,count);ArrayResize(dx,count);ArrayResize(dv,count);for(int i=0;i<count;i++){out[i]=0.0;valid[i]=false;plus[i]=0.0;minus[i]=0.0;tr[i]=0.0;sp[i]=0.0;sm[i]=0.0;st[i]=0.0;dx[i]=0.0;dv[i]=false;}
 for(int i=1;i<count;i++){double up=h[i]-h[i-1],dn=l[i-1]-l[i];plus[i]=(up>dn&&up>0.0)?up:0.0;minus[i]=(dn>up&&dn>0.0)?dn:0.0;tr[i]=MathMax(h[i]-l[i],MathMax(MathAbs(h[i]-c[i-1]),MathAbs(l[i]-c[i-1])));}
 if(count<period)return true;sp[period-1]=0.0;sm[period-1]=0.0;st[period-1]=0.0;for(int j=0;j<period;j++){sp[period-1]+=plus[j];sm[period-1]+=minus[j];st[period-1]+=tr[j];}sp[period-1]/=period;sm[period-1]/=period;st[period-1]/=period;
 for(int i=period;i<count;i++){sp[i]=(sp[i-1]*(period-1)+plus[i])/period;sm[i]=(sm[i-1]*(period-1)+minus[i])/period;st[i]=(st[i-1]*(period-1)+tr[i])/period;}
 for(int i=period-1;i<count;i++){if(st[i]==0.0)continue;double denom=sp[i]+sm[i];if(denom==0.0)continue;dx[i]=100.0*MathAbs(sp[i]-sm[i])/denom;dv[i]=true;}
 double seed=0.0;int seen=0;bool seeded=false;double state=0.0;for(int i=0;i<count;i++){if(!dv[i])continue;if(!seeded){seed+=dx[i];seen++;if(seen==period){state=seed/period;out[i]=state;valid[i]=true;seeded=true;}}else{state=(state*(period-1)+dx[i])/period;out[i]=state;valid[i]=true;}}
 return true;}
#endif
'''


def tester() -> str:
    blocks = []
    for index, scenario in enumerate(json.loads(SCENARIOS.read_text())["scenarios"]):
        n = len(scenario["close"])
        p = scenario["period"]
        if p == 0:
            blocks.append(
                f'FileWrite(f,"{scenario["id"]}","ADX","adx","NULL","NULL","NULL","true","invalid_input","invalid_period");'
            )
            continue
        blocks.append(
            f'''double h{index}[{n}]={{{_array(scenario["high"])}}};double l{index}[{n}]={{{_array(scenario["low"])}}};double c{index}[{n}]={{{_array(scenario["close"])}}};string t{index}[{n}]={{{_strings(scenario["timestamps"])}}};double a{index}[];bool v{index}[];
if(!NoraAdxCompute(h{index},l{index},c{index},{n},{p},a{index},v{index})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}
for(int i=0;i<{n};i++){{FileWrite(f,"{scenario["id"]}","ADX","adx",i,t{index}[i],v{index}[i]?DoubleToString(a{index}[i],17):"NULL",v{index}[i]?"false":"true",v{index}[i]?"steady_state":"warmup_or_null",v{index}[i]?"ok":"warmup");}}'''
        )
    return f'''#property strict
#include "{RUNTIME}"
int OnInit(){{int f=FileOpen("{CSV}",FILE_WRITE|FILE_CSV|FILE_ANSI,'\\t');if(f==INVALID_HANDLE){{Print("{FAIL}");return INIT_FAILED;}}FileWrite(f,{_strings(CSV_SCHEMA)});{''.join(blocks)}FileClose(f);Print("{MARKER}");return INIT_SUCCEEDED;}}
void OnDeinit(const int reason){{}}
'''


def generate(out: Path, evidence: dict) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    runtime_bytes = runtime().encode()
    tester_bytes = tester().encode()
    runtime_sha = hashlib.sha256(runtime_bytes).hexdigest()
    tester_sha = hashlib.sha256(tester_bytes).hexdigest()
    runtime_identity = sha({"role": "runtime", "content_sha256": runtime_sha})
    tester_identity = sha({"role": "tester", "runtime_identity": runtime_identity, "content_sha256": tester_sha})
    package = {
        "schema_version": "nora.phase2_adx_executable_package_v1",
        "target_identifier": "layer1_adx",
        "rust_evidence_identity": evidence["rust_evidence_identity"],
        "expected_vector_identity": evidence["expected_vector_identity"],
        "output_schema": CSV_SCHEMA,
        "output_schema_identity": sha(CSV_SCHEMA),
        "runtime_identity": runtime_identity,
        "tester_identity": tester_identity,
        "runtime_sha256": runtime_sha,
        "tester_sha256": tester_sha,
        "result_filename": CSV,
        "completion_marker": MARKER,
        "failure_marker": FAIL,
        "native_execution_attempted": False,
        "native_parity_accepted": False,
        "grammar_admitted": False,
        "searchable": False,
    }
    package["package_identity"] = sha(package)
    (out / RUNTIME).write_bytes(runtime_bytes)
    (out / TESTER).write_bytes(tester_bytes)
    (out / PACKAGE).write_text(canon(package) + "\n")
    return package
