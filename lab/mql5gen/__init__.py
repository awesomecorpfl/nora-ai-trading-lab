"""Deterministic MQL5 nullable-semantics runtime generation for Phase 2F."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

RUNTIME_VERSION = "nora_mql5_nullable_runtime_v1"
SOURCE_FILENAME = "NoraPhase2RuntimeV1.mqh"
MANIFEST_FILENAME = "NoraPhase2RuntimeV1.manifest.json"
IDENTITY_DOMAIN = "nora.mql5.runtime.nullable_semantics_v1.semantic.v1"
SUPPORTED_AST_NODES = ["numeric_series", "number", "boolean_series", "compare", "and", "or", "not"]
SUPPORTED_OPERATORS = ["gt", "gte", "lt", "lte", "and", "or", "not"]
TRI_VALUES = ["null", "false", "true"]

NOT_TABLE = {"null": "null", "false": "true", "true": "false"}
AND_TABLE = {
    "null": {"null": "null", "false": "false", "true": "null"},
    "false": {"null": "false", "false": "false", "true": "false"},
    "true": {"null": "null", "false": "false", "true": "true"},
}
OR_TABLE = {
    "null": {"null": "null", "false": "null", "true": "true"},
    "false": {"null": "null", "false": "false", "true": "true"},
    "true": {"null": "true", "false": "true", "true": "true"},
}
COMPARISON_CASES = [[2.0, 1.0], [1.0, 2.0], [None, 1.0], [1.0, None], [None, None]]
COMPARISON_TABLES = {
    "gt": ["true", "false", "null", "null", "null"],
    "gte": ["true", "false", "null", "null", "null"],
    "lt": ["false", "true", "null", "null", "null"],
    "lte": ["false", "true", "null", "null", "null"],
}
TRIGGER_TABLE = {"null": False, "false": False, "true": True}

_TYPE_DEFINITIONS = """enum NoraTriBoolV1 { NORA_BOOL_NULL_V1 = -1, NORA_BOOL_FALSE_V1 = 0, NORA_BOOL_TRUE_V1 = 1 }; struct NoraNullableDoubleV1 { bool is_null; double value; };"""
_SEMANTIC_TABLES = json.dumps(
    {"not": NOT_TABLE, "and": AND_TABLE, "or": OR_TABLE, "comparisons": COMPARISON_TABLES, "trigger": TRIGGER_TABLE},
    sort_keys=True, separators=(",", ":"),
)

_SOURCE = """#ifndef NORA_PHASE2_RUNTIME_V1_MQH
#define NORA_PHASE2_RUNTIME_V1_MQH

enum NoraTriBoolV1
{
   NORA_BOOL_NULL_V1  = -1,
   NORA_BOOL_FALSE_V1 = 0,
   NORA_BOOL_TRUE_V1  = 1
};

struct NoraNullableDoubleV1
{
   bool   is_null;
   double value;
};

NoraTriBoolV1 NoraBoolNullV1()
{
   return NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraBoolFalseV1()
{
   return NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraBoolTrueV1()
{
   return NORA_BOOL_TRUE_V1;
}

bool NoraBoolIsNullV1(const NoraTriBoolV1 input)
{
   return input == NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraBoolGetValueV1(const NoraTriBoolV1 input)
{
   return input;
}

NoraNullableDoubleV1 NoraNumericNullV1()
{
   NoraNullableDoubleV1 result;
   result.is_null = true;
   result.value = 0.0;
   return result;
}

NoraNullableDoubleV1 NoraNumericValueV1(const double input)
{
   NoraNullableDoubleV1 result;
   result.is_null = false;
   result.value = input;
   return result;
}

bool NoraNumericIsNullV1(const NoraNullableDoubleV1 &input)
{
   return input.is_null;
}

bool NoraNumericTryGetValueV1(const NoraNullableDoubleV1 &input, double &output)
{
   if(input.is_null)
      return false;
   output = input.value;
   return true;
}

NoraTriBoolV1 NoraBoolNotV1(const NoraTriBoolV1 input)
{
   if(input == NORA_BOOL_NULL_V1)
      return NORA_BOOL_NULL_V1;
   if(input == NORA_BOOL_TRUE_V1)
      return NORA_BOOL_FALSE_V1;
   return NORA_BOOL_TRUE_V1;
}

NoraTriBoolV1 NoraBoolAndV1(const NoraTriBoolV1 left, const NoraTriBoolV1 right)
{
   if(left == NORA_BOOL_FALSE_V1 || right == NORA_BOOL_FALSE_V1)
      return NORA_BOOL_FALSE_V1;
   if(left == NORA_BOOL_TRUE_V1 && right == NORA_BOOL_TRUE_V1)
      return NORA_BOOL_TRUE_V1;
   return NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraBoolOrV1(const NoraTriBoolV1 left, const NoraTriBoolV1 right)
{
   if(left == NORA_BOOL_TRUE_V1 || right == NORA_BOOL_TRUE_V1)
      return NORA_BOOL_TRUE_V1;
   if(left == NORA_BOOL_FALSE_V1 && right == NORA_BOOL_FALSE_V1)
      return NORA_BOOL_FALSE_V1;
   return NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraCompareGtV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value > right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCompareGteV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value >= right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCompareLtV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value < right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCompareLteV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value <= right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

bool NoraConditionTriggersV1(const NoraTriBoolV1 condition)
{
   return condition == NORA_BOOL_TRUE_V1;
}

#endif
"""


class GenerationError(ValueError):
    """Deterministic control-plane generation failure."""


def _part(hasher: "hashlib._Hash", value: bytes) -> None:
    hasher.update(len(value).to_bytes(8, "big"))
    hasher.update(value)


def _runtime_identity(source: bytes, source_sha256: str, nodes: list[str], operators: list[str]) -> str:
    digest = hashlib.sha256()
    _part(digest, IDENTITY_DOMAIN.encode())
    _part(digest, RUNTIME_VERSION.encode())
    _part(digest, _TYPE_DEFINITIONS.encode())
    for node in nodes:
        _part(digest, node.encode())
    for operator in operators:
        _part(digest, operator.encode())
    _part(digest, _SEMANTIC_TABLES.encode())
    _part(digest, source)
    _part(digest, source_sha256.encode())
    return digest.hexdigest()


def runtime_identity_for_test(*, operators: list[str] | None = None, source: bytes | None = None) -> str:
    """Return an identity for focused inventory/source sensitivity tests."""
    source = _SOURCE.encode("utf-8") if source is None else source
    return _runtime_identity(source, hashlib.sha256(source).hexdigest(), SUPPORTED_AST_NODES, operators or SUPPORTED_OPERATORS)


def _manifest(source: bytes) -> dict[str, object]:
    source_sha256 = hashlib.sha256(source).hexdigest()
    return {
        "runtime_version": RUNTIME_VERSION,
        "source_filename": SOURCE_FILENAME,
        "supported_ast_nodes": list(SUPPORTED_AST_NODES),
        "supported_operators": list(SUPPORTED_OPERATORS),
        "source_sha256": source_sha256,
        "runtime_identity": _runtime_identity(source, source_sha256, SUPPORTED_AST_NODES, SUPPORTED_OPERATORS),
    }


def _publish(output_dir: Path, filename: str, content: bytes) -> None:
    destination = output_dir / filename
    temporary = output_dir / ("." + filename + ".partial")
    if temporary.exists():
        raise GenerationError(f"task-owned temporary output already exists: {temporary.name}")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, destination)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise GenerationError(f"atomic publish {filename}: {error}") from error


def generate(output_dir: str | os.PathLike[str], runtime_version: str = RUNTIME_VERSION) -> dict[str, object]:
    """Generate the deterministic header and manifest into an existing directory."""
    if runtime_version != RUNTIME_VERSION:
        raise GenerationError(f"unsupported runtime_version; expected {RUNTIME_VERSION}")
    if isinstance(output_dir, str) and not output_dir.strip():
        raise GenerationError("output directory must be a non-empty existing directory")
    directory = Path(output_dir)
    if not directory.is_dir():
        raise GenerationError("output directory must be a non-empty existing directory")
    header = directory / SOURCE_FILENAME
    manifest_path = directory / MANIFEST_FILENAME
    if header.exists() or manifest_path.exists():
        raise GenerationError("generated runtime targets must not already exist")
    source = _SOURCE.encode("utf-8")
    manifest = _manifest(source)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    published_header = False
    try:
        _publish(directory, SOURCE_FILENAME, source)
        published_header = True
        _publish(directory, MANIFEST_FILENAME, manifest_bytes)
    except GenerationError:
        if published_header:
            header.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise
    return {"ok": True, **manifest, "header_path": str(header), "manifest_path": str(manifest_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lab.mql5gen")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--runtime-version", default=RUNTIME_VERSION)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(generate(args.output_dir, args.runtime_version), sort_keys=True, separators=(",", ":")))
        return 0
    except GenerationError as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


__all__ = ["GenerationError", "generate", "main", "runtime_identity_for_test"]
