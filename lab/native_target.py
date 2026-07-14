"""Typed, target-neutral mechanics for Phase-2 native evidence contracts.

Target descriptors contain immutable names and roles, never expected rows or native
results. Existing execution contracts remain authoritative and byte-compatible.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from lab.phase2_execution import canon, sha

POLICY = "nora.metaeditor_cli_success_v1"
EDITOR = r"C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe"
BUILD = "5.0.0.5836"
DEPENDENCY_GRAPH = {"source": [], "compile_input": ["source"],
                    "compiler_output": ["compile_input"],
                    "execution_packet": ["compiler_output"],
                    "final_batch": ["execution_packet"]}


@dataclass(frozen=True)
class NativeTargetDescriptor:
    schema_version: str
    target_identifier: str
    compile_input_schema: str
    compiler_output_schema: str
    compile_evidence_schema: str
    packet_schema: str
    precompile_batch_schema: str
    final_batch_schema: str
    returned_package_schema: str
    runtime_filename: str
    tester_filename: str
    package_filename: str
    ex5_filename: str
    compile_input_filename: str
    result_csv_filename: str
    compiler_script: str
    execution_script: str
    collection_script: str
    completion_marker: str
    failure_marker: str
    reconciliation_implementation: str
    host_contexts: tuple[str, ...]
    package_member_roles: tuple[str, ...]

    def value(self) -> dict:
        value = asdict(self)
        value["host_contexts"] = list(self.host_contexts)
        value["package_member_roles"] = list(self.package_member_roles)
        return value

    @property
    def identity(self) -> str:
        return sha(self.value())


def raw_sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def file_sha(path: Path) -> str: return raw_sha(Path(path).read_bytes())


def safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def identified(value: dict, field: str) -> dict:
    result = dict(value); result[field] = sha(value); return result


def validate_dependency_graph(nodes: dict) -> list[str]:
    errors: list[str] = []
    for node, deps in nodes.items():
        if node not in DEPENDENCY_GRAPH or node in deps or any(x not in DEPENDENCY_GRAPH[node] for x in deps):
            errors.append("dependency direction")
    visiting: set[str] = set(); done: set[str] = set()
    def visit(node: str):
        if node in visiting: errors.append("cycle"); return
        if node in done: return
        visiting.add(node)
        for dependency in nodes.get(node, []): visit(dependency)
        visiting.remove(node); done.add(node)
    for node in nodes: visit(node)
    return errors


def compiler_output_identity(record: dict) -> str:
    value = dict(record); value.pop("compiler_output_identity", None); return sha(value)


def validate_compiler_envelope(record: dict, compile_input: dict, evidence_dir: Path,
                               descriptor: NativeTargetDescriptor) -> list[str]:
    errors: list[str] = []
    checks = {
        "schema": record.get("schema_version") == descriptor.compiler_output_schema,
        "target": record.get("target_identifier") == descriptor.target_identifier,
        "descriptor": record.get("target_descriptor_identity") == descriptor.identity,
        "compile input": record.get("compile_input_identity") == compile_input.get("compile_input_identity"),
        "runtime hash": record.get("runtime_sha256") == compile_input.get("runtime_sha256"),
        "tester hash": record.get("tester_sha256") == compile_input.get("tester_sha256"),
        "package": record.get("package_identity") == compile_input.get("package_identity"),
        "compiler": record.get("metaeditor_executable") == EDITOR and record.get("observed_metaeditor_build") == BUILD,
        "policy": record.get("compiler_policy") == POLICY and record.get("policy_decision") in ("accepted_zero", "accepted_metaeditor_5836_one"),
        "exit": record.get("raw_process_exit") in (0, 1) and record.get("normalized_result") == "success",
        "warnings": record.get("warning_count") == 0 and record.get("warnings") == [],
        "errors": record.get("error_count") == 0 and record.get("errors") == [],
        "completion": record.get("completion_state") == "completed" and record.get("failure_reason") in (None, ""),
        "freshness": record.get("freshness_proof") == {"preexisting_ex5_removed_or_isolated": True, "produced_after_invocation_start": True, "single_unambiguous_ex5": True},
    }
    errors.extend(key for key, valid in checks.items() if not valid)
    for kind in ("log", "ex5"):
        relative = record.get(f"{kind}_path", "")
        if not safe_relative(relative): errors.append(f"{kind} path"); continue
        path = Path(evidence_dir) / relative
        if not path.is_file(): errors.append(f"missing {kind}"); continue
        if path.stat().st_size != record.get(f"{kind}_size") or file_sha(path) != record.get(f"{kind}_sha256"):
            errors.append(f"{kind} binding")
    claimed = record.get("compiler_output_identity")
    if claimed not in (None, compiler_output_identity(record)): errors.append("output identity")
    return errors


def atomic_publish(destination: Path, prefix: str, writer, *, inject_failure=False):
    destination = Path(destination)
    if destination.exists(): raise ValueError("occupied destination")
    temporary = Path(tempfile.mkdtemp(prefix=prefix, dir=destination.parent))
    try:
        result = writer(temporary)
        if inject_failure: raise RuntimeError("injected publication interruption")
        temporary.replace(destination)
        return result
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True); raise


def inventory_identity(items: list[dict]) -> str:
    return sha([{"path": x["path"], "role": x["role"]} for x in items])


def manifest_identity(value: dict, field: str) -> str:
    normalized = dict(value); normalized.pop(field, None)
    return sha(normalized)


# Frozen market-history synchronization/download evidence vocabulary. An
# embedded-fixture canary must never cause the MT5 tester to synchronize or
# download broker history; the launcher scans the captured tester journal for
# these markers and fails closed if any appear. Keep in lockstep with the
# PowerShell launcher (phase-0a-h/windows/execute-*-packet.ps1).
HISTORY_SYNCHRONIZATION_FORBIDDEN_MARKERS = (
    "symbol to be synchronized",
    "symbol synchronized",
    "history synchronized",
    "history data to synchronize",
    "history cache allocated",
    "history begins from",
    "quality of analyzed history",
    "common synchronization completed",
)


def detect_history_synchronization(journal_text: str) -> list[str]:
    """Return the forbidden markers present in a tester journal segment.

    A non-empty result proves market-history synchronization/download occurred
    during the run and the run must not be accepted.
    """
    lowered = (journal_text or "").lower()
    return [marker for marker in HISTORY_SYNCHRONIZATION_FORBIDDEN_MARKERS if marker in lowered]
