"""RED boundary for exhaustive native nullable-runtime semantic parity."""
from __future__ import annotations

import json
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_ROOT = ROOT / "tests/fixtures/phase2v_nullable_runtime_native"
INDEX = NATIVE_ROOT / "native_evidence_manifest.json"
REQUIRED_OPERATIONS = ("not", "and", "or", "gt", "gte", "lt", "lte", "trigger")
REQUIRED_STAGES = ("tester_configuration_loaded", "testing_agent_started", "ea_loaded", "ea_initialized", "fixture_execution_started", "result_csv_written", "fixture_execution_completed", "tester_completed", "terminal_shutdown")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exhaustive_nullable_runtime_native_semantics_are_sealed():
    """The native package must exercise every frozen Phase-2F operation."""
    assert INDEX.is_file(), "exhaustive nullable-runtime native package is not sealed"
    manifest = json.loads(INDEX.read_text(encoding="utf-8"))
    assert manifest["scope"] == "frozen nullable runtime semantic fixture only"
    assert manifest["native_parity"] == "PASS_EXACT"
    assert manifest["runtime_semantic_native_coverage"] is True
    assert tuple(manifest["operations"]) == REQUIRED_OPERATIONS
    assert manifest["grammar_admitted"] is False
    assert manifest["searchable"] is False
    assert manifest["phase3_authorized"] is False
    assert manifest["complete_phase2_gate"] is False
    assert manifest["case_count"] == 44
    tester_source = NATIVE_ROOT / "tester/NoraPhase2ConditionTesterCanaryV1.mq5"
    tester_manifest = json.loads((NATIVE_ROOT / "tester/NoraPhase2ConditionTesterCanaryV1.manifest.json").read_text(encoding="utf-8"))
    assert manifest["tester_identity"] == tester_manifest["tester_identity"]
    assert manifest["tester_source_sha256"] == _sha256(tester_source)
    assert manifest["tester_source_sha256"] == tester_manifest["source_sha256"]
    assert _sha256(NATIVE_ROOT / "compile/NoraPhase2ConditionTesterCanaryV1.ex5") == manifest["compile"]["ex5_sha256"]
    assert manifest["compile"]["error_count"] == 0
    assert manifest["compile"]["warning_count"] == 0
    for context, run in manifest["runs"].items():
        assert run["exit_code"] == 0, context
        assert run["completion_marker"] is True, context
        assert run["failure_marker"] is False, context
        assert run["reconciliation"] == "PASS_EXACT", context
        evidence = ROOT / run["evidence_path"]
        assert evidence.is_file(), context
        execution = json.loads(evidence.read_text(encoding="utf-8-sig"))
        assert execution["status"] == "completed", context
        assert execution["native_process_exit_status"] == 0, context
        assert execution["result_fresh"] is True, context
        assert all(execution["stages"].get(stage) is True for stage in REQUIRED_STAGES), context
        csv_path = evidence.parent / "nora_phase2_condition_tester_v1.csv"
        assert csv_path.is_file(), context
        assert _sha256(csv_path) == run["csv_sha256"], context
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 45, context
        assert all(row["row_pass"].lower() == "true" for row in rows[:-1]), context
        assert rows[-1]["overall_pass"].lower() == "true", context
        assert rows[-1]["failed_rows"] == "0", context
