"""Canonical Phase-2 Windows Firewall preservation and verification."""
from __future__ import annotations

import argparse, copy, hashlib, json, re, sys
from pathlib import Path
from typing import Any

SCHEMA="nora.phase2_firewall_inventory_v1"
NORA_PREFIX="noraphase2containment-"
PROFILES={"domain","private","public"}
RULE_FIELDS=("view","name","instance_id","group","enabled","direction","action","profile",
 "policy_store","policy_store_source_type","policy_store_source","edge_traversal","interface_types",
 "owner","programs","services","protocols","local_ports","remote_ports","icmp_types",
 "local_addresses","remote_addresses","interfaces","security","packages","local_users","remote_users")
PROFILE_FIELDS=("name","enabled","default_inbound","default_outbound","allow_local_firewall_rules",
 "allow_local_ipsec_rules","notify_on_listen","policy_store_source")
HEX40=re.compile(r"^[0-9a-f]{40}$")

class FirewallError(ValueError): pass
def canonical(v:Any)->bytes:return (json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def digest(v:Any)->str:return hashlib.sha256(canonical(v)).hexdigest()
def _s(v:Any)->str|None:
    if v is None:return None
    return str(v).strip().lower()
def _path(v:Any)->str|None:
    s=_s(v)
    if s is None:return None
    return re.sub(r"\\+",r"\\",s.replace("/","\\"))
def _arr(v:Any,paths=False)->list:
    if v is None:return []
    if not isinstance(v,list):raise FirewallError("collection is not an array")
    f=_path if paths else _s
    return sorted({x for x in (f(x) for x in v) if x not in (None,"")})
def normalize(value:dict)->dict:
    if not isinstance(value,dict) or value.get("schema_version")!=SCHEMA:raise FirewallError("unsupported schema version")
    if not HEX40.fullmatch(str(value.get("repository_commit",""))):raise FirewallError("invalid repository commit")
    ps=[]
    for raw in value.get("profiles",[]):
        p={k:(_s(raw.get(k)) if k!="enabled" else raw.get(k)) for k in PROFILE_FIELDS}
        if not isinstance(p["enabled"],bool):raise FirewallError("profile enabled is unavailable")
        ps.append(p)
    if {p["name"] for p in ps}!=PROFILES or len(ps)!=3:raise FirewallError("profile set is incomplete or ambiguous")
    ps.sort(key=lambda x:x["name"])
    def rules(key):
        out=[]
        for raw in value.get(key,[]):
            if not isinstance(raw,dict):raise FirewallError("malformed rule")
            r={k:_s(raw.get(k)) for k in RULE_FIELDS}
            r["enabled"]=raw.get("enabled")
            if not isinstance(r["enabled"],bool):raise FirewallError("rule enabled is unavailable")
            for k in ("interface_types","services","protocols","local_ports","remote_ports","icmp_types","local_addresses","remote_addresses","interfaces","security","packages","local_users","remote_users"):
                r[k]=_arr(raw.get(k))
            r["programs"]=_arr(raw.get("programs"),True)
            out.append(r)
        out.sort(key=lambda r:tuple(r.get(k) or "" for k in ("view","policy_store_source_type","policy_store_source","instance_id","name")))
        ids=[(r["view"],r["policy_store_source_type"],r["policy_store_source"],r["instance_id"],r["name"]) for r in out]
        if len(ids)!=len(set(ids)):raise FirewallError("duplicate stable rule identity")
        return out
    return {"schema_version":SCHEMA,"profiles":ps,"effective_rules":rules("effective_rules"),"persistent_rules":rules("persistent_rules")}
def legacy_projection(value:dict)->list:
    """Reproduce the historical PowerShell six-field projection exactly."""
    rows=[]
    for r in sorted(value.get("effective_rules",[]),key=lambda x:str(x.get("name","")).lower()):
        enabled=r.get("enabled")
        rows.append({"name":r.get("name"),"enabled":"True" if enabled is True else "False" if enabled is False else str(enabled),
                     "direction":r.get("direction"),"action":r.get("action"),"profile":r.get("profile"),"group":r.get("group")})
    return rows
def legacy_digest(value:dict)->str:
    payload=json.dumps(legacy_projection(value),separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
def evaluate(value:dict,qualified_paths:list[str]|None=None)->dict:
    n=normalize(value); paths={_path(x) for x in (qualified_paths or [])};violations=[]
    for p in n["profiles"]:
        if not p["enabled"]:violations.append("profile_disabled:"+p["name"])
        if p["default_inbound"] is None or p["default_outbound"] is None:violations.append("profile_default_unavailable:"+p["name"])
    nora=[]
    for r in n["effective_rules"]:
        is_nora=(r["name"] or "").startswith(NORA_PREFIX) or (r["group"] or "").startswith(NORA_PREFIX)
        if is_nora:nora.append(r)
        if r["enabled"] and r["action"]=="allow":
            for p in r["programs"]:
                if p.endswith("\\terminal64.exe") or p.endswith("\\metatester64.exe") or p in paths:violations.append("unsafe_executable_allow:"+(r["name"] or ""))
    if nora:violations.append("stale_nora_rules")
    semantic=digest(n); unrelated=copy.deepcopy(n);unrelated["effective_rules"]=[r for r in n["effective_rules"] if not ((r["name"]or"").startswith(NORA_PREFIX)or(r["group"]or"").startswith(NORA_PREFIX))];unrelated["persistent_rules"]=[r for r in n["persistent_rules"] if not ((r["name"]or"").startswith(NORA_PREFIX)or(r["group"]or"").startswith(NORA_PREFIX))]
    reported=value.get("legacy_digest"); legacy=reported if isinstance(reported,str) and re.fullmatch(r"[0-9a-f]{64}",reported) else legacy_digest(value)
    return {"schema_version":"nora.phase2_firewall_invariant_report_v1","verdict":"PASS" if not violations else "FAIL","violations":violations,"canonical_digest":semantic,"unrelated_digest":digest(unrelated),"profile_digest":digest(n["profiles"]),"nora_digest":digest(nora),"legacy_digest":legacy,"legacy_source":"windows_exact" if reported==legacy else "diagnostic_reconstruction","effective_rule_count":len(n["effective_rules"]),"persistent_rule_count":len(n["persistent_rules"]),"nora_rule_count":len(nora)}
def compare(a:dict,b:dict)->dict:
    x,y=evaluate(a),evaluate(b); fields=("canonical_digest","unrelated_digest","profile_digest")
    return {"schema_version":"nora.phase2_firewall_equality_report_v1","verdict":"PASS" if all(x[k]==y[k] for k in fields) else "FAIL","baseline":x,"final":y,"equal":{k:x[k]==y[k] for k in fields}}
def main(argv=None):
    p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True)
    for c in ("verify","report"):
        q=s.add_parser(c);q.add_argument("inventory",type=Path)
    q=s.add_parser("compare");q.add_argument("baseline",type=Path);q.add_argument("final",type=Path)
    a=p.parse_args(argv)
    try:
        if a.cmd=="compare": out=compare(json.loads(a.baseline.read_bytes()),json.loads(a.final.read_bytes()))
        else: out=evaluate(json.loads(a.inventory.read_bytes()))
        print(json.dumps(out,sort_keys=True));return 0 if out["verdict"]=="PASS" else 1
    except (OSError,json.JSONDecodeError,FirewallError) as e:print("firewall-error: "+str(e),file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
