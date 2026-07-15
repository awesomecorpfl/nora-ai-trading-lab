import copy
from pathlib import Path

import pytest

import lab.phase2_ten_strategy_v2 as v2
from lab.native_target import NATIVE_EXECUTION_REQUIRED_ROLES, identified
from lab.phase2_execution import sha
from lab.phase2_ten_strategy import FIX


def _record():
    ci=v2.build_compile_input()
    return {"schema_version":v2.COMPILER_OUTPUT_SCHEMA,
            "compiler_descriptor_identity":ci["compiler_descriptor_identity"],
            "compile_input_identity":ci["compile_input_identity"],
            "compiler_output_identity":"1"*64,"ex5_sha256":"2"*64,"ex5_path":v2.EX5}


def _reidentify(contract):
    contract.pop("native_execution_contract_identity",None)
    contract["native_execution_contract_identity"]=sha(contract)
    return contract


def test_complete_compiler_only_descriptor_is_accepted_and_execution_roles_rejected():
    value=identified(v2.compiler_descriptor().value(),"compiler_descriptor_identity")
    assert v2.validate_compiler_descriptor(value)==[]
    value["windows_packet_launcher"]="wrong boundary"
    assert any("execution role" in x for x in v2.validate_compiler_descriptor(value))
    value=identified(v2.compiler_descriptor().value(),"compiler_descriptor_identity");value.pop("tester_source")
    assert "missing compiler field:tester_source" in v2.validate_compiler_descriptor(value)


def test_execution_changes_do_not_change_compile_input_identity(monkeypatch):
    before=v2.build_compile_input()["compile_input_identity"]
    original=v2.file_sha
    monkeypatch.setattr(v2,"file_sha",lambda p:"f"*64 if Path(p).name=="execute-ten-strategy-packet.ps1" else original(p))
    assert v2.build_compile_input()["compile_input_identity"]==before
    assert v2.native_execution_contract()["native_execution_contract_identity"]!=v2.load(v2.NATIVE_CONTRACT_FILE)["native_execution_contract_identity"]


def test_source_build_command_and_policy_change_compile_identity():
    base=v2.build_compile_input()["compile_input_identity"]
    assert v2.build_compile_input(runtime=b"changed")["compile_input_identity"]!=base
    assert v2.build_compile_input(build="5.0.0.changed")["compile_input_identity"]!=base
    assert v2.build_compile_input(invocation_schema="changed")["compile_input_identity"]!=base
    assert v2.build_compile_input(invocation_template="changed")["compile_input_identity"]!=base
    assert v2.build_compile_input(success_policy="changed")["compile_input_identity"]!=base


def test_complete_genuine_native_role_set_is_accepted():
    contract=v2.native_execution_contract()
    assert {x["role"] for x in contract["roles"]}==set(NATIVE_EXECUTION_REQUIRED_ROLES)
    assert v2.validate_native_execution_contract(contract)==[]
    assert all(x["native_acceptance_eligible"] for x in contract["roles"])
    assert all(not x["native_acceptance_eligible"] for x in contract["synthetic_roles"])


@pytest.mark.parametrize("missing",NATIVE_EXECUTION_REQUIRED_ROLES)
def test_each_required_genuine_role_missing_is_rejected(missing):
    contract=copy.deepcopy(v2.native_execution_contract())
    contract["roles"]=[x for x in contract["roles"] if x["role"]!=missing]
    _reidentify(contract)
    assert "missing role:"+missing in v2.validate_native_execution_contract(contract)


def test_duplicate_synthetic_substitution_and_path_hash_mismatch_rejected():
    contract=copy.deepcopy(v2.native_execution_contract());contract["roles"].append(copy.deepcopy(contract["roles"][0]));_reidentify(contract)
    assert "duplicate role" in v2.validate_native_execution_contract(contract)
    contract=copy.deepcopy(v2.native_execution_contract());role=next(x for x in contract["roles"] if x["role"]=="atomic_genuine_returned_package_builder");role.update(type="synthetic_protocol_fixture",native_acceptance_eligible=False);_reidentify(contract)
    errors=v2.validate_native_execution_contract(contract);assert any("synthetic substitution" in x for x in errors)
    contract=copy.deepcopy(v2.native_execution_contract());contract["roles"][1]["path"]="wrong/path";_reidentify(contract)
    assert any("path mismatch" in x for x in v2.validate_native_execution_contract(contract))
    contract=copy.deepcopy(v2.native_execution_contract());contract["roles"][1]["sha256"]="0"*64;_reidentify(contract)
    assert any("hash mismatch" in x for x in v2.validate_native_execution_contract(contract))


@pytest.mark.parametrize("filename",["execute-ten-strategy-packet.ps1","collect-ten-strategy-environment.ps1","phase2_ten_strategy_v2.py"])
def test_execution_component_bytes_change_packet_and_acceptance_identity(monkeypatch,filename):
    before_packet=v2.build_execution_packet(_record())
    before_batch=v2.build_final_batch(_record())
    original=v2.file_sha
    monkeypatch.setattr(v2,"file_sha",lambda p:"e"*64 if Path(p).name==filename else original(p))
    after_packet=v2.build_execution_packet(_record())
    after_batch=v2.build_final_batch(_record())
    assert after_packet["execution_packet_identity"]!=before_packet["execution_packet_identity"]
    assert after_batch["final_batch_identity"]!=before_batch["final_batch_identity"]


def test_historical_v1_compiler_evidence_readable_but_rejected_for_v2():
    final=FIX/"native_corrected_final"
    record=v2.load(final/"compile/compiler_record.json")
    assert record["schema_version"]=="nora.ten_strategy_compiler_output_v1"
    assert record["compiler_output_identity"]=="87a48eb8bf0297b46e438f7f5f692dde7b918a66eeca530f384bd6fc6fabfe26"
    with pytest.raises(ValueError,match="historical v1"):
        v2.build_execution_packet(record)


def test_old_mixed_target_descriptor_is_stale_for_v2_acceptance():
    old=v2.load(FIX/"target_descriptor.json")
    assert old["schema_version"]=="nora.native_target_descriptor_v1"
    assert "stale descriptor" in v2.validate_native_execution_contract(old)


def test_frozen_v2_descriptors_and_readiness_are_current():
    assert v2.load(v2.COMPILER_DESCRIPTOR_FILE)==identified(v2.compiler_descriptor().value(),"compiler_descriptor_identity")
    assert v2.load(v2.NATIVE_CONTRACT_FILE)==v2.native_execution_contract()
    assert v2.load(v2.COMPILE_INPUT_FILE)==v2.build_compile_input()
    assert v2.load(v2.PRECOMPILE_FILE)==v2.build_precompile()
    state=v2.load(v2.READINESS_FILE);assert state==v2.local_readiness()
    assert state["genuine_v2_recompilation_required"] and not state["final_packet_ready"]
    assert not state["native_execution_attempted"] and not state["searchable"]


def test_execution_only_runner_rebind_preserves_the_sealed_compiler_and_ex5(tmp_path):
    source=FIX/"native_v2_compiler_final"
    result=v2.reissue_final_from_sealed_compiler(source,tmp_path/"reissued")
    record=v2.load(source/"compile/compiler_record.json")
    packet=v2.load(tmp_path/"reissued"/"execution_packet.json")
    assert result["compiler_output_identity"]==record["compiler_output_identity"]
    assert packet["ex5_sha256"]==record["ex5_sha256"]
    assert packet==v2.build_execution_packet(record)
    assert v2.load(tmp_path/"reissued"/"final_batch.json")==v2.build_final_batch(record)
