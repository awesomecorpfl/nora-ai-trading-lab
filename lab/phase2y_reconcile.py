"""Fixed-vector reconciliation over a strictly ingested returned package."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

from .phase2x_batch import canon, load
from .phase2y_ingest import ingest

VERSION = "nora.phase2y.reconcile_v2"
TOL = "abs(actual-expected) <= 1e-12 + 1e-9*abs(expected)"
PRECEDENCE = ("FAIL_CONTRACT", "FAIL_IDENTITY", "FAIL_COMPILE", "FAIL_INTERRUPTED", "FAIL_INCOMPLETE", "FAIL_RUNTIME", "FAIL_ROW_ALIGNMENT", "FAIL_NULL_ALIGNMENT", "FAIL_VALUE_MISMATCH", "PASS_WITHIN_TOLERANCE", "PASS_EXACT")


def _rank(classification):
    return PRECEDENCE.index(classification)


def _ingested(value):
    return value if isinstance(value, dict) and "returned_result_schema_version" in value else ingest(value)


def _target_reconcile(target, received):
    if received["classification"]:
        return {"id": target["id"], "classification": received["classification"], "ordered_reasons": received["reasons"], "field_maximum_errors": {}, "structural_validation": False}
    expected_vectors = target["expected_vectors"]
    rows = received["rows"]
    if len(rows) != expected_vectors["row_count"] or [row.get("row") for row in rows] != expected_vectors["rows"]:
        return {"id": target["id"], "classification": "FAIL_ROW_ALIGNMENT", "ordered_reasons": ["row identifiers"], "field_maximum_errors": {}, "structural_validation": False}
    fields = [field for field in expected_vectors["vectors"] if field not in ("row", "close", "source", "null_masks")]
    reasons = []
    maxima = {}
    classification = "PASS_EXACT"
    for field in fields:
        expected = expected_vectors["vectors"][field]
        actual = [row.get(field) for row in rows]
        if [value is None for value in actual] != expected_vectors["vectors"]["null_masks"][field]:
            classification = "FAIL_NULL_ALIGNMENT"
            reasons.append(field + ": null alignment")
            continue
        measurements = []
        for row_index, (actual_value, expected_value) in enumerate(zip(actual, expected)):
            if expected_value is None:
                continue
            if not isinstance(actual_value, (int, float)) or not math.isfinite(actual_value):
                return {"id": target["id"], "classification": "FAIL_CONTRACT", "ordered_reasons": [field + ": nonfinite or nonnumeric"], "field_maximum_errors": maxima, "structural_validation": False}
            absolute = abs(actual_value - expected_value)
            relative = absolute / max(abs(expected_value), 1e-15)
            measurements.append({"row": row_index, "expected": expected_value, "actual": actual_value, "absolute_error": absolute, "relative_error": relative})
            if absolute > 1e-12 + 1e-9 * abs(expected_value):
                classification = "FAIL_VALUE_MISMATCH"
            elif absolute and classification == "PASS_EXACT":
                classification = "PASS_WITHIN_TOLERANCE"
        if measurements:
            maxima[field] = {"maximum_absolute": max(measurements, key=lambda item: (item["absolute_error"], item["row"])), "maximum_relative": max(measurements, key=lambda item: (item["relative_error"], item["row"]))}
        if classification == "FAIL_VALUE_MISMATCH":
            reasons.append(field + ": tolerance")
    if any(reason.endswith("null alignment") for reason in reasons):
        classification = "FAIL_NULL_ALIGNMENT"
    return {"id": target["id"], "classification": classification, "ordered_reasons": reasons, "field_maximum_errors": maxima, "structural_validation": not classification.startswith("FAIL_")}


def reconcile(value):
    """Reconcile an ingested value or a returned-directory path; never mutate state."""
    received = _ingested(value)
    base = {"protocol_version": VERSION, "numeric_policy": {"formula": TOL, "relative_denominator": "max(abs(expected), 1e-15)"}, "native_parity_updated": False, "synthetic_protocol_fixture": received.get("synthetic_protocol_fixture", False)}
    if not received.get("accepted"):
        base.update({"classification": received["classification"], "ordered_reasons": received["reasons"], "targets": [], "returned_result_identity": hashlib.sha256(canon(received)).hexdigest()})
        return base
    batch = load()
    targets = [_target_reconcile(target, received["targets"][target["id"]]) for target in batch["targets"]]
    overall = min((target["classification"] for target in targets), key=_rank)
    base.update({"batch_identity": received["batch_identity"], "returned_result_schema_version": received["returned_result_schema_version"], "returned_package_semantic_identity": received["returned_package_semantic_identity"], "file_inventory_validation": received["file_inventory_valid"], "targets": targets, "classification": overall, "ordered_reasons": [reason for target in targets for reason in target["ordered_reasons"]], "returned_result_identity": hashlib.sha256(canon(received)).hexdigest()})
    return base


def publish(value, destination, fail_publish=False):
    """Atomically publish immutable reconciliation evidence, refusing overwrite."""
    out = Path(destination)
    if out.exists():
        raise ValueError("existing reconciliation evidence")
    evidence = reconcile(value)
    tmp = out.with_suffix(".tmp")
    try:
        tmp.write_bytes(canon(evidence) + b"\n")
        if fail_publish:
            raise RuntimeError("injected reconciliation publication failure")
        tmp.replace(out)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return evidence
