"""Tests for the edge-survival scaffold.

These lock the fail-closed semantics that make the scaffold impossible to
retrofit around: missing/partial metrics, post-result freezing, identity
substitution, and provenance gaps must all refuse. The one happy-path test
proves the full ceremony assembles when every invariant holds.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lab.phase2_edge_survival_scaffold import (
    REQUIRED_PROVENANCE_FIELDS,
    assemble_edge_survival_report,
    bind_native_provenance,
    freeze_reference_metrics,
    freeze_similarity_budget,
)
from lab.phase2_native_similarity import METRICS
from lab.mql5gen import edge_survival_skeleton as skeleton


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REFERENCE_METRICS = {
    "trade_count": 20.0,
    "gross_pnl": 420.0,
    "net_pnl": 350.0,
    "profit_factor": 1.6,
    "max_drawdown": 120.0,
    "win_rate": 0.55,
    "average_trade": 17.5,
}
BUDGETS = {metric: {"max_relative_delta": 0.25} for metric in METRICS}
NATIVE_METRICS = {
    **REFERENCE_METRICS,
    "trade_count": 22.0,
    "gross_pnl": 440.0,
    "net_pnl": 310.0,
    "edge_survives": True,
}
PROVENANCE = {
    "symbol": "EURUSD",
    "server_identity": "Darwinex-Live",
    "timeframe": "M5",
    "date_range_start": "2020.01.01",
    "date_range_end": "2024.12.31",
    "timezone_identity": "UTC+0",
    "spread_model": "darwinex_live_variable",
    "commission_model": "7_usd_per_lot_round_trip",
    "slippage_model": "tester_default",
    "source_identity": "broker_native_mt5_build_5836",
}


def _freeze_reference(frozen_at="2026-01-01T00:00:00+00:00"):
    return freeze_reference_metrics(
        finalist_identity="finalist_001",
        metrics=REFERENCE_METRICS,
        edge_survives=True,
        reference_runner_identity="rust_reference_v1",
        frozen_at=frozen_at,
    )


def _freeze_budget(reference, frozen_at="2026-01-02T00:00:00+00:00"):
    return freeze_similarity_budget(
        finalist_identity="finalist_001",
        reference_identity=reference["reference_identity"],
        budgets=BUDGETS,
        gate_authority="gasper",
        edge_survives_definition="net_pnl remains positive and within 25% relative budget",
        native_cost_included=True,
        frozen_at=frozen_at,
    )


def _bind_provenance():
    return bind_native_provenance(PROVENANCE)


# ---------------------------------------------------------------------------
# Reference freeze
# ---------------------------------------------------------------------------

def test_reference_freeze_produces_stable_identity():
    r1 = _freeze_reference()
    r2 = _freeze_reference()
    assert r1["reference_identity"] == r2["reference_identity"]
    assert r1["schema_version"] == "nora.phase2_edge_survival_reference_v1"
    assert set(r1["metrics"]) == set(METRICS)


def test_reference_freeze_rejects_missing_metric():
    bad = copy.deepcopy(REFERENCE_METRICS)
    del bad["profit_factor"]
    with pytest.raises(ValueError, match="missing"):
        freeze_reference_metrics(
            finalist_identity="finalist_001",
            metrics=bad,
            edge_survives=True,
            reference_runner_identity="rust_reference_v1",
        )


def test_reference_freeze_rejects_non_boolean_edge_survives():
    with pytest.raises(ValueError, match="edge_survives"):
        freeze_reference_metrics(
            finalist_identity="finalist_001",
            metrics=REFERENCE_METRICS,
            edge_survives="true",
            reference_runner_identity="rust_reference_v1",
        )


def test_reference_freeze_rejects_empty_finalist():
    with pytest.raises(ValueError, match="finalist_identity"):
        freeze_reference_metrics(
            finalist_identity="",
            metrics=REFERENCE_METRICS,
            edge_survives=True,
            reference_runner_identity="rust_reference_v1",
        )


def test_reference_identity_is_tamper_evident():
    r1 = _freeze_reference()
    r2 = freeze_reference_metrics(
        finalist_identity="finalist_002",
        metrics=REFERENCE_METRICS,
        edge_survives=True,
        reference_runner_identity="rust_reference_v1",
        frozen_at="2026-01-01T00:00:00+00:00",
    )
    assert r1["reference_identity"] != r2["reference_identity"]


# ---------------------------------------------------------------------------
# Budget freeze
# ---------------------------------------------------------------------------

def test_budget_freeze_produces_stable_identity():
    ref = _freeze_reference()
    b1 = _freeze_budget(ref)
    b2 = _freeze_budget(ref)
    assert b1["budget_freeze_identity"] == b2["budget_freeze_identity"]
    assert b1["schema_version"] == "nora.phase2_edge_survival_budget_freeze_v1"
    assert b1["native_cost_included"] is True


def test_budget_freeze_rejects_partial_budget_map():
    ref = _freeze_reference()
    partial = {m: {"max_relative_delta": 0.1} for m in METRICS[:-1]}
    with pytest.raises(ValueError, match="cover every"):
        freeze_similarity_budget(
            finalist_identity="finalist_001",
            reference_identity=ref["reference_identity"],
            budgets=partial,
            gate_authority="gasper",
            edge_survives_definition="x",
            native_cost_included=True,
        )


def test_budget_freeze_rejects_negative_tolerance():
    ref = _freeze_reference()
    bad = copy.deepcopy(BUDGETS)
    bad["net_pnl"] = {"max_relative_delta": -0.1}
    with pytest.raises(ValueError, match="non-negative"):
        freeze_similarity_budget(
            finalist_identity="finalist_001",
            reference_identity=ref["reference_identity"],
            budgets=bad,
            gate_authority="gasper",
            edge_survives_definition="x",
            native_cost_included=True,
        )


def test_budget_freeze_rejects_empty_edge_definition():
    ref = _freeze_reference()
    with pytest.raises(ValueError, match="edge_survives_definition"):
        freeze_similarity_budget(
            finalist_identity="finalist_001",
            reference_identity=ref["reference_identity"],
            budgets=BUDGETS,
            gate_authority="gasper",
            edge_survives_definition="   ",
            native_cost_included=True,
        )


# ---------------------------------------------------------------------------
# Provenance binding
# ---------------------------------------------------------------------------

def test_provenance_binding_produces_stable_identity():
    p1 = _bind_provenance()
    p2 = _bind_provenance()
    assert p1["provenance_identity"] == p2["provenance_identity"]
    assert set(p1["provenance"]) == set(REQUIRED_PROVENANCE_FIELDS)


def test_provenance_binding_rejects_missing_field():
    bad = copy.deepcopy(PROVENANCE)
    del bad["server_identity"]
    with pytest.raises(ValueError, match="server_identity"):
        bind_native_provenance(bad)


def test_provenance_binding_rejects_empty_field():
    bad = copy.deepcopy(PROVENANCE)
    bad["symbol"] = ""
    with pytest.raises(ValueError, match="provenance.symbol"):
        bind_native_provenance(bad)


def test_provenance_identity_is_tamper_evident():
    p1 = _bind_provenance()
    bad = copy.deepcopy(PROVENANCE)
    bad["timeframe"] = "H1"
    p2 = bind_native_provenance(bad)
    assert p1["provenance_identity"] != p2["provenance_identity"]


# ---------------------------------------------------------------------------
# Report assembly — the ceremony
# ---------------------------------------------------------------------------

def test_assemble_report_happy_path():
    ref = _freeze_reference(frozen_at="2026-01-01T00:00:00+00:00")
    budget = _freeze_budget(ref, frozen_at="2026-01-02T00:00:00+00:00")
    prov = _bind_provenance()
    report = assemble_edge_survival_report(
        reference=ref,
        budget_freeze=budget,
        native_provenance=prov,
        native_metrics=NATIVE_METRICS,
        native_observed_at="2026-01-03T00:00:00+00:00",
    )
    assert report["schema_version"] == "nora.phase2_edge_survival_report_v1"
    assert report["edge_survival_accepted"] is True
    assert report["native_parity_accepted"] is False
    assert report["searchable"] is False
    assert len(report["report_identity"]) == 64
    assert report["reference_identity"] == ref["reference_identity"]
    assert report["budget_freeze_identity"] == budget["budget_freeze_identity"]
    assert report["provenance_identity"] == prov["provenance_identity"]


def test_assemble_report_rejects_reference_frozen_after_native():
    ref = _freeze_reference(frozen_at="2026-01-05T00:00:00+00:00")
    budget = _freeze_budget(ref, frozen_at="2026-01-02T00:00:00+00:00")
    prov = _bind_provenance()
    with pytest.raises(ValueError, match="reference must be frozen before"):
        assemble_edge_survival_report(
            reference=ref,
            budget_freeze=budget,
            native_provenance=prov,
            native_metrics=NATIVE_METRICS,
            native_observed_at="2026-01-03T00:00:00+00:00",
        )


def test_assemble_report_rejects_budget_frozen_after_native():
    ref = _freeze_reference(frozen_at="2026-01-01T00:00:00+00:00")
    budget = _freeze_budget(ref, frozen_at="2026-01-05T00:00:00+00:00")
    prov = _bind_provenance()
    with pytest.raises(ValueError, match="budget must be frozen before"):
        assemble_edge_survival_report(
            reference=ref,
            budget_freeze=budget,
            native_provenance=prov,
            native_metrics=NATIVE_METRICS,
            native_observed_at="2026-01-03T00:00:00+00:00",
        )


def test_assemble_report_rejects_budget_not_bound_to_reference():
    ref_a = _freeze_reference(frozen_at="2026-01-01T00:00:00+00:00")
    # Freeze a budget for a *different* reference identity.
    ref_b = freeze_reference_metrics(
        finalist_identity="finalist_002",
        metrics={**REFERENCE_METRICS, "trade_count": 99.0},
        edge_survives=True,
        reference_runner_identity="rust_reference_v1",
        frozen_at="2026-01-01T00:00:00+00:00",
    )
    budget_b = _freeze_budget(ref_b, frozen_at="2026-01-02T00:00:00+00:00")
    prov = _bind_provenance()
    with pytest.raises(ValueError, match="budget freeze does not bind"):
        assemble_edge_survival_report(
            reference=ref_a,
            budget_freeze=budget_b,
            native_provenance=prov,
            native_metrics=NATIVE_METRICS,
            native_observed_at="2026-01-03T00:00:00+00:00",
        )


def test_assemble_report_rejects_wrong_schema_inputs():
    ref = _freeze_reference()
    budget = _freeze_budget(ref)
    prov = _bind_provenance()
    with pytest.raises(ValueError, match="reference must be"):
        assemble_edge_survival_report(
            reference={"schema_version": "wrong"},
            budget_freeze=budget,
            native_provenance=prov,
            native_metrics=NATIVE_METRICS,
            native_observed_at="2026-01-03T00:00:00+00:00",
        )


def test_assemble_report_rejects_missing_native_metric():
    ref = _freeze_reference(frozen_at="2026-01-01T00:00:00+00:00")
    budget = _freeze_budget(ref, frozen_at="2026-01-02T00:00:00+00:00")
    prov = _bind_provenance()
    bad = copy.deepcopy(NATIVE_METRICS)
    del bad["win_rate"]
    with pytest.raises(ValueError, match="native_metrics missing"):
        assemble_edge_survival_report(
            reference=ref,
            budget_freeze=budget,
            native_provenance=prov,
            native_metrics=bad,
            native_observed_at="2026-01-03T00:00:00+00:00",
        )


def test_assemble_report_rejects_non_boolean_native_edge_survives():
    ref = _freeze_reference(frozen_at="2026-01-01T00:00:00+00:00")
    budget = _freeze_budget(ref, frozen_at="2026-01-02T00:00:00+00:00")
    prov = _bind_provenance()
    bad = {**NATIVE_METRICS, "edge_survives": "yes"}
    with pytest.raises(ValueError, match="edge_survives"):
        assemble_edge_survival_report(
            reference=ref,
            budget_freeze=budget,
            native_provenance=prov,
            native_metrics=bad,
            native_observed_at="2026-01-03T00:00:00+00:00",
        )


def test_assemble_report_carries_provenance_substitution_resistance():
    """The similarity report inside must bind the exact provenance identity."""
    ref = _freeze_reference(frozen_at="2026-01-01T00:00:00+00:00")
    budget = _freeze_budget(ref, frozen_at="2026-01-02T00:00:00+00:00")
    prov = _bind_provenance()
    report = assemble_edge_survival_report(
        reference=ref,
        budget_freeze=budget,
        native_provenance=prov,
        native_metrics=NATIVE_METRICS,
        native_observed_at="2026-01-03T00:00:00+00:00",
    )
    # The similarity sub-report must carry the provenance dict and its identity
    # must match what the scaffold bound.
    assert report["similarity"]["provenance"] == prov["provenance"]
    assert report["provenance_identity"] == prov["provenance_identity"]


# ---------------------------------------------------------------------------
# EA skeleton generator
# ---------------------------------------------------------------------------

def test_skeleton_generator_produces_stable_artifacts(tmp_path: Path):
    m1 = skeleton.generate(tmp_path / "a")
    m2 = skeleton.generate(tmp_path / "b")
    assert m1["skeleton_identity"] == m2["skeleton_identity"]
    assert m1["schema_version"] == "nora.phase2_edge_survival_ea_skeleton_v1"
    assert m1["skeleton_not_strategic"] is True
    assert (tmp_path / "a" / skeleton.EA_FILENAME).exists()
    assert (tmp_path / "a" / skeleton.MANIFEST_FILENAME).exists()


def test_skeleton_csv_schema_covers_cost_model_and_disposition():
    cols = set(skeleton.CSV_COLUMNS)
    required = {
        "entry_price",
        "exit_price",
        "gross_price_return",
        "cost_model_spread",
        "cost_model_commission",
        "cost_model_slippage",
        "native_edge_survives_flag",
        "terminal_source_disposition",
    }
    assert required <= cols


def test_skeleton_source_declares_extension_points(tmp_path: Path):
    m = skeleton.generate(tmp_path / "x")
    source = (tmp_path / "x" / skeleton.EA_FILENAME).read_text()
    assert "EvaluateEntry" in source
    assert "EvaluateExit" in source
    assert "MQL_TESTER" in source  # tester-only guard
    assert "OrderSend" in source  # the guarded order-send boundary
    assert m["extension_point_contract"]["EvaluateEntry"].startswith("returns OP_BUY")


def test_skeleton_is_not_strategic_by_default(tmp_path: Path):
    m = skeleton.generate(tmp_path / "y")
    assert m["skeleton_not_strategic"] is True
    assert "not a finalist" in m["note"]


# ---------------------------------------------------------------------------
# Scaffold deferral contract — the fixtures are not finalists
# ---------------------------------------------------------------------------

def test_scaffold_note_documents_deferral():
    """The scaffold must self-document that the ten fixtures are not finalists."""
    import lab.phase2_edge_survival_scaffold as mod
    doc = mod.__doc__ or ""
    assert "finalist" in doc.lower()
    assert "retrofit" in doc.lower() or "scaffold" in doc.lower()
