from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab.mql5gen.layer1_batch import _array, _nulls, _strings
from lab.phase2_execution import canon, sha
from lab.phase2_layer1 import CSV_SCHEMA

RUNTIME = "NoraPhase2StochasticRuntimeV1.mqh"
TESTER = "NoraPhase2StochasticTesterV1.mq5"
PACKAGE = "phase2_stochastic_executable_package.json"
CSV = "nora_phase2_stochastic_v1.csv"
MARKER = "NORA_PHASE2_STOCHASTIC_COMPLETE_V1"
FAIL = "NORA_PHASE2_STOCHASTIC_FAIL_V1"
ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "tests/fixtures/phase2_stochastic_scenarios.json"


def runtime() -> str:
    return '''#ifndef NORA_PHASE2_STOCHASTIC_RUNTIME_V1_MQH
#define NORA_PHASE2_STOCHASTIC_RUNTIME_V1_MQH
bool NoraStochasticCompute(const double &h[],const double &l[],const double &c[],const bool &n[],const int count,const int period,const int dperiod,double &k[],double &d[],bool &kn[],bool &dn[]){
 if(period<1||dperiod<1)return false;ArrayResize(k,count);ArrayResize(d,count);ArrayResize(kn,count);ArrayResize(dn,count);for(int i=0;i<count;i++){k[i]=0.0;d[i]=0.0;kn[i]=true;dn[i]=true;}
 for(int i=period-1;i<count;i++){double hi=-DBL_MAX,lo=DBL_MAX;bool missing=false;for(int j=i+1-period;j<=i;j++){if(n[j]){missing=true;break;}hi=MathMax(hi,h[j]);lo=MathMin(lo,l[j]);}if(missing)continue;k[i]=(hi==lo?50.0:100.0*(c[i]-lo)/(hi-lo));kn[i]=false;}
 for(int i=0;i<count;i++){if(i+1<dperiod)continue;double total=0.0;bool missing=false;for(int j=i+1-dperiod;j<=i;j++){if(kn[j]){missing=true;break;}total+=k[j];}if(!missing){d[i]=total/dperiod;dn[i]=false;}}
 return true;}
#endif
'''


def tester() -> str:
    blocks = []
    for index, scenario in enumerate(json.loads(SCENARIOS.read_text())["scenarios"]):
        n = len(scenario["close"])
        p = scenario["period"]
        dp = scenario["d_period"]
        if p == 0 or dp == 0:
            blocks.append(
                f'FileWrite(f,"{scenario["id"]}","Stochastic","k","NULL","NULL","NULL","true","invalid_input","invalid_period");'
                f'FileWrite(f,"{scenario["id"]}","Stochastic","d","NULL","NULL","NULL","true","invalid_input","invalid_period");'
            )
            continue
        blocks.append(
            f'''double h{index}[{n}]={{{_array(scenario["high"])}}};double l{index}[{n}]={{{_array(scenario["low"])}}};double c{index}[{n}]={{{_array(scenario["close"])}}};bool n{index}[{n}]={{{_nulls(scenario["close"])}}};string t{index}[{n}]={{{_strings(scenario["timestamps"])}}};double k{index}[];double d{index}[];bool kn{index}[];bool dn{index}[];
if(!NoraStochasticCompute(h{index},l{index},c{index},n{index},{n},{p},{dp},k{index},d{index},kn{index},dn{index})){{FileClose(f);Print("{FAIL}");return INIT_FAILED;}}
for(int i=0;i<{n};i++){{FileWrite(f,"{scenario["id"]}","Stochastic","k",i,t{index}[i],kn{index}[i]?"NULL":DoubleToString(k{index}[i],17),kn{index}[i]?"true":"false",kn{index}[i]?"warmup_or_null":"steady_state",kn{index}[i]?"warmup":"ok");FileWrite(f,"{scenario["id"]}","Stochastic","d",i,t{index}[i],dn{index}[i]?"NULL":DoubleToString(d{index}[i],17),dn{index}[i]?"true":"false",dn{index}[i]?"warmup_or_null":"steady_state",dn{index}[i]?"warmup":"ok");}}'''
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
        "schema_version": "nora.phase2_stochastic_executable_package_v1",
        "target_identifier": "layer1_stochastic",
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
