"""Repository-owned compile-only orchestration for the Phase 2I canary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
RUNTIME_IDENTITY = "2ba6078adcd10d991d3ef1ada26baa791a0c6054707a84acaceaa6fe23f2b176"
RUNTIME_SOURCE_SHA256 = "42b7239442090a68fdacdc481925cd6b9819b572ea083efce3f3e3cbbb27d2a4"
CONDITION_IDENTITY = "22ff3c2cc2d387173eb066c428eac99f663263a6d7dda773f44647ec371509bd"
CONDITION_SOURCE_SHA256 = "1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4"
FIXTURE_IDENTITY = "ab09f18f446897f5cd28adcfc4a1260688cc8c397c58ba400516db6006e89d1e"
FIXTURE_SOURCE_SHA256 = "b3b98996545d1277d4b2fa51db7c14c943ad733c018717110dab45e05f0022a7"
CANARY_MANIFEST_FILENAME = "compile_manifest.json"


class CompileError(RuntimeError):
    """Deterministic compile-control failure."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _part(digest: "hashlib._Hash", value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def _verify_manifest(path: Path, expected: dict[str, str], identity_key: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
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


def _compile_identity(compiler_path: str, compiler_version: str, exit_code: int, errors: int, warnings: int, ex5_filename: str, source_hashes: list[str]) -> str:
    digest = hashlib.sha256()
    for value in [COMPILE_IDENTITY_DOMAIN, COMPILE_CONTRACT_VERSION, RUNTIME_IDENTITY, CONDITION_IDENTITY, FIXTURE_IDENTITY, *source_hashes, compiler_path, compiler_version, str(exit_code), str(errors), str(warnings), ex5_filename]:
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
        if not compiler_path or not compiler_version or exit_code != 0 or errors != 0 or warnings != 0:
            raise CompileError("compile acceptance requires observed compiler identity and zero errors/warnings")
        ex5_sha = hashlib.sha256(ex5_bytes).hexdigest(); log_sha = hashlib.sha256(log_bytes).hexdigest(); source_hashes = [RUNTIME_SOURCE_SHA256, CONDITION_SOURCE_SHA256, FIXTURE_SOURCE_SHA256]
        contract_identity = _compile_identity(compiler_path, compiler_version, exit_code, errors, warnings, EX5_FILENAME, source_hashes)
        manifest = {"compile_contract_version": COMPILE_CONTRACT_VERSION, "host_alias": HOST_ALIAS, "compiler_path": compiler_path, "compiler_version": compiler_version, "runtime_identity": RUNTIME_IDENTITY, "condition_translation_identity": CONDITION_IDENTITY, "fixture_identity": FIXTURE_IDENTITY, "runtime_source_sha256": RUNTIME_SOURCE_SHA256, "condition_source_sha256": CONDITION_SOURCE_SHA256, "fixture_source_sha256": FIXTURE_SOURCE_SHA256, "compiler_exit_code": exit_code, "error_count": errors, "warning_count": warnings, "log_sha256": log_sha, "ex5_filename": EX5_FILENAME, "ex5_sha256": ex5_sha, "ex5_size_bytes": len(ex5_bytes), "compile_contract_identity": contract_identity, "status": "compiled"}
        _atomic_write(output / EX5_FILENAME, ex5_bytes); _atomic_write(output / LOG_FILENAME, log_bytes); _atomic_write(output / CANARY_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
        return {"ok": True, **manifest, "output_dir": str(output)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lab.mt5")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile-condition-canary")
    compile_parser.add_argument("--runtime", required=True)
    compile_parser.add_argument("--condition", required=True)
    compile_parser.add_argument("--script", required=True)
    compile_parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        result = compile_condition_canary(args.runtime, args.condition, args.script, args.output_dir)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except CompileError as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


__all__ = ["CompileError", "compile_condition_canary", "main"]
