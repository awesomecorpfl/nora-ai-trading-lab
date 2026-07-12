"""Repository-owned compile-only orchestration for the Phase 2I canary."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

COMPILE_CONTRACT_VERSION = "nora_mql5_condition_compile_v1"
COMPILE_IDENTITY_DOMAIN = "nora.mt5.condition_compile_contract_v1.semantic.v1"
HOST_ALIAS = "nora-win10"
REMOTE_TARGET = "Gasper@127.0.0.1"
SSH_BASE = ("ssh", "-F", "/dev/null", "-i", str(Path.home() / ".ssh/nora_win10"), "-p", "2222", "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes")
SCP_BASE = ("scp", "-F", "/dev/null", "-i", str(Path.home() / ".ssh/nora_win10"), "-P", "2222", "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes")
REMOTE_ROOT = "NoraPhase2I"
RUNTIME_FILENAME = "NoraPhase2RuntimeV1.mqh"
CONDITION_FILENAME = "NoraPhase2ConditionV1.mqh"
SCRIPT_FILENAME = "NoraPhase2ConditionFixtureV1.mq5"
EX5_FILENAME = "NoraPhase2ConditionFixtureV1.ex5"
LOG_FILENAME = "compile.log"
REMOTE_RESULT_FILENAME = "compile.json"
RUNTIME_IDENTITY = "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d"
RUNTIME_SOURCE_SHA256 = "97de0194d7715b32ce104a9889d1a4af46cff6d0759d637f21e41025a98ee043"
CONDITION_IDENTITY = "1fa3d6613348a2fa532c4393e2a95795546c9cc5e2c86d010ee30fa9fe9632af"
CONDITION_SOURCE_SHA256 = "1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4"
FIXTURE_IDENTITY = "d283a5a37e64f426f39f813d1f2f68fa64e4c92cbd61b2cdbd59b9f1eac1f858"
FIXTURE_SOURCE_SHA256 = "b3b98996545d1277d4b2fa51db7c14c943ad733c018717110dab45e05f0022a7"
CANARY_MANIFEST_FILENAME = "compile_manifest.json"
EXECUTION_CONTRACT_VERSION = "nora_mt5_condition_execution_v1"
EXECUTION_IDENTITY_DOMAIN = "nora.mt5.condition_execution_v1.semantic.v1"
SEMANTIC_RESULT_IDENTITY_DOMAIN = "nora.mt5.condition_semantic_result_v1.semantic.v1"
EXECUTION_LOG_FILENAME = "execution.log"
EXECUTION_MANIFEST_FILENAME = "execution_manifest.json"
RESULT_FILENAME = "nora_phase2_condition_fixture_v1.csv"
CSV_SCHEMA = ["record_type", "row_index", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]
EXPECTED_NULLABLE_VECTOR = ["null", "null", "false", "true", "true", "true", "true", "true", "true", "true", "true", "true"]
EXPECTED_TRIGGER_VECTOR = [False, False, False, True, True, True, True, True, True, True, True, True]
TERMINAL_PRODUCT = "MetaTrader 5"
TERMINAL_VERSION = "5.0.0.5836"
EXECUTION_TIMEOUT_SECONDS = 60
BROKER_NATIVE_SYMBOL = "GDAXI"
CANARY_PROFILE = "NoraPhase2ConditionCanaryV1"
TESTER_SOURCE = "NoraPhase2ConditionTesterCanaryV1.mq5"
TESTER_EX5 = "NoraPhase2ConditionTesterCanaryV1.ex5"
TESTER_MANIFEST = "NoraPhase2ConditionTesterCanaryV1.manifest.json"
TESTER_RESULT = "nora_phase2_condition_tester_v1.csv"
TESTER_COMPILE_DOMAIN = "nora.mt5.condition_tester_compile_v1.semantic.v1"
TESTER_EXECUTION_DOMAIN = "nora.mt5.condition_tester_execution_v1.semantic.v1"


class CompileError(RuntimeError):
    """Deterministic compile-control failure."""


class ExecutionError(RuntimeError):
    """Deterministic execution/reconciliation failure."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _part(digest: "hashlib._Hash", value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def _normalized_log_sha256(content: bytes) -> str:
    try:
        text = content.decode("utf-16") if b"\x00" in content[:256] else content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("utf-8", errors="replace")
    text = re.sub(r"C:\\Users\\Gasper\\NoraPhase2I\\compile-[^\\]+\\source\\", "<remote-source>/", text)
    text = re.sub(r"Result:\s*(\d+\s+errors?,\s+\d+\s+warnings?)(?:,\s*[^\r\n]*)?", r"Result: \1", text)
    text = re.sub(r"\s+", " ", text)
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip()) + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _verify_manifest(path: Path, expected: dict[str, str], identity_key: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompileError(f"manifest unreadable or malformed: {path.name}") from error
    if not isinstance(value, dict):
        raise CompileError(f"manifest must be an object: {path.name}")
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise CompileError(f"frozen contract mismatch for {identity_key}: {key}")
    return value


def _verify_sources(runtime: Path, condition: Path, script: Path) -> tuple[dict, dict]:
    if runtime.name != RUNTIME_FILENAME or condition.name != CONDITION_FILENAME or script.name != SCRIPT_FILENAME:
        raise CompileError("source filenames do not match the frozen include contract")
    for path in (runtime, condition, script):
        if not path.is_file():
            raise CompileError(f"source file absent: {path.name}")
    runtime_manifest = _verify_manifest(runtime.parent / "NoraPhase2RuntimeV1.manifest.json", {"runtime_identity": RUNTIME_IDENTITY, "source_sha256": RUNTIME_SOURCE_SHA256}, "runtime")
    condition_manifest = _verify_manifest(condition.parent / "NoraPhase2ConditionV1.manifest.json", {"runtime_identity": RUNTIME_IDENTITY, "translation_identity": CONDITION_IDENTITY, "source_sha256": CONDITION_SOURCE_SHA256, "canonical_ast_identity": "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664"}, "condition")
    fixture_manifest = _verify_manifest(script.parent / "NoraPhase2ConditionFixtureV1.manifest.json", {"runtime_identity": RUNTIME_IDENTITY, "condition_translation_identity": CONDITION_IDENTITY, "fixture_identity": FIXTURE_IDENTITY, "source_sha256": FIXTURE_SOURCE_SHA256, "canonical_ast_identity": "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664"}, "fixture")
    expected_hashes = ((runtime, RUNTIME_SOURCE_SHA256), (condition, CONDITION_SOURCE_SHA256), (script, FIXTURE_SOURCE_SHA256))
    for path, expected_hash in expected_hashes:
        actual = _sha256(path)
        if actual != expected_hash:
            raise CompileError(f"frozen source hash mismatch: {path.name}")
    return condition_manifest, fixture_manifest


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise CompileError(detail)
    return result


def _ssh(command: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run([*SSH_BASE, REMOTE_TARGET, command], check=check)


def _scp(sources: list[str], destination: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run([*SCP_BASE, *sources, destination], check=check)


def _atomic_write(path: Path, content: bytes) -> None:
    temporary = path.with_name("." + path.name + ".partial")
    if temporary.exists() or path.exists():
        raise CompileError(f"local output target already exists: {path.name}")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise CompileError(f"atomic local publication failed: {path.name}") from error


def _atomic_execution_write(path: Path, content: bytes) -> None:
    temporary = path.with_name("." + path.name + ".partial")
    if temporary.exists() or path.exists():
        raise ExecutionError(f"local output target already exists: {path.name}")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise ExecutionError(f"atomic local publication failed: {path.name}") from error


def _compile_identity(compiler_path: str, compiler_version: str, exit_code: int, errors: int, warnings: int, ex5_filename: str, source_hashes: list[str], normalized_log_sha256: str) -> str:
    digest = hashlib.sha256()
    for value in [COMPILE_IDENTITY_DOMAIN, COMPILE_CONTRACT_VERSION, RUNTIME_IDENTITY, CONDITION_IDENTITY, FIXTURE_IDENTITY, *source_hashes, compiler_path, compiler_version, str(exit_code), str(errors), str(warnings), ex5_filename, normalized_log_sha256]:
        _part(digest, value.encode("utf-8"))
    return digest.hexdigest()


def compile_condition_canary(runtime: str | os.PathLike[str], condition: str | os.PathLike[str], script: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    runtime_path, condition_path, script_path = Path(runtime), Path(condition), Path(script)
    condition_manifest, fixture_manifest = _verify_sources(runtime_path, condition_path, script_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name in (EX5_FILENAME, LOG_FILENAME, CANARY_MANIFEST_FILENAME):
        if (output / name).exists():
            raise CompileError(f"local output target already exists: {name}")
    run_id = "compile-" + uuid.uuid4().hex
    local_failure_log: bytes | None = None
    with tempfile.TemporaryDirectory(prefix="phase2i-remote-") as incoming:
        incoming_path = Path(incoming)
        ps_path = Path(__file__).resolve().parents[2] / "phase-0a-h/windows/compile-condition-canary.ps1"
        for source in (runtime_path, condition_path, script_path):
            target = incoming_path / source.name
            target.write_bytes(source.read_bytes())
        ps_target = incoming_path / ps_path.name
        ps_target.write_bytes(ps_path.read_bytes())
        remote_incoming = f"$env:USERPROFILE\\{REMOTE_ROOT}\\incoming\\{run_id}"
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path {remote_incoming} | Out-Null"')
        _scp([str(incoming_path / name) for name in (RUNTIME_FILENAME, CONDITION_FILENAME, SCRIPT_FILENAME, ps_path.name)], f"{REMOTE_TARGET}:{REMOTE_ROOT}/incoming/{run_id}/")
        remote_ps = f"C:\\Users\\Gasper\\{REMOTE_ROOT}\\incoming\\{run_id}\\{ps_path.name}"
        remote_root = f"C:\\Users\\Gasper\\{REMOTE_ROOT}\\{run_id}"
        result = _ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{remote_ps}" -IncomingRoot "C:\\Users\\Gasper\\{REMOTE_ROOT}\\incoming\\{run_id}" -RunId "{run_id}"', check=False)
        local_result_path = incoming_path / REMOTE_RESULT_FILENAME
        local_log_path = incoming_path / LOG_FILENAME
        local_ex5_path = incoming_path / EX5_FILENAME
        for remote_name, local_path in ((REMOTE_RESULT_FILENAME, local_result_path), (LOG_FILENAME, local_log_path), (EX5_FILENAME, local_ex5_path)):
            _scp([f"{REMOTE_TARGET}:{REMOTE_ROOT}/{run_id}/{remote_name}"], str(local_path), check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\{REMOTE_ROOT}\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\{REMOTE_ROOT}\\incoming\\{run_id}\'"', check=False)
        if local_log_path.is_file():
            local_failure_log = local_log_path.read_bytes()
        if not local_result_path.is_file():
            raise CompileError("remote compile result was not retrieved")
        try:
            remote_result = json.loads(local_result_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            raise CompileError("remote compile result is malformed") from error
        if result.returncode != 0 or remote_result.get("status") != "compiled":
            if local_failure_log is not None:
                _atomic_write(output / LOG_FILENAME, local_failure_log)
            raise CompileError(f"compiler failed: exit={remote_result.get('compiler_exit_code')} errors={remote_result.get('error_count')} warnings={remote_result.get('warning_count')}")
        if not local_log_path.is_file() or not local_ex5_path.is_file() or local_ex5_path.stat().st_size == 0:
            raise CompileError("compile acceptance requires a non-empty ex5 and compiler log")
        log_bytes = local_log_path.read_bytes(); ex5_bytes = local_ex5_path.read_bytes()
        compiler_path = str(remote_result.get("compiler_path", "")); compiler_version = str(remote_result.get("compiler_version", "")); exit_code = int(remote_result.get("compiler_exit_code", -1)); errors = int(remote_result.get("error_count", -1)); warnings = int(remote_result.get("warning_count", -1))
        if not compiler_path or not compiler_version or errors != 0 or warnings != 0:
            raise CompileError("compile acceptance requires observed compiler identity and zero errors/warnings")
        ex5_sha = hashlib.sha256(ex5_bytes).hexdigest(); log_sha = hashlib.sha256(log_bytes).hexdigest(); normalized_log_sha = _normalized_log_sha256(log_bytes); source_hashes = [RUNTIME_SOURCE_SHA256, CONDITION_SOURCE_SHA256, FIXTURE_SOURCE_SHA256]
        contract_identity = _compile_identity(compiler_path, compiler_version, exit_code, errors, warnings, EX5_FILENAME, source_hashes, normalized_log_sha)
        manifest = {"compile_contract_version": COMPILE_CONTRACT_VERSION, "host_alias": HOST_ALIAS, "compiler_path": compiler_path, "compiler_version": compiler_version, "runtime_identity": RUNTIME_IDENTITY, "condition_translation_identity": CONDITION_IDENTITY, "fixture_identity": FIXTURE_IDENTITY, "runtime_source_sha256": RUNTIME_SOURCE_SHA256, "condition_source_sha256": CONDITION_SOURCE_SHA256, "fixture_source_sha256": FIXTURE_SOURCE_SHA256, "compiler_exit_code": exit_code, "error_count": errors, "warning_count": warnings, "log_sha256": log_sha, "normalized_log_sha256": normalized_log_sha, "ex5_filename": EX5_FILENAME, "ex5_sha256": ex5_sha, "ex5_size_bytes": len(ex5_bytes), "compile_contract_identity": contract_identity, "status": "compiled"}
        _atomic_write(output / EX5_FILENAME, ex5_bytes); _atomic_write(output / LOG_FILENAME, log_bytes); _atomic_write(output / CANARY_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
        return {"ok": True, **manifest, "output_dir": str(output)}


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutionError(f"{label} manifest is unreadable or malformed") from error
    if not isinstance(value, dict):
        raise ExecutionError(f"{label} manifest must be an object")
    return value


def _verify_execution_contract(compile_manifest_path: Path, ex5_path: Path, fixture_manifest_path: Path) -> dict:
    compile_manifest = _read_json(compile_manifest_path, "compile")
    expected_compile = {
        "compile_contract_identity": "a089a280eeebe82be78660410391323887cade8d36c0c26c2173e8ab4076558d",
        "compiler_version": TERMINAL_VERSION,
        "runtime_identity": RUNTIME_IDENTITY,
        "condition_translation_identity": CONDITION_IDENTITY,
        "fixture_identity": FIXTURE_IDENTITY,
        "runtime_source_sha256": RUNTIME_SOURCE_SHA256,
        "condition_source_sha256": CONDITION_SOURCE_SHA256,
        "fixture_source_sha256": FIXTURE_SOURCE_SHA256,
        "compiler_exit_code": 1,
        "error_count": 0,
        "warning_count": 0,
        "ex5_filename": EX5_FILENAME,
        "status": "compiled",
    }
    for key, expected in expected_compile.items():
        if compile_manifest.get(key) != expected:
            raise ExecutionError(f"frozen compile contract mismatch: {key}")
    if ex5_path.name != EX5_FILENAME or not ex5_path.is_file() or ex5_path.stat().st_size == 0:
        raise ExecutionError("compiled ex5 is absent or empty")
    ex5_sha = _sha256(ex5_path)
    if compile_manifest.get("ex5_sha256") != ex5_sha:
        raise ExecutionError("compiled ex5 hash does not match compile manifest")
    fixture = _read_json(fixture_manifest_path, "fixture")
    expected_fixture = {
        "fixture_identity": FIXTURE_IDENTITY,
        "runtime_identity": RUNTIME_IDENTITY,
        "condition_translation_identity": CONDITION_IDENTITY,
        "canonical_ast_identity": "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664",
        "source_sha256": FIXTURE_SOURCE_SHA256,
        "row_count": 12,
        "result_filename": RESULT_FILENAME,
        "expected_nullable_vector": EXPECTED_NULLABLE_VECTOR,
        "expected_trigger_vector": EXPECTED_TRIGGER_VECTOR,
    }
    for key, expected in expected_fixture.items():
        if fixture.get(key) != expected:
            raise ExecutionError(f"frozen fixture contract mismatch: {key}")
    if fixture_manifest_path.name != "NoraPhase2ConditionFixtureV1.manifest.json":
        raise ExecutionError("fixture manifest filename does not match frozen contract")
    return {"compile": compile_manifest, "fixture": fixture, "ex5_sha256": ex5_sha}


def _canonical_nullable(value: str, field: str) -> str:
    if value not in {"null", "false", "true"}:
        raise ExecutionError(f"invalid nullable token in {field}")
    return value


def _canonical_bool(value: str, field: str) -> bool:
    if value not in {"false", "true"}:
        raise ExecutionError(f"invalid Boolean token in {field}")
    return value == "true"


def reconcile_condition_csv(csv_path: str | os.PathLike[str], fixture_manifest: str | os.PathLike[str]) -> dict[str, object]:
    """Strictly reconcile one native canary CSV against the frozen fixture contract."""
    fixture = _read_json(Path(fixture_manifest), "fixture")
    if fixture.get("row_count") != 12 or fixture.get("expected_nullable_vector") != EXPECTED_NULLABLE_VECTOR or fixture.get("expected_trigger_vector") != EXPECTED_TRIGGER_VECTOR:
        raise ExecutionError("fixture expectations do not match frozen vectors")
    try:
        text = Path(csv_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise ExecutionError("result CSV is unreadable or not UTF-8") from error
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as error:
        raise ExecutionError("result CSV is empty") from error
    if header != CSV_SCHEMA:
        raise ExecutionError("result CSV header does not match frozen schema")
    records = list(reader)
    if len(records) != 13:
        raise ExecutionError("result CSV must contain exactly 12 rows and one summary")
    rows: list[dict[str, object]] = []
    for expected_index, values in enumerate(records[:12]):
        if len(values) != len(CSV_SCHEMA) or values[0] != "row":
            raise ExecutionError(f"malformed row record at index {expected_index}")
        if values[1] != str(expected_index):
            raise ExecutionError("row indices must be exactly 0..11 in order")
        actual_nullable = _canonical_nullable(values[2], "actual_nullable")
        expected_nullable = _canonical_nullable(values[3], "expected_nullable")
        actual_trigger = _canonical_bool(values[4], "actual_trigger")
        expected_trigger = _canonical_bool(values[5], "expected_trigger")
        row_pass = _canonical_bool(values[6], "row_pass")
        if values[7:] != ["", "", "", ""]:
            raise ExecutionError("row record contains unexpected summary fields")
        if expected_nullable != EXPECTED_NULLABLE_VECTOR[expected_index] or expected_trigger != EXPECTED_TRIGGER_VECTOR[expected_index]:
            raise ExecutionError("row expected value disagrees with frozen fixture vector")
        if actual_nullable != expected_nullable or actual_trigger != expected_trigger or not row_pass:
            raise ExecutionError(f"row {expected_index} failed nullable-condition reconciliation")
        rows.append({"row_index": expected_index, "actual_nullable": actual_nullable, "expected_nullable": expected_nullable, "actual_trigger": actual_trigger, "expected_trigger": expected_trigger, "row_pass": row_pass})
    summary = records[12]
    if len(summary) != len(CSV_SCHEMA) or summary[0] != "summary" or summary[1] != "-1":
        raise ExecutionError("result CSV summary record is malformed")
    if summary[2:6] != ["", "", "", ""]:
        raise ExecutionError("summary contains unexpected row value fields")
    overall_pass = _canonical_bool(summary[6], "overall_pass")
    try:
        row_count, passed_rows, failed_rows = (int(summary[index]) for index in (7, 8, 9))
    except (TypeError, ValueError) as error:
        raise ExecutionError("summary counts must be integers") from error
    if summary[10] not in {"false", "true"}:
        raise ExecutionError("invalid summary overall_pass token")
    if row_count != 12 or passed_rows != 12 or failed_rows != 0 or not overall_pass or summary[10] != "true":
        raise ExecutionError("summary does not prove a 12-row pass")
    return {"rows": rows, "summary": {"row_count": row_count, "passed_rows": passed_rows, "failed_rows": failed_rows, "overall_pass": overall_pass}, "nullable_vector": [row["actual_nullable"] for row in rows], "trigger_vector": [row["actual_trigger"] for row in rows], "row_pass_vector": [row["row_pass"] for row in rows]}


def _identity(domain: str, values: list[str]) -> str:
    digest = hashlib.sha256()
    for value in [domain, *values]:
        _part(digest, value.encode("utf-8"))
    return digest.hexdigest()


def _verify_tester_fixture(path: Path) -> dict:
    value = _read_json(path, "tester fixture")
    expected = {"tester_fixture_version": "nora_mql5_condition_tester_canary_v1", "runtime_identity": RUNTIME_IDENTITY, "condition_translation_identity": CONDITION_IDENTITY, "evaluation_ast_identity": "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664", "source_evidence_fixture_identity": FIXTURE_IDENTITY, "row_count": 12, "result_filename": TESTER_RESULT, "source_filename": TESTER_SOURCE}
    for key, item in expected.items():
        if value.get(key) != item: raise CompileError(f"tester fixture contract mismatch: {key}")
    if _sha256(path.parent / TESTER_SOURCE) != value.get("source_sha256"): raise CompileError("tester fixture source hash mismatch")
    return value


def compile_tester_canary(runtime: str | os.PathLike[str], condition: str | os.PathLike[str], tester_source: str | os.PathLike[str], tester_manifest: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    runtime_path, condition_path, source_path = Path(runtime), Path(condition), Path(tester_source)
    _verify_sources(runtime_path, condition_path, Path(__file__).resolve().parents[2] / "tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.mq5")
    fixture = _verify_tester_fixture(Path(tester_manifest))
    if source_path.name != TESTER_SOURCE or _sha256(source_path) != fixture["source_sha256"]: raise CompileError("tester source does not match tester fixture manifest")
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    for name in (TESTER_EX5, LOG_FILENAME, CANARY_MANIFEST_FILENAME):
        if (output/name).exists(): raise CompileError(f"local output target already exists: {name}")
    run_id="tester-compile-"+uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="phase2j-tester-") as temp:
        temp=Path(temp); helper=Path(__file__).resolve().parents[2]/"phase-0a-h/windows/compile-condition-tester-canary.ps1"
        for source in (runtime_path,condition_path,source_path,helper): (temp/source.name).write_bytes(source.read_bytes())
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase2J\\incoming\\{run_id} | Out-Null"')
        _scp([str(temp/x) for x in (RUNTIME_FILENAME,CONDITION_FILENAME,TESTER_SOURCE,helper.name)],f"{REMOTE_TARGET}:NoraPhase2J/incoming/{run_id}/")
        result=_ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\Gasper\\NoraPhase2J\\incoming\\{run_id}\\{helper.name}" -IncomingRoot "C:\\Users\\Gasper\\NoraPhase2J\\incoming\\{run_id}" -RunId "{run_id}"',check=False)
        for name in ("compile.json",LOG_FILENAME,TESTER_EX5): _scp([f"{REMOTE_TARGET}:NoraPhase2J/{run_id}/{name}"],str(temp/name),check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2J\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2J\\incoming\\{run_id}\'"',check=False)
        remote=_read_json(temp/"compile.json","remote tester compile")
        if result.returncode or remote.get("status")!="compiled" or remote.get("error_count")!=0 or remote.get("warning_count")!=0: raise CompileError("tester compiler failed")
        ex5=temp/TESTER_EX5; log=temp/LOG_FILENAME
        if not ex5.is_file() or not log.is_file() or not ex5.stat().st_size: raise CompileError("tester compiler did not return ex5/log")
        ex5bytes=ex5.read_bytes(); logbytes=log.read_bytes(); exsha=hashlib.sha256(ex5bytes).hexdigest(); norm=_normalized_log_sha256(logbytes)
        identity=_identity(TESTER_COMPILE_DOMAIN,[fixture["tester_fixture_identity"],str(remote["compiler_version"]),exsha,norm])
        manifest={"tester_compile_contract_version":"nora_mql5_condition_tester_compile_v1","compiler_path":remote["compiler_path"],"compiler_version":remote["compiler_version"],"compiler_exit_code":remote["compiler_exit_code"],"error_count":0,"warning_count":0,"tester_fixture_identity":fixture["tester_fixture_identity"],"ex5_filename":TESTER_EX5,"ex5_sha256":exsha,"ex5_size_bytes":len(ex5bytes),"normalized_log_sha256":norm,"compile_contract_identity":identity,"status":"compiled"}
        _atomic_write(output/TESTER_EX5,ex5bytes);_atomic_write(output/LOG_FILENAME,logbytes);_atomic_write(output/CANARY_MANIFEST_FILENAME,(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode())
        return {"ok":True,**manifest,"output_dir":str(output)}


def execute_tester_canary(compile_manifest: str | os.PathLike[str], ex5: str | os.PathLike[str], tester_manifest: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    compile_value=_read_json(Path(compile_manifest),"tester compile"); fixture=_verify_tester_fixture(Path(tester_manifest)); ex5_path=Path(ex5)
    if compile_value.get("status")!="compiled" or compile_value.get("tester_fixture_identity")!=fixture["tester_fixture_identity"] or compile_value.get("ex5_sha256")!=_sha256(ex5_path): raise ExecutionError("tester compile/fixture contract mismatch")
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    for name in (TESTER_RESULT,"tester.log",EXECUTION_MANIFEST_FILENAME):
        if (output/name).exists(): raise ExecutionError(f"local output target already exists: {name}")
    run_id="tester-execute-"+uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="phase2j-tester-exec-") as temp:
        temp=Path(temp); helper=Path(__file__).resolve().parents[2]/"phase-0a-h/windows/execute-condition-tester-canary.ps1";(temp/TESTER_EX5).write_bytes(ex5_path.read_bytes());(temp/helper.name).write_bytes(helper.read_bytes())
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase2J\\incoming\\{run_id} | Out-Null"')
        _scp([str(temp/TESTER_EX5),str(temp/helper.name)],f"{REMOTE_TARGET}:NoraPhase2J/incoming/{run_id}/")
        result=_ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\Gasper\\NoraPhase2J\\incoming\\{run_id}\\{helper.name}" -IncomingRoot "C:\\Users\\Gasper\\NoraPhase2J\\incoming\\{run_id}" -RunId "{run_id}"',check=False)
        for name in ("execution.json","tester.log",TESTER_RESULT,"tester.htm"): _scp([f"{REMOTE_TARGET}:NoraPhase2J/{run_id}/{name}"],str(temp/name),check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2J\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2J\\incoming\\{run_id}\'"',check=False)
        remote=_read_json(temp/"execution.json","remote tester execution")
        if result.returncode or remote.get("status")!="completed" or not remote.get("result_fresh"):
            if (temp/"tester.log").is_file(): _atomic_execution_write(output/"tester.log",(temp/"tester.log").read_bytes())
            raise ExecutionError(f"tester execution failed: {remote.get('error','unknown')}")
        required=("tester_configuration_loaded","testing_agent_started","ea_loaded","ea_initialized","fixture_execution_started","result_csv_written","fixture_execution_completed","tester_completed","terminal_shutdown")
        missing=[x for x in required if remote.get("stages",{}).get(x) is not True]
        if missing: raise ExecutionError("tester launch evidence missing stages: "+",".join(missing))
        csv=temp/TESTER_RESULT
        reconciliation=reconcile_condition_csv(csv,Path(__file__).resolve().parents[2]/"tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.manifest.json")
        csvbytes=csv.read_bytes(); exsha=_sha256(ex5_path); semantic=json.dumps({"rows":reconciliation["rows"],"summary":reconciliation["summary"]},sort_keys=True,separators=(",",":")); nullable=json.dumps(reconciliation["nullable_vector"],separators=(",",":")); trigger=json.dumps(reconciliation["trigger_vector"],separators=(",",":")); rowpass=json.dumps(reconciliation["row_pass_vector"],separators=(",",":")); summary=json.dumps(reconciliation["summary"],sort_keys=True,separators=(",",":"))
        execution=_identity(TESTER_EXECUTION_DOMAIN,[fixture["tester_fixture_identity"],compile_value["compile_contract_identity"],exsha,TERMINAL_VERSION,semantic])
        semantic_id=_identity(SEMANTIC_RESULT_IDENTITY_DOMAIN,[FIXTURE_IDENTITY,fixture["tester_fixture_identity"],TERMINAL_PRODUCT,TERMINAL_VERSION,nullable,trigger,rowpass,summary])
        manifest={"status":"passed","terminal_path":remote["terminal_path"],"terminal_version":remote["terminal_version"],"tester_fixture_identity":fixture["tester_fixture_identity"],"compile_contract_identity":compile_value["compile_contract_identity"],"ex5_sha256":exsha,"result_csv_sha256":hashlib.sha256(csvbytes).hexdigest(),"nullable_vector":reconciliation["nullable_vector"],"trigger_vector":reconciliation["trigger_vector"],"row_pass_vector":reconciliation["row_pass_vector"],**reconciliation["summary"],"execution_identity":execution,"semantic_result_identity":semantic_id,"launch_stages":remote["stages"]}
        _atomic_execution_write(output/TESTER_RESULT,csvbytes);_atomic_execution_write(output/"tester.log",(temp/"tester.log").read_bytes());_atomic_execution_write(output/EXECUTION_MANIFEST_FILENAME,(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode())
        if (temp/"tester.htm").is_file(): _atomic_execution_write(output/"tester.htm",(temp/"tester.htm").read_bytes())
        return {"ok":True,**manifest,"output_dir":str(output)}


def _require_launch_evidence(remote: dict[str, object]) -> None:
    stages = remote.get("stages")
    if not isinstance(stages, dict):
        raise ExecutionError("native launch evidence is absent")
    required = ("terminal_started", "startup_configuration_loaded", "chart_opened", "script_loaded", "script_started", "result_csv_created", "script_completed", "terminal_shutdown")
    missing = [name for name in required if stages.get(name) is not True]
    if missing:
        raise ExecutionError("native launch evidence missing stages: " + ",".join(missing))


def execute_condition_canary(compile_manifest: str | os.PathLike[str], ex5: str | os.PathLike[str], fixture_manifest: str | os.PathLike[str], output_dir: str | os.PathLike[str], *, symbol: str = BROKER_NATIVE_SYMBOL, profile: str = CANARY_PROFILE) -> dict[str, object]:
    compile_path, ex5_path, fixture_path = Path(compile_manifest), Path(ex5), Path(fixture_manifest)
    contracts = _verify_execution_contract(compile_path, ex5_path, fixture_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name in (RESULT_FILENAME, EXECUTION_LOG_FILENAME, EXECUTION_MANIFEST_FILENAME):
        if (output / name).exists():
            raise ExecutionError(f"local output target already exists: {name}")
    run_id = "execute-" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="phase2j-remote-") as incoming:
        incoming_path = Path(incoming)
        helper = Path(__file__).resolve().parents[2] / "phase-0a-h/windows/execute-condition-canary.ps1"
        (incoming_path / EX5_FILENAME).write_bytes(ex5_path.read_bytes())
        (incoming_path / helper.name).write_bytes(helper.read_bytes())
        remote_incoming = f"$env:USERPROFILE\\NoraPhase2J\\incoming\\{run_id}"
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path {remote_incoming} | Out-Null"')
        _scp([str(incoming_path / EX5_FILENAME), str(incoming_path / helper.name)], f"{REMOTE_TARGET}:NoraPhase2J/incoming/{run_id}/")
        remote_ps = f"C:\\Users\\Gasper\\NoraPhase2J\\incoming\\{run_id}\\{helper.name}"
        result = _ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{remote_ps}" -IncomingRoot "C:\\Users\\Gasper\\NoraPhase2J\\incoming\\{run_id}" -RunId "{run_id}" -RequestedSymbol "{symbol}" -ProfileName "{profile}" -TimeoutSeconds {EXECUTION_TIMEOUT_SECONDS}', check=False)
        local_result = incoming_path / "execution.json";local_log = incoming_path / EXECUTION_LOG_FILENAME;local_csv = incoming_path / RESULT_FILENAME;local_journal = incoming_path / "terminal-journal.log"
        for remote_name, local_path in (("execution.json", local_result), (EXECUTION_LOG_FILENAME, local_log), (RESULT_FILENAME, local_csv), ("terminal-journal.log", local_journal)):
            _scp([f"{REMOTE_TARGET}:NoraPhase2J/{run_id}/{remote_name}"], str(local_path), check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2J\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2J\\incoming\\{run_id}\'"', check=False)
        if not local_result.is_file():
            raise ExecutionError("remote execution result was not retrieved")
        try:
            remote = json.loads(local_result.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            raise ExecutionError("remote execution result is malformed") from error
        if result.returncode != 0 or remote.get("status") != "completed" or remote.get("terminal_version") != TERMINAL_VERSION or remote.get("result_filename") != RESULT_FILENAME or not remote.get("result_fresh"):
            if local_log.is_file():
                _atomic_execution_write(output / EXECUTION_LOG_FILENAME, local_log.read_bytes())
            if local_journal.is_file():
                _atomic_execution_write(output / "terminal-journal.log", local_journal.read_bytes())
            raise ExecutionError(f"native execution failed: {remote.get('error', remote.get('status', 'unknown'))}")
        if not local_csv.is_file() or local_csv.stat().st_size == 0 or not local_log.is_file():
            raise ExecutionError("fresh result CSV or execution log was not retrieved")
        _require_launch_evidence(remote)
        try:
            reconciliation = reconcile_condition_csv(local_csv, fixture_path)
        except ExecutionError:
            _atomic_execution_write(output / RESULT_FILENAME, local_csv.read_bytes())
            _atomic_execution_write(output / EXECUTION_LOG_FILENAME, local_log.read_bytes())
            if local_journal.is_file():
                _atomic_execution_write(output / "terminal-journal.log", local_journal.read_bytes())
            raise
        csv_bytes = local_csv.read_bytes();log_bytes = local_log.read_bytes();result_sha = hashlib.sha256(csv_bytes).hexdigest();ex5_sha = contracts["ex5_sha256"]
        semantic_content = json.dumps({"schema": CSV_SCHEMA, "rows": reconciliation["rows"], "summary": reconciliation["summary"]}, sort_keys=True, separators=(",", ":"))
        nullable_json = json.dumps(reconciliation["nullable_vector"], separators=(",", ":"));trigger_json = json.dumps(reconciliation["trigger_vector"], separators=(",", ":"));row_pass_json = json.dumps(reconciliation["row_pass_vector"], separators=(",", ":"));summary_json = json.dumps(reconciliation["summary"], sort_keys=True, separators=(",", ":"))
        terminal_version = str(remote["terminal_version"]);terminal_path = str(remote["terminal_path"])
        execution_identity = _identity(EXECUTION_IDENTITY_DOMAIN, [EXECUTION_CONTRACT_VERSION, RUNTIME_IDENTITY, CONDITION_IDENTITY, FIXTURE_IDENTITY, contracts["compile"]["compile_contract_identity"], TERMINAL_PRODUCT, terminal_version, ex5_sha, json.dumps(CSV_SCHEMA, separators=(",", ":")), nullable_json, trigger_json, row_pass_json, summary_json, semantic_content])
        semantic_identity = _identity(SEMANTIC_RESULT_IDENTITY_DOMAIN, [FIXTURE_IDENTITY, TERMINAL_PRODUCT, terminal_version, nullable_json, trigger_json, row_pass_json, summary_json, semantic_content])
        manifest = {"execution_contract_version": EXECUTION_CONTRACT_VERSION, "host_alias": HOST_ALIAS, "terminal_path": terminal_path, "terminal_version": terminal_version, "terminal_process_id": remote.get("terminal_process_id"), "profile_name": remote.get("profile_name", profile), "requested_symbol": remote.get("requested_symbol", symbol), "resolved_broker_symbol": remote.get("resolved_broker_symbol", symbol), "period": remote.get("period", "M1"), "script_name": remote.get("script_name", "NoraPhase2ConditionFixtureV1"), "script_load_observed": remote.get("stages", {}).get("script_loaded"), "fresh_csv_observed": remote.get("stages", {}).get("result_csv_created"), "launch_stages": remote.get("stages"), "compiler_version": TERMINAL_VERSION, "compile_contract_identity": contracts["compile"]["compile_contract_identity"], "fixture_identity": FIXTURE_IDENTITY, "ex5_sha256": ex5_sha, "result_filename": RESULT_FILENAME, "result_csv_sha256": result_sha, "row_count": reconciliation["summary"]["row_count"], "passed_rows": reconciliation["summary"]["passed_rows"], "failed_rows": reconciliation["summary"]["failed_rows"], "overall_pass": reconciliation["summary"]["overall_pass"], "nullable_vector": reconciliation["nullable_vector"], "trigger_vector": reconciliation["trigger_vector"], "row_pass_vector": reconciliation["row_pass_vector"], "execution_identity": execution_identity, "semantic_result_identity": semantic_identity, "status": "passed"}
        _atomic_execution_write(output / RESULT_FILENAME, csv_bytes);_atomic_execution_write(output / EXECUTION_LOG_FILENAME, log_bytes);_atomic_execution_write(output / EXECUTION_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
        return {"ok": True, **manifest, "output_dir": str(output)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lab.mt5")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile-condition-canary")
    compile_parser.add_argument("--runtime", required=True)
    compile_parser.add_argument("--condition", required=True)
    compile_parser.add_argument("--script", required=True)
    compile_parser.add_argument("--output-dir", required=True)
    tester_compile_parser = sub.add_parser("compile-condition-tester-canary")
    tester_compile_parser.add_argument("--runtime", required=True);tester_compile_parser.add_argument("--condition", required=True);tester_compile_parser.add_argument("--tester-source", required=True);tester_compile_parser.add_argument("--tester-manifest", required=True);tester_compile_parser.add_argument("--output-dir", required=True)
    execute_parser = sub.add_parser("execute-condition-canary")
    execute_parser.add_argument("--compile-manifest", required=True)
    execute_parser.add_argument("--ex5", required=True)
    execute_parser.add_argument("--fixture-manifest", required=True)
    execute_parser.add_argument("--output-dir", required=True)
    execute_parser.add_argument("--symbol", default=BROKER_NATIVE_SYMBOL)
    execute_parser.add_argument("--profile", default=CANARY_PROFILE)
    tester_execute_parser = sub.add_parser("execute-condition-tester-canary")
    tester_execute_parser.add_argument("--compile-manifest", required=True);tester_execute_parser.add_argument("--ex5", required=True);tester_execute_parser.add_argument("--tester-manifest", required=True);tester_execute_parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "compile-condition-canary":
            result = compile_condition_canary(args.runtime, args.condition, args.script, args.output_dir)
        elif args.command == "compile-condition-tester-canary":
            result = compile_tester_canary(args.runtime,args.condition,args.tester_source,args.tester_manifest,args.output_dir)
        elif args.command == "execute-condition-canary":
            result = execute_condition_canary(args.compile_manifest, args.ex5, args.fixture_manifest, args.output_dir, symbol=args.symbol, profile=args.profile)
        else:
            result = execute_tester_canary(args.compile_manifest,args.ex5,args.tester_manifest,args.output_dir)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (CompileError, ExecutionError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


__all__ = ["CompileError", "ExecutionError", "compile_condition_canary", "compile_tester_canary", "execute_condition_canary", "execute_tester_canary", "reconcile_condition_csv", "main"]
