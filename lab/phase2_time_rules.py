"""Frozen fixed-epoch evidence for the Phase-2 time-rule canary."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
from lab.phase2_time_contracts import contracts,canon,identity

VERSION="nora.phase2.time_rule_plan_v1"
RULES={"friday_close":"16:25","session":{"start":"09:30","end":"16:00"},"rollover":{"start":"23:50","end":"00:10"},"monday_delay":{"start":"00:00","end":"00:15"},"orb":{"start":"09:30","end":"10:00"}}
SCENARIOS=[
 ("winter_utc",1736942400,"UTC","declared_not_converted"),("summer_utc",1748957400,"UTC","declared_not_converted"),
 ("spring_before",1741503540,"UTC","declared_not_converted"),("spring_after",1741503600,"UTC","declared_not_converted"),
 ("fall_first_hour",1762061400,"UTC","declared_not_converted"),("fall_second_hour",1762065000,"UTC","declared_not_converted"),
 ("friday_pre",1749241440,"UTC","declared_not_converted"),("friday_exact",1749241500,"UTC","declared_not_converted"),("friday_post",1749241560,"UTC","declared_not_converted"),("friday_winter",1733520300,"UTC","declared_not_converted"),
 ("rollover_before",1736286540,"broker","broker_declared"),("rollover_start",1736286600,"broker","broker_declared"),("rollover_end",1736287800,"broker","broker_declared"),
 ("monday_delay",1736114700,"broker","broker_declared"),("monday_permitted",1736115300,"broker","broker_declared"),
 ("orb_open",1748932200,"broker","broker_declared"),("orb_end",1748934000,"broker","broker_declared"),
 ("already_converted_rejected",1748957400,"UTC","already_converted"),
]

def scenarios(): return [{"id":a,"epoch":b,"source_clock":c,"conversion_state":d} for a,b,c,d in SCENARIOS]
def task():
 c=contracts(); return {"task_version":1,"task_type":"time_rules_v1","contract_identities":{"dataset":c["dataset"]["dataset_clock_identity"],"strategy":c["strategy"]["strategy_clock_identity"],"session":c["session"]["session_clock_identity"],"dst":c["dst_regime"]["identity"],"anchoring":c["anchoring"]["anchoring_identity"],"reasons":c["reasons"]["reason_code_identity"]},"rules":RULES,"scenarios":scenarios()}
def plan_identity(): return identity({"version":VERSION,"contracts":task()["contract_identities"],"rules":RULES,"scenarios":scenarios()})
def evidence(binary:Path):
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/"task.json";p.write_text(canon(task())+'\n');r=subprocess.run([str(binary),str(p)],capture_output=True,text=True);assert r.returncode==0,r.stderr;out=json.loads(r.stdout)
 return {"schema_version":VERSION,"time_rule_plan_identity":plan_identity(),"task":task(),"scenario_order":[x["id"] for x in scenarios()],"scenario_identities":{x["id"]:identity(x) for x in scenarios()},"task_output_identity":out["time_rule_semantic_identity"],"expected_vectors":out["rows"],"expected_vector_identity":identity(out["rows"]),"csv_schema":["scenario_id","source_epoch","source_clock","new_york","broker","utc_offset_seconds","dst","session_member","friday_close","rollover","monday_delay","orb","m5_anchor_epoch","h1_anchor_epoch","conversion_state","reason_code","pass"],"reason_code_identity":contracts()["reasons"]["reason_code_identity"]}
