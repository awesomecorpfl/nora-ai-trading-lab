"""Strict filesystem ingestion for returned Phase-2Y V1 packages."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

from .phase2x_batch import load
from .phase2y_return_contract import VERSION, validate

MANIFEST_NAME = "returned_result_manifest.json"
PRECEDENCE = ("FAIL_CONTRACT", "FAIL_IDENTITY", "FAIL_COMPILE", "FAIL_INTERRUPTED", "FAIL_INCOMPLETE", "FAIL_RUNTIME")


def _fail(classification, reason):
    return {"accepted": False, "classification": classification, "reasons": [reason], "synthetic_protocol_fixture": True}


def _resolved(root, relative):
    path = root / relative
    if path.is_symlink() or any(part.is_symlink() for part in path.parents if part != root.parent):
        raise ValueError("symlink")
    resolved = path.resolve(strict=True)
    resolved.relative_to(root)
    return resolved


def _parse_csv(path, schema):
    try:
        text = path.read_text(encoding=schema["encoding"])
        rows = list(csv.reader(text.splitlines(), delimiter=schema["delimiter"], strict=True))
    except Exception as exc:
        raise ValueError("malformed csv:" + str(exc)) from exc
    if not rows or rows[0] != schema["columns"]:
        raise ValueError("csv columns")
    output = []
    for values in rows[1:]:
        if len(values) != len(schema["columns"]):
            raise ValueError("csv width")
        item = {}
        for column, raw in zip(schema["columns"], values):
            if raw == schema["null_representation"]:
                if column not in schema["numeric_columns"]:
                    raise ValueError("invalid null token")
                item[column] = None
            elif raw == "" or raw != raw.strip():
                raise ValueError("invalid csv token")
            elif column == schema["row_identifier_column"]:
                try:
                    item[column] = int(raw)
                except ValueError as exc:
                    raise ValueError("row identifier") from exc
            elif column in schema["numeric_columns"]:
                try:
                    number = float(raw)
                except ValueError as exc:
                    raise ValueError("numeric token") from exc
                if not math.isfinite(number):
                    raise ValueError("nonfinite numeric")
                item[column] = number
            else:
                item[column] = raw
        output.append(item)
    if len(output) != schema["expected_row_count"]:
        raise ValueError("csv row count")
    return output


def ingest(directory, manifest_name=MANIFEST_NAME):
    """Verify a returned directory and create a normalized immutable result.

    No manifest claim is accepted until it is bound to an existing regular file,
    exact inventory member, size, hash, and declared CSV schema.
    """
    root = Path(directory).resolve()
    try:
        manifest_path = _resolved(root, manifest_name)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _fail("FAIL_CONTRACT", "manifest:" + str(exc))
    contract = validate(manifest)
    if not contract["valid"]:
        identity_only = contract["errors"] and all(error == "batch" or error == "vector identity" or error == "result filename" or error.startswith("identity:") for error in contract["errors"])
        if identity_only:
            return _fail("FAIL_IDENTITY", ";".join(contract["errors"]))
        return _fail("FAIL_CONTRACT", ";".join(contract["errors"]))
    batch = load()
    if manifest["batch_identity"] != batch["batch_identity"]:
        return _fail("FAIL_IDENTITY", "batch identity")
    inventory = {item["relative_path"]: item for item in manifest["files"]}
    try:
        actual = set()
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            if path.is_symlink():
                raise ValueError("symlink")
            actual.add(path.relative_to(root).as_posix())
        declared = set(inventory)
        allowed_actual = declared | {manifest_name}
        if actual != allowed_actual:
            raise ValueError("inventory missing or unexpected")
        for relative, item in inventory.items():
            path = _resolved(root, relative)
            if not path.is_file():
                raise ValueError("not regular file")
            data = path.read_bytes()
            if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError("file hash or size")
    except Exception as exc:
        return _fail("FAIL_CONTRACT", "filesystem:" + str(exc))

    normalized = {"returned_result_schema_version": manifest["schema_version"], "returned_package_semantic_identity": manifest["returned_package_semantic_identity"], "batch_identity": manifest["batch_identity"], "file_inventory_valid": True, "targets": {}, "synthetic_protocol_fixture": True}
    overall = None
    for target in batch["targets"]:
        source = next(item for item in manifest["targets"] if item["target_identifier"] == target["id"])
        identity_fields = ("rust_task_identity", "rust_component_identity", "expected_vector_identity", "runtime_identity", "tester_identity", "package_identity")
        if any(source.get(key) != (target["expected_vectors"]["expected_vector_identity"] if key == "expected_vector_identity" else target.get(key)) for key in identity_fields):
            classification, reason = "FAIL_IDENTITY", "target identity"
        elif not source["compiler"]["success"] or source["compiler"]["error_count"] or (source["compiler"]["warning_count"] and not source["compiler"].get("warnings_allowed", False)):
            classification, reason = "FAIL_COMPILE", "compiler"
        elif source["runtime"]["interrupted"] or manifest["interrupted"]:
            classification, reason = "FAIL_INTERRUPTED", "interrupted"
        elif source["runtime"]["timeout"] or source["runtime"]["incomplete"] or manifest["timeout"] or manifest["incomplete"]:
            classification, reason = "FAIL_INCOMPLETE", "timeout or incomplete"
        elif not source["runtime"]["success"] or source["runtime"]["failure_marker_observed"] or not source["runtime"]["completion_marker_observed"]:
            classification, reason = "FAIL_RUNTIME", "runtime"
        else:
            classification, reason = None, None
        try:
            csv_path = _resolved(root, source["runtime"]["result_csv_reference"])
            rows = _parse_csv(csv_path, source["csv_schema"])
        except Exception as exc:
            return _fail("FAIL_CONTRACT", "csv:" + str(exc))
        normalized["targets"][target["id"]] = {"classification": classification, "reasons": [] if reason is None else [reason], "rows": rows, "identities": {key: source[key] for key in identity_fields}, "compiler": source["compiler"], "runtime": source["runtime"], "references": {"compiler_log": source["compiler"]["log_reference"], "journal": source["runtime"]["journal_reference"], "report": source["runtime"]["report_reference"], "result": source["runtime"]["result_csv_reference"]}, "csv_schema": source["csv_schema"]}
        if classification and (overall is None or PRECEDENCE.index(classification) < PRECEDENCE.index(overall)):
            overall = classification
    normalized["classification"] = overall
    normalized["accepted"] = overall is None
    return normalized
