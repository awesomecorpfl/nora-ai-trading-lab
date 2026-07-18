"""Stateful local MQL5 translation for row-aware Cross/Slope conditions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab.mql5gen import GenerationError, RUNTIME_IDENTITY, _verify_runtime_manifest

TRANSLATOR_VERSION = "nora_mql5_stateful_condition_translator_v1"
SOURCE_FILENAME = "NoraPhase2StatefulConditionV1.mqh"
MANIFEST_FILENAME = "NoraPhase2StatefulConditionV1.manifest.json"
DOMAIN = "nora.mql5.stateful_condition_translator_v1.semantic.v1"


def _canon(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _string(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise GenerationError(f"{where} must be a non-empty string")
    return value


def _ref(value: object, expected: str = "numeric") -> dict:
    if not isinstance(value, dict) or set(value) != {"series", "type"}:
        raise GenerationError("stateful series reference fields are invalid")
    if _string(value.get("type"), "series reference.type") != expected:
        raise GenerationError(f"stateful series reference must be {expected}")
    return {"series": _string(value.get("series"), "series reference.series"), "type": expected}


def _feature_ref(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {"type", "name"} or value.get("type") != "series":
        raise GenerationError("stateful feature input must be a series reference")
    return {"type": "series", "name": _string(value.get("name"), "feature series.name")}


def _node(value: object) -> tuple[dict, str]:
    if not isinstance(value, dict):
        raise GenerationError("stateful AST node must be an object")
    if value.get("type") == "slope":
        if set(value) != {"type", "input", "lookback"} or value.get("lookback") != 1:
            raise GenerationError("stateful slope admission requires lookback 1")
        return {"type": "slope", "input": _feature_ref(value["input"]), "lookback": 1}, "numeric"
    kind = _string(value.get("kind"), "stateful AST node.kind")
    if kind == "numeric_series":
        if set(value) != {"kind", "ref"}:
            raise GenerationError("stateful numeric_series fields are invalid")
        return {"kind": kind, "ref": _ref(value["ref"])}, "numeric"
    if kind == "number":
        if set(value) != {"kind", "value"} or isinstance(value.get("value"), bool) or not isinstance(value.get("value"), (int, float)):
            raise GenerationError("stateful number fields are invalid")
        number = float(value["value"])
        if number != number or abs(number) == float("inf"):
            raise GenerationError("stateful number must be finite")
        return {"kind": kind, "value": 0.0 if number == 0.0 else number}, "numeric"
    if kind == "cross":
        if set(value) != {"kind", "direction", "left", "right"} or value["direction"] not in {"above", "below"}:
            raise GenerationError("stateful cross fields are invalid")
        left, left_type = _node(value["left"])
        right, right_type = _node(value["right"])
        if left_type != "numeric" or right_type != "numeric":
            raise GenerationError("stateful cross operands must be numeric")
        return {"kind": kind, "direction": value["direction"], "left": left, "right": right}, "boolean"
    if kind == "compare":
        if set(value) != {"kind", "op", "left", "right"} or value["op"] not in {"gt", "gte", "lt", "lte"}:
            raise GenerationError("stateful compare fields are invalid")
        left, left_type = _node(value["left"])
        right, right_type = _node(value["right"])
        if left_type != "numeric" or right_type != "numeric":
            raise GenerationError("stateful compare operands must be numeric")
        return {"kind": kind, "op": value["op"], "left": left, "right": right}, "boolean"
    if kind in {"and", "or"}:
        if set(value) != {"kind", "args"} or not isinstance(value["args"], list) or len(value["args"]) < 2:
            raise GenerationError(f"stateful {kind} arguments are invalid")
        args = []
        for item in value["args"]:
            parsed, item_type = _node(item)
            if item_type != "boolean":
                raise GenerationError(f"stateful {kind} requires boolean arguments")
            args.append(parsed)
        return {"kind": kind, "args": args}, "boolean"
    if kind == "not":
        if set(value) != {"kind", "arg"}:
            raise GenerationError("stateful not fields are invalid")
        arg, arg_type = _node(value["arg"])
        if arg_type != "boolean":
            raise GenerationError("stateful not requires a boolean argument")
        return {"kind": kind, "arg": arg}, "boolean"
    raise GenerationError(f"unknown stateful AST node {kind!r}")


def _canonical(raw: object) -> dict:
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "root"} or raw["schema_version"] != 1:
        raise GenerationError("stateful AST document must be schema version 1")
    root, root_type = _node(raw["root"])
    if root_type != "boolean":
        raise GenerationError("stateful AST root must be boolean")
    return {"schema_version": 1, "root": root}


def _bindings(ast: dict) -> list[dict[str, str]]:
    names: set[str] = set()

    def visit(node: dict) -> None:
        if node.get("kind") == "numeric_series":
            names.add(node["ref"]["series"])
        elif node.get("type") == "slope":
            names.add(node["input"]["name"])
        elif node.get("kind") in {"cross", "compare"}:
            visit(node["left"]); visit(node["right"])
        elif node.get("kind") in {"and", "or"}:
            for arg in node["args"]: visit(arg)
        elif node.get("kind") == "not":
            visit(node["arg"])

    visit(ast["root"])
    result = []
    for name in sorted(names):
        safe = "".join(c if c.isalnum() or c == "_" else "_" for c in name) or "series"
        digest = hashlib.sha256(("numeric\0" + name).encode()).hexdigest()[:12]
        result.append({"original_series_name": name, "series_type": "numeric", "previous_parameter_name": f"nora_prev_{safe}_{digest}", "current_parameter_name": f"nora_curr_{safe}_{digest}"})
    return result


def _expression(node: dict, bindings: dict[str, dict[str, str]], current: bool = True) -> str:
    kind = node.get("kind")
    if kind == "numeric_series":
        binding = bindings[node["ref"]["series"]]
        return binding["current_parameter_name" if current else "previous_parameter_name"]
    if kind == "number":
        return f"NoraNumericValueV1({node['value']:.17g})"
    if node.get("type") == "slope":
        binding = bindings[node["input"]["name"]]
        return f"NoraStatefulSlope1V1({binding['current_parameter_name']}, {binding['previous_parameter_name']})"
    if kind == "cross":
        helper = "NoraStatefulCrossAboveV1" if node["direction"] == "above" else "NoraStatefulCrossBelowV1"
        return f"{helper}({_expression(node['left'], bindings, False)}, {_expression(node['right'], bindings, False)}, {_expression(node['left'], bindings, True)}, {_expression(node['right'], bindings, True)})"
    if kind == "compare":
        return f"NoraCompare{node['op'].capitalize()}V1({_expression(node['left'], bindings)}, {_expression(node['right'], bindings)})"
    if kind == "not":
        return f"NoraBoolNotV1({_expression(node['arg'], bindings)})"
    if kind in {"and", "or"}:
        helper = "NoraBoolAndV1" if kind == "and" else "NoraBoolOrV1"
        result = _expression(node["args"][0], bindings)
        for arg in node["args"][1:]: result = f"{helper}({result}, {_expression(arg, bindings)})"
        return result
    raise GenerationError(f"stateful expression does not support {kind!r}")


def _helpers() -> str:
    return """\nNoraNullableDoubleV1 NoraStatefulSlope1V1(const NoraNullableDoubleV1 &current, const NoraNullableDoubleV1 &previous)\n{\n   if(current.is_null || previous.is_null) return NoraNumericNullV1();\n   NoraNullableDoubleV1 result; result.is_null = false; result.value = current.value - previous.value; return result;\n}\n\nNoraTriBoolV1 NoraStatefulCrossAboveV1(const NoraNullableDoubleV1 &left_previous, const NoraNullableDoubleV1 &right_previous, const NoraNullableDoubleV1 &left_current, const NoraNullableDoubleV1 &right_current)\n{\n   if(left_previous.is_null || right_previous.is_null || left_current.is_null || right_current.is_null) return NoraBoolNullV1();\n   return (left_previous.value <= right_previous.value && left_current.value > right_current.value) ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;\n}\n\nNoraTriBoolV1 NoraStatefulCrossBelowV1(const NoraNullableDoubleV1 &left_previous, const NoraNullableDoubleV1 &right_previous, const NoraNullableDoubleV1 &left_current, const NoraNullableDoubleV1 &right_current)\n{\n   if(left_previous.is_null || right_previous.is_null || left_current.is_null || right_current.is_null) return NoraBoolNullV1();\n   return (left_previous.value >= right_previous.value && left_current.value < right_current.value) ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;\n}\n"""


def translate_stateful_condition(ast_path: str | Path, runtime_manifest_path: str | Path, output_dir: str | Path) -> dict[str, object]:
    runtime_manifest = Path(runtime_manifest_path)
    if not runtime_manifest.is_file():
        raise GenerationError("stateful runtime manifest is not readable")
    _verify_runtime_manifest(runtime_manifest)
    try:
        raw = json.loads(Path(ast_path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError("stateful AST input is unreadable") from error
    canonical = _canonical(raw)
    bindings_list = _bindings(canonical)
    bindings = {item["original_series_name"]: item for item in bindings_list}
    ast_identity = _sha(b"nora-ast-semantic-v1" + _canon(canonical).encode())
    prefix = ast_identity[:16]
    function_name = f"NoraStatefulCondition_{prefix}_V1"
    trigger_name = f"NoraStatefulTrigger_{prefix}_V1"
    params = []
    args = []
    for item in bindings_list:
        params.extend([f"const NoraNullableDoubleV1 &{item['previous_parameter_name']}", f"const NoraNullableDoubleV1 &{item['current_parameter_name']}"])
        args.extend([item["previous_parameter_name"], item["current_parameter_name"]])
    expression = _expression(canonical["root"], bindings)
    parameter_block = ",\n   ".join(params)
    argument_block = ",\n         ".join(args)
    source_text = f"#ifndef NORA_PHASE2_STATEFUL_CONDITION_{prefix.upper()}_V1_MQH\n#define NORA_PHASE2_STATEFUL_CONDITION_{prefix.upper()}_V1_MQH\n\n#include \"NoraPhase2RuntimeV1.mqh\"\n{_helpers()}\nNoraTriBoolV1 {function_name}(\n   {parameter_block}\n)\n{{\n   return {expression};\n}}\n\nbool {trigger_name}(\n   {parameter_block}\n)\n{{\n   return NoraConditionTriggersV1({function_name}(\n      {argument_block}\n   ));\n}}\n\n#endif\n"
    source = source_text.encode()
    source_sha = _sha(source)
    manifest = {"translator_version": TRANSLATOR_VERSION, "runtime_identity": RUNTIME_IDENTITY, "canonical_ast_identity": ast_identity, "stateful": True, "row_contract": "previous_current_v1", "function_name": function_name, "trigger_function_name": trigger_name, "series_bindings": bindings_list, "source_filename": SOURCE_FILENAME, "source_sha256": source_sha}
    manifest["translation_identity"] = _sha(DOMAIN.encode() + _canon(manifest).encode() + source)
    output = Path(output_dir)
    if not output.is_dir():
        raise GenerationError("stateful output directory must already exist")
    header, manifest_path = output / SOURCE_FILENAME, output / MANIFEST_FILENAME
    if header.exists() or manifest_path.exists():
        raise GenerationError("stateful translation targets already exist")
    header.write_bytes(source)
    try:
        manifest_path.write_text(_canon(manifest) + "\n")
    except OSError:
        header.unlink(missing_ok=True)
        raise
    return {**manifest, "header_path": str(header), "manifest_path": str(manifest_path)}
