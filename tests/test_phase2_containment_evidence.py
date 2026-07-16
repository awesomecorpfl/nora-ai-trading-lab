import json
import hashlib
import copy
import zipfile
from pathlib import Path

import pytest

from lab.phase2_containment_evidence import EvidenceError, SCHEMA, publish, verify
from lab.phase2_firewall_preservation import SCHEMA as FIREWALL_SCHEMA


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


def complete_firewall():
    profiles=[{"name":n,"enabled":True,"default_inbound":"block","default_outbound":"allow","allow_local_firewall_rules":"true","allow_local_ipsec_rules":"true","notify_on_listen":"false","policy_store_source":"local"} for n in ("Domain","Private","Public")]
    rule={"view":"effective","name":"safe","instance_id":"id1","group":"system","enabled":True,"direction":"inbound","action":"allow","profile":"any","policy_store":"activestore","policy_store_source_type":"local","policy_store_source":"local","edge_traversal":"none","interface_types":[],"owner":None,"programs":[],"services":[],"protocols":["tcp"],"local_ports":["22"],"remote_ports":[],"icmp_types":[],"local_addresses":[],"remote_addresses":[],"interfaces":[],"security":[],"packages":[],"local_users":[],"remote_users":[]}
    return {"schema_version":FIREWALL_SCHEMA,"host_identity":"host","repository_commit":"a"*40,"captured_utc":"now","profiles":profiles,"effective_rules":[rule],"persistent_rules":[],"diagnostics":{}}


def firewall_source(tmp_path, post=None):
    root=source(tmp_path); pre=complete_firewall(); post=copy.deepcopy(post or pre)
    (root/"firewall_inventory_pre.json").write_text(json.dumps(pre),encoding="utf-8")
    (root/"firewall_inventory_post.json").write_text(json.dumps(post),encoding="utf-8")
    summary=metadata(); summary["firewall_preservation"]={"schema_version":"nora.phase2_operation_firewall_binding_v2","capture_tool_sha256":"d"*64,"pre_inventory":{"sha256":hashlib.sha256((root/"firewall_inventory_pre.json").read_bytes()).hexdigest()},"post_inventory":{"sha256":hashlib.sha256((root/"firewall_inventory_post.json").read_bytes()).hexdigest()}}
    return root,summary


def test_fedora_recomputes_complete_firewall_and_rejects_temporal_substitution(tmp_path):
    root,summary=firewall_source(tmp_path/"source")
    package=tmp_path/"case.zip";digest=publish(root,package,summary)
    assert verify(package,digest)["firewall_recomputed"]["verdict"]=="PASS"
    stale=copy.deepcopy(complete_firewall());stale["effective_rules"][0]["enabled"]=False
    root,summary=firewall_source(tmp_path/"stale",stale)
    summary["firewall_preservation"]["pre_inventory"]["sha256"]="0"*64
    stale_package=tmp_path/"stale.zip";publish(root,stale_package,summary)
    with pytest.raises(EvidenceError,match="firewall semantic inequality"):
        verify(stale_package)


def test_fedora_rejects_swapped_or_semantically_different_post_inventory(tmp_path):
    changed=complete_firewall();changed["profiles"][0]["enabled"]=False
    root,summary=firewall_source(tmp_path/"source",changed);package=tmp_path/"case.zip";publish(root,package,summary)
    with pytest.raises(EvidenceError,match="firewall invariant failure"):
        verify(package)


def test_fedora_rejects_one_byte_firewall_member_tampering(tmp_path):
    root,summary=firewall_source(tmp_path/"source");package=tmp_path/"case.zip";publish(root,package,summary)
    tampered=tmp_path/"tampered.zip"
    with zipfile.ZipFile(package) as zin, zipfile.ZipFile(tampered,"w",compression=zipfile.ZIP_STORED) as zout:
        for info in zin.infolist():
            data=zin.read(info.filename)
            if info.filename=="firewall_inventory_pre.json": data=data[:-1]+(b" " if data[-1:]!=b" " else b"!")
            zout.writestr(info,data)
    with pytest.raises(EvidenceError):
        verify(tampered)
