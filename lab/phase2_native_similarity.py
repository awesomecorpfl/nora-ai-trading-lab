"""Similarity-based broker-native validation for the ten-strategy suite.

This is deliberately separate from the embedded-fixture exact canary. The native
broker path may differ from Python/Rust because of source data, timezone, spread,
slippage, bar construction, and tester semantics. Acceptance therefore requires an
explicit pre-frozen budget map and edge-survival verdict, never trade-for-trade
identity.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "nora.phase2_broker_native_similarity_v1"
METRICS = (
    "trade_count",
    "gross_pnl",
    "net_pnl",
    "profit_factor",
    "max_drawdown",
    "win_rate",
    "average_trade",
)


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


def validate_budget_map(budgets: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    if not isinstance(budgets, dict) or set(budgets) != set(METRICS):
        raise ValueError("budget map must explicitly cover every native similarity metric")
    normalized: dict[str, dict[str, float]] = {}
    for metric in METRICS:
        budget = budgets[metric]
        if not isinstance(budget, dict):
            raise ValueError(f"budget for {metric} must be an object")
        keys = set(budget)
        if keys not in ({"max_abs_delta"}, {"max_relative_delta"}, {"max_abs_delta", "max_relative_delta"}):
            raise ValueError(f"budget for {metric} must declare absolute and/or relative tolerance")
        normalized[metric] = {}
        for key, value in budget.items():
            value = _number(value, f"{metric}.{key}")
            if value < 0:
                raise ValueError(f"{metric}.{key} must be non-negative")
            normalized[metric][key] = value
    return normalized


def _validate_metrics(metrics: dict[str, Any], label: str) -> None:
    if not isinstance(metrics, dict) or set(METRICS) - set(metrics):
        raise ValueError(f"{label} must contain all native similarity metrics")
    for field in METRICS:
        _number(metrics[field], f"{label}.{field}")
    if not isinstance(metrics.get("edge_survives"), bool):
        raise ValueError(f"{label}.edge_survives must be boolean")


def compare_metrics(reference: dict[str, Any], native: dict[str, Any], budgets: dict[str, dict[str, float]]) -> dict[str, Any]:
    _validate_metrics(reference, "reference")
    _validate_metrics(native, "native")
    budgets = validate_budget_map(budgets)
    comparisons = {}
    passed = True
    for metric in METRICS:
        expected = _number(reference[metric], f"reference.{metric}")
        observed = _number(native[metric], f"native.{metric}")
        absolute_delta = abs(observed - expected)
        relative_delta = absolute_delta / max(abs(expected), 1e-12)
        budget = budgets[metric]
        checks = []
        if "max_abs_delta" in budget:
            checks.append(absolute_delta <= budget["max_abs_delta"])
        if "max_relative_delta" in budget:
            checks.append(relative_delta <= budget["max_relative_delta"])
        metric_passed = all(checks)
        passed = passed and metric_passed
        comparisons[metric] = {
            "reference": expected,
            "native": observed,
            "absolute_delta": absolute_delta,
            "relative_delta": relative_delta,
            "budget": budget,
            "passed": metric_passed,
        }
    edge_survives = reference["edge_survives"] and native["edge_survives"]
    return {
        "schema_version": SCHEMA,
        "comparison_mode": "similarity_not_exact_parity",
        "metrics": comparisons,
        "reference_edge_survives": reference["edge_survives"],
        "native_edge_survives": native["edge_survives"],
        "edge_survives": edge_survives,
        "passed": passed and edge_survives,
        "budget_map": budgets,
    }


def build_similarity_report(*, reference: dict[str, Any], native: dict[str, Any], budgets: dict[str, dict[str, float]],
                            provenance: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError("native similarity provenance is required")
    result = compare_metrics(reference, native, budgets)
    body = {
        "schema_version": SCHEMA,
        "validation_mode": "broker_native_edge_survival",
        "comparison_mode": result.pop("comparison_mode"),
        "provenance": provenance,
        "reference": reference,
        "native": native,
        "comparison": result,
        "edge_survival_accepted": result["passed"],
        "native_parity_accepted": False,
        "searchable": False,
    }
    body["similarity_report_identity"] = _sha(body)
    return body
