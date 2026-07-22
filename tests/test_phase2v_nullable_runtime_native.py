"""RED boundary for exhaustive native nullable-runtime semantic parity."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_ROOT = ROOT / "tests/fixtures/phase2v_nullable_runtime_native"
INDEX = NATIVE_ROOT / "native_evidence_manifest.json"
REQUIRED_OPERATIONS = ("not", "and", "or", "gt", "gte", "lt", "lte", "trigger")


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
    assert manifest["compile"]["error_count"] == 0
    assert manifest["compile"]["warning_count"] == 0
    for context, run in manifest["runs"].items():
        assert run["exit_code"] == 0, context
        assert run["completion_marker"] is True, context
        assert run["failure_marker"] is False, context
        assert run["reconciliation"] == "PASS_EXACT", context
        assert Path(ROOT / run["evidence_path"]).is_file(), context
