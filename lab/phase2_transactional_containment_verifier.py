"""Independent verifier.  It deliberately has no import of the publisher module."""
from __future__ import annotations
import hashlib, io, json, subprocess, sys, zipfile
from pathlib import Path

SCHEMA="nora.phase2_transactional_containment_v1"; TYPE="nora.phase2_transactional_containment_acceptance_v1"; STATUS="TRANSACTIONAL_CONTAINMENT_ACCEPTED"
ANCESTORS=("9ae03da91b5d8875e8a0766b580d382628b57beb","e80336696bc8c58e117086ed5d2510b40044915a","e24791e1dec440910fdbfad325aeb0a7aa8c1090")
ROWS=("classification","same-before","changed-before","cleanup","same-after","changed-after")
M="docs/evidence/phase2/terminal-state-matrix/phase2-tstm-1-case-20260717T080912Z"
STATUS_REL="docs/phase2_transactional_containment_status_v1.json"
def canon(v): return (json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def ident(d,v): return sha(d.encode()+b"\0"+canon(v))
def bad(s): raise ValueError(s)
def bind(x,root,where):
    if not isinstance(x,dict) or set(x)!={"path","size","sha256"} or Path(x["path"]).is_absolute() or ".." in Path(x["path"]).parts: bad(where)
    p=root/x["path"]
    if not p.is_file() or p.is_symlink(): bad(where)
    b=p.read_bytes()
    if len(b)!=x["size"] or sha(b)!=x["sha256"]: bad(where)
    return b
def archive(x,root,case,op):
    z=zipfile.ZipFile(io.BytesIO(bind(x,root,"package"))); ns=z.namelist()
    if "manifest.json" not in ns or "summary.json" not in ns or "case-envelope.json" in ns: bad("archive convention")
    m=json.loads(z.read("manifest.json"));
    if m.get("schema")!="nora.phase2_containment_atomic_evidence_v1" or m.get("case_id")!=case or m.get("operation_id")!=op: bad("archive manifest identity")
    if {x.get("path") for x in m.get("members",[])}!=set(ns)-{"manifest.json","summary.json"}: bad("archive member list")
    for x in m["members"]:
        b=z.read(x["path"])
        if set(x)!={"path","size","sha256"} or len(b)!=x["size"] or sha(b)!=x["sha256"]: bad("archive member")
def worktree(root, publication_id, artifact_sha=None):
    rows=subprocess.check_output(["git","-C",str(root),"status","--porcelain","--untracked-files=all"],text=True).splitlines()
    for row in rows:
        if row.startswith("?? "): continue
        p=row[3:]
        if p != STATUS_REL: bad("repository state")
        try: s=json.loads((root/STATUS_REL).read_bytes())
        except Exception: bad("status file")
        if set(s)!={"schema_version","owner","status","acceptance_id","artifact_sha256"} or s["schema_version"]!="nora.phase2_transactional_containment_status_v1" or s["owner"]!="transactional_containment_v1" or s["status"]!=STATUS: bad("status binding")
        bound=root/f"docs/evidence/phase2/transactional-containment/{s['acceptance_id']}/acceptance.json"
        if not bound.is_file() or sha(bound.read_bytes())!=s["artifact_sha256"]: bad("status artifact binding")
        if artifact_sha is not None and (s["acceptance_id"]!=publication_id or s["artifact_sha256"]!=artifact_sha): bad("status artifact binding")
def verify(path:Path,root:Path)->dict:
    d=json.loads(path.read_bytes()); required={"schema_version","acceptance_type","status","timestamp","repository","publication","implementation","prerequisites","baseline_digests","synthetic","croq","matrix","diagnostics","safety","governance","acceptance","semantic_identity"}
    if set(d)!=required or d["schema_version"]!=SCHEMA or d["acceptance_type"]!=TYPE or d["status"]!=STATUS: bad("strict header")
    canonical_path=root/d["publication"]["path"]
    worktree(root,d["publication"]["id"],sha(path.read_bytes()) if path.resolve()==canonical_path.resolve() else None)
    if subprocess.check_output(["git","-C",str(root),"symbolic-ref","--short","HEAD"],text=True).strip()!="main": bad("repository state")
    head=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    for a in ANCESTORS:
        if subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",a,head]).returncode: bad("ancestry")
    if d["repository"].get("head")!=head or d["repository"].get("branch")!="main" or d["repository"].get("required_ancestors")!=list(ANCESTORS): bad("head binding")
    r=d["repository"]
    if r.get("accepted_baseline_commit")!=ANCESTORS[0] or r.get("launch_id")!="synlc-20260717T034100Z" or r.get("campaign_id")!="sync-20260717T034100Z" or r.get("baseline_path")!="docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/semantic-firewall-baseline.json" or r.get("baseline_size")!=14374 or r.get("baseline_sha256")!="366f13ed170e26d679981c8f1692325997315883891ea17eb2366daf8f4d0497": bad("baseline identity")
    p=d["prerequisites"]
    if d["implementation"].get("aggregate_identity") != ident("nora.phase2-tca-1.aggregate-prerequisites",p): bad("aggregate prerequisite identity")
    if set(d["implementation"]) != {"publisher_cli","publisher_module","verifier_cli","verifier_module","schema","aggregate_identity"}: bad("implementation identity shape")
    for k in ("publisher_cli","publisher_module","verifier_cli","verifier_module","schema"):
        x=d["implementation"][k]; b=bind({"path":x["path"],"size":x["size"],"sha256":x["sha256"]},root,"implementation")
        if x.get("identity") != ident("nora.phase2-tca-1.component."+k,x["sha256"]): bad("implementation identity")
    if set(p)!={"baseline_manifest","baseline","croq_manifest","croq_envelope","croq_package","matrix_manifest","matrix_result","matrix_envelope","safety","synthetic","diagnostics","diagnostic_references","governance_manifest","gate_fixture","parity_inventory","runner"}: bad("prerequisite shape")
    for k in ("baseline_manifest","baseline","croq_manifest","croq_envelope","matrix_manifest","matrix_result","matrix_envelope","safety","diagnostic_references","governance_manifest","gate_fixture","parity_inventory","runner"): bind(p[k],root,k)
    for k in ("synthetic","diagnostics"):
        if not isinstance(p[k],list): bad(k)
        for i,x in enumerate(p[k]): bind(x,root,f"{k}[{i}]")
    refs=json.loads(bind(p["diagnostic_references"],root,"diagnostic references"))
    expected_diag=[Path(x["path"]).parent.name.replace("failed-","") for x in p["diagnostics"]]
    if refs.get("not_credited")!=expected_diag or refs.get("accepted_case")!="phase2-tstm-1-case-20260717T080912Z": bad("diagnostic reference set")
    mr=json.loads(bind(p["matrix_result"],root,"result")); env=json.loads(bind(p["matrix_envelope"],root,"envelope")); safety=json.loads(bind(p["safety"],root,"safety")); gate=json.loads(bind(p["gate_fixture"],root,"gate")); inv=json.loads(bind(p["parity_inventory"],root,"inventory"))
    if sha((root/"docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/semantic-firewall-baseline.json").read_bytes())!="366f13ed170e26d679981c8f1692325997315883891ea17eb2366daf8f4d0497" or env.get("case_type")!="abandoned_reuse" or env.get("final_verdict")!="PASS": bad("baseline/envelope")
    if d["baseline_digests"]!={"canonical":"179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8","unrelated":"179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8","profile":"209cb421ee9b3ab58588443ab1e25157d95b219d2d09d0c071a27b82f0e8bd72","nora":"37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570"}: bad("baseline digests")
    if mr.get("required_row_count")!=6 or mr.get("credited_row_count")!=6 or mr.get("missing_row_count")!=0 or mr.get("operation_ids_unique") is not True or mr.get("complete_coverage") is not True or mr.get("final_baseline_equal") is not True or mr.get("final_invariant_verdict")!="PASS": bad("matrix result")
    if safety.get("post_cleanup",{}).get("terminal_tester_processes")!=0 or safety.get("post_cleanup",{}).get("nora_rules")!=0: bad("safety")
    if gate.get("complete_phase2_gate") is not False or gate.get("phase3_authorized") is not False or gate.get("search_authorized") is not False or gate.get("searchable") is not False or inv.get("inventory_summary",{}).get("item_count")!=51: bad("governance")
    case=env["case_id"]
    if len(env.get("operations",[]))!=6 or [x.get("operation_id") for x in env["operations"]]!=mr["matrix_contract_identity"]["operation_ids"]: bad("envelope operations")
    for r in mr["rows"]:
        if r.get("row_id") not in ROWS or r.get("credit")!="GRANTED" or r.get("fedora_recomputation")!="PASS" or r.get("windows_recomputation")!="PASS": bad("row")
        x={"path":r["evidence_path"],"size":r["evidence_size"],"sha256":r["evidence_sha256"]}; archive(x,root,case,r["operation_id"])
    if len({r["row_id"] for r in mr["rows"]})!=6 or [r["row_id"] for r in mr["rows"]]!=list(ROWS): bad("row coverage")
    if any(d["safety"].get(k)!=0 for k in ("nora_rules","terminal_processes","tester_processes","terminal_tester_processes","related_processes","partial_or_pending")) or d["safety"].get("cleanup")!="resolved/PASS" or d["governance"]["phase2_status"]!="INCOMPLETE": bad("published boundary")
    if d.get("synthetic",{}).get("outcomes") != {"detached_bootstrap":"PASS","campaign_exit_before_owner":"PASS","duplicate_race":"PASS","OWNER_BINDING_MISMATCH":"PASS"}: bad("synthetic outcomes")
    if d.get("croq",{}).get("credit")!="GRANTED:CROQ-1_ONLY" or d["croq"].get("final_verdict")!="PASS" or d["croq"].get("operation_count")!=1: bad("CROQ credit")
    if len(d.get("matrix",{}).get("package_bindings",[]))!=6 or any(set(x)!={"path","size","sha256","manifest_sha256","operation_id","row_id"} for x in d["matrix"]["package_bindings"]): bad("matrix package bindings")
    if any(x.get("credit")!="NON_CREDIT" or x.get("reference")!="diagnostic-attempt-references.not_credited" for x in d.get("diagnostics",[])): bad("diagnostic substitution")
    sem=ident("nora.phase2-tca-1.semantic",{k:v for k,v in d.items() if k not in {"timestamp","semantic_identity"}})
    if d["semantic_identity"]!=sem: bad("semantic identity")
    manifest=path.parent/"manifest.json"
    if manifest.is_file():
        pm=json.loads(manifest.read_bytes())
        if pm.get("schema")!="nora.phase2_transactional_containment_publication_manifest_v1": bad("publication manifest")
        for m in pm.get("members",[]):
            q=path.parent/m["path"]
            if not q.is_file() or len(q.read_bytes())!=m["size"] or sha(q.read_bytes())!=m["sha256"]: bad("publication member")
    return {"verdict":"PASS","acceptance_type":TYPE,"semantic_identity":sem}
if __name__=="__main__":
    try: print(json.dumps(verify(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)>2 else Path.cwd()),sort_keys=True))
    except Exception as e: print(f"FAIL: {e}",file=sys.stderr); sys.exit(1)
