"""Canonical Phase-2 provisional strategy ledger budget acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_ten_strategy_suite"
BUDGET = FIXTURE / "strategy_provisional_parity_budget.json"
TRADE_MANIFEST = FIXTURE / "trade_reconciliation_manifest.json"
SUITE = FIXTURE / "strategy_suite.json"

STRUCTURAL_FIELDS = [
    "strategy_identity",
    "trade_ordinal",
    "direction",
    "signal_index",
    "signal_timestamp",
    "entry_index",
    "entry_timestamp",
    "exit_index",
    "exit_timestamp",
    "exit_reason",
    "no_trade_reason",
    "terminal_source_disposition",
    "strategy_order",
    "trade_count",
    "ledger_order",
    "null_state",
    "marker_states",
]
NUMERIC_FIELDS = [
    "entry_price",
    "initial_stop",
    "initial_target",
    "exit_price",
    "holding_bars",
    "gross_price_return",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_strategy_provisional_budget_is_canonically_frozen():
    assert BUDGET.is_file(), "strategy provisional parity budget is not sealed"
    budget = json.loads(BUDGET.read_text(encoding="utf-8"))
    protocol = json.loads((FIXTURE / "reconciliation_protocol.json").read_text())
    frozen_budget = json.loads((FIXTURE / "budget_map.json").read_text())
    trade_manifest = json.loads(TRADE_MANIFEST.read_text(encoding="utf-8"))
    suite = json.loads(SUITE.read_text(encoding="utf-8"))

    assert budget["schema_version"] == "nora.phase2.strategy_provisional_parity_budget_v1"
    assert budget["classification"] == "PASS_EXACT"
    assert budget["scope"] == "embedded ten-strategy suite only; not performance or edge acceptance"
    assert budget["binding_mode"] == "suite_scoped_with_representative_canary"
    assert budget["strategy_suite_identity"] == suite["suite_identity"]
    assert budget["trade_reconciliation_manifest_sha256"] == _sha256(TRADE_MANIFEST)
    assert budget["native_acceptance_manifest_sha256"] == trade_manifest["native_acceptance_manifest_sha256"]
    assert budget["protocol_identity"] == protocol["strategy_reconciliation_protocol_identity"]
    assert budget["budget_map_identity"] == frozen_budget["applicable_budget_map_identity"]
    assert budget["structural_fields"] == STRUCTURAL_FIELDS
    assert budget["numeric_fields"] == NUMERIC_FIELDS
    assert budget["evidence_contexts"] == ["A1", "A2", "B1", "B2"]

    canary = next(item for item in suite["strategies"] if item["strategy_identifier"] == "trend_pullback_1")
    assert budget["representative_canary"]["strategy_identifier"] == "trend_pullback_1"
    assert budget["representative_canary"]["strategy_identity"] == canary["strategy_identity"]

    for field in STRUCTURAL_FIELDS:
        assert budget["fields"][field] == {
            "kind": "exact",
            "absolute": 0.0,
            "relative": 0.0,
            "ulp": 0,
        }
    for field in NUMERIC_FIELDS:
        assert budget["fields"][field] == {
            "kind": "exact_zero",
            "absolute": 0.0,
            "relative": 0.0,
            "ulp": 0,
        }

    assert budget["global_tolerance"] is False
    assert budget["retroactive_widening"] is False
    assert budget["grammar_admitted"] is False
    assert budget["search_authorized"] is False
    assert budget["phase3_authorized"] is False
    assert budget["complete_phase2_gate"] is False
    assert "MACD" not in json.dumps(budget)
    assert "Histogram" not in json.dumps(budget)
    assert "Signal" not in json.dumps(budget)
