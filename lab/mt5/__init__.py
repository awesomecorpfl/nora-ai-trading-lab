"""Repository-owned compile-only orchestration for the Phase 2I canary."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from datetime import datetime, timezone
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

SERIES_RUNTIME_FILENAME = "NoraPhase2SeriesRuntimeV1.mqh"
SERIES_RUNTIME_MANIFEST = "NoraPhase2SeriesRuntimeV1.manifest.json"
SERIES_TESTER_SOURCE = "NoraPhase2SeriesTesterCanaryV1.mq5"
SERIES_TESTER_EX5 = "NoraPhase2SeriesTesterCanaryV1.ex5"
SERIES_TESTER_MANIFEST = "NoraPhase2SeriesTesterCanaryV1.manifest.json"
SERIES_TESTER_RESULT = "nora_phase2_series_tester_v1.csv"
SERIES_COMPILE_DOMAIN = "nora.mt5.series_tester_compile_v1.semantic.v1"
SERIES_EXECUTION_DOMAIN = "nora.mt5.series_tester_execution_v1.semantic.v1"
SERIES_SEMANTIC_RESULT_DOMAIN = "nora.mt5.series_semantic_result_v1.semantic.v1"
SERIES_CSV_SCHEMA = ["record_type", "row_index", "actual_sma", "expected_sma", "actual_cross_above", "expected_cross_above", "actual_cross_below", "expected_cross_below", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]
SERIES_EXPECTED_SMA = [None, None, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334]
SERIES_EXPECTED_ABOVE = [None, None, None, True, False, False, False, False, False, False, False, False]
SERIES_EXPECTED_BELOW = [None, None, None, True, False, False, False, False, False, False, False, False]
SERIES_EXPECTED_NULLABLE = ["null", "null", "false", "true", "true", "true", "true", "true", "true", "true", "true", "true"]
SERIES_EXPECTED_TRIGGER = [False, False, False, True, True, True, True, True, True, True, True, True]
SERIES_RUNTIME_IDENTITY = "4102f23095201f5c37e8a6737d32f22eb31713f4f0ec9cae68803e6d3efbce8e"
SERIES_RUNTIME_SOURCE_SHA256 = "6fbbe35045be59cdf571a623e38a213ca053be32fab153f858d461c1d4ac1b2d"
SERIES_TESTER_IDENTITY = "78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4"
SERIES_TESTER_SOURCE_SHA256 = "bc62801db8965d268e192d3dadb8ba7b11a7c5e3d5a432fbadd3f2241a4d2757"
SERIES_COMPILE_CONTRACT_VERSION = "nora.mql5.series_tester_compile_v1"
SERIES_EXECUTION_CONTRACT_VERSION = "nora.mt5.series_tester_execution_v1"
SERIES_SEMANTIC_RESULT_VERSION = "nora.mt5.series_semantic_result_v1"

SLOPE_RUNTIME_FILENAME = "NoraPhase2SlopeRuntimeV1.mqh"
SLOPE_RUNTIME_MANIFEST = "NoraPhase2SlopeRuntimeV1.manifest.json"
SLOPE_TESTER_SOURCE = "NoraPhase2SlopeTesterCanaryV1.mq5"
SLOPE_TESTER_EX5 = "NoraPhase2SlopeTesterCanaryV1.ex5"
SLOPE_TESTER_MANIFEST = "NoraPhase2SlopeTesterCanaryV1.manifest.json"
SLOPE_TESTER_RESULT = "nora_phase2_slope_tester_v1.csv"
SLOPE_COMPILE_DOMAIN = "nora.mt5.slope_tester_compile_v1.semantic.v1"
SLOPE_EXECUTION_DOMAIN = "nora.mt5.slope_tester_execution_v1.semantic.v1"
SLOPE_SEMANTIC_RESULT_DOMAIN = "nora.mt5.slope_semantic_result_v1.semantic.v1"
SLOPE_CSV_SCHEMA = ["record_type", "row_index", "actual_slope", "expected_slope", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]
SLOPE_EXPECTED_VECTOR = [None, None, None, 0.00033333333333351867, 0.00003333333333310762, 0.00036666666666684833, 0.00003333333333310762, 0.00036666666666684833, 0.00003333333333310762, 0.00036666666666684833, 0.00003333333333310762, 0.00036666666666684833]
SLOPE_NULL_POSITIONS = [0, 1, 2]
SLOPE_RUNTIME_IDENTITY = "cb9eee8e4c03d6c6d95c6ba384701187c93730f77fafe3a22a2f8902410c68ae"
SLOPE_RUNTIME_SOURCE_SHA256 = "a3b2dc447b59e6800dee7c875e9d25ea2353fc32b04c73391871623c08842c80"
SLOPE_TESTER_IDENTITY = "a25fe8a6b459499debdbc9d48c8d4dd498a9684bf67b196501ebed743b48b54d"
SLOPE_TESTER_SOURCE_SHA256 = "6d4f2e9f0a7e1dcd33004500dfea8deaad4c5a4e9804e57ef8377369f67a4f53"
SLOPE_INPUT_IDENTITY = "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383"
SLOPE_RUST_SLOPE_IDENTITY = "45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499"
SLOPE_COMPILE_CONTRACT_VERSION = "nora.mql5.slope_tester_compile_v1"
SLOPE_EXECUTION_CONTRACT_VERSION = "nora.mt5.slope_tester_execution_v1"
SLOPE_SEMANTIC_RESULT_VERSION = "nora.mt5.slope_semantic_result_v1"


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


def _canonical_numeric(value: str, field: str) -> str:
    if value == "null":
        return "null"
    try:
        float(value)
        return value
    except ValueError:
        raise ExecutionError(f"invalid numeric token in {field}")


def _numeric_match(actual: str, expected_value: object) -> bool:
    if expected_value is None:
        return actual == "null"
    if actual == "null":
        return False
    try:
        return abs(float(actual) - float(expected_value)) < 0.000000000000001
    except ValueError:
        return False


def _canonical_cross(value: str, field: str) -> str:
    if value not in {"null", "true", "false"}:
        raise ExecutionError(f"invalid cross token in {field}")
    return value


def reconcile_series_csv(csv_path: str | os.PathLike[str], tester_manifest: str | os.PathLike[str]) -> dict[str, object]:
    """Strictly reconcile one native series canary CSV against the frozen Phase-2K tester contract."""
    fixture = _read_json(Path(tester_manifest), "tester fixture")
    if fixture.get("csv_schema") != SERIES_CSV_SCHEMA:
        raise ExecutionError("tester expectations do not match frozen vectors")
    expected_sma = fixture.get("expected_sma_vector", [])
    expected_above = fixture.get("expected_cross_above_vector", [])
    expected_below = fixture.get("expected_cross_below_vector", [])
    expected_nullable = fixture.get("expected_nullable_vector", [])
    expected_trigger = fixture.get("expected_trigger_vector", [])
    if len(expected_sma) != 12 or len(expected_above) != 12 or len(expected_below) != 12 or len(expected_nullable) != 12 or len(expected_trigger) != 12:
        raise ExecutionError("tester expectations do not match frozen vectors")
    try:
        text = Path(csv_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise ExecutionError("result CSV is unreadable or not UTF-8") from error
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as error:
        raise ExecutionError("result CSV is empty") from error
    if header != SERIES_CSV_SCHEMA:
        raise ExecutionError("result CSV header does not match frozen schema")
    records = list(reader)
    if len(records) != 13:
        raise ExecutionError("result CSV must contain exactly 12 rows and one summary")
    rows: list[dict[str, object]] = []
    for expected_index, values in enumerate(records[:12]):
        if len(values) != len(SERIES_CSV_SCHEMA) or values[0] != "row":
            raise ExecutionError(f"malformed row record at index {expected_index}")
        if values[1] != str(expected_index):
            raise ExecutionError("row indices must be exactly 0..11 in order")
        actual_sma = _canonical_numeric(values[2], "actual_sma")
        expected_sma_val = _canonical_numeric(values[3], "expected_sma")
        actual_above = _canonical_cross(values[4], "actual_cross_above")
        expected_above_val = _canonical_cross(values[5], "expected_cross_above")
        actual_below = _canonical_cross(values[6], "actual_cross_below")
        expected_below_val = _canonical_cross(values[7], "expected_cross_below")
        actual_nullable = _canonical_nullable(values[8], "actual_nullable")
        expected_nullable_val = _canonical_nullable(values[9], "expected_nullable")
        actual_trigger = _canonical_bool(values[10], "actual_trigger")
        expected_trigger_val = _canonical_bool(values[11], "expected_trigger")
        row_pass = _canonical_bool(values[12], "row_pass")
        if values[13:] != ["", "", "", ""]:
            raise ExecutionError("row record contains unexpected summary fields")
        if not _numeric_match(expected_sma_val, expected_sma[expected_index]) or expected_above_val != (str(expected_above[expected_index]).lower() if expected_above[expected_index] is not None else "null") or expected_below_val != (str(expected_below[expected_index]).lower() if expected_below[expected_index] is not None else "null") or expected_nullable_val != expected_nullable[expected_index] or expected_trigger_val != expected_trigger[expected_index]:
            raise ExecutionError("row expected value disagrees with frozen fixture vector")
        if not _numeric_match(actual_sma, expected_sma[expected_index]) or actual_above != expected_above_val or actual_below != expected_below_val or actual_nullable != expected_nullable_val or actual_trigger != expected_trigger_val or not row_pass:
            raise ExecutionError(f"row {expected_index} failed series reconciliation")
        rows.append({"row_index": expected_index, "actual_sma": actual_sma, "expected_sma": expected_sma_val, "actual_cross_above": actual_above, "expected_cross_above": expected_above_val, "actual_cross_below": actual_below, "expected_cross_below": expected_below_val, "actual_nullable": actual_nullable, "expected_nullable": expected_nullable_val, "actual_trigger": actual_trigger, "expected_trigger": expected_trigger_val, "row_pass": row_pass})
    summary = records[12]
    if len(summary) != len(SERIES_CSV_SCHEMA) or summary[0] != "summary" or summary[1] != "-1":
        raise ExecutionError("result CSV summary record is malformed")
    if summary[2:12] != ["", "", "", "", "", "", "", "", "", ""]:
        raise ExecutionError("summary contains unexpected row value fields")
    overall_pass = _canonical_bool(summary[12], "overall_pass")
    try:
        row_count, passed_rows, failed_rows = (int(summary[index]) for index in (13, 14, 15))
    except (TypeError, ValueError) as error:
        raise ExecutionError("summary counts must be integers") from error
    if summary[16] not in {"false", "true"}:
        raise ExecutionError("invalid summary overall_pass token")
    if row_count != 12 or passed_rows != 12 or failed_rows != 0 or not overall_pass or summary[16] != "true":
        raise ExecutionError("summary does not prove a 12-row pass")
    return {"rows": rows, "summary": {"row_count": row_count, "passed_rows": passed_rows, "failed_rows": failed_rows, "overall_pass": overall_pass}, "sma_vector": [row["actual_sma"] for row in rows], "cross_above_vector": [row["actual_cross_above"] for row in rows], "cross_below_vector": [row["actual_cross_below"] for row in rows], "nullable_vector": [row["actual_nullable"] for row in rows], "trigger_vector": [row["actual_trigger"] for row in rows], "row_pass_vector": [row["row_pass"] for row in rows]}


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


def _verify_series_tester_fixture(path: Path) -> dict:
    value = _read_json(path, "series tester fixture")
    expected = {"tester_fixture_version": "nora_mql5.series_tester_canary_v1", "nullable_runtime_identity": "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d", "series_runtime_identity": SERIES_RUNTIME_IDENTITY, "condition_translation_identity": CONDITION_IDENTITY, "evaluation_ast_identity": "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664", "rust_source_data_identity": "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383", "rust_sma_artifact_identity": "bd53bf9c88cd55fbf8d0fffb791648ff7ee6bf585efd4294042671e79eb995e9", "rust_cross_artifact_identity": "274e22b09159252cc2a964cf08623de8dd9743c3152fea672a0c9ead749ff814", "source_filename": SERIES_TESTER_SOURCE}
    for key, item in expected.items():
        if value.get(key) != item: raise CompileError(f"series tester fixture contract mismatch: {key}")
    if _sha256(path.parent / SERIES_TESTER_SOURCE) != value.get("source_sha256"): raise CompileError("series tester fixture source hash mismatch")
    return value


def compile_series_tester_canary(runtime: str | os.PathLike[str], condition: str | os.PathLike[str], series_runtime: str | os.PathLike[str], tester_source: str | os.PathLike[str], tester_manifest: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    runtime_path, condition_path, series_runtime_path, source_path = Path(runtime), Path(condition), Path(series_runtime), Path(tester_source)
    _verify_sources(runtime_path, condition_path, Path(__file__).resolve().parents[2] / "tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.mq5")
    fixture = _verify_series_tester_fixture(Path(tester_manifest))
    if source_path.name != SERIES_TESTER_SOURCE or _sha256(source_path) != fixture["source_sha256"]: raise CompileError("series tester source does not match tester fixture manifest")
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    for name in (SERIES_TESTER_EX5, LOG_FILENAME, CANARY_MANIFEST_FILENAME):
        if (output/name).exists(): raise CompileError(f"local output target already exists: {name}")
    run_id="series-tester-compile-"+uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="phase2l-tester-") as temp:
        temp=Path(temp); helper=Path(__file__).resolve().parents[2]/"phase-0a-h/windows/compile-series-tester-canary.ps1"
        for source in (runtime_path,condition_path,series_runtime_path,source_path,helper): (temp/source.name).write_bytes(source.read_bytes())
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase2L\\incoming\\{run_id} | Out-Null"')
        _scp([str(temp/x) for x in (RUNTIME_FILENAME,CONDITION_FILENAME,SERIES_RUNTIME_FILENAME,SERIES_TESTER_SOURCE,helper.name)],f"{REMOTE_TARGET}:NoraPhase2L/incoming/{run_id}/")
        result=_ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\Gasper\\NoraPhase2L\\incoming\\{run_id}\\{helper.name}" -IncomingRoot "C:\\Users\\Gasper\\NoraPhase2L\\incoming\\{run_id}" -RunId "{run_id}"',check=False)
        for name in ("compile.json",LOG_FILENAME,SERIES_TESTER_EX5): _scp([f"{REMOTE_TARGET}:NoraPhase2L/{run_id}/{name}"],str(temp/name),check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2L\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2L\\incoming\\{run_id}\'"',check=False)
        remote=_read_json(temp/"compile.json","remote series tester compile")
        if result.returncode or remote.get("status")!="compiled" or remote.get("error_count")!=0 or remote.get("warning_count")!=0: raise CompileError("series tester compiler failed")
        ex5=temp/SERIES_TESTER_EX5; log=temp/LOG_FILENAME
        if not ex5.is_file() or not log.is_file() or not ex5.stat().st_size: raise CompileError("series tester compiler did not return ex5/log")
        ex5bytes=ex5.read_bytes(); logbytes=log.read_bytes(); exsha=hashlib.sha256(ex5bytes).hexdigest(); norm=_normalized_log_sha256(logbytes)
        identity=_identity(SERIES_COMPILE_DOMAIN,[fixture["tester_fixture_identity"],str(remote["compiler_version"]),exsha,norm])
        manifest={"tester_compile_contract_version":"nora_mql5_series_tester_compile_v1","compiler_path":remote["compiler_path"],"compiler_version":remote["compiler_version"],"compiler_exit_code":remote["compiler_exit_code"],"error_count":0,"warning_count":0,"tester_fixture_identity":fixture["tester_fixture_identity"],"ex5_filename":SERIES_TESTER_EX5,"ex5_sha256":exsha,"ex5_size_bytes":len(ex5bytes),"normalized_log_sha256":norm,"compile_contract_identity":identity,"status":"compiled"}
        _atomic_write(output/SERIES_TESTER_EX5,ex5bytes);_atomic_write(output/LOG_FILENAME,logbytes);_atomic_write(output/CANARY_MANIFEST_FILENAME,(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode())
        return {"ok":True,**manifest,"output_dir":str(output)}


def execute_series_tester_canary(compile_manifest: str | os.PathLike[str], ex5: str | os.PathLike[str], tester_manifest: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    compile_value=_read_json(Path(compile_manifest),"series tester compile"); fixture=_verify_series_tester_fixture(Path(tester_manifest)); ex5_path=Path(ex5)
    if compile_value.get("status")!="compiled" or compile_value.get("tester_fixture_identity")!=fixture["tester_fixture_identity"] or compile_value.get("ex5_sha256")!=_sha256(ex5_path): raise ExecutionError("series tester compile/fixture contract mismatch")
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    for name in (SERIES_TESTER_RESULT,"tester.log",EXECUTION_MANIFEST_FILENAME):
        if (output/name).exists(): raise ExecutionError(f"local output target already exists: {name}")
    run_id="series-tester-execute-"+uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="phase2l-tester-exec-") as temp:
        temp=Path(temp); helper=Path(__file__).resolve().parents[2]/"phase-0a-h/windows/execute-series-tester-canary.ps1";(temp/SERIES_TESTER_EX5).write_bytes(ex5_path.read_bytes());(temp/helper.name).write_bytes(helper.read_bytes())
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase2L\\incoming\\{run_id} | Out-Null"')
        _scp([str(temp/SERIES_TESTER_EX5),str(temp/helper.name)],f"{REMOTE_TARGET}:NoraPhase2L/incoming/{run_id}/")
        result=_ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\Gasper\\NoraPhase2L\\incoming\\{run_id}\\{helper.name}" -IncomingRoot "C:\\Users\\Gasper\\NoraPhase2L\\incoming\\{run_id}" -RunId "{run_id}"',check=False)
        for name in ("execution.json","tester.log",SERIES_TESTER_RESULT,"tester.htm"): _scp([f"{REMOTE_TARGET}:NoraPhase2L/{run_id}/{name}"],str(temp/name),check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2L\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2L\\incoming\\{run_id}\'"',check=False)
        remote=_read_json(temp/"execution.json","remote series tester execution")
        if result.returncode or remote.get("status")!="completed" or not remote.get("result_fresh"):
            if (temp/"tester.log").is_file(): _atomic_execution_write(output/"tester.log",(temp/"tester.log").read_bytes())
            raise ExecutionError(f"series tester execution failed: {remote.get('error','unknown')}")
        required=("tester_configuration_loaded","testing_agent_started","ea_loaded","ea_initialized","fixture_execution_started","result_csv_written","fixture_execution_completed","tester_completed","terminal_shutdown")
        missing=[x for x in required if remote.get("stages",{}).get(x) is not True]
        if missing: raise ExecutionError("series tester launch evidence missing stages: "+",".join(missing))
        csv=temp/SERIES_TESTER_RESULT
        reconciliation=reconcile_series_csv(csv,Path(__file__).resolve().parents[2]/"tests/fixtures/phase2k_mql5_sma_cross/tester/NoraPhase2SeriesTesterCanaryV1.manifest.json")
        csvbytes=csv.read_bytes(); exsha=_sha256(ex5_path); semantic=json.dumps({"rows":reconciliation["rows"],"summary":reconciliation["summary"]},sort_keys=True,separators=(",",":")); sma=json.dumps(reconciliation["sma_vector"],separators=(",",":")); above=json.dumps(reconciliation["cross_above_vector"],separators=(",",":")); below=json.dumps(reconciliation["cross_below_vector"],separators=(",",":")); nullable=json.dumps(reconciliation["nullable_vector"],separators=(",",":")); trigger=json.dumps(reconciliation["trigger_vector"],separators=(",",":")); rowpass=json.dumps(reconciliation["row_pass_vector"],separators=(",",":")); summary=json.dumps(reconciliation["summary"],sort_keys=True,separators=(",",":"))
        execution=_identity(SERIES_EXECUTION_DOMAIN,[fixture["tester_fixture_identity"],compile_value["compile_contract_identity"],exsha,TERMINAL_VERSION,semantic])
        semantic_id=_identity(SERIES_SEMANTIC_RESULT_DOMAIN,[SERIES_TESTER_IDENTITY,TERMINAL_PRODUCT,TERMINAL_VERSION,sma,above,below,nullable,trigger,rowpass,summary])
        manifest={"status":"passed","terminal_path":remote["terminal_path"],"terminal_version":remote["terminal_version"],"tester_fixture_identity":fixture["tester_fixture_identity"],"compile_contract_identity":compile_value["compile_contract_identity"],"ex5_sha256":exsha,"result_csv_sha256":hashlib.sha256(csvbytes).hexdigest(),"sma_vector":reconciliation["sma_vector"],"cross_above_vector":reconciliation["cross_above_vector"],"cross_below_vector":reconciliation["cross_below_vector"],"nullable_vector":reconciliation["nullable_vector"],"trigger_vector":reconciliation["trigger_vector"],"row_pass_vector":reconciliation["row_pass_vector"],**reconciliation["summary"],"execution_identity":execution,"semantic_result_identity":semantic_id,"launch_stages":remote["stages"]}
        _atomic_execution_write(output/SERIES_TESTER_RESULT,csvbytes);_atomic_execution_write(output/"tester.log",(temp/"tester.log").read_bytes());_atomic_execution_write(output/EXECUTION_MANIFEST_FILENAME,(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode())
        if (temp/"tester.htm").is_file(): _atomic_execution_write(output/"tester.htm",(temp/"tester.htm").read_bytes())
        return {"ok":True,**manifest,"output_dir":str(output)}


def _verify_slope_tester_fixture(path: Path) -> dict:
    value = _read_json(path, "slope tester fixture")
    expected = {"slope_tester_version": "nora_mql5_slope_tester_canary_v1", "nullable_runtime_identity": RUNTIME_IDENTITY, "slope_runtime_identity": SLOPE_RUNTIME_IDENTITY, "rust_input_identity": SLOPE_INPUT_IDENTITY, "rust_slope_identity": SLOPE_RUST_SLOPE_IDENTITY, "lookback": 1, "row_count": 12, "result_filename": SLOPE_TESTER_RESULT, "source_filename": SLOPE_TESTER_SOURCE}
    for key, item in expected.items():
        if value.get(key) != item:
            raise CompileError(f"slope tester fixture contract mismatch: {key}")
    if _sha256(path.parent / SLOPE_TESTER_SOURCE) != value.get("source_sha256"):
        raise CompileError("slope tester fixture source hash mismatch")
    return value


def reconcile_slope_csv(csv_path: str | os.PathLike[str], tester_manifest: str | os.PathLike[str]) -> dict[str, object]:
    fixture = _read_json(Path(tester_manifest), "slope tester fixture")
    if fixture.get("result_filename") != SLOPE_TESTER_RESULT:
        raise ExecutionError("slope tester expectations do not match frozen vectors")
    expected_slope = fixture.get("expected_slope_vector", [])
    if len(expected_slope) != 12:
        raise ExecutionError("slope tester expectations do not match frozen vectors")
    try:
        text = Path(csv_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise ExecutionError("result CSV is unreadable or not UTF-8") from error
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as error:
        raise ExecutionError("result CSV is empty") from error
    if header != SLOPE_CSV_SCHEMA:
        raise ExecutionError("result CSV header does not match frozen schema")
    records = list(reader)
    if len(records) != 13:
        raise ExecutionError("result CSV must contain exactly 12 rows and one summary")
    rows: list[dict[str, object]] = []
    for expected_index, values in enumerate(records[:12]):
        if len(values) != len(SLOPE_CSV_SCHEMA) or values[0] != "row":
            raise ExecutionError(f"malformed row record at index {expected_index}")
        if values[1] != str(expected_index):
            raise ExecutionError("row indices must be exactly 0..11 in order")
        actual_slope = _canonical_numeric(values[2], "actual_slope")
        expected_slope_val = _canonical_numeric(values[3], "expected_slope")
        row_pass = _canonical_bool(values[4], "row_pass")
        if values[5:] != ["", "", "", ""]:
            raise ExecutionError("row record contains unexpected summary fields")
        expected = expected_slope[expected_index]
        if expected is None and expected_slope_val != "null":
            raise ExecutionError("row expected value disagrees with frozen fixture vector")
        if expected is not None and not _numeric_match(expected_slope_val, expected):
            raise ExecutionError("row expected value disagrees with frozen fixture vector")
        if expected is None and actual_slope != "null":
            raise ExecutionError(f"row {expected_index} failed slope reconciliation")
        if expected is not None and not _numeric_match(actual_slope, expected):
            raise ExecutionError(f"row {expected_index} failed slope reconciliation")
        if not row_pass:
            raise ExecutionError(f"row {expected_index} row_pass is false")
        rows.append({"row_index": expected_index, "actual_slope": actual_slope, "expected_slope": expected_slope_val, "row_pass": row_pass})
    summary = records[12]
    if len(summary) != len(SLOPE_CSV_SCHEMA) or summary[0] != "summary" or summary[1] != "-1":
        raise ExecutionError("result CSV summary record is malformed")
    if summary[2:4] != ["", ""]:
        raise ExecutionError("summary contains unexpected row value fields")
    overall_pass = _canonical_bool(summary[4], "overall_pass")
    try:
        row_count, passed_rows, failed_rows = (int(summary[index]) for index in (5, 6, 7))
    except (TypeError, ValueError) as error:
        raise ExecutionError("summary counts must be integers") from error
    if summary[8] not in {"false", "true"}:
        raise ExecutionError("invalid summary overall_pass token")
    if row_count != 12 or passed_rows != 12 or failed_rows != 0 or not overall_pass or summary[8] != "true":
        raise ExecutionError("summary does not prove a 12-row pass")
    finite_differences = [abs(float(row["actual_slope"]) - float(expected_slope[index])) for index, row in enumerate(rows) if row["actual_slope"] != "null"]
    return {"rows": rows, "summary": {"row_count": row_count, "passed_rows": passed_rows, "failed_rows": failed_rows, "overall_pass": overall_pass}, "slope_vector": [row["actual_slope"] for row in rows], "expected_slope_vector": [row["expected_slope"] for row in rows], "row_pass_vector": [row["row_pass"] for row in rows], "max_finite_abs_difference": max(finite_differences, default=0.0)}


def compile_slope_tester_canary(runtime: str | os.PathLike[str], slope_runtime: str | os.PathLike[str], tester_source: str | os.PathLike[str], tester_manifest: str | os.PathLike[str], output_dir: str | os.PathLike[str], invocation_command: str) -> dict[str, object]:
    orchestration_start = datetime.now(timezone.utc)
    runtime_path, slope_runtime_path, source_path = Path(runtime), Path(slope_runtime), Path(tester_source)
    if runtime_path.name != RUNTIME_FILENAME or _sha256(runtime_path) != RUNTIME_SOURCE_SHA256:
        raise CompileError("frozen source hash mismatch: NoraPhase2RuntimeV1.mqh")
    if slope_runtime_path.name != SLOPE_RUNTIME_FILENAME or _sha256(slope_runtime_path) != SLOPE_RUNTIME_SOURCE_SHA256:
        raise CompileError("frozen source hash mismatch: NoraPhase2SlopeRuntimeV1.mqh")
    fixture = _verify_slope_tester_fixture(Path(tester_manifest))
    if source_path.name != SLOPE_TESTER_SOURCE or _sha256(source_path) != fixture["source_sha256"]:
        raise CompileError("slope tester source does not match tester fixture manifest")
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    for name in (SLOPE_TESTER_EX5, LOG_FILENAME, CANARY_MANIFEST_FILENAME):
        if (output / name).exists():
            raise CompileError(f"local output target already exists: {name}")
    run_id = "slope-tester-compile-" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="phase2n-tester-") as temp:
        temp = Path(temp)
        helper = Path(__file__).resolve().parents[2] / "phase-0a-h/windows/compile-slope-tester-canary.ps1"
        for source in (runtime_path, slope_runtime_path, source_path, helper):
            (temp / source.name).write_bytes(source.read_bytes())
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase2N\\incoming\\{run_id} | Out-Null"')
        _scp([str(temp / x) for x in (RUNTIME_FILENAME, SLOPE_RUNTIME_FILENAME, SLOPE_TESTER_SOURCE, helper.name)], f"{REMOTE_TARGET}:NoraPhase2N/incoming/{run_id}/")
        result = _ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\Gasper\\NoraPhase2N\\incoming\\{run_id}\\{helper.name}" -IncomingRoot "C:\\Users\\Gasper\\NoraPhase2N\\incoming\\{run_id}" -RunId "{run_id}"', check=False)
        for name in ("compile.json", LOG_FILENAME, SLOPE_TESTER_EX5):
            _scp([f"{REMOTE_TARGET}:NoraPhase2N/{run_id}/{name}"], str(temp / name), check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2N\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2N\\incoming\\{run_id}\'"', check=False)
        remote = _read_json(temp / "compile.json", "remote slope tester compile")
        if result.returncode or remote.get("status") != "compiled" or remote.get("error_count") != 0 or remote.get("warning_count") != 0:
            raise CompileError("slope tester compiler failed")
        ex5 = temp / SLOPE_TESTER_EX5; log = temp / LOG_FILENAME
        if not ex5.is_file() or not log.is_file() or not ex5.stat().st_size:
            raise CompileError("slope tester compiler did not return ex5/log")
        ex5bytes = ex5.read_bytes(); logbytes = log.read_bytes()
        exsha = hashlib.sha256(ex5bytes).hexdigest(); norm = _normalized_log_sha256(logbytes)
        identity = _identity(SLOPE_COMPILE_DOMAIN, [fixture["slope_tester_identity"], str(remote["compiler_version"]), exsha, norm])
        orchestration_complete = datetime.now(timezone.utc)
        manifest = {"tester_compile_contract_version": SLOPE_COMPILE_CONTRACT_VERSION, "compiler_path": remote["compiler_path"], "compiler_version": remote["compiler_version"], "compiler_exit_code": remote["compiler_exit_code"], "error_count": remote["error_count"], "warning_count": remote["warning_count"], "tester_fixture_identity": fixture["slope_tester_identity"], "slope_runtime_identity": SLOPE_RUNTIME_IDENTITY, "slope_runtime_source_sha256": SLOPE_RUNTIME_SOURCE_SHA256, "tester_source_sha256": fixture["source_sha256"], "ex5_filename": SLOPE_TESTER_EX5, "ex5_sha256": exsha, "ex5_size_bytes": len(ex5bytes), "normalized_log_sha256": norm, "compile_contract_identity": identity, "status": "compiled", "orchestration_command": invocation_command, "working_directory": str(Path.cwd()), "orchestration_start_utc": orchestration_start.isoformat(), "orchestration_completion_utc": orchestration_complete.isoformat(), "orchestration_exit_status": 0, "native_evidence": remote}
        _atomic_write(output / SLOPE_TESTER_EX5, ex5bytes); _atomic_write(output / LOG_FILENAME, logbytes); _atomic_write(output / CANARY_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode())
        return {"ok": True, **manifest, "output_dir": str(output)}


def execute_slope_tester_canary(compile_manifest: str | os.PathLike[str], ex5: str | os.PathLike[str], tester_manifest: str | os.PathLike[str], output_dir: str | os.PathLike[str], invocation_command: str) -> dict[str, object]:
    orchestration_start = datetime.now(timezone.utc)
    compile_value = _read_json(Path(compile_manifest), "slope tester compile")
    fixture = _verify_slope_tester_fixture(Path(tester_manifest))
    ex5_path = Path(ex5)
    if compile_value.get("status") != "compiled" or compile_value.get("tester_fixture_identity") != fixture["slope_tester_identity"] or compile_value.get("ex5_sha256") != _sha256(ex5_path):
        raise ExecutionError("slope tester compile/fixture contract mismatch")
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    for name in (SLOPE_TESTER_RESULT, "tester.log", EXECUTION_MANIFEST_FILENAME):
        if (output / name).exists():
            raise ExecutionError(f"local output target already exists: {name}")
    run_id = "slope-tester-execute-" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="phase2n-tester-exec-") as temp:
        temp = Path(temp)
        helper = Path(__file__).resolve().parents[2] / "phase-0a-h/windows/execute-slope-tester-canary.ps1"
        (temp / SLOPE_TESTER_EX5).write_bytes(ex5_path.read_bytes())
        (temp / helper.name).write_bytes(helper.read_bytes())
        _ssh(f'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase2N\\incoming\\{run_id} | Out-Null"')
        _scp([str(temp / SLOPE_TESTER_EX5), str(temp / helper.name)], f"{REMOTE_TARGET}:NoraPhase2N/incoming/{run_id}/")
        result = _ssh(f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\Gasper\\NoraPhase2N\\incoming\\{run_id}\\{helper.name}" -IncomingRoot "C:\\Users\\Gasper\\NoraPhase2N\\incoming\\{run_id}" -RunId "{run_id}"', check=False)
        for name in ("execution.json", "tester.log", "lifecycle.jsonl", "tester-journal.log", "tester.ini.normalized", SLOPE_TESTER_RESULT, "tester.htm"):
            _scp([f"{REMOTE_TARGET}:NoraPhase2N/{run_id}/{name}"], str(temp / name), check=False)
        _ssh(f'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2N\\{run_id}\'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue \'$env:USERPROFILE\\NoraPhase2N\\incoming\\{run_id}\'"', check=False)
        remote = _read_json(temp / "execution.json", "remote slope tester execution")
        if result.returncode or remote.get("status") != "completed" or not remote.get("result_fresh"):
            if (temp / "tester.log").is_file():
                _atomic_execution_write(output / "tester.log", (temp / "tester.log").read_bytes())
            raise ExecutionError(f"slope tester execution failed: {remote.get('error', 'unknown')}")
        required = ("tester_configuration_loaded", "testing_agent_started", "ea_loaded", "ea_initialized", "fixture_execution_started", "result_csv_written", "fixture_execution_completed", "tester_completed", "terminal_shutdown")
        missing = [x for x in required if remote.get("stages", {}).get(x) is not True]
        if missing:
            raise ExecutionError("slope tester launch evidence missing stages: " + ",".join(missing))
        csv_path = temp / SLOPE_TESTER_RESULT
        try:
            reconciliation = reconcile_slope_csv(csv_path, Path(__file__).resolve().parents[2] / "tests/fixtures/phase2m_mql5_slope/NoraPhase2SlopeTesterCanaryV1.manifest.json")
        except ExecutionError:
            for preserved_name in (SLOPE_TESTER_RESULT, "tester.log", "lifecycle.jsonl", "tester-journal.log", "tester.ini.normalized"):
                preserved = temp / preserved_name
                if preserved.is_file() and not (output / preserved_name).exists():
                    _atomic_execution_write(output / preserved_name, preserved.read_bytes())
            raise
        csvbytes = csv_path.read_bytes(); exsha = _sha256(ex5_path)
        semantic = json.dumps({"rows": reconciliation["rows"], "summary": reconciliation["summary"]}, sort_keys=True, separators=(",", ":"))
        slope = json.dumps(reconciliation["slope_vector"], separators=(",", ":")); rowpass = json.dumps(reconciliation["row_pass_vector"], separators=(",", ":")); summary = json.dumps(reconciliation["summary"], sort_keys=True, separators=(",", ":"))
        execution = _identity(SLOPE_EXECUTION_DOMAIN, [fixture["slope_tester_identity"], compile_value["compile_contract_identity"], exsha, TERMINAL_VERSION, semantic])
        semantic_id = _identity(SLOPE_SEMANTIC_RESULT_DOMAIN, [SLOPE_TESTER_IDENTITY, SLOPE_INPUT_IDENTITY, SLOPE_RUST_SLOPE_IDENTITY, TERMINAL_PRODUCT, TERMINAL_VERSION, slope, rowpass, summary])
        orchestration_complete = datetime.now(timezone.utc)
        manifest = {"status": "passed", "terminal_path": remote["terminal_path"], "terminal_version": remote["terminal_version"], "tester_fixture_identity": fixture["slope_tester_identity"], "compile_contract_identity": compile_value["compile_contract_identity"], "ex5_sha256": exsha, "result_csv_sha256": hashlib.sha256(csvbytes).hexdigest(), "slope_vector": reconciliation["slope_vector"], "expected_slope_vector": reconciliation["expected_slope_vector"], "row_pass_vector": reconciliation["row_pass_vector"], "null_positions": [index for index, value in enumerate(reconciliation["slope_vector"]) if value == "null"], "max_finite_abs_difference": reconciliation["max_finite_abs_difference"], **reconciliation["summary"], "execution_identity": execution, "semantic_result_identity": semantic_id, "launch_stages": remote["stages"], "orchestration_command": invocation_command, "working_directory": str(Path.cwd()), "orchestration_start_utc": orchestration_start.isoformat(), "orchestration_completion_utc": orchestration_complete.isoformat(), "orchestration_exit_status": 0, "native_evidence": remote}
        _atomic_execution_write(output / SLOPE_TESTER_RESULT, csvbytes); _atomic_execution_write(output / "tester.log", (temp / "tester.log").read_bytes()); _atomic_execution_write(output / "lifecycle.jsonl", (temp / "lifecycle.jsonl").read_bytes()); _atomic_execution_write(output / "tester-journal.log", (temp / "tester-journal.log").read_bytes()); _atomic_execution_write(output / "tester.ini", (temp / "tester.ini.normalized").read_bytes()); _atomic_execution_write(output / EXECUTION_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode())
        if (temp / "tester.htm").is_file():
            _atomic_execution_write(output / "tester.htm", (temp / "tester.htm").read_bytes())
        return {"ok": True, **manifest, "output_dir": str(output)}


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
    series_compile_parser = sub.add_parser("compile-series-tester-canary")
    series_compile_parser.add_argument("--runtime", required=True);series_compile_parser.add_argument("--condition", required=True);series_compile_parser.add_argument("--series-runtime", required=True);series_compile_parser.add_argument("--tester-source", required=True);series_compile_parser.add_argument("--tester-manifest", required=True);series_compile_parser.add_argument("--output-dir", required=True)
    series_execute_parser = sub.add_parser("execute-series-tester-canary")
    series_execute_parser.add_argument("--compile-manifest", required=True);series_execute_parser.add_argument("--ex5", required=True);series_execute_parser.add_argument("--tester-manifest", required=True);series_execute_parser.add_argument("--output-dir", required=True)
    slope_compile_parser = sub.add_parser("compile-slope-tester-canary")
    slope_compile_parser.add_argument("--runtime", required=True);slope_compile_parser.add_argument("--slope-runtime", required=True);slope_compile_parser.add_argument("--tester-source", required=True);slope_compile_parser.add_argument("--tester-manifest", required=True);slope_compile_parser.add_argument("--output-dir", required=True);slope_compile_parser.add_argument("--invocation-command", required=True)
    slope_execute_parser = sub.add_parser("execute-slope-tester-canary")
    slope_execute_parser.add_argument("--compile-manifest", required=True);slope_execute_parser.add_argument("--ex5", required=True);slope_execute_parser.add_argument("--tester-manifest", required=True);slope_execute_parser.add_argument("--output-dir", required=True);slope_execute_parser.add_argument("--invocation-command", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "compile-condition-canary":
            result = compile_condition_canary(args.runtime, args.condition, args.script, args.output_dir)
        elif args.command == "compile-condition-tester-canary":
            result = compile_tester_canary(args.runtime,args.condition,args.tester_source,args.tester_manifest,args.output_dir)
        elif args.command == "execute-condition-canary":
            result = execute_condition_canary(args.compile_manifest, args.ex5, args.fixture_manifest, args.output_dir, symbol=args.symbol, profile=args.profile)
        elif args.command == "execute-condition-tester-canary":
            result = execute_tester_canary(args.compile_manifest,args.ex5,args.tester_manifest,args.output_dir)
        elif args.command == "compile-series-tester-canary":
            result = compile_series_tester_canary(args.runtime,args.condition,args.series_runtime,args.tester_source,args.tester_manifest,args.output_dir)
        elif args.command == "compile-slope-tester-canary":
            result = compile_slope_tester_canary(args.runtime,args.slope_runtime,args.tester_source,args.tester_manifest,args.output_dir,args.invocation_command)
        elif args.command == "execute-slope-tester-canary":
            result = execute_slope_tester_canary(args.compile_manifest,args.ex5,args.tester_manifest,args.output_dir,args.invocation_command)
        else:
            result = execute_series_tester_canary(args.compile_manifest,args.ex5,args.tester_manifest,args.output_dir)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (CompileError, ExecutionError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


__all__ = ["CompileError", "ExecutionError", "compile_condition_canary", "compile_tester_canary", "execute_condition_canary", "execute_tester_canary", "compile_series_tester_canary", "execute_series_tester_canary", "compile_slope_tester_canary", "execute_slope_tester_canary", "reconcile_condition_csv", "reconcile_series_csv", "reconcile_slope_csv", "main"]
