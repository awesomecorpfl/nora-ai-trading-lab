"""Versioned, filesystem-neutral returned-result package contract (Phase-2Y)."""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath

from .phase2x_batch import canon, load

VERSION = "nora.phase2y.returned_package_v1"
ROLES = {"manifest", "compiler_log", "runtime_journal", "tester_report", "result_csv"}


def semantic(value):
    """Repository-standard content identity for a JSON value."""
    return hashlib.sha256(canon(value)).hexdigest()


def returned_package_identity(manifest):
    value = dict(manifest)
    value.pop("returned_package_semantic_identity", None)
    return semantic(value)


def _path_ok(value):
    return isinstance(value, str) and bool(value) and not PurePosixPath(value).is_absolute() and ".." not in PurePosixPath(value).parts


def _error(errors, value):
    if value not in errors:
        errors.append(value)


def validate(manifest):
    """Validate all V1 claims without trusting an on-disk package.

    Filesystem verification belongs to :mod:`phase2y_ingest`; this function
    deliberately validates only the complete manifest schema and its internal
    bindings.
    """
    batch = load()
    errors = []
    if not isinstance(manifest, dict):
        return {"valid": False, "errors": ["manifest type"], "synthetic_protocol_fixture": True}
    required = ("schema_version", "batch_identity", "run_identifier", "declared_target_count", "targets",
                "batch_completion_state", "interrupted", "timeout", "incomplete", "returned_package_semantic_identity", "files")
    for key in required:
        if key not in manifest:
            _error(errors, "missing:" + key)
    if manifest.get("schema_version") != VERSION:
        _error(errors, "schema")
    if manifest.get("batch_identity") != batch["batch_identity"]:
        _error(errors, "batch")
    if not isinstance(manifest.get("run_identifier"), str) or not manifest.get("run_identifier"):
        _error(errors, "run identifier")
    targets = manifest.get("targets")
    files = manifest.get("files")
    if not isinstance(targets, list):
        targets = []
        _error(errors, "targets type")
    if not isinstance(files, list):
        files = []
        _error(errors, "files type")
    if manifest.get("declared_target_count") != len(targets):
        _error(errors, "target count")
    expected = {target["id"]: target for target in batch["targets"]}
    ids = [target.get("target_identifier") if isinstance(target, dict) else None for target in targets]
    if len(ids) != len(set(ids)):
        _error(errors, "duplicate target")
    if set(ids) != set(expected):
        _error(errors, "missing or unknown target")
    if manifest.get("batch_completion_state") not in {"completed", "failed", "interrupted", "incomplete"}:
        _error(errors, "batch completion state")
    for key in ("interrupted", "timeout", "incomplete"):
        if not isinstance(manifest.get(key), bool):
            _error(errors, "state type:" + key)
    if manifest.get("batch_completion_state") == "completed" and any(manifest.get(k) for k in ("interrupted", "timeout", "incomplete")):
        _error(errors, "completed batch state conflict")
    if manifest.get("returned_package_semantic_identity") != returned_package_identity(manifest):
        _error(errors, "returned package identity")

    seen_result_names = set()
    references = {}
    for target in targets:
        if not isinstance(target, dict):
            _error(errors, "target type")
            continue
        ident = target.get("target_identifier")
        frozen = expected.get(ident)
        if not frozen:
            _error(errors, "unknown target")
            continue
        identity_fields = ("rust_task_identity", "rust_component_identity", "runtime_identity", "tester_identity", "package_identity")
        for key in identity_fields:
            if target.get(key) != frozen.get(key):
                _error(errors, "identity:" + key)
        if target.get("expected_vector_identity") != frozen["expected_vectors"]["expected_vector_identity"]:
            _error(errors, "vector identity")
        if target.get("expected_result_filename") != frozen["result_filename"] or target.get("actual_result_filename") != frozen["result_filename"]:
            _error(errors, "result filename")
        name = target.get("actual_result_filename")
        if name in seen_result_names:
            _error(errors, "duplicate result filename")
        seen_result_names.add(name)
        compiler = target.get("compiler")
        runtime = target.get("runtime")
        schema = target.get("csv_schema")
        if not isinstance(compiler, dict):
            _error(errors, "compiler record")
        else:
            for key in ("invoked", "exit_status", "success", "warnings", "warning_count", "errors", "error_count", "log_reference"):
                if key not in compiler:
                    _error(errors, "missing compiler:" + key)
            if not isinstance(compiler.get("invoked"), bool) or not isinstance(compiler.get("success"), bool) or not isinstance(compiler.get("exit_status"), int):
                _error(errors, "compiler state")
            if compiler.get("success") and compiler.get("exit_status") != 0:
                _error(errors, "compiler success exit conflict")
            if compiler.get("success") and compiler.get("errors"):
                _error(errors, "compiler success errors conflict")
            if compiler.get("warning_count") != len(compiler.get("warnings", [])):
                _error(errors, "warning count")
            if compiler.get("error_count") != len(compiler.get("errors", [])):
                _error(errors, "error count")
        if not isinstance(runtime, dict):
            _error(errors, "runtime record")
        else:
            for key in ("invoked", "completion_status", "success", "interrupted", "timeout", "incomplete", "completion_marker_observed", "failure_marker_observed", "journal_reference", "report_reference", "result_csv_reference"):
                if key not in runtime:
                    _error(errors, "missing runtime:" + key)
            if runtime.get("completion_marker_observed") and runtime.get("failure_marker_observed"):
                _error(errors, "conflicting runtime markers")
            if runtime.get("success") and (runtime.get("interrupted") or runtime.get("timeout") or runtime.get("incomplete") or runtime.get("failure_marker_observed")):
                _error(errors, "runtime success conflict")
        if not isinstance(schema, dict):
            _error(errors, "csv schema")
        else:
            for key in ("encoding", "delimiter", "header_required", "columns", "row_identifier_column", "numeric_columns", "null_representation", "expected_row_count", "target_binding"):
                if key not in schema:
                    _error(errors, "missing csv:" + key)
            vectors = frozen["expected_vectors"]
            if schema.get("columns") != vectors["columns"] or schema.get("row_identifier_column") != "row" or schema.get("expected_row_count") != vectors["row_count"] or schema.get("target_binding") != ident:
                _error(errors, "csv binding")
            if not schema.get("header_required") or not isinstance(schema.get("delimiter"), str) or not isinstance(schema.get("encoding"), str):
                _error(errors, "csv format")
        if isinstance(compiler, dict):
            references[compiler.get("log_reference")] = (ident, "compiler_log")
        if isinstance(runtime, dict):
            references[runtime.get("journal_reference")] = (ident, "runtime_journal")
            references[runtime.get("report_reference")] = (ident, "tester_report")
            references[runtime.get("result_csv_reference")] = (ident, "result_csv")

    paths = set()
    inventory = {}
    for item in files:
        if not isinstance(item, dict):
            _error(errors, "file record")
            continue
        path = item.get("relative_path")
        if not _path_ok(path):
            _error(errors, "path")
        if path in paths:
            _error(errors, "duplicate path")
        paths.add(path)
        if item.get("role") not in ROLES:
            _error(errors, "unknown role")
        if not isinstance(item.get("required"), bool) or not isinstance(item.get("size"), int) or item.get("size", -1) < 0 or not isinstance(item.get("sha256"), str) or len(item.get("sha256", "")) != 64:
            _error(errors, "file metadata")
        inventory[path] = item
        binding = item.get("target_binding")
        if binding is not None and binding not in expected:
            _error(errors, "file target binding")
    for path, (ident, role) in references.items():
        item = inventory.get(path)
        if not _path_ok(path) or not item or item.get("role") != role or item.get("target_binding") != ident:
            _error(errors, "reference inventory binding")
    return {"valid": not errors, "errors": errors, "returned_package_semantic_identity": returned_package_identity(manifest), "synthetic_protocol_fixture": True}
