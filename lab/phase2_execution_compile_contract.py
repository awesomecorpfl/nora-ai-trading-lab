"""Acyclic execution-canary compile evidence contracts and atomic importer."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path, PurePosixPath

from lab.mql5gen.execution import PACKAGE, RUNTIME, TESTER, generate
from lab.phase2_execution import canon, sha
from lab.native_target import (raw_sha, identified, compiler_output_identity,
                               validate_dependency_graph)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests/fixtures/phase2_execution_rust_evidence.json"
COMPILER_SCRIPT = ROOT / "phase-0a-h/windows/compile-execution-tester-canary.ps1"
COMPILE_INPUT_VERSION = "nora.execution_compile_input_v1"
COMPILER_OUTPUT_VERSION = "nora.execution_compiler_output_v1"
PACKET_VERSION = "nora.execution_native_packet_v1"
FINAL_BATCH_VERSION = "nora.execution_final_native_batch_v1"
POLICY = "nora.metaeditor_cli_success_v1"
EDITOR = r"C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe"
BUILD = "5.0.0.5836"


def file_sha(path: Path) -> str:
    return raw_sha(path.read_bytes())


def generated_sources() -> tuple[dict, dict[str, bytes]]:
    with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
        out = Path(temporary) / "generated"
        out.mkdir()
        package = generate(EVIDENCE, out)
        return package, {name: (out / name).read_bytes() for name in (RUNTIME, TESTER, PACKAGE)}


def build_compile_input() -> dict:
    package, files = generated_sources()
    script_sha = file_sha(COMPILER_SCRIPT)
    value = {
        "schema_version": COMPILE_INPUT_VERSION,
        "target_identifier": "execution",
        "runtime_identity": package["runtime_identity"],
        "runtime_sha256": raw_sha(files[RUNTIME]),
        "tester_identity": package["tester_identity"],
        "tester_sha256": raw_sha(files[TESTER]),
        "package_source_contract_identity": package["package_identity"],
        "compiler_script_identity": sha({"target": "execution", "sha256": script_sha}),
        "compiler_script_sha256": script_sha,
        "compiler_policy": POLICY,
        "expected_metaeditor_executable": EDITOR,
        "expected_metaeditor_build": BUILD,
        "runtime_source_path": f"generated/phase2_execution/{RUNTIME}",
        "tester_source_path": f"generated/phase2_execution/{TESTER}",
        "expected_ex5_path": "compile/NoraPhase2ExecutionTesterCanaryV1.ex5",
        "compile_command_template": f'{EDITOR} /compile:"{{tester_source}}" /log:"{{compiler_log}}"',
        "required_warning_count": 0,
        "required_error_count": 0,
    }
    return identified(value, "compile_input_identity")


def _safe_relative(value: str) -> bool:
    p = PurePosixPath(value)
    return bool(value) and not p.is_absolute() and ".." not in p.parts and "\\" not in value


def validate_compiler_output(record: dict, compile_input: dict, evidence_dir: Path) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != COMPILER_OUTPUT_VERSION: errors.append("schema")
    if record.get("target_identifier") != "execution": errors.append("target")
    if record.get("compile_input_identity") != compile_input["compile_input_identity"]: errors.append("compile input")
    if record.get("runtime_sha256") != compile_input["runtime_sha256"]: errors.append("runtime hash")
    if record.get("tester_sha256") != compile_input["tester_sha256"]: errors.append("tester hash")
    if record.get("metaeditor_executable") != EDITOR or record.get("observed_metaeditor_build") != BUILD: errors.append("compiler")
    if record.get("compiler_policy") != POLICY or record.get("policy_decision") not in ("accepted_zero", "accepted_metaeditor_5836_one"): errors.append("policy")
    if record.get("raw_process_exit") not in (0, 1) or record.get("normalized_result") != "success": errors.append("exit")
    if record.get("warning_count") != 0 or record.get("warnings") != []: errors.append("warnings")
    if record.get("error_count") != 0 or record.get("errors") != []: errors.append("errors")
    if record.get("completion_state") != "completed" or record.get("failure_reason") not in (None, ""): errors.append("completion")
    if record.get("freshness_proof") != {"preexisting_ex5_removed_or_isolated": True, "produced_after_invocation_start": True, "single_unambiguous_ex5": True}: errors.append("freshness")
    for kind in ("log", "ex5"):
        path = record.get(f"{kind}_path", "")
        if not _safe_relative(path): errors.append(f"{kind} path"); continue
        actual = evidence_dir / path
        if not actual.is_file(): errors.append(f"missing {kind}"); continue
        if actual.stat().st_size != record.get(f"{kind}_size") or file_sha(actual) != record.get(f"{kind}_sha256"): errors.append(f"{kind} binding")
    if record.get("compiler_output_identity") not in (None, compiler_output_identity(record)): errors.append("output identity")
    return errors


def validate_graph(nodes: dict) -> list[str]:
    return validate_dependency_graph(nodes)


def build_packet(record: dict, compile_input: dict, compiler_record_sha256: str) -> dict:
    package, _ = generated_sources(); evidence=json.loads(EVIDENCE.read_text())
    scripts={p.name:{"path":str(p.relative_to(ROOT)),"sha256":file_sha(p),"identity":sha({"path":str(p.relative_to(ROOT)),"sha256":file_sha(p)})} for p in (
        ROOT/"phase-0a-h/windows/execute-execution-tester-canary.ps1", ROOT/"phase-0a-h/windows/build-execution-returned-package.ps1")}
    value={"schema_version":PACKET_VERSION,"compile_input_identity":compile_input["compile_input_identity"],"compiler_output_identity":record["compiler_output_identity"],"compiler_output_record_sha256":compiler_record_sha256,"compiler_log_sha256":record["log_sha256"],"ex5_path":record["ex5_path"],"ex5_size":record["ex5_size"],"ex5_sha256":record["ex5_sha256"],"runtime_identity":package["runtime_identity"],"runtime_sha256":package["runtime_sha256"],"tester_identity":package["tester_identity"],"tester_sha256":package["tester_sha256"],"package_identity":package["package_identity"],"execution_plan_identity":evidence["execution_plan_identity"],"expected_vector_identity":package["expected_execution_vector_identity"],"csv_schema_identity":package["execution_csv_schema_identity"],"scenario_identities":{x["scenario_id"]:x["scenario_identity"] for x in evidence["scenarios"]},"execution_and_collection_scripts":scripts,"evidence_capture_contract_identity":sha({"version":"nora.phase2.execution_tester_evidence_v1","bounded_journal":True,"markers":True}),"host_context_matrix":["GDAXI/M1:A1","GDAXI/M1:A2","AUDCAD/M1:B1","AUDCAD/M1:B2"],"completion_marker":package["completion_marker"],"failure_marker":package["failure_marker"],"result_filename":package["result_filename"]}
    return identified(value,"execution_packet_identity")


def build_final_batch(packet: dict, record: dict, compile_input: dict, inventory: list[dict]) -> dict:
    value={"schema_version":FINAL_BATCH_VERSION,"dependency_graph":{"source":[],"compile_input":["source"],"compiler_output":["compile_input"],"execution_packet":["compiler_output"],"final_batch":["execution_packet"]},"compile_input_identity":compile_input["compile_input_identity"],"compiler_output_identity":record["compiler_output_identity"],"execution_packet_identity":packet["execution_packet_identity"],"ex5_sha256":record["ex5_sha256"],"compiler_log_sha256":record["log_sha256"],"frozen_execution_identities":{"runtime":packet["runtime_identity"],"tester":packet["tester_identity"],"package":packet["package_identity"],"plan":packet["execution_plan_identity"],"vectors":packet["expected_vector_identity"],"csv_schema":packet["csv_schema_identity"],"scenarios":packet["scenario_identities"]},"staged_files":inventory,"precompile_ready":True,"compile_evidence_pending":False,"compile_evidence_imported":True,"final_packet_ready":True,"native_execution_attempted":False,"native_parity_accepted":False,"grammar_admitted":False,"searchable":False,"complete_phase2_gate":False}
    if validate_graph(value["dependency_graph"]): raise ValueError("dependency graph")
    value["staged_inventory_identity"]=sha([{"path":x["path"],"role":x["role"]} for x in inventory]);return identified(value,"final_batch_identity")


def import_evidence(evidence_dir: Path, destination: Path, *, inject_failure: bool = False) -> dict:
    evidence_dir=Path(evidence_dir);destination=Path(destination)
    if destination.exists():raise ValueError("occupied destination")
    allowed={"compiler_record.json","compile.log","NoraPhase2ExecutionTesterCanaryV1.ex5","compile_evidence_manifest.json","inventory.json"}
    if {p.name for p in evidence_dir.iterdir()} != allowed:raise ValueError("unexpected or missing file")
    compile_input=build_compile_input();record=json.loads((evidence_dir/"compiler_record.json").read_text(encoding="utf-8-sig"))
    errors=validate_compiler_output(record,compile_input,evidence_dir)
    if errors:raise ValueError(", ".join(errors))
    record["compiler_output_identity"]=compiler_output_identity(record)
    manifest=json.loads((evidence_dir/"compile_evidence_manifest.json").read_text(encoding="utf-8-sig"))
    allowed_manifest={"schema_version":"nora.execution_compile_evidence_manifest_v1","target_identifier":"execution","compile_input_identity":compile_input["compile_input_identity"]}
    if manifest not in (allowed_manifest,{**allowed_manifest,"compiler_output_identity":record["compiler_output_identity"]}):raise ValueError("compile evidence manifest")
    declared=json.loads((evidence_dir/"inventory.json").read_text(encoding="utf-8-sig"))
    if len(declared)!=len({x.get("path") for x in declared}):raise ValueError("duplicate inventory")
    if {x.get("path") for x in declared}!={"compiler_record.json","compile.log","NoraPhase2ExecutionTesterCanaryV1.ex5","compile_evidence_manifest.json"}:raise ValueError("inventory allowlist")
    for item in declared:
        if not _safe_relative(item["path"]) or file_sha(evidence_dir/item["path"])!=item["sha256"]:raise ValueError("inventory")
    packet=build_packet(record,compile_input,file_sha(evidence_dir/"compiler_record.json"))
    inventory=[{"path":"compile/"+x["path"],"role":x["role"],"sha256":x["sha256"]} for x in declared]+[{"path":"execution_packet.json","role":"execution_packet","sha256":"generated"}]
    batch=build_final_batch(packet,record,compile_input,inventory)
    temporary=Path(tempfile.mkdtemp(prefix=".execution-compile-import-",dir=destination.parent))
    try:
        shutil.copytree(evidence_dir,temporary/"compile")
        (temporary/"compile_input.json").write_text(canon(compile_input)+"\n")
        (temporary/"execution_packet.json").write_text(canon(packet)+"\n")
        (temporary/"final_batch.json").write_text(canon(batch)+"\n")
        if inject_failure:raise RuntimeError("injected import interruption")
        temporary.replace(destination)
    except Exception:shutil.rmtree(temporary,ignore_errors=True);raise
    return {"compile_input_identity":compile_input["compile_input_identity"],"compiler_output_identity":record["compiler_output_identity"],"execution_packet_identity":packet["execution_packet_identity"],"final_batch_identity":batch["final_batch_identity"],"staged_inventory_identity":batch["staged_inventory_identity"]}


def main() -> int:
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("compile-input").add_argument("--output",required=True)
    imp=sub.add_parser("import");imp.add_argument("--evidence-dir",required=True);imp.add_argument("--destination",required=True)
    args=parser.parse_args()
    if args.command=="compile-input":Path(args.output).write_text(canon(build_compile_input())+"\n");return 0
    print(canon(import_evidence(Path(args.evidence_dir),Path(args.destination))));return 0

if __name__ == "__main__":raise SystemExit(main())
