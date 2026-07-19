"""Scaffolding for the broker-native edge-survival gate.

This module is intentionally process scaffolding, not a live validation engine.
The real edge-survival gate (``docs/phase2_broker_native_edge_survival.md``)
requires three inputs that do not exist yet for the ten system-test fixtures:

  1. a selected finalist strategy with a genuine edge claim;
  2. frozen Python/Rust reference metrics for that finalist;
  3. a pre-frozen, human-gated budget map for every similarity metric.

None of the ten fixtures are finalists. Promoting a fixture to finalist status
to run this gate would manufacture a fake edge claim and destroy the credibility
of the survival result. This scaffolding exists so that when a real finalist
arrives (from authorized research, after Phase-3 unfreeze), the gate is already
built, tested, and impossible to retrofit around.

Three primitives are provided:

  ``freeze_reference_metrics`` — freeze the Python/Rust reference metrics for a
  finalist into a tamper-evident artifact with an identity hash. The frozen
  reference must exist before the native result is inspected.

  ``freeze_similarity_budget`` — record the human-gate budget decision as a
  signed artifact with identity, timestamp, and gate-authority field. The
  budget map must be complete, non-negative, and frozen before the native
  result is inspected.

  ``bind_native_provenance`` — bind the broker-native provenance (symbol,
  server, timeframe, date range, timezone, spread, commission, slippage,
  source) into a single identity that the similarity report must carry.

Every primitive fails closed on missing fields, partial inputs, post-result
freezing, identity substitution, and ambiguous provenance. The scaffolding is
deliberately unusable for retrofitting: the similarity report constructor
(``assemble_edge_survival_report``) refuses to run if the reference or budget
was frozen after the native result, and refuses any budget that does not cover
every metric.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from lab.phase2_native_similarity import METRICS, build_similarity_report, validate_budget_map

SCHEMA = "nora.phase2_edge_survival_scaffold_v1"
REFERENCE_SCHEMA = "nora.phase2_edge_survival_reference_v1"
BUDGET_SCHEMA = "nora.phase2_edge_survival_budget_freeze_v1"
PROVENANCE_SCHEMA = "nora.phase2_edge_survival_native_provenance_v1"
REPORT_SCHEMA = "nora.phase2_edge_survival_report_v1"

REQUIRED_PROVENANCE_FIELDS = (
    "symbol",
    "server_identity",
    "timeframe",
    "date_range_start",
    "date_range_end",
    "timezone_identity",
    "spread_model",
    "commission_model",
    "slippage_model",
    "source_identity",
)


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} must be a non-empty object")
    return value


def _require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _require_iso_timestamp(value: Any, label: str) -> str:
    s = _require_str(value, label)
    # Accept ISO 8601 with or without timezone offset; refuse garbage.
    datetime.fromisoformat(s.replace("Z", "+00:00"))
    return s


def freeze_reference_metrics(
    *,
    finalist_identity: str,
    metrics: dict[str, Any],
    edge_survives: bool,
    reference_runner_identity: str,
    frozen_at: str | None = None,
) -> dict[str, Any]:
    """Freeze the Python/Rust reference metrics for a finalist.

    The frozen artifact carries an identity hash that binds the finalist, the
    metrics, the edge-survives flag, and the reference-runner identity. This
    artifact must be created before the native result is inspected.

    ``metrics`` must contain every metric in ``METRICS`` as a number. The
    ``edge_survives`` flag is the reference's own claim about whether its edge
    survives its own execution path — it is not the native verdict.
    """
    _require_str(finalist_identity, "finalist_identity")
    _require_str(reference_runner_identity, "reference_runner_identity")
    if not isinstance(edge_survives, bool):
        raise ValueError("edge_survives must be boolean")
    metrics = _require_dict(metrics, "metrics")
    missing = set(METRICS) - set(metrics)
    if missing:
        raise ValueError(f"reference metrics missing: {sorted(missing)}")
    normalized: dict[str, float] = {}
    for field in METRICS:
        normalized[field] = _require_number(metrics[field], f"metrics.{field}")

    body = {
        "schema_version": REFERENCE_SCHEMA,
        "finalist_identity": finalist_identity,
        "metrics": normalized,
        "edge_survives": edge_survives,
        "reference_runner_identity": reference_runner_identity,
        "frozen_at": _require_iso_timestamp(frozen_at or _now(), "frozen_at"),
    }
    body["reference_identity"] = _sha(
        {
            "finalist_identity": finalist_identity,
            "metrics": normalized,
            "edge_survives": edge_survives,
            "reference_runner_identity": reference_runner_identity,
        }
    )
    return body


def freeze_similarity_budget(
    *,
    finalist_identity: str,
    reference_identity: str,
    budgets: dict[str, dict[str, float]],
    gate_authority: str,
    edge_survives_definition: str,
    native_cost_included: bool,
    frozen_at: str | None = None,
) -> dict[str, Any]:
    """Record the human-gate budget decision as a tamper-evident artifact.

    The budget map is validated by ``validate_budget_map`` (complete coverage
    of every metric, non-negative tolerances). ``edge_survives_definition``
    must be a non-empty human-language statement of what "edge survives"
    means for this finalist. ``gate_authority`` records who decided.
    """
    _require_str(finalist_identity, "finalist_identity")
    _require_str(reference_identity, "reference_identity")
    _require_str(gate_authority, "gate_authority")
    _require_str(edge_survives_definition, "edge_survives_definition")
    if not isinstance(native_cost_included, bool):
        raise ValueError("native_cost_included must be boolean")
    normalized = validate_budget_map(budgets)

    body = {
        "schema_version": BUDGET_SCHEMA,
        "finalist_identity": finalist_identity,
        "reference_identity": reference_identity,
        "budget_map": normalized,
        "gate_authority": gate_authority,
        "edge_survives_definition": edge_survives_definition,
        "native_cost_included": native_cost_included,
        "frozen_at": _require_iso_timestamp(frozen_at or _now(), "frozen_at"),
    }
    body["budget_freeze_identity"] = _sha(
        {
            "finalist_identity": finalist_identity,
            "reference_identity": reference_identity,
            "budget_map": normalized,
            "edge_survives_definition": edge_survives_definition,
            "native_cost_included": native_cost_included,
        }
    )
    return body


def bind_native_provenance(provenance: dict[str, Any]) -> dict[str, Any]:
    """Bind broker-native provenance into a tamper-evident artifact.

    Every field in ``REQUIRED_PROVENANCE_FIELDS`` must be present and non-empty.
    The resulting ``provenance_identity`` must be carried by the similarity
    report; any substitution fails the report.
    """
    provenance = _require_dict(provenance, "provenance")
    missing = [f for f in REQUIRED_PROVENANCE_FIELDS if f not in provenance]
    if missing:
        raise ValueError(f"provenance missing required fields: {missing}")
    for field in REQUIRED_PROVENANCE_FIELDS:
        _require_str(provenance[field], f"provenance.{field}")
    normalized = {field: provenance[field] for field in REQUIRED_PROVENANCE_FIELDS}

    body = {
        "schema_version": PROVENANCE_SCHEMA,
        "provenance": normalized,
    }
    body["provenance_identity"] = _sha(normalized)
    return body


def assemble_edge_survival_report(
    *,
    reference: dict[str, Any],
    budget_freeze: dict[str, Any],
    native_provenance: dict[str, Any],
    native_metrics: dict[str, Any],
    native_observed_at: str,
) -> dict[str, Any]:
    """Assemble the full edge-survival report.

    This refuses to run if:
      - the reference was frozen after the native result was observed;
      - the budget was frozen after the native result was observed;
      - the budget's ``reference_identity`` does not match the frozen reference;
      - any required field is missing or malformed.

    The underlying similarity comparison is delegated to
    ``lab.phase2_native_similarity.build_similarity_report``. The scaffold
    wraps it with the freeze-order and provenance invariants.
    """
    if reference.get("schema_version") != REFERENCE_SCHEMA:
        raise ValueError("reference must be a frozen reference artifact")
    if budget_freeze.get("schema_version") != BUDGET_SCHEMA:
        raise ValueError("budget_freeze must be a frozen budget artifact")
    if native_provenance.get("schema_version") != PROVENANCE_SCHEMA:
        raise ValueError("native_provenance must be a bound provenance artifact")

    native_ts = _require_iso_timestamp(native_observed_at, "native_observed_at")
    ref_ts = _require_iso_timestamp(reference["frozen_at"], "reference.frozen_at")
    budget_ts = _require_iso_timestamp(budget_freeze["frozen_at"], "budget_freeze.frozen_at")

    # Freeze-order invariant: reference and budget must precede native observation.
    ref_dt = datetime.fromisoformat(ref_ts.replace("Z", "+00:00"))
    budget_dt = datetime.fromisoformat(budget_ts.replace("Z", "+00:00"))
    native_dt = datetime.fromisoformat(native_ts.replace("Z", "+00:00"))
    if ref_dt >= native_dt:
        raise ValueError("reference must be frozen before native observation")
    if budget_dt >= native_dt:
        raise ValueError("budget must be frozen before native observation")

    # Budget must bind the exact reference it applies to.
    if budget_freeze["reference_identity"] != reference["reference_identity"]:
        raise ValueError("budget freeze does not bind this reference")

    # Native metrics must include edge_survives and all METRICS.
    native_metrics = _require_dict(native_metrics, "native_metrics")
    if not isinstance(native_metrics.get("edge_survives"), bool):
        raise ValueError("native_metrics.edge_survives must be boolean")
    missing = set(METRICS) - set(native_metrics)
    if missing:
        raise ValueError(f"native_metrics missing: {sorted(missing)}")

    similarity = build_similarity_report(
        reference={
            **reference["metrics"],
            "edge_survives": reference["edge_survives"],
        },
        native=native_metrics,
        budgets=budget_freeze["budget_map"],
        provenance=native_provenance["provenance"],
    )

    report = {
        "schema_version": REPORT_SCHEMA,
        "finalist_identity": reference["finalist_identity"],
        "reference_identity": reference["reference_identity"],
        "budget_freeze_identity": budget_freeze["budget_freeze_identity"],
        "provenance_identity": native_provenance["provenance_identity"],
        "reference_frozen_at": ref_ts,
        "budget_frozen_at": budget_ts,
        "native_observed_at": native_ts,
        "native_cost_included": budget_freeze["native_cost_included"],
        "edge_survives_definition": budget_freeze["edge_survives_definition"],
        "similarity": similarity,
        "edge_survival_accepted": similarity["edge_survival_accepted"],
        "native_parity_accepted": False,
        "searchable": False,
        "scaffold_note": (
            "Assembled by the edge-survival scaffold. The ten system-test "
            "fixtures are not finalists; this report is only meaningful for a "
            "genuine finalist produced by authorized research."
        ),
    }
    report["report_identity"] = _sha(
        {
            "finalist_identity": report["finalist_identity"],
            "reference_identity": report["reference_identity"],
            "budget_freeze_identity": report["budget_freeze_identity"],
            "provenance_identity": report["provenance_identity"],
            "similarity_report_identity": similarity["similarity_report_identity"],
        }
    )
    return report
