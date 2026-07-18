"""Deterministic planted-edge and scrambled-data integrity fixture."""
from __future__ import annotations

import random
from typing import Any

from lab.phase2_execution import sha

SCHEMA = "nora.phase2_placebo_edge_fixture_v1"
CANARY_SEED = 20260718
SCRAMBLE_SEED = 731
LENGTH = 256
EDGE_RETURN = 0.01
DESTRUCTION_THRESHOLD = 0.0025


def _signals() -> list[int]:
    rng = random.Random(CANARY_SEED)
    return [1 if rng.randrange(2) else -1 for _ in range(LENGTH)]


def _statistic(signals: list[int], returns: list[float]) -> float:
    if len(signals) != len(returns) or not signals:
        raise ValueError("placebo vectors must be non-empty and equal length")
    return sum(signal * value for signal, value in zip(signals, returns)) / len(signals)


def _build_without_identity() -> dict[str, Any]:
    signals = _signals()
    returns = [EDGE_RETURN * signal for signal in signals]
    scrambled_returns = returns.copy()
    random.Random(SCRAMBLE_SEED).shuffle(scrambled_returns)
    canary_statistic = _statistic(signals, returns)
    scrambled_statistic = _statistic(signals, scrambled_returns)
    destruction = {
        "absolute_reduction": canary_statistic - scrambled_statistic,
        "destroyed": scrambled_statistic < DESTRUCTION_THRESHOLD,
        "ratio_to_canary": scrambled_statistic / canary_statistic,
    }
    return {
        "schema_version": SCHEMA,
        "contract": {
            "canary_seed": CANARY_SEED,
            "scramble": "seeded_permutation_without_replacement",
            "scramble_seed": SCRAMBLE_SEED,
            "length": LENGTH,
            "edge_statistic": "mean_signal_aligned_return",
            "destruction_threshold": DESTRUCTION_THRESHOLD,
            "threshold_rule": "scrambled_statistic < destruction_threshold",
        },
        "canary": {
            "signals": signals,
            "returns": returns,
            "edge_statistic": canary_statistic,
            "data_identity": sha({"signals": signals, "returns": returns}),
        },
        "scrambled": {
            "signals": signals,
            "returns": scrambled_returns,
            "edge_statistic": scrambled_statistic,
            "data_identity": sha({"signals": signals, "returns": scrambled_returns}),
        },
        "destruction": destruction,
    }


def build_placebo_fixture() -> dict[str, Any]:
    value = _build_without_identity()
    value["fixture_identity"] = sha(value)
    return value


def verify_placebo_fixture(value: dict[str, Any]) -> bool:
    if not isinstance(value, dict):
        raise ValueError("placebo fixture must be an object")
    expected = build_placebo_fixture()
    if value != expected:
        raise ValueError("placebo fixture identity or contract mismatch")
    if not value["destruction"]["destroyed"]:
        raise ValueError("scrambled edge was not destroyed")
    return True
