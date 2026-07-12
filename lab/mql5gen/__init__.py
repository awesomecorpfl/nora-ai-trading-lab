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
TRANSLATOR_VERSION = "nora_mql5_condition_translator_v1"
CONDITION_SOURCE_FILENAME = "NoraPhase2ConditionV1.mqh"
CONDITION_MANIFEST_FILENAME = "NoraPhase2ConditionV1.manifest.json"
TRANSLATION_IDENTITY_DOMAIN = "nora.mql5.condition_translator_v1.semantic.v1"
RUNTIME_IDENTITY = "2ba6078adcd10d991d3ef1ada26baa791a0c6054707a84acaceaa6fe23f2b176"
RUNTIME_SOURCE_SHA256 = "42b7239442090a68fdacdc481925cd6b9819b572ea083efce3f3e3cbbb27d2a4"
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


def _strict_ast(value: object) -> tuple[dict, str]:
    """Validate and canonicalize the accepted Rust AST wire form."""
    if isinstance(value, dict) and "ast" in value:
        value = value["ast"]
    if not isinstance(value, dict) or set(value) != {"schema_version", "root"}:
        raise GenerationError("AST document must contain exactly schema_version and root")
    version = value["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise GenerationError("unsupported AST schema_version; expected 1")

    def required_string(obj: dict, key: str, where: str) -> str:
        if key not in obj or not isinstance(obj[key], str) or not obj[key]:
            raise GenerationError(f"{where}.{key} must be a non-empty string")
        return obj[key]

    def reference(value: object, expected: str) -> dict:
        if not isinstance(value, dict) or set(value) != {"series", "type"}:
            raise GenerationError("series reference has unknown or missing fields")
        series = required_string(value, "series", "series reference")
        actual = required_string(value, "type", "series reference")
        if actual not in {"numeric", "boolean"} or actual != expected:
            raise GenerationError(f"series reference type disagrees with node kind; expected {expected}")
        return {"series": series, "type": actual}

    def node(value: object) -> tuple[dict, str]:
        if not isinstance(value, dict):
            raise GenerationError("AST node must be an object")
        kind = required_string(value, "kind", "AST node")
        if kind == "numeric_series":
            if set(value) != {"kind", "ref"}: raise GenerationError("numeric_series node has unknown fields")
            return {"kind": kind, "ref": reference(value["ref"], "numeric")}, "numeric"
        if kind == "boolean_series":
            if set(value) != {"kind", "ref"}: raise GenerationError("boolean_series node has unknown fields")
            return {"kind": kind, "ref": reference(value["ref"], "boolean")}, "boolean"
        if kind == "number":
            if set(value) != {"kind", "value"}: raise GenerationError("number node has unknown fields")
            number = value["value"]
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not float(number) == float(number) or abs(float(number)) == float("inf"):
                raise GenerationError("number.value must be a finite numeric value")
            number = float(number)
            if number == 0.0: number = 0.0
            return {"kind": kind, "value": number}, "numeric"
        if kind == "compare":
            if set(value) != {"kind", "op", "left", "right"}: raise GenerationError("compare node has unknown fields")
            op = required_string(value, "op", "compare node")
            if op not in {"gt", "gte", "lt", "lte"}: raise GenerationError(f"unknown comparison operator {op!r}")
            left, left_type = node(value["left"]); right, right_type = node(value["right"])
            if left_type != "numeric" or right_type != "numeric": raise GenerationError("compare operands must be numeric")
            return {"kind": kind, "op": op, "left": left, "right": right}, "boolean"
        if kind in {"and", "or"}:
            if set(value) != {"kind", "args"}: raise GenerationError(f"{kind} node has unknown fields")
            args = value["args"]
            if not isinstance(args, list) or len(args) < 2: raise GenerationError(f"{kind}.args must contain at least two boolean arguments")
            parsed = []
            for arg in args:
                parsed_arg, arg_type = node(arg)
                if arg_type != "boolean": raise GenerationError(f"{kind}.args must contain only boolean arguments")
                parsed.append(parsed_arg)
            return {"kind": kind, "args": parsed}, "boolean"
        if kind == "not":
            if set(value) != {"kind", "arg"}: raise GenerationError("not node has unknown fields")
            arg, arg_type = node(value["arg"])
            if arg_type != "boolean": raise GenerationError("not argument must be boolean")
            return {"kind": kind, "arg": arg}, "boolean"
        raise GenerationError(f"unknown AST node kind {kind!r}")

    root, root_type = node(value["root"])
    if root_type != "boolean": raise GenerationError("AST root must resolve to boolean")
    canonical = {"schema_version": 1, "root": root}
    canonical_json = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    ast_identity = hashlib.sha256(b"nora-ast-semantic-v1" + canonical_json.encode("utf-8")).hexdigest()
    return canonical, ast_identity


def _series_bindings(ast: dict) -> list[dict[str, str]]:
    found: dict[str, str] = {}

    def visit(node: dict) -> None:
        kind = node["kind"]
        if kind in {"numeric_series", "boolean_series"}:
            name, series_type = node["ref"]["series"], node["ref"]["type"]
            if name in found and found[name] != series_type:
                raise GenerationError(f"series {name!r} is used with conflicting types")
            found[name] = series_type
        elif kind == "compare":
            visit(node["left"]); visit(node["right"])
        elif kind in {"and", "or"}:
            for arg in node["args"]: visit(arg)
        elif kind == "not":
            visit(node["arg"])

    visit(ast["root"])
    bindings = []
    for series_type, name in sorted((series_type, name) for name, series_type in found.items()):
        safe = "".join(char if ("a" <= char <= "z" or "A" <= char <= "Z" or "0" <= char <= "9" or char == "_") else "_" for char in name)
        if not safe or safe[0].isdigit(): safe = "series_" + safe
        digest = hashlib.sha256((series_type + "\0" + name).encode("utf-8")).hexdigest()[:12]
        prefix = "nora_num_" if series_type == "numeric" else "nora_bool_"
        bindings.append({"original_series_name": name, "series_type": series_type, "parameter_name": prefix + safe + "_" + digest})
    return bindings


def _literal(value: float) -> str:
    text = format(value, ".17g")
    if "e" not in text and "E" not in text and "." not in text: text += ".0"
    return text


def _expression(node: dict, parameters: dict[tuple[str, str], str]) -> str:
    kind = node["kind"]
    if kind in {"numeric_series", "boolean_series"}:
        ref = node["ref"]
        return parameters[(ref["type"], ref["series"])]
    if kind == "number": return f"NoraNumericValueV1({_literal(node['value'])})"
    if kind == "compare":
        return f"NoraCompare{node['op'].capitalize()}V1({_expression(node['left'], parameters)}, {_expression(node['right'], parameters)})"
    if kind == "not": return f"NoraBoolNotV1({_expression(node['arg'], parameters)})"
    if kind in {"and", "or"}:
        helper = "NoraBoolAndV1" if kind == "and" else "NoraBoolOrV1"
        result = _expression(node["args"][0], parameters)
        for arg in node["args"][1:]: result = f"{helper}({result}, {_expression(arg, parameters)})"
        return result
    raise GenerationError(f"unsupported AST node {kind!r}")


def _condition_identity(source: bytes, source_sha256: str, canonical: dict, ast_identity: str, bindings: list[dict[str, str]], function_name: str, trigger_name: str) -> str:
    digest = hashlib.sha256()
    _part(digest, TRANSLATION_IDENTITY_DOMAIN.encode())
    for value in [TRANSLATOR_VERSION, RUNTIME_IDENTITY, ast_identity, json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")), *SUPPORTED_AST_NODES, *SUPPORTED_OPERATORS, json.dumps(bindings, sort_keys=True, separators=(",", ":")), function_name, trigger_name, source_sha256]:
        _part(digest, value.encode("utf-8"))
    _part(digest, source)
    return digest.hexdigest()


def _verify_runtime_manifest(path: Path) -> None:
    try: manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise GenerationError("runtime manifest is unreadable or malformed") from error
    expected_keys = {"runtime_identity", "runtime_version", "source_filename", "source_sha256", "supported_ast_nodes", "supported_operators"}
    if not isinstance(manifest, dict) or set(manifest) != expected_keys: raise GenerationError("runtime manifest has unknown or missing fields")
    if manifest["runtime_version"] != RUNTIME_VERSION or manifest["runtime_identity"] != RUNTIME_IDENTITY or manifest["source_sha256"] != RUNTIME_SOURCE_SHA256 or manifest["source_filename"] != SOURCE_FILENAME or manifest["supported_ast_nodes"] != SUPPORTED_AST_NODES or manifest["supported_operators"] != SUPPORTED_OPERATORS:
        raise GenerationError("runtime manifest contract does not match frozen Phase 2F runtime")


def translate_condition(ast_path: str | os.PathLike[str], runtime_manifest_path: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    """Translate one accepted AST into a deterministic nullable MQL5 condition header."""
    manifest_path = Path(runtime_manifest_path)
    if not manifest_path.is_file(): raise GenerationError("runtime manifest path is not a readable file")
    _verify_runtime_manifest(manifest_path)
    source_ast_path = Path(ast_path)
    try: raw = json.loads(source_ast_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise GenerationError("AST input is unreadable or malformed") from error
    canonical, ast_identity = _strict_ast(raw)
    bindings = _series_bindings(canonical)
    parameters = {(binding["series_type"], binding["original_series_name"]): binding["parameter_name"] for binding in bindings}
    prefix = ast_identity[:16]
    function_name = f"NoraCondition_{prefix}_V1"
    trigger_name = f"NoraTrigger_{prefix}_V1"
    params = []
    for binding in bindings:
        type_name = "const NoraNullableDoubleV1 &" if binding["series_type"] == "numeric" else "NoraTriBoolV1"
        params.append(f"{type_name} {binding['parameter_name']}")
    parameter_block = ",\n   ".join(params)
    argument_block = ",\n         ".join(binding["parameter_name"] for binding in bindings)
    expression = _expression(canonical["root"], parameters)
    source_text = "#ifndef NORA_PHASE2_CONDITION_" + prefix.upper() + "_V1_MQH\n#define NORA_PHASE2_CONDITION_" + prefix.upper() + "_V1_MQH\n\n#include \"NoraPhase2RuntimeV1.mqh\"\n\nNoraTriBoolV1 " + function_name + "(\n   " + parameter_block + "\n)\n{\n   return " + expression + ";\n}\n\nbool " + trigger_name + "(\n   " + parameter_block + "\n)\n{\n   return NoraConditionTriggersV1(\n      " + function_name + "(\n         " + argument_block + "\n      )\n   );\n}\n\n#endif\n"
    source = source_text.encode("utf-8")
    source_sha256 = hashlib.sha256(source).hexdigest()
    translation_identity = _condition_identity(source, source_sha256, canonical, ast_identity, bindings, function_name, trigger_name)
    output = Path(output_dir)
    if not output.is_dir(): raise GenerationError("output directory must be an existing directory")
    header = output / CONDITION_SOURCE_FILENAME
    manifest = output / CONDITION_MANIFEST_FILENAME
    if header.exists() or manifest.exists(): raise GenerationError("generated condition targets must not already exist")
    semantic_manifest = {"translator_version": TRANSLATOR_VERSION, "runtime_identity": RUNTIME_IDENTITY, "canonical_ast_identity": ast_identity, "function_name": function_name, "trigger_function_name": trigger_name, "supported_ast_nodes": list(SUPPORTED_AST_NODES), "supported_operators": list(SUPPORTED_OPERATORS), "series_bindings": bindings, "source_filename": CONDITION_SOURCE_FILENAME, "source_sha256": source_sha256, "translation_identity": translation_identity}
    manifest_bytes = (json.dumps(semantic_manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    published = False
    try:
        _publish(output, CONDITION_SOURCE_FILENAME, source); published = True
        _publish(output, CONDITION_MANIFEST_FILENAME, manifest_bytes)
    except GenerationError:
        if published: header.unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
        raise
    return {"ok": True, **semantic_manifest, "header_path": str(header), "manifest_path": str(manifest)}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    condition_mode = bool(argv and argv[0] == "condition")
    parser = argparse.ArgumentParser(prog="python -m lab.mql5gen")
    if condition_mode:
        parser.add_argument("condition", choices=["condition"])
        parser.add_argument("--ast", required=True)
        parser.add_argument("--runtime-manifest", required=True)
        parser.add_argument("--output-dir", required=True)
    else:
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--runtime-version", default=RUNTIME_VERSION)
    args = parser.parse_args(argv)
    try:
        result = translate_condition(args.ast, args.runtime_manifest, args.output_dir) if condition_mode else generate(args.output_dir, args.runtime_version)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except GenerationError as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


__all__ = ["GenerationError", "generate", "main", "runtime_identity_for_test", "translate_condition"]
