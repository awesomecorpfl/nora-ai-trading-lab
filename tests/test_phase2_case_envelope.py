import copy, hashlib, json
from pathlib import Path

import pytest

from lab.phase2_case_envelope import CaseEnvelopeError, build, publish, sha256, verify
from lab.phase2_containment_evidence import publish as publish_operation

REPO = "a" * 40
RUNNER = "b" * 64
PUBLISHER = "c" * 64
SEQUENCE = ["classification", "same-before", "changed-before", "cleanup", "same-after", "changed-after"]


def _source(root: Path):
    root.mkdir()
    for name, data in {"stdout.txt": b"out", "stderr.txt": b"err", "pre_state.json": b"{}\n",
                       "post_state.json": b"{}\n", "firewall_pre.json": b"{}\n", "firewall_post.json": b"{}\n",
                       "processes.json": b"{}\n", "recovery.json": b"{}\n", "cleanup.json": b"{}\n"}.items():
        (root / name).write_bytes(data)
    return root


def _summary(case_id, op_id, exit_code):
    return {"case_id": case_id, "operation_id": op_id, "expected_verdict": "EXPECTED", "run_id": case_id,
            "repository_commit": REPO, "script_hashes": {"runner": RUNNER, "publisher": PUBLISHER, "containment": "d"*64},
            "windows_hashes": {}, "host_identity": {}, "evidence_root": "C:\\NoraEvidence\\Phase2",
            "transaction_identity": case_id, "executable_paths": [], "executable_hashes": [], "rule_guids": [],
            "rule_names": [], "application_filters": [], "fault_injection_point": None,
            "started_at": "2026-07-16T00:00:00Z", "finished_at": "2026-07-16T00:00:01Z",
            "command": "fixture", "wrapper_identity": {}, "original_containment_exit_code": exit_code,
            "final_caller_exit_code": exit_code, "recovery_result": "not_invoked", "cleanup_result": "not_invoked",
            "unrelated_firewall_result": {}, "final_invariants": {}}


def make_plan(tmp_path: Path):
    case_id = "case-architecture-1"; operations=[]
    for index, op_id in enumerate(SEQUENCE):
        package=tmp_path/f"{op_id}.zip"; exit_code=0 if op_id in {"classification","cleanup"} else 1
        publish_operation(_source(tmp_path/f"src-{op_id}"),package,_summary(case_id,op_id,exit_code))
        receipt=tmp_path/f"{op_id}.receipt.json"
        receipt.write_text(json.dumps({"fedora_destination":str(package)},sort_keys=True)+"\n")
        operations.append({"operation_id":op_id,"operation_type":"cleanup" if op_id=="cleanup" else ("classification" if op_id=="classification" else "reuse_attempt"),
                           "package_path":str(package),"windows_path":f"C:\\NoraEvidence\\Phase2\\cases\\{case_id}\\{op_id}.zip",
                           "package_size":package.stat().st_size,"package_sha256":sha256(package),"original_child_exit":exit_code,
                           "helper_exit":0,"expected_exit":exit_code,"operation_verdict":"PASS",
                           "predecessor_operation_id":None if index==0 else SEQUENCE[index-1],"causal_relationship":"ordered_after_predecessor",
                           "cleanup_recovery_relationship":"cleanup_boundary" if op_id=="cleanup" else ("after_cleanup:cleanup" if index>3 else None),
                           "retrieval":{"receipt_path":str(receipt),"receipt_sha256":sha256(receipt),"fedora_package_sha256":sha256(package),"verification_result":"PASS"}})
    return {"case_id":case_id,"case_type":"abandoned_reuse","repository_commit":REPO,
            "identities":{"native_execution":"e"*64,"runner":RUNNER,"containment":"d"*64,"publisher":PUBLISHER,"verifier":"f"*64,"retrieval_wrapper":"1"*64},
            "declared_sequence":SEQUENCE,"operations":operations,"case_invariants":{"final_rules":0},"published_utc":"2026-07-16T00:01:00Z"}


def test_round_trip_and_identical_idempotency(tmp_path):
    plan=make_plan(tmp_path); envelope=tmp_path/"case.json"; digest=publish(plan,envelope)
    assert publish(plan,envelope)==digest
    assert verify(envelope,digest)["operation_count"]==6
    before=envelope.read_bytes(); assert verify(envelope,digest)["verdict"]=="PASS"; assert envelope.read_bytes()==before


@pytest.mark.parametrize(("mutation","match"),[
    (lambda p:p["operations"].pop(),"operation order"),
    (lambda p:p["operations"].__setitem__(1,copy.deepcopy(p["operations"][0])),"operation order"),
    (lambda p:p["operations"][1].__setitem__("package_path",p["operations"][0]["package_path"]),"duplicate package"),
    (lambda p:p["operations"][1].__setitem__("package_sha256","0"*64),"package identity"),
    (lambda p:p["operations"][1].__setitem__("package_size",0),"package identity"),
    (lambda p:p["operations"][1].__setitem__("original_child_exit",0),"exit mismatch"),
    (lambda p:p["operations"][1].__setitem__("expected_exit",0),"exit mismatch"),
    (lambda p:p["operations"][1].__setitem__("operation_verdict","FAIL"),"verdict mismatch"),
    (lambda p:p["operations"][4].__setitem__("predecessor_operation_id","changed-before"),"predecessor"),
    (lambda p:p["operations"].__setitem__(3,{**p["operations"][3],"operation_type":"reuse_attempt"}),"cleanup sequence"),
    (lambda p:p["identities"].__setitem__("runner","9"*64),"component identity"),
    (lambda p:p.__setitem__("operations",None),"operation order"),
])
def test_structural_failures(tmp_path,mutation,match):
    plan=make_plan(tmp_path); mutation(plan)
    with pytest.raises((CaseEnvelopeError,AttributeError),match=match): build(plan)


def test_foreign_case_and_repository_packages_fail(tmp_path):
    plan=make_plan(tmp_path); package=Path(plan["operations"][0]["package_path"])
    package.unlink(); publish_operation(_source(tmp_path/"foreign"),package,_summary("foreign-case","classification",0))
    plan["operations"][0]["package_size"]=package.stat().st_size; plan["operations"][0]["package_sha256"]=sha256(package)
    with pytest.raises(CaseEnvelopeError,match="foreign operation"): build(plan)


def test_conflicting_envelope_and_receipt_are_rejected(tmp_path):
    plan=make_plan(tmp_path); envelope=tmp_path/"case.json"; publish(plan,envelope)
    changed=copy.deepcopy(plan); changed["case_invariants"]={"final_rules":1}
    with pytest.raises(CaseEnvelopeError,match="conflicting case envelope"): publish(changed,envelope)
    receipt=Path(plan["operations"][0]["retrieval"]["receipt_path"]); receipt.write_text("{}\n")
    with pytest.raises(CaseEnvelopeError,match="retrieval receipt mismatch"): verify(envelope)


@pytest.mark.parametrize("operation_type",["recovery","interruption","concurrency_owner","concurrency_loser"])
def test_schema_represents_future_operation_types(tmp_path,operation_type):
    plan=make_plan(tmp_path); plan["case_type"]="future-structure"; plan["operations"][3]["operation_type"]=operation_type
    assert build(plan)["operations"][3]["operation_type"]==operation_type


def test_repository_owned_abandoned_orchestrator_has_exact_sequence_and_boundaries():
    source=(Path(__file__).parents[1]/"scripts"/"phase2-run-abandoned-case.py").read_text()
    for token in ("classification", "same-before", "changed-before", "cleanup", "same-after", "changed-after",
                  "phase2-exit-propagation-batch", "phase2-retrieve-containment-evidence.py", "runner-operation",
                  "abandon-fixture-cleanup", "verify_operation", "verify_envelope"):
        assert token in source
    assert source.index('("classification"') < source.index('("same-before"') < source.index('("changed-before"') < source.index('("cleanup"') < source.index('("same-after"') < source.index('("changed-after"')


def test_windows_builder_is_atomic_hash_validating_and_path_confined():
    source=(Path(__file__).parents[1]/"phase-0a-h"/"windows"/"phase2-case-envelope.ps1").read_text()
    for token in ("nora.phase2_case_envelope_v1", "ZipArchive", "manifest_sha256", "foreign_package",
                  "component_identity", "operation_exit_or_verdict", "predecessor", "after_cleanup_relationship",
                  "Flush($true)", "[IO.File]::Move", "conflicting_envelope", "reparse_path", "outside_root"):
        assert token in source
    assert "New-NetFirewallRule" not in source and "Remove-NetFirewallRule" not in source


def test_schema_rejects_scalar_or_null_operation_collections_by_contract():
    schema=json.loads((Path(__file__).parents[1]/"docs"/"phase2_case_envelope_schema_v1.json").read_text())
    assert schema["properties"]["declared_sequence"]["type"]=="array"
    assert schema["properties"]["operations"]["type"]=="array"


def test_stale_process_cleanup_is_exactly_bound():
    source=(Path(__file__).parents[1]/"phase-0a-h"/"windows"/"stop-phase2-bound-process.ps1").read_text()
    for token in ("ExpectedStartTimeUtc", "ExpectedCommandLineSha256", "ExpectedOwner", "HashText", "bound process identity mismatch", "Stop-Process -Id $ProcessId"):
        assert token in source
    assert "Get-Process powershell" not in source and "taskkill" not in source.lower()
