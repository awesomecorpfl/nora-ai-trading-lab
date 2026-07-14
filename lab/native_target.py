"""Typed, target-neutral mechanics for Phase-2 native evidence contracts.

Target descriptors contain immutable names and roles, never expected rows or native
results. Existing execution contracts remain authoritative and byte-compatible.
"""
from __future__ import annotations

import hashlib
import json
import re
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


# Typed market-history synchronization/download evidence vocabulary.
# Forensic evidence (FORENSIC_V4) proves the MT5 terminal always mutates cache
# files on every startup (metadata-scale header/index updates, not price-data
# downloads). The categories below classify each frozen marker by what forensic
# evidence proved — not by the marker's wording alone.  See the machine-readable
# classification artifact at docs/phase2_history_sync_marker_classification.json.
HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION = {
    "symbol to be synchronized":           "attempted_sync",
    "symbol synchronized":                 "local_cache_access",
    "history synchronized":                "local_cache_access",
    "history data to synchronize":         "attempted_sync",
    "history cache allocated":             "local_cache_access",
    "history begins from":                 "local_cache_access",
    "quality of analyzed history":         "local_cache_access",
    "common synchronization completed":    "ambiguous",
}

# Categories whose presence in a journal independently fail acceptance. A
# synchronization attempt or local cache access is resolved only by the full
# forensic bundle below.
FORBIDDEN_SUCCESSFUL_DOWNLOAD_MARKERS = (
    "downloaded bars", "downloaded ticks", "ticks downloaded", "bars downloaded",
)
FORBIDDEN_EXTERNAL_MUTATION_MARKERS = ()            # file-hash diff required in addition
ATTEMPTED_SYNC_MARKERS = tuple(k for k, v in HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION.items() if v == "attempted_sync")
LOCAL_CACHE_ACCESS_MARKERS = tuple(k for k, v in HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION.items() if v == "local_cache_access")
AMBIGUOUS_MARKERS = tuple(k for k, v in HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION.items() if v == "ambiguous")

# Explicit price-payload reports are fatal. These patterns intentionally do not
# match the proven 25-byte handshake or 3,720-byte symbol-contract metadata.
PRICE_DATA_PAYLOAD_PATTERNS = (
    r"\b(?:downloaded|received|loaded)\s+\d+\s+(?:bars?|ticks?)\b",
    r"\b(?:bars?|ticks?)\s+(?:downloaded|received)\b",
    r"\bprice[- ]data payload\b",
)


def classify_journal_markers(journal_text: str) -> dict[str, list[str]]:
    """Classify each journal marker into its forensic-evidence-based category."""
    lowered = (journal_text or "").lower()
    result = {
        "successful_download": [],
        "external_mutation": [],
        "attempted_sync": [],
        "local_cache_access": [],
        "ambiguous": [],
    }
    for marker, category in HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION.items():
        if marker in lowered:
            result[category].append(marker)
    result["successful_download"].extend(detect_history_synchronization(lowered))
    return result


def detect_history_synchronization(journal_text: str) -> list[str]:
    """Return journal evidence that independently proves price acquisition."""
    lowered = (journal_text or "").lower()
    hits = [marker for marker in FORBIDDEN_SUCCESSFUL_DOWNLOAD_MARKERS if marker in lowered]
    hits.extend(pattern for pattern in PRICE_DATA_PAYLOAD_PATTERNS if re.search(pattern, lowered))
    return hits


def evaluate_environmental_acceptance(evidence: dict) -> dict:
    """Fail closed on incomplete or price-affecting native-run evidence.

    This contract accepts only embedded-fixture calculations and bounded,
    explicitly classified metadata/header/index maintenance. It never infers
    safety from journal wording or byte-identical cache files alone.
    """
    required = ("embedded_fixture_only", "raw_journal", "before_inventory", "after_inventory",
                "bar_count_before", "bar_count_after", "history_range_before", "history_range_after",
                "downloaded_bars", "downloaded_ticks", "price_data_payload_detected",
                "symbol_contract_metadata", "cache_mutations", "max_cache_delta_bytes",
                "ambiguous_evidence_resolved")
    missing = [key for key in required if key not in evidence or evidence[key] is None]
    if missing:
        return {"accepted": False, "reasons": ["MISSING_FORENSIC_EVIDENCE:" + ",".join(missing)],
                "journal": classify_journal_markers("")}
    reasons = []
    journal = evidence["raw_journal"]
    if not isinstance(journal, str) or not journal.strip(): reasons.append("MISSING_RAW_JOURNAL")
    before, after = evidence["before_inventory"], evidence["after_inventory"]
    if not isinstance(before, dict) or not isinstance(after, dict): reasons.append("INVALID_CACHE_INVENTORY")
    else:
        added, deleted = sorted(set(after) - set(before)), sorted(set(before) - set(after))
        if added: reasons.append("NEW_HISTORY_OR_TICK_FILE:" + ",".join(added))
        if deleted: reasons.append("DELETED_CACHE_FILE:" + ",".join(deleted))
    if evidence["embedded_fixture_only"] is not True: reasons.append("NON_EMBEDDED_CALCULATION_INPUT")
    if evidence["bar_count_before"] != evidence["bar_count_after"]: reasons.append("BAR_COUNT_EXPANSION_OR_CHANGE")
    if evidence["history_range_before"] != evidence["history_range_after"]: reasons.append("HISTORY_RANGE_EXPANSION_OR_CHANGE")
    if evidence["downloaded_bars"] != 0 or evidence["downloaded_ticks"] != 0: reasons.append("REPORTED_BAR_OR_TICK_DOWNLOAD")
    if evidence["price_data_payload_detected"] is not False: reasons.append("PRICE_DATA_PAYLOAD_DETECTED")
    classified = classify_journal_markers(journal)
    if detect_history_synchronization(journal): reasons.append("JOURNAL_PRICE_DATA_PAYLOAD")
    # A generic journal phrase can be ambiguous in isolation. It may be
    # resolved only by the complete retained forensic record; otherwise fail.
    if evidence["ambiguous_evidence_resolved"] is not True: reasons.append("AMBIGUOUS_EVIDENCE")
    allowed = {"symbol_contract_metadata", "cache_header_maintenance", "cache_index_maintenance", "in_memory_cache_allocation"}
    mutations = evidence["cache_mutations"]
    if not isinstance(mutations, list): reasons.append("INVALID_CACHE_MUTATION_RECORD")
    else:
        for mutation in mutations:
            if not isinstance(mutation, dict) or mutation.get("classification") not in allowed:
                reasons.append("AMBIGUOUS_CACHE_MUTATION"); continue
            delta = mutation.get("delta_bytes")
            if not isinstance(delta, int) or abs(delta) > evidence["max_cache_delta_bytes"]:
                reasons.append("UNBOUNDED_CACHE_MUTATION")
    if not isinstance(evidence["symbol_contract_metadata"], list): reasons.append("MISSING_SYMBOL_CONTRACT_METADATA_RECORD")
    return {"accepted": not reasons, "reasons": reasons, "journal": classified}
