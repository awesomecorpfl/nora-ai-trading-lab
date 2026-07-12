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
ATR_DISTANCE_FEATURE_TRANSLATOR_VERSION = "nora.mql5.atr_distance_feature_plan_v1"
ATR_DISTANCE_FEATURE_SOURCE_FILENAME = "NoraPhase2AtrDistanceFeaturePlanV1.mqh"
ATR_DISTANCE_FEATURE_MANIFEST_FILENAME = "NoraPhase2AtrDistanceFeaturePlanV1.manifest.json"
ATR_DISTANCE_FEATURE_TRANSLATION_DOMAIN = "nora.mql5.atr_distance_feature_plan_v1.semantic.v1"
ATR_RUNTIME_IDENTITY = "80445d259d9ac9bcf3a15bf6ec12a160594237ee469b2ee53c46d22f99370194"
DISTANCE_ATR_RUNTIME_IDENTITY = "008c2f3a1824a8a22b03c6b447e3ae1a06cdd6c852381d96c8ca7eefba730c12"
FIXTURE_VERSION = "nora_mql5_condition_fixture_v1"
FIXTURE_SOURCE_FILENAME = "NoraPhase2ConditionFixtureV1.mq5"
FIXTURE_MANIFEST_FILENAME = "NoraPhase2ConditionFixtureV1.manifest.json"
FIXTURE_RESULT_FILENAME = "nora_phase2_condition_fixture_v1.csv"
FIXTURE_IDENTITY_DOMAIN = "nora.mql5.condition_fixture_script_v1.semantic.v1"
TESTER_FIXTURE_VERSION = "nora_mql5_condition_tester_canary_v1"
TESTER_SOURCE_FILENAME = "NoraPhase2ConditionTesterCanaryV1.mq5"
TESTER_MANIFEST_FILENAME = "NoraPhase2ConditionTesterCanaryV1.manifest.json"
TESTER_RESULT_FILENAME = "nora_phase2_condition_tester_v1.csv"
TESTER_IDENTITY_DOMAIN = "nora.mql5.condition_tester_canary_v1.semantic.v1"
FIXTURE_CSV_COLUMNS = ["record_type", "row_index", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]
EVALUATION_AST_IDENTITY = "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664"
EVALUATED_SIGNAL_IDENTITY = "e098bfc87897802116a54ed21cdc2f530619201a22c55f41ac965e39b1bbd5a9"
RUNTIME_IDENTITY = "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d"
RUNTIME_SOURCE_SHA256 = "97de0194d7715b32ce104a9889d1a4af46cff6d0759d637f21e41025a98ee043"
CONDITION_IDENTITY = "1fa3d6613348a2fa532c4393e2a95795546c9cc5e2c86d010ee30fa9fe9632af"
CONDITION_SOURCE_SHA256 = "1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4"
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

bool NoraBoolIsNullV1(NoraTriBoolV1 condition)
{
   return condition == NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraBoolGetValueV1(NoraTriBoolV1 condition)
{
   return condition;
}

NoraNullableDoubleV1 NoraNumericNullV1()
{
   NoraNullableDoubleV1 result;
   result.is_null = true;
   result.value = 0.0;
   return result;
}

NoraNullableDoubleV1 NoraNumericValueV1(double value)
{
   NoraNullableDoubleV1 result;
   result.is_null = false;
   result.value = value;
   return result;
}

bool NoraNumericIsNullV1(const NoraNullableDoubleV1 &value)
{
   return value.is_null;
}

bool NoraNumericTryGetValueV1(const NoraNullableDoubleV1 &value, double &output)
{
   if(value.is_null)
      return false;
   output = value.value;
   return true;
}

NoraTriBoolV1 NoraBoolNotV1(NoraTriBoolV1 condition)
{
   if(condition == NORA_BOOL_NULL_V1)
      return NORA_BOOL_NULL_V1;
   if(condition == NORA_BOOL_TRUE_V1)
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


def _atr_distance_ast(raw: object) -> tuple[dict, list[dict]]:
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "root"} or raw.get("schema_version") != 1:
        raise GenerationError("ATR/Distance feature AST must be a schema-version-1 document")
    features: dict[str, dict] = {}
    def series(value: object) -> dict:
        if not isinstance(value, dict) or set(value) != {"type", "name"} or value.get("type") != "series" or not isinstance(value.get("name"), str) or not value["name"]:
            raise GenerationError("feature series references must be typed numeric series names")
        return {"type": "series", "name": value["name"]}
    def numeric(value: object) -> dict:
        if not isinstance(value, dict): raise GenerationError("feature numeric node must be an object")
        if value.get("type") == "atr":
            if set(value) != {"type", "high", "low", "close", "period", "method"} or value.get("period") != 3 or value.get("method") != "wilder":
                raise GenerationError("ATR admission requires period 3 and wilder method")
            node = {"type": "atr", "high": series(value["high"]), "low": series(value["low"]), "close": series(value["close"]), "period": 3, "method": "wilder"}
        elif value.get("type") == "distance_atr":
            if set(value) != {"type", "value", "reference", "atr"}: raise GenerationError("distance_atr node has unknown fields")
            atr = numeric(value["atr"])
            if atr["type"] != "atr": raise GenerationError("distance_atr.atr must be an admitted atr node")
            node = {"type": "distance_atr", "value": series(value["value"]), "reference": series(value["reference"]), "atr": atr}
        else: raise GenerationError("unsupported numeric feature node")
        canonical = json.dumps(node, sort_keys=True, separators=(",", ":"))
        identity = hashlib.sha256(b"nora-ast-feature-v2" + canonical.encode()).hexdigest()
        if node["type"] == "distance_atr": numeric(node["atr"])
        features[identity] = node
        return node
    def visit(value: object) -> None:
        if not isinstance(value, dict): raise GenerationError("AST node must be an object")
        if "type" in value: numeric(value); return
        kind = value.get("kind")
        if kind == "compare": visit(value.get("left")); visit(value.get("right"))
        elif kind in {"and", "or"}:
            for argument in value.get("args", []): visit(argument)
        elif kind == "not": visit(value.get("arg"))
    visit(raw["root"])
    canonical = {"schema_version": 1, "root": raw["root"]}
    ordered = [{"identity": identity, "node": features[identity]} for identity in sorted(features, key=lambda identity: (features[identity]["type"] != "atr", identity))]
    return canonical, ordered


def translate_atr_distance_feature_plan(ast_path: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    """Emit Stage-A MQL5 buffers for admitted ATR3/Wilder and Distance/ATR features."""
    try: raw = json.loads(Path(ast_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise GenerationError("feature AST is unreadable or malformed") from error
    canonical, features = _atr_distance_ast(raw)
    ast_json = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    ast_identity = hashlib.sha256(b"nora-ast-semantic-v1" + ast_json.encode()).hexdigest()
    definitions, initializers = [], []
    for feature in features:
        prefix = feature["identity"][:16]; name = f"nora_feature_{prefix}"
        definitions.append(f"NoraNullableDoubleV1 {name}[];")
        node = feature["node"]
        if node["type"] == "atr":
            initializers.append(f"{name}[row_index] = NoraAtr3V1(high, low, close, row_index);")
        else:
            dependency = hashlib.sha256(b"nora-ast-feature-v2" + json.dumps(node["atr"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
            initializers.append(f"{name}[row_index] = NoraDistanceAtrV1(NoraNumericValueV1(close[row_index]), NoraNumericValueV1(sma3[row_index]), nora_feature_{dependency}[row_index]);")
    guard = "NORA_PHASE2_ATR_DISTANCE_FEATURE_PLAN_V1_MQH"
    resize = "\n   ".join(f"ArrayResize(nora_feature_{feature['identity'][:16]}, row_count);" for feature in features)
    source_text = f"#ifndef {guard}\n#define {guard}\n\n#include \"NoraPhase2AtrRuntimeV1.mqh\"\n#include \"NoraPhase2DistanceAtrRuntimeV1.mqh\"\n\n" + "\n".join(definitions) + "\n\nvoid NoraPhase2SInitializeFeatures(const double &high[], const double &low[], const double &close[], const double &sma3[], const int row_count)\n{\n   " + resize + "\n   for(int row_index = 0; row_index < row_count; row_index++)\n   {\n      " + "\n      ".join(initializers) + "\n   }\n}\n\n#endif\n"
    source = source_text.encode(); source_sha256 = hashlib.sha256(source).hexdigest()
    digest = hashlib.sha256(); _part(digest, ATR_DISTANCE_FEATURE_TRANSLATION_DOMAIN.encode())
    for value in [ATR_DISTANCE_FEATURE_TRANSLATOR_VERSION, ast_identity, ATR_RUNTIME_IDENTITY, DISTANCE_ATR_RUNTIME_IDENTITY, json.dumps(features, sort_keys=True, separators=(",", ":")), source_sha256]: _part(digest, value.encode())
    _part(digest, source); translation_identity = digest.hexdigest()
    output = Path(output_dir)
    if not output.is_dir(): raise GenerationError("feature output directory must exist")
    header, manifest = output / ATR_DISTANCE_FEATURE_SOURCE_FILENAME, output / ATR_DISTANCE_FEATURE_MANIFEST_FILENAME
    if header.exists() or manifest.exists(): raise GenerationError("feature output targets must not already exist")
    feature_translation_identities = {}
    for feature in features:
        feature_digest = hashlib.sha256(); _part(feature_digest, b"nora.mql5.atr_distance_feature_translation_v1")
        for value in [ATR_DISTANCE_FEATURE_TRANSLATOR_VERSION, ast_identity, ATR_RUNTIME_IDENTITY, DISTANCE_ATR_RUNTIME_IDENTITY, json.dumps(feature, sort_keys=True, separators=(",", ":")), source_sha256]: _part(feature_digest, value.encode())
        _part(feature_digest, source); feature_translation_identities[feature["identity"]] = feature_digest.hexdigest()
    semantic = {"translator_version": ATR_DISTANCE_FEATURE_TRANSLATOR_VERSION, "canonical_ast_identity": ast_identity, "atr_runtime_identity": ATR_RUNTIME_IDENTITY, "distance_atr_runtime_identity": DISTANCE_ATR_RUNTIME_IDENTITY, "features": features, "feature_translation_identities": feature_translation_identities, "source_filename": header.name, "source_sha256": source_sha256, "translation_identity": translation_identity}
    _publish(output, header.name, source)
    try: _publish(output, manifest.name, (json.dumps(semantic, sort_keys=True, separators=(",", ":")) + "\n").encode())
    except GenerationError: header.unlink(missing_ok=True); raise
    return {"ok": True, **semantic, "header_path": str(header), "manifest_path": str(manifest)}


def _verify_condition_manifest(path: Path) -> dict:
    try: manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise GenerationError("condition manifest is unreadable or malformed") from error
    expected_keys = {"translator_version", "runtime_identity", "canonical_ast_identity", "function_name", "trigger_function_name", "supported_ast_nodes", "supported_operators", "series_bindings", "source_filename", "source_sha256", "translation_identity"}
    if not isinstance(manifest, dict) or set(manifest) != expected_keys: raise GenerationError("condition manifest has unknown or missing fields")
    if manifest["translator_version"] != TRANSLATOR_VERSION or manifest["runtime_identity"] != RUNTIME_IDENTITY or manifest["canonical_ast_identity"] != EVALUATION_AST_IDENTITY or manifest["source_filename"] != CONDITION_SOURCE_FILENAME or manifest["source_sha256"] != CONDITION_SOURCE_SHA256 or manifest["translation_identity"] != CONDITION_IDENTITY or manifest["supported_ast_nodes"] != SUPPORTED_AST_NODES or manifest["supported_operators"] != SUPPORTED_OPERATORS:
        raise GenerationError("condition manifest contract does not match frozen Phase 2G translation")
    bindings = manifest["series_bindings"]
    if not isinstance(bindings, list) or not bindings or any(not isinstance(binding, dict) or set(binding) != {"original_series_name", "series_type", "parameter_name"} for binding in bindings):
        raise GenerationError("condition manifest series_bindings are malformed")
    return manifest


def _nullable_text(value: object) -> str:
    if value is None: return "null"
    if value is True: return "true"
    if value is False: return "false"
    raise GenerationError("nullable Boolean values must be null, false, or true")


def _nullable_label(value: object) -> str:
    if value in {"null", "false", "true"}:
        return value
    raise GenerationError("nullable result labels must be null, false, or true")


def _verify_evidence(path: Path, manifest: dict) -> tuple[list[dict], list[str], list[bool]]:
    try: evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise GenerationError("translation evidence is unreadable or malformed") from error
    expected_keys = {"canonical_ast_identity", "rust_evaluated_artifact_identity", "nullable_results", "triggers", "rows"}
    if not isinstance(evidence, dict) or set(evidence) != expected_keys: raise GenerationError("translation evidence has unknown or missing fields")
    if evidence["canonical_ast_identity"] != manifest["canonical_ast_identity"]: raise GenerationError("translation evidence AST identity does not match condition manifest")
    rows = evidence["rows"]
    nullable = evidence["nullable_results"]
    triggers = evidence["triggers"]
    bindings = manifest["series_bindings"]
    binding_names = [binding["original_series_name"] for binding in bindings]
    if not isinstance(rows, list) or len(rows) != 12 or not isinstance(nullable, list) or len(nullable) != 12 or not isinstance(triggers, list) or len(triggers) != 12 or any(type(value) is not bool for value in triggers):
        raise GenerationError("translation evidence must contain exactly 12 rows and vectors")
    checked_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"row_index", "bindings", "rust_nullable_result", "expected_mql5_nullable_result", "trigger"} or row["row_index"] != index:
            raise GenerationError("translation evidence rows must be ordered and complete")
        row_bindings = row["bindings"]
        if not isinstance(row_bindings, dict) or set(row_bindings) != set(binding_names):
            raise GenerationError("translation evidence bindings do not exactly match the condition manifest")
        for binding in bindings:
            value = row_bindings[binding["original_series_name"]]
            if binding["series_type"] == "numeric":
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not float(value) == float(value) or abs(float(value)) == float("inf")):
                    raise GenerationError("translation evidence numeric bindings must be finite or null")
            elif value is not None and not isinstance(value, bool):
                raise GenerationError("translation evidence Boolean bindings must be null, false, or true")
            else:
                _nullable_text(value)
        expected = _nullable_label(row["expected_mql5_nullable_result"])
        if row["rust_nullable_result"] not in {"null", "false", "true"} or type(row["trigger"]) is not bool or _nullable_label(nullable[index]) != expected or triggers[index] != row["trigger"]:
            raise GenerationError("translation evidence expected results are inconsistent")
        checked_rows.append({"row_index": index, "bindings": {name: row["bindings"][name] for name in binding_names}, "expected_nullable": expected, "expected_trigger": bool(row["trigger"])})
    return checked_rows, [_nullable_label(value) for value in nullable], [bool(value) for value in triggers]


def _mql5_value(value: object) -> str:
    if value is None or value == "null": return "NORA_BOOL_NULL_V1"
    if value is True or value == "true": return "NORA_BOOL_TRUE_V1"
    if value is False or value == "false": return "NORA_BOOL_FALSE_V1"
    raise GenerationError("cannot encode an invalid nullable Boolean value")


def _fixture_identity(source: bytes, source_sha256: str, manifest: dict, rows: list[dict], nullable: list[str], triggers: list[bool]) -> str:
    digest = hashlib.sha256()
    _part(digest, FIXTURE_IDENTITY_DOMAIN.encode())
    components = [FIXTURE_VERSION, manifest["runtime_identity"], manifest["translation_identity"], manifest["canonical_ast_identity"], json.dumps(manifest["series_bindings"], sort_keys=True, separators=(",", ":")), json.dumps(rows, sort_keys=True, separators=(",", ":")), json.dumps(nullable, separators=(",", ":")), json.dumps(triggers, separators=(",", ":")), json.dumps(FIXTURE_CSV_COLUMNS, separators=(",", ":")), FIXTURE_RESULT_FILENAME, source_sha256]
    for value in components: _part(digest, value.encode("utf-8"))
    _part(digest, source)
    return digest.hexdigest()


def generate_fixture_script(condition_manifest_path: str | os.PathLike[str], evidence_path: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    """Generate a deterministic MQL5 OnStart replay script from Phase 2G evidence."""
    condition_manifest = _verify_condition_manifest(Path(condition_manifest_path))
    rows, nullable, triggers = _verify_evidence(Path(evidence_path), condition_manifest)
    binding_names = [binding["original_series_name"] for binding in condition_manifest["series_bindings"]]
    arrays = []
    constructors = []
    arguments = []
    for binding in condition_manifest["series_bindings"]:
        original = binding["original_series_name"]
        parameter = binding["parameter_name"]
        safe = "".join(character if character.isalnum() else "_" for character in original)
        array_name = "NoraFixture_" + ("Bool_" if binding["series_type"] == "boolean" else "Num_") + safe
        values = [row["bindings"][original] for row in rows]
        if binding["series_type"] == "boolean":
            arrays.append(f"const NoraTriBoolV1 {array_name}[12] = {{" + ", ".join(_mql5_value(value) for value in values) + "};")
            arguments.append(f"{array_name}[row_index]")
        else:
            null_name = array_name + "_NullMask"
            arrays.append(f"const bool {null_name}[12] = {{" + ", ".join("true" if value is None else "false" for value in values) + "};")
            arrays.append(f"const double {array_name}_Values[12] = {{" + ", ".join("0.0" if value is None else _literal(float(value)) for value in values) + "};")
            constructors.append("NoraNullableDoubleV1 " + array_name + "Value(const int row_index)\n{\n   if(" + null_name + "[row_index])\n      return NoraNumericNullV1();\n   return NoraNumericValueV1(" + array_name + "_Values[row_index]);\n}")
            arguments.append(array_name + "Value(row_index)")
    arrays.append("const NoraTriBoolV1 NoraFixture_ExpectedNullable[12] = {" + ", ".join(_mql5_value(value) for value in nullable) + "};")
    arrays.append("const bool NoraFixture_ExpectedTrigger[12] = {" + ", ".join("true" if value else "false" for value in triggers) + "};")
    args = ",\n         ".join(arguments)
    source_text = "#property strict\n\n#include \"NoraPhase2RuntimeV1.mqh\"\n#include \"NoraPhase2ConditionV1.mqh\"\n\n#define NORA_PHASE2_FIXTURE_ROW_COUNT 12\n\n" + "\n\n".join(arrays + constructors) + "\n\nstring NoraFixtureNullableText(const NoraTriBoolV1 value)\n{\n   if(value == NORA_BOOL_NULL_V1)\n      return \"null\";\n   if(value == NORA_BOOL_TRUE_V1)\n      return \"true\";\n   return \"false\";\n}\n\nstring NoraFixtureTriggerText(const bool value)\n{\n   return value ? \"true\" : \"false\";\n}\n\nvoid OnStart()\n{\n   const string filename = \"" + FIXTURE_RESULT_FILENAME + "\";\n   const int handle = FileOpen(filename, FILE_WRITE | FILE_CSV, ',');\n   if(handle == INVALID_HANDLE)\n   {\n      Print(\"nora_phase2_fixture_error,file_open_failed\");\n      return;\n   }\n   FileWrite(handle, \"record_type\", \"row_index\", \"actual_nullable\", \"expected_nullable\", \"actual_trigger\", \"expected_trigger\", \"row_pass\", \"row_count\", \"passed_rows\", \"failed_rows\", \"overall_pass\");\n   const int row_count = NORA_PHASE2_FIXTURE_ROW_COUNT;\n   int passed_rows = 0;\n   int failed_rows = 0;\n   if(row_count != 12)\n   {\n      FileWrite(handle, \"summary\", -1, \"\", \"\", \"\", \"\", \"false\", row_count, 0, row_count, \"false\");\n      FileClose(handle);\n      return;\n   }\n   for(int row_index = 0; row_index < row_count; row_index++)\n   {\n      NoraTriBoolV1 actual_nullable = " + condition_manifest["function_name"] + "(" + args + ");\n      bool actual_trigger = " + condition_manifest["trigger_function_name"] + "(" + args + ");\n      bool row_pass = actual_nullable == NoraFixture_ExpectedNullable[row_index] && actual_trigger == NoraFixture_ExpectedTrigger[row_index];\n      if(row_pass)\n         passed_rows++;\n      else\n         failed_rows++;\n      FileWrite(handle, \"row\", row_index, NoraFixtureNullableText(actual_nullable), NoraFixtureNullableText(NoraFixture_ExpectedNullable[row_index]), NoraFixtureTriggerText(actual_trigger), NoraFixtureTriggerText(NoraFixture_ExpectedTrigger[row_index]), row_pass ? \"true\" : \"false\", \"\", \"\", \"\", \"\");\n   }\n   FileWrite(handle, \"summary\", -1, \"\", \"\", \"\", \"\", failed_rows == 0 ? \"true\" : \"false\", row_count, passed_rows, failed_rows, failed_rows == 0 ? \"true\" : \"false\");\n   FileClose(handle);\n}\n"
    source = source_text.encode("utf-8")
    source_sha256 = hashlib.sha256(source).hexdigest()
    fixture_identity = _fixture_identity(source, source_sha256, condition_manifest, rows, nullable, triggers)
    output = Path(output_dir)
    if not output.is_dir(): raise GenerationError("output directory must be an existing directory")
    header = output / FIXTURE_SOURCE_FILENAME
    manifest_path = output / FIXTURE_MANIFEST_FILENAME
    if header.exists() or manifest_path.exists(): raise GenerationError("generated fixture targets must not already exist")
    semantic_manifest = {"fixture_version": FIXTURE_VERSION, "runtime_identity": condition_manifest["runtime_identity"], "condition_translation_identity": condition_manifest["translation_identity"], "canonical_ast_identity": condition_manifest["canonical_ast_identity"], "row_count": len(rows), "series_bindings": condition_manifest["series_bindings"], "expected_nullable_vector": nullable, "expected_trigger_vector": triggers, "script_filename": FIXTURE_SOURCE_FILENAME, "result_filename": FIXTURE_RESULT_FILENAME, "source_sha256": source_sha256, "fixture_identity": fixture_identity}
    manifest_bytes = (json.dumps(semantic_manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    published = False
    try:
        _publish(output, FIXTURE_SOURCE_FILENAME, source); published = True
        _publish(output, FIXTURE_MANIFEST_FILENAME, manifest_bytes)
    except GenerationError:
        if published: header.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise
    return {"ok": True, **semantic_manifest, "header_path": str(header), "manifest_path": str(manifest_path)}


def _verify_source_fixture(path: Path) -> dict:
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise GenerationError("source evidence fixture manifest is unreadable or malformed") from error
    expected = {"fixture_identity": "d283a5a37e64f426f39f813d1f2f68fa64e4c92cbd61b2cdbd59b9f1eac1f858", "runtime_identity": RUNTIME_IDENTITY, "condition_translation_identity": CONDITION_IDENTITY, "canonical_ast_identity": EVALUATION_AST_IDENTITY, "row_count": 12, "result_filename": FIXTURE_RESULT_FILENAME, "source_sha256": "b3b98996545d1277d4b2fa51db7c14c943ad733c018717110dab45e05f0022a7"}
    for key, expected_value in expected.items():
        if value.get(key) != expected_value: raise GenerationError("source evidence fixture contract does not match frozen Phase 2H fixture")
    return value


def _tester_identity(source: bytes, source_sha256: str, condition_manifest: dict, source_fixture: dict, rows: list[dict], nullable: list[str], triggers: list[bool]) -> str:
    digest = hashlib.sha256()
    _part(digest, TESTER_IDENTITY_DOMAIN.encode())
    values = [TESTER_FIXTURE_VERSION, condition_manifest["runtime_identity"], condition_manifest["translation_identity"], condition_manifest["canonical_ast_identity"], source_fixture["fixture_identity"], json.dumps(condition_manifest["series_bindings"], sort_keys=True, separators=(",", ":")), json.dumps(rows, sort_keys=True, separators=(",", ":")), json.dumps(nullable, separators=(",", ":")), json.dumps(triggers, separators=(",", ":")), json.dumps(FIXTURE_CSV_COLUMNS, separators=(",", ":")), TESTER_RESULT_FILENAME, source_sha256]
    for value in values: _part(digest, value.encode("utf-8"))
    _part(digest, source)
    return digest.hexdigest()


def generate_tester_canary(condition_manifest_path: str | os.PathLike[str], evidence_path: str | os.PathLike[str], source_fixture_manifest_path: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    """Generate a deterministic, no-trading EA wrapper for the frozen condition fixture."""
    condition_manifest = _verify_condition_manifest(Path(condition_manifest_path))
    source_fixture = _verify_source_fixture(Path(source_fixture_manifest_path))
    rows, nullable, triggers = _verify_evidence(Path(evidence_path), condition_manifest)
    arrays, constructors, arguments = [], [], []
    for binding in condition_manifest["series_bindings"]:
        original, parameter = binding["original_series_name"], binding["parameter_name"]
        safe = "".join(character if character.isalnum() else "_" for character in original)
        name = "NoraTester_" + ("Bool_" if binding["series_type"] == "boolean" else "Num_") + safe
        values = [row["bindings"][original] for row in rows]
        if binding["series_type"] == "boolean":
            arrays.append(f"const NoraTriBoolV1 {name}[12] = {{" + ", ".join(_mql5_value(value) for value in values) + "};")
            arguments.append(f"{name}[row_index]")
        else:
            arrays.append(f"const bool {name}_NullMask[12] = {{" + ", ".join("true" if value is None else "false" for value in values) + "};")
            arrays.append(f"const double {name}_Values[12] = {{" + ", ".join("0.0" if value is None else _literal(float(value)) for value in values) + "};")
            constructors.append("NoraNullableDoubleV1 " + name + "Value(const int row_index)\n{\n   if(" + name + "_NullMask[row_index])\n      return NoraNumericNullV1();\n   return NoraNumericValueV1(" + name + "_Values[row_index]);\n}")
            arguments.append(name + "Value(row_index)")
    arrays.append("const NoraTriBoolV1 NoraTester_ExpectedNullable[12] = {" + ", ".join(_mql5_value(value) for value in nullable) + "};")
    arrays.append("const bool NoraTester_ExpectedTrigger[12] = {" + ", ".join("true" if value else "false" for value in triggers) + "};")
    args = ",\n         ".join(arguments)
    source_text = "#property strict\n\n#include \"NoraPhase2RuntimeV1.mqh\"\n#include \"NoraPhase2ConditionV1.mqh\"\n\n#define NORA_PHASE2_TESTER_ROW_COUNT 12\n\n" + "\n\n".join(arrays + constructors) + "\n\nbool NoraTesterDone = false;\n\nstring NoraTesterNullableText(const NoraTriBoolV1 value)\n{\n   if(value == NORA_BOOL_NULL_V1)\n      return \"null\";\n   if(value == NORA_BOOL_TRUE_V1)\n      return \"true\";\n   return \"false\";\n}\n\nstring NoraTesterBoolText(const bool value)\n{\n   return value ? \"true\" : \"false\";\n}\n\nvoid NoraTesterPublish()\n{\n   const int handle = FileOpen(\"" + TESTER_RESULT_FILENAME + "\", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');\n   if(handle == INVALID_HANDLE)\n   {\n      Print(\"NORA_PHASE2J_FILE_OPEN_FAILED:\" + (string)GetLastError());\n      return;\n   }\n   Print(\"NORA_PHASE2J_FILE_OPEN_OK\");\n   Print(\"NORA_PHASE2J_FIXTURE_BEGIN\");\n   FileWrite(handle, \"record_type\", \"row_index\", \"actual_nullable\", \"expected_nullable\", \"actual_trigger\", \"expected_trigger\", \"row_pass\", \"row_count\", \"passed_rows\", \"failed_rows\", \"overall_pass\");\n   int passed_rows = 0;\n   int failed_rows = 0;\n   for(int row_index = 0; row_index < NORA_PHASE2_TESTER_ROW_COUNT; row_index++)\n   {\n      NoraTriBoolV1 actual_nullable = " + condition_manifest["function_name"] + "(" + args + ");\n      bool actual_trigger = " + condition_manifest["trigger_function_name"] + "(" + args + ");\n      bool row_pass = actual_nullable == NoraTester_ExpectedNullable[row_index] && actual_trigger == NoraTester_ExpectedTrigger[row_index];\n      if(row_pass)\n         passed_rows++;\n      else\n         failed_rows++;\n      FileWrite(handle, \"row\", row_index, NoraTesterNullableText(actual_nullable), NoraTesterNullableText(NoraTester_ExpectedNullable[row_index]), NoraTesterBoolText(actual_trigger), NoraTesterBoolText(NoraTester_ExpectedTrigger[row_index]), NoraTesterBoolText(row_pass), \"\", \"\", \"\", \"\");\n   }\n   bool overall_pass = failed_rows == 0 && passed_rows == NORA_PHASE2_TESTER_ROW_COUNT;\n   FileWrite(handle, \"summary\", -1, \"\", \"\", \"\", \"\", NoraTesterBoolText(overall_pass), NORA_PHASE2_TESTER_ROW_COUNT, passed_rows, failed_rows, NoraTesterBoolText(overall_pass));\n   FileFlush(handle);\n   Print(\"NORA_PHASE2J_CSV_FLUSHED\");\n   FileClose(handle);\n   Print(overall_pass ? \"NORA_PHASE2J_FIXTURE_PASS\" : \"NORA_PHASE2J_FIXTURE_FAIL\");\n}\n\nint OnInit()\n{\n   Print(\"NORA_PHASE2J_EA_INIT_ENTER\");\n   return INIT_SUCCEEDED;\n}\n\nvoid OnTick()\n{\n   if(NoraTesterDone)\n      return;\n   NoraTesterDone = true;\n   NoraTesterPublish();\n   Print(\"NORA_PHASE2J_TESTER_STOP_REQUESTED\");\n   TesterStop();\n}\n"
    source = source_text.encode("utf-8")
    source_sha256 = hashlib.sha256(source).hexdigest()
    tester_identity = _tester_identity(source, source_sha256, condition_manifest, source_fixture, rows, nullable, triggers)
    manifest = {"tester_fixture_version": TESTER_FIXTURE_VERSION, "runtime_identity": condition_manifest["runtime_identity"], "condition_translation_identity": condition_manifest["translation_identity"], "evaluation_ast_identity": condition_manifest["canonical_ast_identity"], "source_evidence_fixture_identity": source_fixture["fixture_identity"], "row_count": 12, "series_bindings": condition_manifest["series_bindings"], "expected_nullable_vector": nullable, "expected_trigger_vector": triggers, "result_filename": TESTER_RESULT_FILENAME, "source_filename": TESTER_SOURCE_FILENAME, "source_sha256": source_sha256, "tester_fixture_identity": tester_identity}
    output = Path(output_dir)
    if not output.is_dir(): raise GenerationError("output directory must be an existing directory")
    target, manifest_path = output / TESTER_SOURCE_FILENAME, output / TESTER_MANIFEST_FILENAME
    if target.exists() or manifest_path.exists(): raise GenerationError("generated tester fixture targets must not already exist")
    _publish(output, TESTER_SOURCE_FILENAME, source)
    try: _publish(output, TESTER_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
    except GenerationError:
        target.unlink(missing_ok=True); raise
    return {"ok": True, **manifest, "source_path": str(target), "manifest_path": str(manifest_path)}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    condition_mode = bool(argv and argv[0] == "condition")
    fixture_mode = bool(argv and argv[0] == "fixture-script")
    tester_mode = bool(argv and argv[0] == "tester-canary")
    series_runtime_mode = bool(argv and argv[0] == "series-runtime")
    series_tester_mode = bool(argv and argv[0] == "series-tester")
    parser = argparse.ArgumentParser(prog="python -m lab.mql5gen")
    if condition_mode:
        parser.add_argument("condition", choices=["condition"])
        parser.add_argument("--ast", required=True)
        parser.add_argument("--runtime-manifest", required=True)
        parser.add_argument("--output-dir", required=True)
    elif fixture_mode:
        parser.add_argument("fixture_script", choices=["fixture-script"])
        parser.add_argument("--condition-manifest", required=True)
        parser.add_argument("--evidence", required=True)
        parser.add_argument("--output-dir", required=True)
    elif tester_mode:
        parser.add_argument("tester_canary", choices=["tester-canary"])
        parser.add_argument("--condition-manifest", required=True)
        parser.add_argument("--evidence", required=True)
        parser.add_argument("--source-fixture-manifest", required=True)
        parser.add_argument("--output-dir", required=True)
    elif series_runtime_mode:
        parser.add_argument("series_runtime", choices=["series-runtime"])
        parser.add_argument("--output-dir", required=True)
    elif series_tester_mode:
        parser.add_argument("series_tester", choices=["series-tester"])
        parser.add_argument("--evidence", required=True)
        parser.add_argument("--runtime-manifest", required=True)
        parser.add_argument("--condition-manifest", required=True)
        parser.add_argument("--output-dir", required=True)
    else:
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--runtime-version", default=RUNTIME_VERSION)
    args = parser.parse_args(argv)
    try:
        if condition_mode:
            result = translate_condition(args.ast, args.runtime_manifest, args.output_dir)
        elif fixture_mode:
            result = generate_fixture_script(args.condition_manifest, args.evidence, args.output_dir)
        elif tester_mode:
            result = generate_tester_canary(args.condition_manifest, args.evidence, args.source_fixture_manifest, args.output_dir)
        elif series_runtime_mode:
            from .series import generate_series_runtime
            result = generate_series_runtime(args.output_dir)
        elif series_tester_mode:
            from .series import generate_series_tester
            result = generate_series_tester(args.evidence, args.runtime_manifest, args.condition_manifest, args.output_dir)
        else:
            result = generate(args.output_dir, args.runtime_version)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except GenerationError as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


__all__ = ["GenerationError", "generate", "generate_fixture_script", "generate_tester_canary", "main", "runtime_identity_for_test", "translate_condition"]
