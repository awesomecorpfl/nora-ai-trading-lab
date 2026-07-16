import json
from pathlib import Path

import pytest

from lab.phase2_containment_evidence import EvidenceError, SCHEMA, publish, verify


def metadata():
    return {
        "case_id": "pkg-test-1", "operation_id": "synthetic", "expected_verdict": "PASS", "run_id": "pkg-test-1",
        "repository_commit": "a" * 40, "script_hashes": {"containment": "b" * 64},
        "windows_hashes": {"containment": "b" * 64}, "host_identity": "host",
        "evidence_root": "C:\\NoraEvidence\\Phase2", "transaction_identity": "tx",
        "executable_paths": ["C:\\Windows\\System32\\notepad.exe"],
        "executable_hashes": ["c" * 64], "fault_injection_point": None,
        "rule_guids": [], "rule_names": [], "application_filters": [],
        "started_at": "2026-07-18T00:00:00Z", "finished_at": "2026-07-18T00:00:01Z",
        "command": ["synthetic"], "wrapper_identity": "wrapper",
        "final_caller_exit_code": 0, "recovery_result": {}, "cleanup_result": {},
        "unrelated_firewall_result": {"equal": True}, "final_invariants": {"rules": 0},
    }


def source(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    for name, data in {
        "stdout.txt": b"out\x00\xff\n", "stderr.txt": b"err\r\n", "pre_state.json": b"{}\n",
        "post_state.json": b"{}\n", "firewall_pre.json": b"[]\n", "firewall_post.json": b"[]\n",
        "processes.json": b"[]\n", "recovery.json": b"{}\n", "cleanup.json": b"{}\n",
    }.items():
        p = tmp_path / name; p.write_bytes(data)
    return tmp_path


def test_atomic_publish_and_verify_round_trip(tmp_path):
    package = tmp_path / "case.zip"
    digest = publish(source(tmp_path / "source"), package, metadata())
    result = verify(package, digest)
    assert result["schema"] == SCHEMA and result["member_count"] == 9
    assert verify(package, digest) == result


def test_missing_member_rejected(tmp_path):
    root = source(tmp_path / "source"); (root / "stderr.txt").unlink()
    with pytest.raises(EvidenceError, match="missing members"):
        publish(root, tmp_path / "case.zip", metadata())


def test_conflicting_duplicate_rejected(tmp_path):
    root = source(tmp_path / "source"); package = tmp_path / "case.zip"
    publish(root, package, metadata()); (root / "stdout.txt").write_bytes(b"changed")
    with pytest.raises(EvidenceError, match="conflicting"):
        publish(root, package, metadata())


def test_wrong_member_and_package_hash_rejected(tmp_path):
    root = source(tmp_path / "source"); package = tmp_path / "case.zip"
    digest = publish(root, package, metadata())
    with pytest.raises(EvidenceError, match="package hash"):
        verify(package, "0" * 64)
    corrupt = tmp_path / "corrupt.zip"; corrupt.write_bytes(package.read_bytes()[:-1])
    with pytest.raises(EvidenceError):
        verify(corrupt, digest)


def test_array_shape_is_required(tmp_path):
    root = source(tmp_path / "source"); bad = metadata(); bad["executable_paths"] = "scalar"
    with pytest.raises(EvidenceError, match="must be an array"):
        publish(root, tmp_path / "case.zip", bad)
