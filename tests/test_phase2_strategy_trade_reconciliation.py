"""Canonical E2 trade-ledger reconciliation acceptance boundary."""
from __future__ import annotations

import json
from pathlib import Path

from lab.phase2_strategy_trade_reconciliation import reconcile_native_context

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_ten_strategy_suite"
MANIFEST = FIXTURE / "trade_reconciliation_manifest.json"
CONTEXTS = ("A1", "A2", "B1", "B2")


def test_trade_by_trade_reconciliation_is_canonically_sealed():
    assert MANIFEST.is_file(), "canonical E2 trade reconciliation is not sealed"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "nora.phase2.strategy_trade_reconciliation_v1"
    assert manifest["classification"] == "PASS_EXACT"
    assert manifest["scope"] == "embedded ten-strategy suite only; not finalist edge proof"
    assert manifest["strategy_count"] == 10
    assert manifest["trade_count_per_context"] == 15
    assert manifest["protocol_identity"] == json.loads(
        (FIXTURE / "reconciliation_protocol.json").read_text()
    )["strategy_reconciliation_protocol_identity"]
    assert manifest["budget_map_identity"] == json.loads(
        (FIXTURE / "budget_map.json").read_text()
    )["applicable_budget_map_identity"]
    assert manifest["native_acceptance_classification"] == "system_smoke_not_edge_claim"
    assert manifest["grammar_admitted"] is False
    assert manifest["searchable"] is False
    assert manifest["complete_phase2_gate"] is False
    assert tuple(manifest["contexts"]) == CONTEXTS

    reconciliations = []
    for context in CONTEXTS:
        record = manifest["runs"][context]
        result = reconcile_native_context(FIXTURE / "native_four_context_accepted" / context.lower())
        assert record["classification"] == "PASS_EXACT", context
        assert record["row_count"] == 15, context
        assert record["reconciliation_identity"] == result["reconciliation_identity"], context
        assert record["csv_sha256"] == result["csv_sha256"], context
        assert record["trade_fields_reconciled"] == result["trade_fields_reconciled"], context
        reconciliations.append(result["reconciliation_identity"])

    assert len(set(reconciliations)) == 1
    assert manifest["cross_context_equivalence"] is True
