"""Versioned empirical numeric-parity measurement for typed native targets."""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from lab.phase2_execution import sha

PROTOCOL_SCHEMA = "nora.numeric_parity_protocol_v1"
MEASUREMENT_SCHEMA = "nora.numeric_measurement_v1"
FAILURE_SCHEMA = "nora.numeric_parity_failure_v1"
EXACT_FIELDS = ("row_count", "timestamps", "scenario_order", "null_state", "warmup_boundary",
                "boolean_decisions", "output_presence", "output_names", "categorical_reason_codes",
                "invalid_input_classification")
FAILURES = ("ROW_COUNT_MISMATCH", "TIMESTAMP_MISMATCH", "SCENARIO_ORDER_MISMATCH",
            "NULL_MISMATCH", "WARMUP_MISMATCH", "OUTPUT_MISSING", "OUTPUT_REORDERED",
            "REASON_CODE_MISMATCH", "INVALID_INPUT_MISMATCH", "NONFINITE_VALUE",
            "NUMERIC_BUDGET_EXCEEDED", "NODE_IDENTITY_MISMATCH", "REFERENCE_MODE_MISMATCH",
            "CROSS_TARGET_EVIDENCE", "COMPILER_FAILURE", "MARKER_FAILURE")


def protocol() -> dict:
    value = {"schema_version": PROTOCOL_SCHEMA, "measurement_schema": MEASUREMENT_SCHEMA,
             "exact_fields": list(EXACT_FIELDS), "numeric_fields": ["rust_value", "mql5_value",
             "absolute_error", "relative_error", "ulp_distance", "maximum_error",
             "percentile_error_summary", "first_divergence", "phase"],
             "budget_scope": "per_node_and_output", "native_policy": "observe_then_propose_then_explicitly_accept",
             "exact_match_classification": "PASS_EXACT", "provisional_budget_reuse": False}
    value["parity_protocol_identity"] = sha(value)
    return value


def failure_vocabulary() -> dict:
    value = {"schema_version": FAILURE_SCHEMA, "codes": list(FAILURES)}
    value["failure_vocabulary_identity"] = sha(value)
    return value


def budget_identity(budgets: dict) -> str:
    return sha({"schema_version": "nora.numeric_budget_v1", "budgets": budgets})


def _ordered(value: float) -> int:
    bits = struct.unpack(">q", struct.pack(">d", value))[0]
    return 0x8000000000000000 - bits if bits < 0 else bits


def ulp_distance(left: float, right: float) -> int:
    return abs(_ordered(left) - _ordered(right))


def measure(rust: list[float], mql5: list[float], phases: list[str]) -> dict:
    if not (len(rust) == len(mql5) == len(phases)): raise ValueError("ROW_COUNT_MISMATCH")
    points = []
    for index, (left, right, phase) in enumerate(zip(rust, mql5, phases)):
        if not math.isfinite(left) or not math.isfinite(right): raise ValueError("NONFINITE_VALUE")
        absolute = abs(left-right); relative = absolute/max(abs(left), abs(right), 1e-300)
        points.append({"row": index, "rust_value": left, "mql5_value": right,
                       "absolute_error": absolute, "relative_error": relative,
                       "ulp_distance": ulp_distance(left, right), "phase": phase})
    absolute = sorted(x["absolute_error"] for x in points)
    relative = sorted(x["relative_error"] for x in points)
    def pct(values, q):
        if not values: return 0.0
        return values[min(len(values)-1, math.ceil(q*len(values))-1)]
    result = {"schema_version": MEASUREMENT_SCHEMA, "points": points,
              "maximum_error": {"absolute": max(absolute, default=0.0), "relative": max(relative, default=0.0),
                                "ulp": max((x["ulp_distance"] for x in points), default=0)},
              "percentile_error_summary": {"p50_absolute": pct(absolute,.5), "p95_absolute": pct(absolute,.95),
                                             "p99_absolute": pct(absolute,.99), "p95_relative": pct(relative,.95)},
              "first_divergence": next((x for x in points if x["absolute_error"] != 0.0), None),
              "exact": all(x["absolute_error"] == 0.0 for x in points)}
    result["numeric_measurement_identity"] = sha(result)
    return result


def within_budget(measurement: dict, budget: dict) -> bool:
    return all(point["absolute_error"] <= budget["absolute"] + budget["relative"] * abs(point["rust_value"])
               and point["ulp_distance"] <= budget["ulp"] for point in measurement["points"])
