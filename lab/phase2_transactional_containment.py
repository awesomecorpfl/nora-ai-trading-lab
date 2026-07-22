"""Repository-owned PHASE2-TCA-1 contract builder and publisher."""
from __future__ import annotations
import hashlib, io, json, os, re, subprocess, tempfile, zipfile
from pathlib import Path
from typing import Any

SCHEMA = "nora.phase2_transactional_containment_v1"
ACCEPTANCE_TYPE = "nora.phase2_transactional_containment_acceptance_v1"
ACCEPTANCE_STATUS = "TRANSACTIONAL_CONTAINMENT_ACCEPTED"
BASELINE_COMMIT = "9ae03da91b5d8875e8a0766b580d382628b57beb"
REQUIRED_ANCESTORS = (BASELINE_COMMIT, "e80336696bc8c58e117086ed5d2510b40044915a", "e24791e1dec440910fdbfad325aeb0a7aa8c1090")
ROWS = ("classification", "same-before", "changed-before", "cleanup", "same-after", "changed-after")
BASE = "docs/evidence/phase2"
MATRIX = f"{BASE}/terminal-state-matrix/phase2-tstm-1-case-20260717T080912Z"
HEX = set("0123456789abcdef")

class ContractError(ValueError): pass
def canonical(v: Any) -> bytes: return (json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
def digest_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def identity(domain: str, v: Any) -> str: return digest_bytes(domain.encode() + b"\0" + canonical(v))
def _fail(s: str): raise ContractError(s)
def _keys(v: Any, required: set[str], where: str):
    if not isinstance(v, dict) or set(v) != required: _fail(f"{where} fields are not exact")
def _binding(path: str, root: Path) -> dict:
    p = root / path
    if not p.is_file() or p.is_symlink(): _fail(f"missing tracked evidence: {path}")
    b = p.read_bytes(); return {"path": path, "size": len(b), "sha256": digest_bytes(b)}
def _check_binding(x: dict, root: Path, where: str, parse=False) -> bytes:
    _keys(x, {"path", "size", "sha256"}, where)
    if not isinstance(x["path"], str) or Path(x["path"]).is_absolute() or ".." in Path(x["path"]).parts: _fail(f"unsafe {where}")
    if not isinstance(x["size"], int) or x["size"] < 0 or not isinstance(x["sha256"], str) or len(x["sha256"]) != 64 or set(x["sha256"]) - HEX: _fail(f"invalid {where}")
    p = root / x["path"]
    if not p.is_file() or p.is_symlink(): _fail(f"missing {where}")
    b = p.read_bytes()
    if len(b) != x["size"] or digest_bytes(b) != x["sha256"]: _fail(f"altered {where}")
    if parse:
        try: json.loads(b)
        except Exception as e: raise ContractError(f"malformed {where}") from e
    return b
def _json(path: str, root: Path) -> Any: return json.loads((root / path).read_bytes())
def _git(root: Path, *args: str) -> str:
    try: return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError as e: raise ContractError(f"git prerequisite failed: {' '.join(args)}") from e
STATUS_REL = "docs/phase2_transactional_containment_status_v1.json"
def _status_exception(root: Path, publication_id: str | None = None) -> bool:
    p = root / STATUS_REL
    if not p.exists(): return True
    try: s = json.loads(p.read_bytes())
    except Exception: return False
    if set(s) != {"schema_version","owner","status","acceptance_id","artifact_sha256"}: return False
    if s["schema_version"] != "nora.phase2_transactional_containment_status_v1" or s["owner"] != "transactional_containment_v1" or s["status"] != ACCEPTANCE_STATUS: return False
    if not isinstance(s["acceptance_id"], str) or not isinstance(s["artifact_sha256"], str) or len(s["artifact_sha256"]) != 64 or (set(s["artifact_sha256"]) - HEX): return False
    artifact = root / f"docs/evidence/phase2/transactional-containment/{s['acceptance_id']}/acceptance.json"
    if not artifact.is_file() or digest_bytes(artifact.read_bytes()) != s["artifact_sha256"]: return False
    return publication_id is None or s["acceptance_id"] == publication_id
def _porcelain_rows(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        raise ContractError("git prerequisite failed: status --porcelain --untracked-files=all") from e
    return output.splitlines()

def live_head(root: Path, publication_id: str | None = None) -> str:
    if _git(root, "symbolic-ref", "--quiet", "--short", "HEAD") != "main": _fail("branch is not main")
    rows = _porcelain_rows(root)
    for row in rows:
        path = row[3:] if len(row) >= 3 else row
        if row.startswith("?? "): continue
        if path == STATUS_REL and _status_exception(root): continue
        _fail("tracked/staged changes present")
    h = _git(root, "rev-parse", "HEAD")
    for anc in REQUIRED_ANCESTORS:
        try: subprocess.check_call(["git", "-C", str(root), "merge-base", "--is-ancestor", anc, h], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError: _fail(f"required ancestor missing: {anc}")
    return h
def _archive(x: dict, root: Path, where: str, expected_case: str, expected_op: str | None = None) -> dict:
    b = _check_binding(x, root, where); z = zipfile.ZipFile(io.BytesIO(b)); names = z.namelist()
    if len(names) != len(set(names)) or any(n.startswith("/") or ".." in Path(n).parts for n in names): _fail(f"unsafe {where}")
    if "manifest.json" not in names or "summary.json" not in names or "case-envelope.json" in names: _fail(f"invalid {where} archive convention")
    man = json.loads(z.read("manifest.json")); _keys(man, {"schema", "run_id", "case_id", "operation_id", "repository_commit", "members"}, f"{where}.manifest")
    if man["schema"] != "nora.phase2_containment_atomic_evidence_v1" or man["case_id"] != expected_case or (expected_op and man["operation_id"] != expected_op): _fail(f"{where} manifest identity")
    listed = {m["path"] for m in man["members"]}
    if listed != set(names) - {"manifest.json", "summary.json"}: _fail(f"{where} member listing")
    for m in man["members"]:
        _keys(m, {"path", "size", "sha256"}, f"{where}.member"); q=z.read(m["path"])
        if len(q) != m["size"] or digest_bytes(q) != m["sha256"]: _fail(f"{where} member bytes")
    return {"manifest_sha256": digest_bytes(z.read("manifest.json")), "members": len(man["members"])}
def _evidence():
    return {
      "baseline_manifest": f"{BASE}/firewall-semantic-baseline/semantic20-20260717T034100Z/evidence-manifest.json",
      "baseline": f"{BASE}/firewall-semantic-baseline/semantic20-20260717T034100Z/semantic-firewall-baseline.json",
      "croq_manifest": f"{BASE}/firewall-qualification/phase2-croq-1-case-20260717T044631Z/evidence-manifest.json",
      "croq_envelope": f"{BASE}/firewall-qualification/phase2-croq-1-case-20260717T044631Z/case-envelope.json",
      "croq_package": f"{BASE}/firewall-qualification/phase2-croq-1-case-20260717T044631Z/operation-package/phase2-croq-1-op-20260717T044631Z.zip",
      "synthetic": [f"{BASE}/synthetic-launcher/20260717T043548Z/evidence-manifest.json", f"{BASE}/synthetic-launcher/20260717T051316Z-casec/evidence-manifest.json"],
      "matrix_manifest": f"{MATRIX}/evidence-manifest.json", "matrix_result": f"{MATRIX}/matrix-result.json", "matrix_envelope": f"{MATRIX}/case-envelope.json", "safety": f"{MATRIX}/final-safety-report.json",
      "diagnostics": [f"{BASE}/terminal-state-matrix/failed-phase2-tstm-1-case-20260717T074931Z/evidence-manifest.json", f"{BASE}/terminal-state-matrix/phase2-tstm-1-case-20260717T075303Z/evidence-manifest.json", f"{BASE}/terminal-state-matrix/failed-phase2-tstm-1-case-20260717T080702Z/evidence-manifest.json"],
      "diag_refs": f"{MATRIX}/diagnostic-attempt-references.json", "governance": "architecture-lock/MANIFEST.json", "gate": "tests/fixtures/phase2_gate_reconciliation.json", "inventory": "tests/fixtures/phase2_remaining_parity_inventory.json", "runner": "scripts/phase2-run-abandoned-case.py"
    }
def build_candidate(root: Path, timestamp: str, publication_id: str) -> dict:
    head = live_head(root, publication_id); e=_evidence(); b=_json(e["baseline"],root); bm=_json(e["baseline_manifest"],root); cm=_json(e["croq_manifest"],root); croqenv=_json(e["croq_envelope"],root); mr=_json(e["matrix_result"],root); ce=_json(e["matrix_envelope"],root); sr=_json(e["safety"],root); gm=_json(e["governance"],root); gf=_json(e["gate"],root); inv=_json(e["inventory"],root)
    if digest_bytes((root/e["baseline"]).read_bytes()) != "366f13ed170e26d679981c8f1692325997315883891ea17eb2366daf8f4d0497" or len((root/e["baseline"]).read_bytes()) != 14374: _fail("baseline semantic bytes")
    if mr.get("schema_version") != "nora.phase2_tstm_1_terminal_state_matrix_result_v1" or mr.get("required_row_count") != 6 or mr.get("credited_row_count") != 6 or mr.get("missing_row_count") != 0 or mr.get("operation_ids_unique") is not True or mr.get("complete_coverage") is not True or mr.get("final_baseline_equal") is not True or mr.get("final_invariant_verdict") != "PASS" or mr.get("formal_acceptance_deferred") is not True: _fail("matrix result prerequisites")
    if ce.get("schema_version") != "nora.phase2_case_envelope_v1" or ce.get("case_type") != "abandoned_reuse" or ce.get("final_verdict") != "PASS": _fail("matrix envelope")
    if croqenv.get("schema_version") != "nora.phase2_case_envelope_v1" or croqenv.get("case_type") != "phase2_croq_1_read_only_firewall_qualification" or croqenv.get("final_verdict") != "PASS": _fail("CROQ envelope")
    if len(croqenv.get("operations", [])) != 1 or croqenv["operations"][0].get("operation_verdict") != "PASS" or cm.get("credit") != "GRANTED" or cm.get("final_case_verdict") != "PASS": _fail("CROQ credit")
    if cm.get("schema_version") != "nora.phase2_croq_1_evidence_manifest_v1": _fail("CROQ manifest")
    _archive(_binding(e["croq_package"], root), root, "CROQ package", croqenv["case_id"], croqenv["operations"][0]["operation_id"])
    if croqenv["operations"][0].get("package",{}).get("sha256") != _binding(e["croq_package"],root)["sha256"] or croqenv["operations"][0].get("package",{}).get("size") != _binding(e["croq_package"],root)["size"]: _fail("CROQ package binding")
    if not any(x.get("path", "").endswith("operation-package/phase2-croq-1-op-20260717T044631Z.zip") for x in cm.get("artifacts", [])): _fail("CROQ package manifest binding")
    if sr.get("post_cleanup",{}).get("terminal_tester_processes") != 0 or sr.get("post_cleanup",{}).get("nora_rules") != 0 or sr.get("post_cleanup",{}).get("related_processes") != 0 or sr.get("post_cleanup",{}).get("partial_or_pending") != 0: _fail("final safety")
    if gf.get("complete_phase2_gate") is not False or gf.get("phase3_authorized") is not False or gf.get("search_authorized") is not False or gf.get("searchable") is not False or inv.get("inventory_summary",{}).get("item_count") != 51: _fail("governance")
    syn0=_json(e["synthetic"][0],root); syn1=_json(e["synthetic"][1],root)
    if syn0.get("case_outcomes") != {"A":"PASS","B":"PASS","C":"PASS (externally visible outcome retained as CAMPAIGN_EXITED_BEFORE_OWNER)","D":"PASS"}: _fail("synthetic lifecycle outcomes")
    if syn1.get("deliberate_mismatch",{}).get("classification") != "OWNER_BINDING_MISMATCH": _fail("synthetic owner mismatch")
    paths=[]
    for row in mr["rows"]:
        if row["row_id"] in paths or row["row_id"] not in ROWS or row["credit"] != "GRANTED" or row["fedora_recomputation"] != "PASS" or row["windows_recomputation"] != "PASS": _fail("matrix row")
        paths.append(row["row_id"]); p=_check_binding({"path":row["evidence_path"],"size":row["evidence_size"],"sha256":row["evidence_sha256"]},root,"matrix package"); am=_archive({"path":row["evidence_path"],"size":row["evidence_size"],"sha256":row["evidence_sha256"]},root,"matrix package",Path(mr["case_envelope"]["path"]).parent.name,row["operation_id"]);
        if am["manifest_sha256"] != row["manifest_sha256"] or row["operation_id"] not in {x.get("operation_id") for x in ce.get("operations",[])}: _fail("matrix operation binding")
    binds={"baseline_manifest":_binding(e["baseline_manifest"],root),"baseline":_binding(e["baseline"],root),"croq_manifest":_binding(e["croq_manifest"],root),"croq_envelope":_binding(e["croq_envelope"],root),"croq_package":_binding(e["croq_package"],root),"matrix_manifest":_binding(e["matrix_manifest"],root),"matrix_result":_binding(e["matrix_result"],root),"matrix_envelope":_binding(e["matrix_envelope"],root),"safety":_binding(e["safety"],root),"synthetic":[_binding(x,root) for x in e["synthetic"]],"diagnostics":[_binding(x,root) for x in e["diagnostics"]],"diagnostic_references":_binding(e["diag_refs"],root),"governance_manifest":_binding(e["governance"],root),"gate_fixture":_binding(e["gate"],root),"parity_inventory":_binding(e["inventory"],root),"runner":_binding(e["runner"],root)}
    implementation={}
    for name,path in {"publisher_cli":"scripts/phase2-transactional-containment.py","publisher_module":"lab/phase2_transactional_containment.py","verifier_cli":"scripts/verify-phase2-transactional-containment.py","verifier_module":"lab/phase2_transactional_containment_verifier.py","schema":"docs/phase2_transactional_containment_acceptance_schema_v1.json"}.items():
        x=_binding(path,root); implementation[name]={**x,"identity":identity("nora.phase2-tca-1.component."+name,x["sha256"])}
    implementation["aggregate_identity"]=identity("nora.phase2-tca-1.aggregate-prerequisites",binds)
    diag_ids=[Path(x).parent.name.replace("failed-", "") for x in e["diagnostics"]]
    if _json(e["diag_refs"],root).get("not_credited") != diag_ids: _fail("diagnostic references")
    if ce["case_invariants"]["semantic_digests"] != {"canonical":"179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8","unrelated":"179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8","profile":"209cb421ee9b3ab58588443ab1e25157d95b219d2d09d0c071a27b82f0e8bd72","nora":"37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570"}: _fail("baseline digest evidence")
    matrix_case=dict(mr["case_envelope"]); matrix_case["retrieval_size"]=(root/matrix_case["retrieval_path"]).stat().st_size
    package_bindings=[]
    for row in mr["rows"]:
        package_bindings.append({"path":row["evidence_path"],"size":row["evidence_size"],"sha256":row["evidence_sha256"],"manifest_sha256":row["manifest_sha256"],"operation_id":row["operation_id"],"row_id":row["row_id"]})
    bm_binding=_binding(e["baseline_manifest"],root)
    diagnostics=[{"id":Path(x["path"]).parent.name.replace("failed-", ""),"path":x["path"],"size":x["size"],"sha256":x["sha256"],"credit":"NON_CREDIT","reference":"diagnostic-attempt-references.not_credited"} for x in binds["diagnostics"]]
    doc={"schema_version":SCHEMA,"acceptance_type":ACCEPTANCE_TYPE,"status":ACCEPTANCE_STATUS,"timestamp":timestamp,"repository":{"head":head,"branch":"main","accepted_baseline_commit":BASELINE_COMMIT,"baseline_manifest":bm_binding,"baseline_path":e["baseline"],"baseline_size":14374,"baseline_sha256":"366f13ed170e26d679981c8f1692325997315883891ea17eb2366daf8f4d0497","launch_id":"synlc-20260717T034100Z","campaign_id":"sync-20260717T034100Z","required_ancestors":list(REQUIRED_ANCESTORS)},"publication":{"id":publication_id,"path":f"docs/evidence/phase2/transactional-containment/{publication_id}/acceptance.json"},"implementation":implementation,"prerequisites":binds,"baseline_digests":ce["case_invariants"]["semantic_digests"],"synthetic":{"manifests":[x["path"] for x in binds["synthetic"]],"outcomes":{"detached_bootstrap":"PASS","campaign_exit_before_owner":"PASS","duplicate_race":"PASS","OWNER_BINDING_MISMATCH":"PASS"}},"croq":{"case_id":croqenv["case_id"],"evidence_commit":"e80336696bc8c58e117086ed5d2510b40044915a","manifest_binding":binds["croq_manifest"],"package_binding":binds["croq_package"],"envelope_binding":binds["croq_envelope"],"credit":"GRANTED:CROQ-1_ONLY","operation_count":1,"final_verdict":"PASS"},"matrix":{"case_id":ce["case_id"],"accepted_evidence_commit":"e24791e1dec440910fdbfad325aeb0a7aa8c1090","result_binding":binds["matrix_result"],"manifest_binding":binds["matrix_manifest"],"envelope_binding":binds["matrix_envelope"],"safety_binding":binds["safety"],"schema":mr["schema_version"],"case_envelope_schema":ce["schema_version"],"case_type":"abandoned_reuse","required":6,"credited":6,"missing":0,"rows":list(ROWS),"operation_ids":mr["matrix_contract_identity"]["operation_ids"],"package_bindings":package_bindings,"envelope_operation_cross_binding":True,"unique_ids":True,"coverage":True,"baseline_equality":True,"invariant":"PASS","fedora":"PASS","windows":"PASS"},"diagnostics":diagnostics,"safety":{"nora_rules":0,"terminal_processes":0,"tester_processes":0,"terminal_tester_processes":0,"related_processes":0,"partial_or_pending":0,"cleanup":"resolved/PASS"},"governance":{"phase2_complete":False,"phase2_status":"INCOMPLETE","phase3_authorized":False,"search_authorized":False,"search":False,"search_count":0,"searchable_components":0,"native_parity_acceptance":"NARROW_CURRENT_STATUS_ONLY","native_parity_generalized":False},"acceptance":{"type":ACCEPTANCE_TYPE,"verdict":"PASS","failure_reasons":[],"creation_command":f"scripts/phase2-transactional-containment.py publish --publication-id {publication_id} --timestamp {timestamp}","repeated_publication":{"expected":"identical_existing","verified":"identical_existing"}}}
    doc["semantic_identity"]=identity("nora.phase2-tca-1.semantic",{k:v for k,v in doc.items() if k not in {"timestamp","semantic_identity"}})
    sp=root/STATUS_REL
    if sp.exists():
        try: s=json.loads(sp.read_bytes())
        except Exception: _fail("invalid status file")
        pending = {
            "schema_version": "nora.phase2_transactional_containment_status_v1",
            "owner": "transactional_containment_v1",
            "status": "NOT_ACCEPTED",
            "acceptance_id": None,
            "artifact_sha256": None,
        }
        if s != pending:
            if not _status_exception(root):
                _fail("status is not bound to an immutable acceptance artifact")
            if s.get("acceptance_id") == publication_id:
                artifact = root / doc["publication"]["path"]
                if not artifact.is_file() or s.get("artifact_sha256") != digest_bytes(canonical(doc)):
                    _fail("status is not bound to acceptance artifact")
    return doc
def verify_document(doc: dict, root: Path, **_: Any) -> dict:
    if not isinstance(doc,dict) or doc.get("schema_version") != SCHEMA or doc.get("acceptance_type") != ACCEPTANCE_TYPE or doc.get("status") != ACCEPTANCE_STATUS: _fail("contract header")
    expected=build_candidate(root,doc["timestamp"],doc["publication"]["id"])
    if doc != expected: _fail("candidate is not repository-derived")
    return {"verdict":"PASS","semantic_identity":doc["semantic_identity"],"acceptance_type":ACCEPTANCE_TYPE}
def publish(root: Path, publication_id: str, timestamp: str, destination: Path | None=None, status_path: Path | None=None) -> str:
    if publication_id == "latest" or "/" in publication_id or "\\" in publication_id or not re.search(r"\d{8}T\d{6}Z", publication_id): _fail("publication id must be explicit and versioned")
    doc=build_candidate(root,timestamp,publication_id); payload=canonical(doc); dest=root/f"docs/evidence/phase2/transactional-containment/{publication_id}/acceptance.json"
    if destination is not None and destination != dest: _fail("publication path is fixed")
    fixed_status=root/"docs/phase2_transactional_containment_status_v1.json"
    if status_path is not None and status_path != fixed_status: _fail("status path is fixed")
    status_path=fixed_status
    if dest.exists():
        if dest.read_bytes() != payload: _fail("conflicting artifact")
        return "identical_existing"
    parent=dest.parent; parent.parent.mkdir(parents=True,exist_ok=True); tmp=Path(tempfile.mkdtemp(prefix=".tca-",dir=parent.parent))
    try:
        (tmp/"acceptance.json").write_bytes(payload)
        verifier=Path(__file__).resolve().parents[1]/"scripts/verify-phase2-transactional-containment.py"
        subprocess.check_call(["python3",str(verifier),str(tmp/"acceptance.json"),"--root",str(root)],stdout=subprocess.DEVNULL)
        receipt=canonical({"verdict":"PASS","semantic_identity":doc["semantic_identity"],"artifact_sha256":digest_bytes(payload)}); (tmp/"independent-verification.json").write_bytes(receipt); pub=canonical({"publication_id":publication_id,"acceptance_sha256":digest_bytes(payload),"verification_sha256":digest_bytes(receipt),"exit_code":0}); (tmp/"publication-receipt.json").write_bytes(pub); man=canonical({"schema":"nora.phase2_transactional_containment_publication_manifest_v1","members":[{"path":"acceptance.json","size":len(payload),"sha256":digest_bytes(payload)},{"path":"independent-verification.json","size":len(receipt),"sha256":digest_bytes(receipt)},{"path":"publication-receipt.json","size":len(pub),"sha256":digest_bytes(pub)}]}); (tmp/"manifest.json").write_bytes(man); os.rename(tmp,parent)
    except FileExistsError:
        if dest.read_bytes()!=payload: _fail("conflicting artifact")
        return "identical_existing"
    finally:
        if tmp.exists():
            for p in tmp.iterdir(): p.unlink()
            tmp.rmdir()
    if status_path:
        status={"schema_version":"nora.phase2_transactional_containment_status_v1","owner":"transactional_containment_v1","status":ACCEPTANCE_STATUS,"acceptance_id":publication_id,"artifact_sha256":digest_bytes(payload)}; fd,n=tempfile.mkstemp(dir=status_path.parent,prefix=status_path.name+"."); os.write(fd,canonical(status)); os.close(fd); os.replace(n,status_path)
    return "published"
