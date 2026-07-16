"""Build and independently verify immutable Phase-2 multi-operation envelopes."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

SCHEMA = "nora.phase2_case_envelope_v1"
PACKAGE_SCHEMA = "nora.phase2_containment_atomic_evidence_v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
OP_TYPES = {"classification", "reuse_attempt", "cleanup", "recovery", "interruption",
            "concurrency_owner", "concurrency_loser", "publication", "retrieval", "verification"}
IDENTITIES = {"native_execution", "runner", "containment", "publisher", "verifier", "retrieval_wrapper"}


class CaseEnvelopeError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _hex(value: Any, name: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise CaseEnvelopeError(f"invalid {name}")
    return value


def _read_package(path: Path) -> tuple[dict, dict, str, int, str, str]:
    if not path.is_file() or path.is_symlink():
        raise CaseEnvelopeError("missing or unsafe operation package")
    package_hash, size = sha256(path), path.stat().st_size
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
                raise CaseEnvelopeError("unsafe or duplicate operation member")
            summary_bytes, manifest_bytes = archive.read("summary.json"), archive.read("manifest.json")
            summary, manifest = json.loads(summary_bytes), json.loads(manifest_bytes)
            listed = manifest.get("members")
            if not isinstance(listed, list) or any(not isinstance(x, dict) for x in listed):
                raise CaseEnvelopeError("invalid operation manifest")
            by_name = {x.get("path"): x for x in listed}
            if len(by_name) != len(listed) or set(by_name) != set(names) - {"summary.json", "manifest.json"}:
                raise CaseEnvelopeError("operation manifest member mismatch")
            for name, item in by_name.items():
                data = archive.read(name)
                if len(data) != item.get("size") or hashlib.sha256(data).hexdigest() != item.get("sha256"):
                    raise CaseEnvelopeError(f"operation member mismatch: {name}")
            pre = hashlib.sha256(archive.read("pre_state.json") + archive.read("firewall_pre.json")).hexdigest()
            post = hashlib.sha256(archive.read("post_state.json") + archive.read("firewall_post.json")).hexdigest()
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise CaseEnvelopeError("invalid operation package") from exc
    if summary.get("schema") != PACKAGE_SCHEMA or manifest.get("schema") != PACKAGE_SCHEMA:
        raise CaseEnvelopeError("operation package schema mismatch")
    for field in ("run_id", "case_id", "operation_id", "repository_commit"):
        if summary.get(field) != manifest.get(field):
            raise CaseEnvelopeError(f"operation {field} mismatch")
    return summary, manifest, package_hash, size, hashlib.sha256(manifest_bytes).hexdigest(), pre + ":" + post


def build(plan: dict[str, Any]) -> dict[str, Any]:
    case_id, sequence = plan.get("case_id"), plan.get("declared_sequence")
    if not IDENT.fullmatch(case_id or "") or not isinstance(sequence, list) or not sequence or len(sequence) != len(set(sequence)):
        raise CaseEnvelopeError("invalid case identity or sequence")
    if not re.fullmatch(r"[0-9a-f]{40}", plan.get("repository_commit", "")):
        raise CaseEnvelopeError("invalid repository commit")
    identities = plan.get("identities")
    if not isinstance(identities, dict) or set(identities) != IDENTITIES:
        raise CaseEnvelopeError("invalid identity set")
    for key, value in identities.items():
        if value is not None: _hex(value, f"{key} identity")
    operations = plan.get("operations")
    if not isinstance(operations, list) or [x.get("operation_id") for x in operations] != sequence:
        raise CaseEnvelopeError("operation order mismatch")
    if len({x.get("package_path") for x in operations}) != len(operations):
        raise CaseEnvelopeError("duplicate package reference")
    rendered = []
    for index, spec in enumerate(operations):
        op_id, op_type = spec.get("operation_id"), spec.get("operation_type")
        if not IDENT.fullmatch(op_id or "") or op_type not in OP_TYPES:
            raise CaseEnvelopeError("invalid operation identity or type")
        expected_predecessor = None if index == 0 else sequence[index - 1]
        if spec.get("predecessor_operation_id") != expected_predecessor:
            raise CaseEnvelopeError("operation predecessor mismatch")
        summary, manifest, digest, size, manifest_hash, states = _read_package(Path(spec["package_path"]))
        pre_digest, post_digest = states.split(":")
        if summary.get("case_id") != case_id or summary.get("run_id") != case_id or summary.get("operation_id") != op_id:
            raise CaseEnvelopeError("foreign operation package")
        if summary.get("repository_commit") != plan["repository_commit"]:
            raise CaseEnvelopeError("foreign repository operation")
        expected_hash = spec.get("package_sha256"); expected_size = spec.get("package_size")
        if digest != expected_hash or size != expected_size:
            raise CaseEnvelopeError("operation package identity mismatch")
        child_exit = summary.get("original_containment_exit_code")
        if child_exit != spec.get("original_child_exit") or spec.get("expected_exit") != child_exit:
            raise CaseEnvelopeError("operation exit mismatch")
        verdict = spec.get("operation_verdict")
        if verdict != "PASS":
            raise CaseEnvelopeError("operation verdict mismatch")
        if (summary.get("script_hashes", {}).get("runner") != identities["runner"]
                or summary.get("script_hashes", {}).get("publisher") != identities["publisher"]
                or summary.get("script_hashes", {}).get("containment") != identities["containment"]):
            raise CaseEnvelopeError("operation component identity mismatch")
        receipt = spec.get("retrieval")
        if not isinstance(receipt, dict) or set(receipt) != {"receipt_path", "receipt_sha256", "fedora_package_sha256", "verification_result"}:
            raise CaseEnvelopeError("invalid retrieval binding")
        _hex(receipt["receipt_sha256"], "receipt hash")
        if receipt["fedora_package_sha256"] != digest or receipt["verification_result"] != "PASS":
            raise CaseEnvelopeError("retrieval verification mismatch")
        rendered.append({
            "operation_id": op_id, "operation_type": op_type,
            "package": {"windows_path": spec["windows_path"], "size": size, "sha256": digest, "manifest_sha256": manifest_hash},
            "original_child_exit": child_exit, "helper_exit": spec.get("helper_exit"),
            "expected_exit": spec["expected_exit"], "operation_verdict": verdict,
            "started_utc": summary.get("started_at"), "finished_utc": summary.get("finished_at"),
            "precondition_state_sha256": pre_digest, "postcondition_state_sha256": post_digest,
            "predecessor_operation_id": expected_predecessor, "causal_relationship": spec.get("causal_relationship"),
            "cleanup_recovery_relationship": spec.get("cleanup_recovery_relationship"), "retrieval": receipt,
        })
    cleanup_positions = [i for i, x in enumerate(rendered) if x["operation_type"] == "cleanup"]
    if plan.get("case_type") == "abandoned_reuse":
        if cleanup_positions != [3]: raise CaseEnvelopeError("abandoned case cleanup sequence mismatch")
        if any(rendered[i]["cleanup_recovery_relationship"] != "after_cleanup:cleanup" for i in (4, 5)):
            raise CaseEnvelopeError("after-cleanup relationship mismatch")
    return {"schema_version": SCHEMA, "case_id": case_id, "case_type": plan.get("case_type"),
            "repository_commit": plan["repository_commit"], "identities": identities,
            "declared_sequence": sequence, "operations": rendered,
            "case_invariants": plan.get("case_invariants", {}), "final_verdict": "PASS",
            "failure_stage": None, "failure_reason": None, "published_utc": plan.get("published_utc")}


def publish(plan: dict[str, Any], destination: Path) -> str:
    payload = canonical(build(plan)); destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != payload: raise CaseEnvelopeError("conflicting case envelope")
        return sha256(destination)
    fd, name = tempfile.mkstemp(prefix=destination.name + ".partial.", dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return sha256(destination)


def verify(envelope: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    if not envelope.is_file() or envelope.is_symlink(): raise CaseEnvelopeError("missing envelope")
    digest = sha256(envelope)
    if expected_sha256 and digest != expected_sha256: raise CaseEnvelopeError("envelope hash mismatch")
    try: value = json.loads(envelope.read_bytes())
    except json.JSONDecodeError as exc: raise CaseEnvelopeError("malformed envelope") from exc
    if value.get("schema_version") != SCHEMA or value.get("final_verdict") != "PASS": raise CaseEnvelopeError("invalid envelope verdict")
    sequence, operations = value.get("declared_sequence"), value.get("operations")
    if not isinstance(sequence, list) or not isinstance(operations, list) or [x.get("operation_id") for x in operations] != sequence:
        raise CaseEnvelopeError("invalid envelope operation order")
    for op in operations:
        receipt = Path(op["retrieval"]["receipt_path"])
        if not receipt.is_file() or sha256(receipt) != op["retrieval"]["receipt_sha256"]:
            raise CaseEnvelopeError("retrieval receipt mismatch")
        receipt_value = json.loads(receipt.read_bytes())
        package = Path(receipt_value["fedora_destination"])
        if sha256(package) != op["package"]["sha256"] or sha256(package) != op["retrieval"]["fedora_package_sha256"]:
            raise CaseEnvelopeError("Fedora operation package mismatch")
        summary, _, _, size, manifest_hash, _ = _read_package(package)
        if size != op["package"]["size"] or manifest_hash != op["package"]["manifest_sha256"] or summary["operation_id"] != op["operation_id"]:
            raise CaseEnvelopeError("Fedora operation reference mismatch")
    return {"schema_version": SCHEMA, "case_id": value["case_id"], "operation_count": len(operations), "envelope_sha256": digest, "verdict": "PASS"}
