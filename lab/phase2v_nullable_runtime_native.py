"""Deterministic exhaustive Phase-2V nullable-runtime native tester generation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import cast

RUNTIME_IDENTITY = "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d"
RUNTIME_SOURCE_SHA256 = "97de0194d7715b32ce104a9889d1a4af46cff6d0759d637f21e41025a98ee043"
TESTER_VERSION = "nora_mql5_nullable_runtime_semantic_tester_v1"
TESTER_SOURCE_FILENAME = "NoraPhase2ConditionTesterCanaryV1.mq5"
TESTER_MANIFEST_FILENAME = "NoraPhase2ConditionTesterCanaryV1.manifest.json"
RESULT_FILENAME = "nora_phase2_condition_tester_v1.csv"
IDENTITY_DOMAIN = "nora.mql5.nullable_runtime_semantic_tester_v1.semantic.v1"
OPERATIONS = ["not", "and", "or", "gt", "gte", "lt", "lte", "trigger"]
TRI = ["null", "false", "true"]


def _part(h: "hashlib._Hash", value: str) -> None:
    raw = value.encode("utf-8")
    h.update(len(raw).to_bytes(8, "big"))
    h.update(raw)


def _value(value: object) -> str:
    if value is None or value == "null":
        return "NORA_BOOL_NULL_V1"
    if value is True or value == "true":
        return "NORA_BOOL_TRUE_V1"
    if value is False or value == "false":
        return "NORA_BOOL_FALSE_V1"
    raise ValueError(f"invalid tri-state value: {value!r}")


def _double(value: object) -> str:
    if value is None:
        return "0.0"
    numeric = float(cast(float, value))  # fixture validation guarantees finite numeric cases
    text = format(numeric, ".17g")
    return text if "." in text or "e" in text.lower() else text + ".0"


def _load_fixture(path: Path) -> dict:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    if fixture.get("runtime_version") != "nora_mql5_nullable_runtime_v1":
        raise ValueError("semantic fixture runtime version is not frozen Phase-2F")
    if fixture.get("and_order") != TRI or fixture.get("or_order") != TRI:
        raise ValueError("semantic fixture tri-state ordering diverges")
    if len(fixture.get("and", [])) != 3 or any(len(row) != 3 for row in fixture["and"]):
        raise ValueError("semantic fixture AND table is incomplete")
    if len(fixture.get("or", [])) != 3 or any(len(row) != 3 for row in fixture["or"]):
        raise ValueError("semantic fixture OR table is incomplete")
    if len(fixture.get("comparison_cases", [])) != 5:
        raise ValueError("semantic fixture comparison cases are incomplete")
    if any(len(fixture["comparisons"].get(op, [])) != 5 for op in ("gt", "gte", "lt", "lte")):
        raise ValueError("semantic fixture comparison table is incomplete")
    if set(fixture.get("trigger", {})) != set(TRI):
        raise ValueError("semantic fixture trigger table is incomplete")
    return fixture


def _cases(fixture: dict) -> list[dict]:
    cases: list[dict] = []
    for value in TRI:
        cases.append({"operation": "not", "left": value, "expected": fixture["not"][value]})
    for i, left in enumerate(TRI):
        for j, right in enumerate(TRI):
            cases.append({"operation": "and", "left": left, "right": right, "expected": fixture["and"][i][j]})
    for i, left in enumerate(TRI):
        for j, right in enumerate(TRI):
            cases.append({"operation": "or", "left": left, "right": right, "expected": fixture["or"][i][j]})
    for operation in ("gt", "gte", "lt", "lte"):
        for index, case in enumerate(fixture["comparison_cases"]):
            cases.append({"operation": operation, "left": case["left"], "right": case["right"], "expected": fixture["comparisons"][operation][index]})
    for value in TRI:
        cases.append({"operation": "trigger", "left": value, "expected": fixture["trigger"][value]})
    return cases


def _source(cases: list[dict]) -> str:
    arrays: list[str] = []
    for index, case in enumerate(cases):
        arrays.append(f"const NoraTriBoolV1 NoraRuntime_Expected[{len(cases)}] = {{" + ", ".join(_value(c["left"]) if c["operation"] == "trigger" else _value(c["expected"]) for c in cases) + "};")
        break
    expected_triggers = []
    for case in cases:
        if case["operation"] == "trigger":
            expected_triggers.append("true" if case["expected"] else "false")
        else:
            expected_triggers.append("true" if case["expected"] == "true" else "false")
    lines = [
        "#property strict", "", '#include "NoraPhase2RuntimeV1.mqh"', "",
        f"#define NORA_PHASE2_RUNTIME_CASE_COUNT {len(cases)}", "",
        *arrays,
        "const bool NoraRuntime_ExpectedTrigger[" + str(len(cases)) + "] = {" + ", ".join(expected_triggers) + "};",
        "",
        "string NoraRuntime_TriText(const NoraTriBoolV1 value)", "{", '   if(value == NORA_BOOL_NULL_V1) return "null";', '   if(value == NORA_BOOL_TRUE_V1) return "true";', '   return "false";', "}",
        "string NoraRuntime_BoolText(const bool value)", "{", '   return value ? "true" : "false";', "}", "",
        "NoraTriBoolV1 NoraRuntime_ActualNullable(const int index)", "{", "   switch(index)", "   {",
    ]
    for index, case in enumerate(cases):
        op = case["operation"]
        left = ""
        if op in {"not", "and", "or", "trigger"}:
            left = _value(case["left"])
        if op == "not": expr = f"NoraBoolNotV1({left})"
        elif op in {"and", "or"}: expr = f"NoraBool{'And' if op == 'and' else 'Or'}V1({left}, {_value(case['right'])})"
        elif op in {"gt", "gte", "lt", "lte"}:
            lnull = case["left"] is None
            rnull = case["right"] is None
            l = "NoraNumericNullV1()" if lnull else f"NoraNumericValueV1({_double(case['left'])})"
            r = "NoraNumericNullV1()" if rnull else f"NoraNumericValueV1({_double(case['right'])})"
            expr = f"NoraCompare{op.capitalize()}V1({l}, {r})"
        else: expr = left
        lines += [f"      case {index}: return {expr};"]
    lines += ["   }", "   return NORA_BOOL_NULL_V1;", "}", "", "bool NoraRuntime_ActualTrigger(const int index)", "{", "   switch(index)", "   {"]
    for index, case in enumerate(cases):
        if case["operation"] == "trigger":
            lines.append(f"      case {index}: return NoraConditionTriggersV1({_value(case['left'])});")
        else:
            lines.append(f"      case {index}: return NoraConditionTriggersV1(NoraRuntime_ActualNullable({index}));")
    lines += ["   }", "   return false;", "}", "", "bool NoraRuntimeDone = false;", "", "void NoraRuntimePublish()", "{", f'   const int count = {len(cases)};', f'   const int handle = FileOpen("{RESULT_FILENAME}", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, \',\');', "   if(handle == INVALID_HANDLE) { Print(\"NORA_PHASE2V_RUNTIME_FILE_OPEN_FAILED\"); return; }", "   Print(\"NORA_PHASE2V_RUNTIME_BEGIN\");", '   FileWrite(handle, "record_type", "row_index", "operation", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");', "   int passed = 0;", "   int failed = 0;", "   for(int index = 0; index < count; index++)", "   {", "      NoraTriBoolV1 actual = NoraRuntime_ActualNullable(index);", "      bool trigger = NoraRuntime_ActualTrigger(index);", "      bool row_pass = actual == NoraRuntime_Expected[index] && trigger == NoraRuntime_ExpectedTrigger[index];", "      if(row_pass) passed++; else failed++;", "      FileWrite(handle, \"row\", index, \"semantic\", NoraRuntime_TriText(actual), NoraRuntime_TriText(NoraRuntime_Expected[index]), NoraRuntime_BoolText(trigger), NoraRuntime_BoolText(NoraRuntime_ExpectedTrigger[index]), NoraRuntime_BoolText(row_pass), \"\", \"\", \"\", \"\");", "   }", "   bool overall = failed == 0 && passed == count;", '   FileWrite(handle, "summary", -1, "semantic", "", "", "", "", NoraRuntime_BoolText(overall), count, passed, failed, NoraRuntime_BoolText(overall));', "   FileFlush(handle); FileClose(handle);", "   Print(overall ? \"NORA_PHASE2V_RUNTIME_PASS\" : \"NORA_PHASE2V_RUNTIME_FAIL\");", "}", "", "int OnInit()", "{", "   Print(\"NORA_PHASE2V_RUNTIME_EA_INIT_ENTER\");", "   return INIT_SUCCEEDED;", "}", "", "void OnTick()", "{", "   if(NoraRuntimeDone) return;", "   NoraRuntimeDone = true;", "   NoraRuntimePublish();", "   TesterStop();", "}", ""]
    return "\n".join(lines)


def generate(output_dir: str | os.PathLike[str], fixture_path: str | os.PathLike[str]) -> dict:
    output = Path(output_dir)
    if not output.is_dir():
        raise ValueError("output directory must be an existing directory")
    source_path = output / TESTER_SOURCE_FILENAME
    manifest_path = output / TESTER_MANIFEST_FILENAME
    if source_path.exists() or manifest_path.exists():
        raise ValueError("generated runtime tester targets must not already exist")
    fixture = _load_fixture(Path(fixture_path))
    cases = _cases(fixture)
    source = _source(cases).encode("utf-8")
    source_sha = hashlib.sha256(source).hexdigest()
    fixture_sha = hashlib.sha256(Path(fixture_path).read_bytes()).hexdigest()
    identity = hashlib.sha256()
    _part(identity, IDENTITY_DOMAIN)
    for value in (TESTER_VERSION, RUNTIME_IDENTITY, RUNTIME_SOURCE_SHA256, fixture_sha, json.dumps(cases, sort_keys=True, separators=(",", ":")), source_sha):
        _part(identity, value)
    manifest = {"schema_version": "nora.phase2v.nullable_runtime_tester_v1", "tester_version": TESTER_VERSION, "scope": "frozen nullable runtime semantic fixture only", "runtime_identity": RUNTIME_IDENTITY, "runtime_source_sha256": RUNTIME_SOURCE_SHA256, "semantic_fixture_sha256": fixture_sha, "operations": OPERATIONS, "case_count": len(cases), "cases": cases, "source_filename": TESTER_SOURCE_FILENAME, "source_sha256": source_sha, "tester_identity": identity.hexdigest(), "result_filename": RESULT_FILENAME}
    source_path.write_bytes(source)
    try:
        manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    except OSError:
        source_path.unlink(missing_ok=True)
        raise
    return {"ok": True, **manifest, "source_path": str(source_path), "manifest_path": str(manifest_path)}


__all__ = ["generate", "OPERATIONS", "RESULT_FILENAME", "TESTER_SOURCE_FILENAME", "TESTER_MANIFEST_FILENAME"]
