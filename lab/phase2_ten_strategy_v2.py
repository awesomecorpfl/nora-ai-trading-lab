"""V2 compiler-semantic and genuine native-execution identity boundaries.

V1 artifacts remain readable historical evidence. They are deliberately not
accepted by any function in this module for V2 native acceptance.
"""
from __future__ import annotations

import csv
import json
import shutil
import tempfile
from pathlib import Path

from lab.mql5gen.ten_strategy import CSV, PACKAGE, RUNTIME, TESTER, generate
from lab.native_target import (
    BUILD, COMPILER_LOG_REDACTION_POLICY_IDENTITY, EDITOR, POLICY,
    CompilerSemanticDescriptor, NATIVE_EXECUTION_REQUIRED_ROLES,
    evaluate_environmental_acceptance, file_sha, identified, inventory_identity,
    raw_sha, safe_relative, validate_compiler_log_redaction, validate_typed_roles,
    compiler_output_identity, atomic_publish,
)
from lab.phase2_execution import canon, sha
from lab.phase2_ten_strategy import FIX, EXECUTION_IDENTITY, TIME_IDENTITY
from lab.phase2_ten_strategy_native import (
    budget_map, expected_rows, load, reconciliation_protocol, reconcile_rows,
)

ROOT = Path(__file__).resolve().parents[1]
TARGET = "phase2_ten_strategy_suite"
COMPILER_DESCRIPTOR_FILE = FIX / "compiler_descriptor_v2.json"
NATIVE_CONTRACT_FILE = FIX / "native_execution_contract_v2.json"
COMPILE_INPUT_FILE = FIX / "compile_input_v2.json"
PRECOMPILE_FILE = FIX / "precompile_batch_v2.json"
READINESS_FILE = FIX / "local_readiness_v2.json"
EX5 = "NoraPhase2TenStrategyTesterCanaryV1.ex5"
COMPILER_OUTPUT_SCHEMA = "nora.ten_strategy_compiler_output_v2"
COMPILER_EVIDENCE_SCHEMA = "nora.ten_strategy_compile_evidence_manifest_v2"
COMPILE_INPUT_SCHEMA = "nora.ten_strategy_compile_input_v2"
PRECOMPILE_SCHEMA = "nora.ten_strategy_precompile_batch_v2"
NATIVE_CONTRACT_SCHEMA = "nora.ten_strategy_native_execution_role_contract_v2"
EXECUTION_PACKET_SCHEMA = "nora.ten_strategy_native_packet_v2"
FINAL_BATCH_SCHEMA = "nora.ten_strategy_final_native_batch_v2"
RETURNED_SCHEMA = "nora.ten_strategy_atomic_returned_package_v2"
HOST_CONTEXTS = ("GDAXI/M1:corrected-A1", "GDAXI/M1:corrected-A2",
                 "AUDCAD/M1:corrected-B1", "AUDCAD/M1:corrected-B2")
FORBIDDEN_COMPILER_FIELDS = {"windows_packet_launcher", "environmental_forensic_collector",
                             "native_execution_contract", "returned_package_builder",
                             "importer", "reconciliation"}


def _generated() -> tuple[dict, dict[str, bytes]]:
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        package = generate(Path(directory))
        data = {name: (Path(directory) / name).read_bytes() for name in (RUNTIME, TESTER, PACKAGE)}
    return package, data


def compiler_descriptor(*, build: str = BUILD, invocation_schema: str = "nora.metaeditor_compile_invocation_v2",
                        invocation_template: str | None = None, success_policy: str = POLICY, runtime: bytes | None = None,
                        tester: bytes | None = None) -> CompilerSemanticDescriptor:
    package, data = _generated()
    runtime = data[RUNTIME] if runtime is None else runtime
    tester = data[TESTER] if tester is None else tester
    output_contract = {
        "schema_version": "nora.metaeditor_ex5_output_contract_v2",
        "path": "compile/" + EX5,
        "fresh_invocation_required": True,
        "stale_substitution_forbidden": True,
    }
    return CompilerSemanticDescriptor(
        schema_version="nora.compiler_semantic_descriptor_v2",
        target_identifier=TARGET,
        runtime_source={"path": "generated/" + RUNTIME, "sha256": raw_sha(runtime), "role": "mql5_include"},
        tester_source={"path": "generated/" + TESTER, "sha256": raw_sha(tester), "role": "mql5_compile_unit"},
        include_sources=({"path": "generated/" + RUNTIME, "sha256": raw_sha(runtime), "role": "mql5_include"},),
        compiler_product_identity="metaquotes.metaeditor64",
        compiler_executable=EDITOR,
        required_build=build,
        invocation_schema=invocation_schema,
        invocation_template=invocation_template or f'{EDITOR} /compile:"{{tester_source}}" /log:"{{compiler_log}}"',
        success_policy=success_policy,
        compiler_output_schema=COMPILER_OUTPUT_SCHEMA,
        compiler_evidence_schema=COMPILER_EVIDENCE_SCHEMA,
        compiler_log_evidence_schema="nora.raw_bound_redacted_compiler_log_v1",
        redaction_policy_identity=COMPILER_LOG_REDACTION_POLICY_IDENTITY,
        output_ex5_contract=output_contract,
        source_schema_version="nora.phase2_ten_strategy_mql5_source_v1",
        package_schema_version=package["schema_version"],
        compile_allowlist=("generated/" + TESTER, "generated/" + RUNTIME),
    )


def build_compile_input(**descriptor_overrides) -> dict:
    descriptor = compiler_descriptor(**descriptor_overrides)
    package, data = _generated()
    value = {
        "schema_version": COMPILE_INPUT_SCHEMA,
        "target_identifier": TARGET,
        "compiler_descriptor_identity": descriptor.identity,
        "source_files": [descriptor.tester_source, *descriptor.include_sources],
        "compiler_product_identity": descriptor.compiler_product_identity,
        "expected_metaeditor_executable": descriptor.compiler_executable,
        "expected_metaeditor_build": descriptor.required_build,
        "compiler_invocation_schema": descriptor.invocation_schema,
        "compile_command_template": descriptor.invocation_template,
        "compiler_success_policy": descriptor.success_policy,
        "compiler_output_schema": descriptor.compiler_output_schema,
        "compiler_log_evidence_schema": descriptor.compiler_log_evidence_schema,
        "redaction_policy_identity": descriptor.redaction_policy_identity,
        "output_ex5_contract": descriptor.output_ex5_contract,
        "runtime_identity": package["runtime_identity"],
        "runtime_sha256": raw_sha(data[RUNTIME]),
        "tester_identity": package["tester_identity"],
        "tester_sha256": raw_sha(data[TESTER]),
        "package_identity": package["package_identity"],
        "compile_allowlist": list(descriptor.compile_allowlist),
        "required_warning_count": 0,
        "required_error_count": 0,
    }
    return identified(value, "compile_input_identity")


def validate_compiler_descriptor(value: dict) -> list[str]:
    errors = []
    required = {"runtime_source", "tester_source", "compiler_product_identity", "compiler_executable",
                "required_build", "invocation_schema", "invocation_template", "success_policy",
                "compiler_output_schema", "compiler_evidence_schema", "compiler_log_evidence_schema",
                "redaction_policy_identity", "output_ex5_contract", "compile_allowlist"}
    for field in sorted(required - set(value)): errors.append("missing compiler field:" + field)
    for field in sorted(FORBIDDEN_COMPILER_FIELDS & set(value)): errors.append("execution role in compiler descriptor:" + field)
    claimed = value.get("compiler_descriptor_identity")
    if claimed and sha({k: v for k, v in value.items() if k != "compiler_descriptor_identity"}) != claimed:
        errors.append("compiler descriptor identity")
    return errors


def _role(role: str, path: str, schema: str, *, digest: str | None = None,
          hash_kind: str = "repository_file_bytes") -> dict:
    if digest is None: digest = file_sha(ROOT / path)
    return {"type": "genuine_native_role", "role": role, "path": path,
            "sha256": digest, "hash_kind": hash_kind,
            "schema_version_identity": sha({"role": role, "schema_version": schema}),
            "native_acceptance_eligible": True}


def native_execution_contract() -> dict:
    package, data = _generated()
    output_contract = compiler_descriptor().output_ex5_contract
    roles = [
        _role("compiled_ex5", "compile/" + EX5, output_contract["schema_version"],
              digest=sha(output_contract), hash_kind="compiler_output_contract_identity"),
        _role("windows_packet_launcher", "phase-0a-h/windows/execute-ten-strategy-packet.ps1", "nora.ten_strategy_windows_launcher_v2"),
        _role("persistent_windows_evidence_runner", "phase-0a-h/windows/phase2-evidence-runner.ps1", "nora.phase2_persistent_evidence_runner_v1"),
        _role("tester_configuration_builder", "phase-0a-h/windows/build-ten-strategy-tester-config.ps1", "nora.ten_strategy_tester_configuration_v2"),
        _role("environmental_forensic_collector", "phase-0a-h/windows/collect-ten-strategy-environment.ps1", "nora.ten_strategy_environment_inventory_v2"),
        _role("journal_environmental_acceptance_evaluator", "lab/native_target.py", "nora.environmental_acceptance_option_b_v2"),
        _role("completion_failure_marker_contract", "docs/phase2_ten_strategy_marker_contract_v2.json", "nora.ten_strategy_completion_failure_marker_contract_v2"),
        _role("native_csv_ledger_producer", "tests/fixtures/phase2_ten_strategy_suite/generated/" + TESTER, "nora.ten_strategy_csv_ledger_v1", digest=raw_sha(data[TESTER])),
        _role("atomic_genuine_returned_package_builder", "phase-0a-h/windows/build-ten-strategy-returned-package.ps1", RETURNED_SCHEMA),
        _role("fedora_transfer_retrieval_orchestrator", "scripts/phase2-ten-strategy-native-orchestrate", "nora.ten_strategy_transfer_retrieval_v2"),
        _role("genuine_returned_package_importer", "scripts/phase2-ten-strategy-ingest-returned", "nora.ten_strategy_genuine_importer_v2"),
        _role("exact_reconciliation_implementation", "lab/phase2_ten_strategy_v2.py", "nora.ten_strategy_exact_reconciliation_v2"),
    ]
    synthetic = [{"type": "synthetic_protocol_fixture", "role": "synthetic_protocol_fixture",
                  "path": "scripts/phase2-ten-strategy-build-synthetic-package",
                  "sha256": file_sha(ROOT / "scripts/phase2-ten-strategy-build-synthetic-package"),
                  "schema_version_identity": sha({"schema_version": "nora.ten_strategy_synthetic_fixture_v1"}),
                  "native_acceptance_eligible": False}]
    value = {
        "schema_version": NATIVE_CONTRACT_SCHEMA,
        "target_identifier": TARGET,
        "roles": roles,
        "synthetic_roles": synthetic,
        "compiled_ex5_materialization": "fresh_v2_genuine_compiler_evidence_required",
        "execution_schema_versions": [EXECUTION_PACKET_SCHEMA, FINAL_BATCH_SCHEMA, RETURNED_SCHEMA],
        "environmental_policy_identity": file_sha(ROOT / "docs/phase2_history_sync_marker_classification.json"),
        "fixture_identity": load(FIX / "fixture_suite.json")["input_fixture_identity"],
        "suite_identity": load(FIX / "strategy_suite.json")["suite_identity"],
        "target_host_contract": {"contexts": list(HOST_CONTEXTS), "timeframe": "M1"},
        "atomic_package_schema": RETURNED_SCHEMA,
        "reconciliation_schema": "nora.ten_strategy_exact_reconciliation_v2",
    }
    errors = validate_typed_roles(roles)
    if errors: raise ValueError(", ".join(errors))
    return identified(value, "native_execution_contract_identity")


def validate_native_execution_contract(value: dict, *, materialized: bool = False) -> list[str]:
    errors: list[str] = []
    if value.get("schema_version") != NATIVE_CONTRACT_SCHEMA: errors.append("stale descriptor")
    roles = value.get("roles") if isinstance(value.get("roles"), list) else []
    errors.extend(validate_typed_roles(roles))
    if materialized:
        ex5 = next((x for x in roles if x.get("role") == "compiled_ex5"), {})
        if ex5.get("hash_kind") != "artifact_bytes": errors.append("unmaterialized compiled_ex5")
        if value.get("compiler_evidence_version") != "v2": errors.append("historical v1 compiler evidence")
        if not value.get("compiler_output_identity"): errors.append("missing compiler evidence")
    expected_paths = {x["role"]: x["path"] for x in native_execution_contract()["roles"]}
    for role in roles:
        path = role.get("path", "")
        if role.get("role") in expected_paths and path != expected_paths[role["role"]]: errors.append("role path mismatch:" + role["role"])
        if role.get("hash_kind") == "repository_file_bytes" and safe_relative(path):
            file_path = ROOT / path
            if not file_path.is_file() or file_sha(file_path) != role.get("sha256"): errors.append("role hash mismatch:" + str(role.get("role")))
    claimed = value.get("native_execution_contract_identity")
    if claimed and sha({k: v for k, v in value.items() if k != "native_execution_contract_identity"}) != claimed: errors.append("contract identity")
    return errors


def materialize_native_execution_contract(compiler_record: dict) -> dict:
    ci = build_compile_input()
    if compiler_record.get("schema_version") != COMPILER_OUTPUT_SCHEMA: raise ValueError("historical v1 compiler evidence")
    if compiler_record.get("compiler_descriptor_identity") != ci["compiler_descriptor_identity"]: raise ValueError("compiler descriptor mismatch")
    if compiler_record.get("compile_input_identity") != ci["compile_input_identity"]: raise ValueError("compile input mismatch")
    value = native_execution_contract()
    value.pop("native_execution_contract_identity")
    ex5 = next(x for x in value["roles"] if x["role"] == "compiled_ex5")
    ex5["sha256"] = compiler_record["ex5_sha256"]
    ex5["hash_kind"] = "artifact_bytes"
    value["compiler_evidence_version"] = "v2"
    value["compiler_output_identity"] = compiler_record["compiler_output_identity"]
    value["compile_input_identity"] = compiler_record["compile_input_identity"]
    value = identified(value, "native_execution_contract_identity")
    errors = validate_native_execution_contract(value, materialized=True)
    if errors: raise ValueError(", ".join(errors))
    return value


def build_execution_packet(compiler_record: dict) -> dict:
    """Build only after fresh V2 compilation; historical V1 records fail closed."""
    contract = materialize_native_execution_contract(compiler_record)
    ci = build_compile_input()
    value = {"schema_version": EXECUTION_PACKET_SCHEMA, "target_identifier": TARGET,
             "compiler_descriptor_identity": ci["compiler_descriptor_identity"],
             "compile_input_identity": ci["compile_input_identity"],
             "compiler_evidence_version": "v2",
             "compiler_output_identity": compiler_record["compiler_output_identity"],
             "ex5_sha256": compiler_record["ex5_sha256"], "ex5_path": compiler_record["ex5_path"],
             "native_execution_contract": contract,
             "native_execution_contract_identity": contract["native_execution_contract_identity"],
             "suite_identity": load(FIX / "strategy_suite.json")["suite_identity"],
             "fixture_identity": load(FIX / "fixture_suite.json")["input_fixture_identity"],
             "execution_contract_identity": EXECUTION_IDENTITY,
             "time_rule_contract_identity": TIME_IDENTITY,
             "environmental_policy_identity": contract["environmental_policy_identity"],
             "reconciliation_protocol_identity": reconciliation_protocol()["strategy_reconciliation_protocol_identity"],
             "budget_map_identity": budget_map()["applicable_budget_map_identity"],
             "host_context_matrix": list(HOST_CONTEXTS), "completion_marker": "NORA_PHASE2_TEN_STRATEGY_COMPLETE_V1",
             "failure_marker": "NORA_PHASE2_TEN_STRATEGY_FAIL_V1", "result_filename": CSV}
    return identified(value, "execution_packet_identity")


def build_final_batch(compiler_record: dict) -> dict:
    packet = build_execution_packet(compiler_record)
    staged = [{"path": role["path"], "role": role["role"], "sha256": role["sha256"]}
              for role in packet["native_execution_contract"]["roles"]]
    staged.append({"path": "execution_packet.json", "role": "execution_packet", "sha256": raw_sha((canon(packet) + "\n").encode())})
    value = {"schema_version": FINAL_BATCH_SCHEMA, "target_identifier": TARGET,
             "compile_input_identity": packet["compile_input_identity"],
             "compiler_output_identity": packet["compiler_output_identity"],
             "execution_packet_identity": packet["execution_packet_identity"],
             "native_execution_contract_identity": packet["native_execution_contract_identity"],
             "staged_files": staged, "staged_inventory_identity": inventory_identity(staged),
             "native_acceptance_identity": sha({"packet": packet["execution_packet_identity"],
                                                   "reconciliation": packet["native_execution_contract"]["roles"][-1]["sha256"]}),
             "native_execution_attempted": False, "native_parity_accepted": False,
             "searchable": False, "complete_phase2_gate": False}
    return identified(value, "final_batch_identity")


def stage_final(final_dir: Path, destination: Path) -> dict:
    """Reproducibly stage the materialized V2 execution packet and bound roles."""
    final_dir = Path(final_dir); packet = load(final_dir / "execution_packet.json"); batch = load(final_dir / "final_batch.json")
    if packet.get("schema_version") != EXECUTION_PACKET_SCHEMA or batch.get("execution_packet_identity") != packet.get("execution_packet_identity"):
        raise ValueError("final packet preflight")
    if batch != build_final_batch(load(final_dir / "compile/compiler_record.json")): raise ValueError("stale final batch")
    def write(tmp):
        for item in batch["staged_files"]:
            target = tmp / item["path"]; target.parent.mkdir(parents=True, exist_ok=True)
            if item["role"] == "compiled_ex5": shutil.copy2(final_dir / item["path"], target)
            elif item["role"] == "execution_packet": target.write_text(canon(packet) + "\n")
            else: shutil.copy2(ROOT / item["path"], target)
            if file_sha(target) != item["sha256"]: raise ValueError("final staging hash")
        (tmp / "final_batch.json").write_text(canon(batch) + "\n")
        return {"execution_packet_identity": packet["execution_packet_identity"],
                "final_batch_identity": batch["final_batch_identity"],
                "staged_inventory_identity": batch["staged_inventory_identity"]}
    return atomic_publish(Path(destination), ".ten-strategy-v2-final-stage-", write)


def build_precompile() -> dict:
    descriptor = compiler_descriptor()
    ci = build_compile_input()
    _, data = _generated()
    items = [
        {"path": "generated/" + RUNTIME, "role": "mql5_include", "sha256": raw_sha(data[RUNTIME])},
        {"path": "generated/" + TESTER, "role": "mql5_compile_unit", "sha256": raw_sha(data[TESTER])},
        {"path": "generated/" + PACKAGE, "role": "source_package_manifest", "sha256": raw_sha(data[PACKAGE])},
        {"path": "generated/ten_strategy_compile_input_v2.json", "role": "compile_input", "sha256": raw_sha((canon(ci) + "\n").encode())},
        {"path": "scripts/phase2-ten-strategy-build-compile-input", "role": "compiler_staging_entrypoint", "sha256": file_sha(ROOT / "scripts/phase2-ten-strategy-build-compile-input")},
    ]
    value = {"schema_version": PRECOMPILE_SCHEMA, "target_identifier": TARGET,
             "compiler_descriptor_identity": descriptor.identity,
             "compile_input_identity": ci["compile_input_identity"], "files": items,
             "staged_inventory_identity": inventory_identity(items),
             "compile_evidence_pending": True,
             "final_packet_ready": False, "native_execution_attempted": False,
             "native_parity_accepted": False, "searchable": False, "complete_phase2_gate": False}
    return identified(value, "precompile_batch_identity")


def stage_precompile(destination: Path) -> dict:
    batch = build_precompile(); ci = build_compile_input(); _, data = _generated()
    generated_data = {RUNTIME: data[RUNTIME], TESTER: data[TESTER], PACKAGE: data[PACKAGE],
                      "ten_strategy_compile_input_v2.json": (canon(ci) + "\n").encode()}
    def write(tmp):
        for item in batch["files"]:
            target = tmp / item["path"]; target.parent.mkdir(parents=True, exist_ok=True)
            if item["path"].startswith("generated/"): target.write_bytes(generated_data[target.name])
            else: shutil.copy2(ROOT / item["path"], target)
            if file_sha(target) != item["sha256"]: raise ValueError("precompile staging hash")
        (tmp / "compiler_descriptor_v2.json").write_text(canon(identified(compiler_descriptor().value(), "compiler_descriptor_identity")) + "\n")
        (tmp / "precompile_batch_v2.json").write_text(canon(batch) + "\n")
        return {"compiler_descriptor_identity": compiler_descriptor().identity,
                "compile_input_identity": ci["compile_input_identity"],
                "precompile_batch_identity": batch["precompile_batch_identity"],
                "staged_inventory_identity": batch["staged_inventory_identity"]}
    return atomic_publish(Path(destination), ".ten-strategy-v2-precompile-", write)


def validate_v2_compiler_record(record: dict, evidence_dir: Path) -> list[str]:
    ci = build_compile_input(); errors = []
    checks = {
        "schema": record.get("schema_version") == COMPILER_OUTPUT_SCHEMA,
        "target": record.get("target_identifier") == TARGET,
        "compiler descriptor": record.get("compiler_descriptor_identity") == ci["compiler_descriptor_identity"],
        "compile input": record.get("compile_input_identity") == ci["compile_input_identity"],
        "runtime hash": record.get("runtime_sha256") == ci["runtime_sha256"],
        "tester hash": record.get("tester_sha256") == ci["tester_sha256"],
        "package": record.get("package_identity") == ci["package_identity"],
        "compiler": record.get("metaeditor_executable") == EDITOR and record.get("observed_metaeditor_build") == BUILD,
        "policy": record.get("compiler_policy") == POLICY and record.get("policy_decision") in ("accepted_zero", "accepted_metaeditor_5836_one"),
        "exit": record.get("raw_process_exit") in (0, 1) and record.get("normalized_result") == "success",
        "warnings": record.get("warning_count") == 0 and record.get("warnings") == [],
        "errors": record.get("error_count") == 0 and record.get("errors") == [],
        "completion": record.get("completion_state") == "completed" and record.get("failure_reason") in (None, ""),
        "freshness": record.get("freshness_proof") == {"preexisting_ex5_removed_or_isolated": True, "produced_after_invocation_start": True, "single_unambiguous_ex5": True},
        "genuine": record.get("synthetic_protocol_fixture") is False,
    }
    errors.extend(key for key, valid in checks.items() if not valid)
    for kind in ("log", "ex5"):
        relative = record.get(kind + "_path", "")
        if not safe_relative(relative): errors.append(kind + " path"); continue
        path = Path(evidence_dir) / relative
        if not path.is_file(): errors.append("missing " + kind); continue
        if path.stat().st_size != record.get(kind + "_size") or file_sha(path) != record.get(kind + "_sha256"): errors.append(kind + " binding")
    if record.get("compiler_output_identity") != compiler_output_identity(record): errors.append("output identity")
    return errors


def import_genuine_compiler_evidence(evidence_dir: Path, destination: Path, raw_log_path: Path) -> dict:
    evidence_dir = Path(evidence_dir)
    allowed = {"compiler_record.json", "compile.redacted.log", EX5, "compile_evidence_manifest.json", "inventory.json"}
    if not evidence_dir.is_dir() or {x.name for x in evidence_dir.iterdir()} != allowed: raise ValueError("compiler evidence file set")
    record = load(evidence_dir / "compiler_record.json")
    errors = validate_v2_compiler_record(record, evidence_dir) + validate_compiler_log_redaction(record, evidence_dir, raw_log_path)
    if errors: raise ValueError(", ".join(errors))
    expected_manifest = {"schema_version": COMPILER_EVIDENCE_SCHEMA, "target_identifier": TARGET,
                         "compiler_descriptor_identity": compiler_descriptor().identity,
                         "compile_input_identity": build_compile_input()["compile_input_identity"]}
    if load(evidence_dir / "compile_evidence_manifest.json") != expected_manifest: raise ValueError("compile evidence manifest")
    inventory = load(evidence_dir / "inventory.json")
    if {x.get("path") for x in inventory} != allowed - {"inventory.json"}: raise ValueError("compiler inventory allowlist")
    for item in inventory:
        if not safe_relative(item.get("path", "")) or file_sha(evidence_dir / item["path"]) != item.get("sha256"): raise ValueError("compiler inventory binding")
    packet, batch = build_execution_packet(record), build_final_batch(record)
    def write(tmp):
        shutil.copytree(evidence_dir, tmp / "compile")
        (tmp / "compiler_descriptor_v2.json").write_text(canon(identified(compiler_descriptor().value(), "compiler_descriptor_identity")) + "\n")
        (tmp / "compile_input_v2.json").write_text(canon(build_compile_input()) + "\n")
        (tmp / "native_execution_contract_v2.json").write_text(canon(packet["native_execution_contract"]) + "\n")
        (tmp / "execution_packet.json").write_text(canon(packet) + "\n")
        (tmp / "final_batch.json").write_text(canon(batch) + "\n")
        return {"compiler_output_identity": record["compiler_output_identity"],
                "execution_packet_identity": packet["execution_packet_identity"],
                "final_batch_identity": batch["final_batch_identity"]}
    return atomic_publish(Path(destination), ".ten-strategy-v2-compiler-import-", write)


def reissue_final_from_sealed_compiler(sealed_dir: Path, destination: Path) -> dict:
    """Rebind a valid V2 compiler record to changed execution-only roles.

    This never recompiles, regenerates, or substitutes the EX5.  It is valid
    only before the first native launch and keeps compiler evidence immutable.
    """
    sealed_dir = Path(sealed_dir)
    record = load(sealed_dir / "compile" / "compiler_record.json")
    errors = validate_v2_compiler_record(record, sealed_dir / "compile")
    if errors:
        raise ValueError("sealed compiler record: " + ", ".join(errors))
    packet, batch = build_execution_packet(record), build_final_batch(record)
    def write(tmp):
        shutil.copytree(sealed_dir / "compile", tmp / "compile")
        (tmp / "compiler_descriptor_v2.json").write_text(canon(identified(compiler_descriptor().value(), "compiler_descriptor_identity")) + "\n")
        (tmp / "compile_input_v2.json").write_text(canon(build_compile_input()) + "\n")
        (tmp / "native_execution_contract_v2.json").write_text(canon(packet["native_execution_contract"]) + "\n")
        (tmp / "execution_packet.json").write_text(canon(packet) + "\n")
        (tmp / "final_batch.json").write_text(canon(batch) + "\n")
        return {"compiler_output_identity": record["compiler_output_identity"],
                "execution_packet_identity": packet["execution_packet_identity"],
                "final_batch_identity": batch["final_batch_identity"]}
    return atomic_publish(Path(destination), ".ten-strategy-v2-execution-rebind-", write)


def local_readiness() -> dict:
    value = {"schema_version": "nora.ten_strategy_local_readiness_v2", "target_identifier": TARGET,
             "compiler_descriptor_identity": compiler_descriptor().identity,
             "compile_input_identity": build_compile_input()["compile_input_identity"],
             "precompile_batch_identity": build_precompile()["precompile_batch_identity"],
             "staged_inventory_identity": build_precompile()["staged_inventory_identity"],
             "native_execution_contract_identity": native_execution_contract()["native_execution_contract_identity"],
             "historical_v1_compiler_evidence": "valid_source_correct_not_v2_native_eligible",
             "genuine_v2_recompilation_required": True, "compile_evidence_pending": True,
             "final_packet_ready": False, "native_execution_attempted": False,
             "native_parity_accepted": False, "grammar_admitted": False,
             "searchable": False, "complete_phase2_gate": False, "production_data_required": False}
    return identified(value, "local_readiness_identity")


def freeze() -> dict:
    descriptor = identified(compiler_descriptor().value(), "compiler_descriptor_identity")
    values = {"compiler_descriptor_v2.json": descriptor,
              "native_execution_contract_v2.json": native_execution_contract(),
              "compile_input_v2.json": build_compile_input(),
              "precompile_batch_v2.json": build_precompile(),
              "local_readiness_v2.json": local_readiness()}
    for name, value in values.items(): (FIX / name).write_text(canon(value) + "\n")
    return values


def _parse_csv(path: Path) -> list[dict]:
    nullable = set(("trade_ordinal", "signal_index", "signal_timestamp", "entry_index", "entry_timestamp",
                    "entry_price", "initial_stop", "initial_target", "exit_index", "exit_timestamp",
                    "exit_price", "holding_bars", "gross_price_return", "no_trade_reason"))
    integers = {"trade_ordinal", "signal_index", "entry_index", "exit_index", "holding_bars"}
    numeric = {"entry_price", "initial_stop", "initial_target", "exit_price", "gross_price_return"}
    with path.open(newline="", encoding="utf-8-sig") as handle: rows = list(csv.DictReader(handle, delimiter="\t"))
    result = []
    for row in rows:
        parsed = {}
        for key, value in row.items():
            if key in nullable and value == "NULL": parsed[key] = None
            elif key in integers: parsed[key] = int(value)
            elif key in numeric: parsed[key] = float(value)
            else: parsed[key] = value
        result.append(parsed)
    return result


def import_genuine_returned_package(package_dir: Path, execution_packet: dict) -> dict:
    package_dir = Path(package_dir)
    required = {"execution.json", CSV, "terminal-journal.log", "tester-journal.log", "tester.htm",
                "completion-marker.json", "failure-marker.json", "environment-before.json",
                "environment-after.json", "environmental-evaluation.json", "returned_inventory.json",
                "returned_result_manifest.json"}
    if not package_dir.is_dir() or {x.name for x in package_dir.iterdir()} != required: raise ValueError("atomic returned file set")
    if execution_packet.get("schema_version") != EXECUTION_PACKET_SCHEMA: raise ValueError("stale execution packet")
    if execution_packet.get("compiler_evidence_version") != "v2": raise ValueError("historical v1 compiler evidence")
    manifest = load(package_dir / "returned_result_manifest.json")
    execution = load(package_dir / "execution.json")
    if manifest.get("schema_version") != RETURNED_SCHEMA: raise ValueError("returned schema")
    if manifest.get("execution_packet_identity") != execution_packet.get("execution_packet_identity"): raise ValueError("packet identity")
    inventory = load(package_dir / "returned_inventory.json")
    if file_sha(package_dir / "returned_inventory.json") != manifest.get("returned_inventory_sha256"): raise ValueError("inventory identity")
    if {x.get("path") for x in inventory} != required - {"returned_inventory.json", "returned_result_manifest.json"}: raise ValueError("inventory allowlist")
    for item in inventory:
        path = item.get("path", "")
        if not safe_relative(path) or file_sha(package_dir / path) != item.get("sha256") or (package_dir / path).stat().st_size != item.get("size"): raise ValueError("inventory binding")
    completion, failure = load(package_dir / "completion-marker.json"), load(package_dir / "failure-marker.json")
    if completion.get("present") is not True or failure.get("present") is not False: raise ValueError("marker failure")
    environmental = load(package_dir / "environmental-evaluation.json")
    evidence = environmental.get("evidence", {})
    before, after = load(package_dir / "environment-before.json"), load(package_dir / "environment-after.json")
    def indexed(inventory):
        return {item["path"]: {"size": item["size"], "last_write_utc": item["last_write_utc"], "sha256": item["sha256"]}
                for item in inventory.get("files", [])}
    if evidence.get("before_inventory") != indexed(before) or evidence.get("after_inventory") != indexed(after):
        raise ValueError("environment inventory substitution")
    if evidence.get("bar_count_before") != before.get("observed_bar_count") or evidence.get("bar_count_after") != after.get("observed_bar_count"):
        raise ValueError("environment bar-count substitution")
    before_range = [before.get("earliest_history_timestamp"), before.get("latest_history_timestamp")]
    after_range = [after.get("earliest_history_timestamp"), after.get("latest_history_timestamp")]
    if evidence.get("history_range_before") != before_range or evidence.get("history_range_after") != after_range:
        raise ValueError("environment history-range substitution")
    journals = (package_dir / "terminal-journal.log").read_text(encoding="utf-8-sig") + "\n" + (package_dir / "tester-journal.log").read_text(encoding="utf-8-sig")
    if evidence.get("raw_journal") != journals: raise ValueError("raw journal substitution")
    recomputed = evaluate_environmental_acceptance(evidence)
    if environmental.get("verdict") != recomputed or not recomputed["accepted"]: raise ValueError("environmental rejection")
    reconciliation = reconcile_rows(_parse_csv(package_dir / CSV))
    value = {"schema_version": "nora.ten_strategy_genuine_ingestion_v2", "run_identifier": execution.get("run_identifier"),
             "execution_packet_identity": execution_packet["execution_packet_identity"],
             "atomic_package_identity": sha(manifest), "environmental_verdict": recomputed,
             "reconciliation_identity": reconciliation["reconciliation_identity"], "classification": "PASS_EXACT"}
    return identified(value, "ingestion_identity")
