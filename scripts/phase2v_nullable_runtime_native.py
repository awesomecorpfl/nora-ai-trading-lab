#!/usr/bin/env python3
"""Run and seal the dedicated Phase-2V exhaustive nullable-runtime tester."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "nora-win10"
REMOTE_ROOT = r"C:\Users\Gasper\NoraPhase2R"
PACKAGE = ROOT / "tests/fixtures/phase2v_nullable_runtime_native"
TESTER = PACKAGE / "tester"
RUNTIME = ROOT / "tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.mqh"
CONDITION = ROOT / "tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.mqh"
COMPILE_HELPER = ROOT / "phase-0a-h/windows/compile-condition-tester-durable.ps1"
EXECUTE_HELPER = ROOT / "phase-0a-h/windows/execute-condition-tester-durable.ps1"
# The accepted durable siblings are the launcher/evidence path. These temporary
# helper variants only bind the new tester source hash and requested symbol.
BASE_COMPILE = ROOT / "phase-0a-h/windows/compile-condition-tester-canary-durable.ps1"
BASE_EXECUTE = ROOT / "phase-0a-h/windows/execute-condition-tester-canary-durable.ps1"
REQUIRED_STAGES = ("tester_configuration_loaded", "testing_agent_started", "ea_loaded", "ea_initialized", "fixture_execution_started", "result_csv_written", "fixture_execution_completed", "tester_completed", "terminal_shutdown")
CONTEXTS = {"A1": "GDAXI", "A2": "GDAXI", "B1": "AUDCAD", "B2": "AUDCAD"}


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=ROOT, check=check, capture_output=True, text=True)


def ssh(command: str, *, check: bool = True) -> subprocess.CompletedProcess:
    return run(["ssh", "-o", "BatchMode=yes", REMOTE, command], check=check)


def scp(source: str, destination: str, *, check: bool = True) -> subprocess.CompletedProcess:
    return run(["scp", "-q", source, destination], check=check)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def win(path: str) -> str:
    return path.replace("\\", "/")


def compile_package(staging: Path) -> tuple[dict, Path]:
    tester_source = TESTER / "NoraPhase2ConditionTesterCanaryV1.mq5"
    tester_sha = sha(tester_source)
    helper = staging / BASE_COMPILE.name
    text = BASE_COMPILE.read_text(encoding="utf-8")
    replacements = {
        "'2d9dd772d35be45d3fce07da275f7fb22479e54d0d4cdc2cf20ff1440d6f5c1e'": repr(tester_sha),
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise RuntimeError(f"compile helper substitution guard failed for {old}")
        text = text.replace(old, new)
    helper.write_text(text, encoding="utf-8", newline="\n")
    run_id = "nullable-runtime-compile-" + uuid.uuid4().hex
    incoming = f"{REMOTE_ROOT}\\incoming\\{run_id}"
    ssh(f"powershell -NoProfile -Command \"New-Item -ItemType Directory -Force -Path '{incoming}' | Out-Null\"")
    for source in (RUNTIME, CONDITION, tester_source, helper):
        scp(str(source if source != helper else helper), f"{REMOTE}:{win(incoming)}/")
    compile_proc = ssh(f'powershell -NoProfile -ExecutionPolicy Bypass -File "{incoming}\\{helper.name}" -IncomingRoot "{incoming}" -RunId "{run_id}"', check=False)
    remote_root = f"{REMOTE_ROOT}\\{run_id}"
    out = staging / "compile"
    out.mkdir()
    for name in ("compile.json", "compile.log", "NoraPhase2ConditionTesterCanaryV1.ex5"):
        scp(f"{REMOTE}:{win(remote_root)}/{name}", str(out / name), check=False)
    ssh(f"powershell -NoProfile -Command \"Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '{remote_root}'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '{incoming}'\"", check=False)
    if not (out / "compile.json").is_file():
        raise RuntimeError(f"compile evidence missing; ssh_rc={compile_proc.returncode}; stdout={compile_proc.stdout}; stderr={compile_proc.stderr}")
    compile_value = json.loads((out / "compile.json").read_text(encoding="utf-8-sig"))
    if compile_value.get("status") != "compiled" or compile_value.get("error_count") != 0 or compile_value.get("warning_count") != 0:
        raise RuntimeError(f"compile rejected: {compile_value}")
    return compile_value, out / "NoraPhase2ConditionTesterCanaryV1.ex5"


def execute_context(staging: Path, ex5: Path, label: str, symbol: str) -> tuple[dict, Path]:
    helper = staging / f"execute-{label}.ps1"
    text = BASE_EXECUTE.read_text(encoding="utf-8")
    if symbol == "AUDCAD":
        if text.count("Symbol=GDAXI") != 1:
            raise RuntimeError("AUDCAD helper substitution guard failed")
        text = text.replace("Symbol=GDAXI", "Symbol=AUDCAD")
    helper.write_text(text, encoding="utf-8", newline="\n")
    run_id = f"nullable-runtime-{label.lower()}-" + uuid.uuid4().hex
    incoming = f"{REMOTE_ROOT}\\incoming\\{run_id}"
    ssh(f"powershell -NoProfile -Command \"New-Item -ItemType Directory -Force -Path '{incoming}' | Out-Null\"")
    scp(str(ex5), f"{REMOTE}:{win(incoming)}/NoraPhase2ConditionTesterCanaryV1.ex5")
    scp(str(helper), f"{REMOTE}:{win(incoming)}/{helper.name}")
    ssh(f'powershell -NoProfile -ExecutionPolicy Bypass -File "{incoming}\\{helper.name}" -IncomingRoot "{incoming}" -RunId "{run_id}"', check=False)
    remote_root = f"{REMOTE_ROOT}\\{run_id}"
    out = staging / label.lower()
    out.mkdir()
    names = ("execution.json", "tester.log", "tester-journal.log", "lifecycle.jsonl", "tester.ini", "nora_phase2_condition_tester_v1.csv")
    for name in names:
        scp(f"{REMOTE}:{win(remote_root)}/{name}", str(out / name), check=False)
    ssh(f"powershell -NoProfile -Command \"Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '{remote_root}'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '{incoming}'\"", check=False)
    execution = json.loads((out / "execution.json").read_text(encoding="utf-8-sig"))
    return execution, out


def reconcile(path: Path, cases: list[dict]) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    data = [row for row in rows if row["record_type"] == "row"]
    summary = next(row for row in rows if row["record_type"] == "summary")
    if len(data) != len(cases) or summary["overall_pass"].lower() != "true":
        raise RuntimeError("runtime CSV row count or overall pass is invalid")
    for index, row in enumerate(data):
        expected_nullable = cases[index]["left"] if cases[index]["operation"] == "trigger" else cases[index]["expected"]
        expected_trigger = (cases[index]["expected"] if cases[index]["operation"] == "trigger" else cases[index]["expected"] == "true")
        if row["actual_nullable"] != expected_nullable or row["actual_trigger"].lower() != str(expected_trigger).lower() or row["row_pass"].lower() != "true":
            raise RuntimeError(f"row {index} mismatch: {row}")
    return {"row_count": len(data), "passed_rows": int(summary["passed_rows"]), "failed_rows": int(summary["failed_rows"]), "overall_pass": True}


def _journal_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if "NORA_PHASE2V_RUNTIME" in text:
            return text
    return raw.decode("utf-8", errors="replace")


def main() -> int:
    index = PACKAGE / "native_evidence_manifest.json"
    if index.exists():
        raise SystemExit(f"refusing to overwrite sealed evidence: {index}")
    tester_manifest = json.loads((TESTER / "NoraPhase2ConditionTesterCanaryV1.manifest.json").read_text())
    cases = tester_manifest["cases"]
    with tempfile.TemporaryDirectory(prefix="phase2v-runtime-") as temp:
        staging = Path(temp)
        compile_value, ex5 = compile_package(staging)
        compile_dir = PACKAGE / "compile"
        compile_dir.mkdir(exist_ok=False)
        for name in ("compile.json", "compile.log", "NoraPhase2ConditionTesterCanaryV1.ex5"):
            shutil.copy2(staging / "compile" / name, compile_dir / name)
        runs = {}
        for label, symbol in CONTEXTS.items():
            execution, run_dir = execute_context(staging, ex5, label, symbol)
            target = PACKAGE / label.lower()
            target.mkdir(exist_ok=False)
            for name in ("execution.json", "tester.log", "tester-journal.log", "lifecycle.jsonl", "tester.ini", "nora_phase2_condition_tester_v1.csv"):
                source = run_dir / name
                if source.is_file():
                    shutil.copy2(source, target / name)
            reconciliation = reconcile(run_dir / "nora_phase2_condition_tester_v1.csv", cases)
            journal = _journal_text(run_dir / "tester-journal.log")
            if execution.get("status") != "completed" or execution.get("native_process_exit_status") != 0 or not execution.get("result_fresh"):
                raise RuntimeError(f"{label} lifecycle rejected: {execution}")
            if any(execution.get("stages", {}).get(stage) is not True for stage in REQUIRED_STAGES):
                raise RuntimeError(f"{label} missing lifecycle stage")
            if "NORA_PHASE2V_RUNTIME_PASS" not in journal or "NORA_PHASE2V_RUNTIME_FAIL" in journal:
                raise RuntimeError(f"{label} completion marker rejected")
            runs[label] = {"run_id": execution["run_id"], "symbol": f"{symbol}/M1", "exit_code": 0, "completion_marker": True, "failure_marker": False, "reconciliation": "PASS_EXACT", "evidence_path": f"tests/fixtures/phase2v_nullable_runtime_native/{label.lower()}/execution.json", "csv_sha256": sha(target / "nora_phase2_condition_tester_v1.csv"), "row_count": reconciliation["row_count"]}
    manifest = {"schema_version": "nora.phase2v.nullable_runtime_native_acceptance_v1", "scope": "frozen nullable runtime semantic fixture only", "native_parity": "PASS_EXACT", "runtime_semantic_native_coverage": True, "runtime_identity": tester_manifest["runtime_identity"], "runtime_source_sha256": tester_manifest["runtime_source_sha256"], "semantic_fixture_sha256": tester_manifest["semantic_fixture_sha256"], "tester_identity": tester_manifest["tester_identity"], "tester_source_sha256": tester_manifest["source_sha256"], "operations": tester_manifest["operations"], "case_count": tester_manifest["case_count"], "contexts": list(CONTEXTS), "compile": {"error_count": compile_value["error_count"], "warning_count": compile_value["warning_count"], "compiler_version": compile_value["compiler_version"], "ex5_sha256": sha(PACKAGE / "compile/NoraPhase2ConditionTesterCanaryV1.ex5"), "evidence_path": "tests/fixtures/phase2v_nullable_runtime_native/compile/compile.json"}, "runs": runs, "grammar_admitted": False, "searchable": False, "phase3_authorized": False, "complete_phase2_gate": False, "evidence_commit": "PENDING_COMMIT"}
    index.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "sealed", "manifest": str(index), "contexts": list(runs)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
