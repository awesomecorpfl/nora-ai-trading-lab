from __future__ import annotations

import copy
import pytest

from lab.phase2_native_similarity import (
    METRICS,
    build_similarity_report,
    compare_metrics,
    validate_budget_map,
)


REFERENCE = {
    "trade_count": 20,
    "gross_pnl": 42.0,
    "net_pnl": 35.0,
    "profit_factor": 1.6,
    "max_drawdown": 12.0,
    "win_rate": 0.55,
    "average_trade": 1.75,
    "edge_survives": True,
}
NATIVE = {**REFERENCE, "trade_count": 22, "gross_pnl": 44.0, "net_pnl": 31.0}
BUDGETS = {metric: {"max_relative_delta": 0.25} for metric in METRICS}


def test_similarity_report_accepts_explicit_budget_and_preserves_non_searchable_state():
    report = build_similarity_report(
        reference=REFERENCE,
        native=NATIVE,
        budgets=BUDGETS,
        provenance={"symbol": "GDAXI", "timeframe": "M1", "source": "broker_native_mt5"},
    )
    assert report["validation_mode"] == "broker_native_edge_survival"
    assert report["comparison_mode"] == "similarity_not_exact_parity"
    assert report["comparison"]["passed"] is True
    assert report["edge_survival_accepted"] is True
    assert report["native_parity_accepted"] is False
    assert report["searchable"] is False
    assert len(report["similarity_report_identity"]) == 64


def test_similarity_report_rejects_metric_outside_budget():
    native = copy.deepcopy(NATIVE)
    native["net_pnl"] = -10.0
    result = compare_metrics(REFERENCE, native, BUDGETS)
    assert result["passed"] is False
    assert result["edge_survives"] is True
    assert result["metrics"]["net_pnl"]["passed"] is False


def test_similarity_report_requires_native_edge_survival():
    native = {**NATIVE, "edge_survives": False}
    result = compare_metrics(REFERENCE, native, BUDGETS)
    assert result["passed"] is False
    assert result["edge_survives"] is False


def test_budget_map_must_be_complete_and_non_negative():
    with pytest.raises(ValueError, match="cover every"):
        validate_budget_map({metric: {"max_relative_delta": 0.1} for metric in METRICS[:-1]})
    invalid = {metric: {"max_relative_delta": 0.1} for metric in METRICS}
    invalid["net_pnl"] = {"max_relative_delta": -0.1}
    with pytest.raises(ValueError, match="non-negative"):
        validate_budget_map(invalid)


def test_similarity_does_not_claim_exact_trade_identity():
    result = compare_metrics(REFERENCE, {**NATIVE, "trade_count": 25}, BUDGETS)
    assert result["metrics"]["trade_count"]["reference"] != result["metrics"]["trade_count"]["native"]
    assert result["schema_version"] == "nora.phase2_broker_native_similarity_v1"
