"""Deterministic Phase-2K SMA/cross source generation."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from . import GenerationError, _publish

SERIES_RUNTIME_VERSION = "nora_mql5_series_runtime_v1"
SERIES_SOURCE_FILENAME = "NoraPhase2SeriesRuntimeV1.mqh"
SERIES_MANIFEST_FILENAME = "NoraPhase2SeriesRuntimeV1.manifest.json"
SERIES_DOMAIN = "nora.mql5.series_runtime_v1.semantic.v1"
TESTER_VERSION = "nora_mql5.series_tester_canary_v1"
TESTER_SOURCE_FILENAME = "NoraPhase2SeriesTesterCanaryV1.mq5"
TESTER_MANIFEST_FILENAME = "NoraPhase2SeriesTesterCanaryV1.manifest.json"
TESTER_DOMAIN = "nora.mql5.series_tester_canary_v1.semantic.v1"
RUNTIME_IDENTITY = "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d"
CONDITION_IDENTITY = "1fa3d6613348a2fa532c4393e2a95795546c9cc5e2c86d010ee30fa9fe9632af"
AST_IDENTITY = "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664"
INPUT_IDENTITY = "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383"
INDICATOR_IDENTITY = "bd53bf9c88cd55fbf8d0fffb791648ff7ee6bf585efd4294042671e79eb995e9"
CROSS_IDENTITY = "274e22b09159252cc2a964cf08623de8dd9743c3152fea672a0c9ead749ff814"
NULLABLE_SEMANTICS = {"warmup": "first period minus one rows are null", "null_input": "any null in the window yields null", "sum": "left-to-right finite IEEE-754 sum divided by period", "cross": {"first_row": "null", "null_propagation": "null if either current or previous operand is null", "above": "previous_left <= previous_right and current_left > current_right", "below": "previous_left >= previous_right and current_left < current_right"}}
CSV_COLUMNS = ["record_type", "row_index", "actual_sma", "expected_sma", "actual_cross_above", "expected_cross_above", "actual_cross_below", "expected_cross_below", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]

RAW_CLOSE = [1.1003, 1.1009, 1.1006, 1.1013, 1.1010, 1.1017, 1.1014, 1.1021, 1.1018, 1.1025, 1.1022, 1.1029]
EXPECTED_SMA = [None, None, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334]
EXPECTED_ABOVE = [None, None, None, True, False, False, False, False, False, False, False, False]
EXPECTED_BELOW = [None, None, None, True, False, False, False, False, False, False, False, False]
EXPECTED_NULLABLE = ["null", "null", "false", "true", "true", "true", "true", "true", "true", "true", "true", "true"]
EXPECTED_TRIGGER = [False, False, False, True, True, True, True, True, True, True, True, True]

_SERIES_SOURCE = r'''#ifndef NORA_PHASE2_SERIES_RUNTIME_V1_MQH
#define NORA_PHASE2_SERIES_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraSma3V1(const double &values[], const bool &null_mask[], const int row_index)
{
   if(row_index < 2 || null_mask[row_index - 2] || null_mask[row_index - 1] || null_mask[row_index])
      return NoraNumericNullV1();
   double sum = values[row_index - 2] + values[row_index - 1] + values[row_index];
   double result = sum / 3.0;
   if(!MathIsValidNumber(result))
      return NoraNumericNullV1();
   return NoraNumericValueV1(result);
}

NoraTriBoolV1 NoraCrossAboveV1(const NoraNullableDoubleV1 &left_previous, const NoraNullableDoubleV1 &right_previous, const NoraNullableDoubleV1 &left_current, const NoraNullableDoubleV1 &right_current)
{
   if(left_previous.is_null || right_previous.is_null || left_current.is_null || right_current.is_null)
      return NORA_BOOL_NULL_V1;
   return left_previous.value <= right_previous.value && left_current.value > right_current.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCrossBelowV1(const NoraNullableDoubleV1 &left_previous, const NoraNullableDoubleV1 &right_previous, const NoraNullableDoubleV1 &left_current, const NoraNullableDoubleV1 &right_current)
{
   if(left_previous.is_null || right_previous.is_null || left_current.is_null || right_current.is_null)
      return NORA_BOOL_NULL_V1;
   return left_previous.value >= right_previous.value && left_current.value < right_current.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

#endif
'''

def _part(h, value: bytes) -> None:
    h.update(len(value).to_bytes(8, "big")); h.update(value)

def _identity(domain: str, values: list[object]) -> str:
    h = hashlib.sha256(); _part(h, domain.encode())
    for value in values: _part(h, json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
    return h.hexdigest()

def _literal(value: float) -> str:
    return format(value, ".17g")

def _text(value):
    if value is None: return "null"
    if isinstance(value, bool): return "true" if value else "false"
    return format(float(value), ".16f")

def _validate_evidence(path: Path) -> dict:
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e: raise GenerationError("series evidence is unreadable or malformed") from e
    required = {"rust_source_data_identity", "rust_sma_artifact_identity", "rust_cross_artifact_identity", "input_series_name", "input_vector", "input_null_positions", "sma_period", "expected_sma", "expected_cross_above", "expected_cross_below", "expected_nullable_vector", "expected_trigger_vector"}
    if set(data) != required: raise GenerationError("series evidence fields are inconsistent")
    if data["input_series_name"] != "close" or data["sma_period"] != 3: raise GenerationError("series evidence is not the accepted close/sma3 fixture")
    if data["rust_source_data_identity"] != INPUT_IDENTITY or data["rust_sma_artifact_identity"] != INDICATOR_IDENTITY or data["rust_cross_artifact_identity"] != CROSS_IDENTITY: raise GenerationError("Rust series artifact identity does not match the accepted fixture")
    vectors = [data["input_vector"], data["expected_sma"], data["expected_cross_above"], data["expected_cross_below"], data["expected_nullable_vector"], data["expected_trigger_vector"]]
    if any(len(v) != 12 for v in vectors): raise GenerationError("series evidence vectors must have length 12")
    if data["input_null_positions"] or any(not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in data["input_vector"]): raise GenerationError("input close values must be finite and non-null")
    if data["expected_nullable_vector"] != EXPECTED_NULLABLE or data["expected_trigger_vector"] != EXPECTED_TRIGGER: raise GenerationError("condition evidence does not preserve the accepted vector")
    return data

def generate_series_runtime(output_dir: str | os.PathLike[str]) -> dict[str, object]:
    out = Path(output_dir)
    if not out.is_dir(): raise GenerationError("output directory must be an existing directory")
    source = _SERIES_SOURCE.encode(); sha = hashlib.sha256(source).hexdigest()
    identity = _identity(SERIES_DOMAIN, [SERIES_RUNTIME_VERSION, RUNTIME_IDENTITY, ["sma", "cross_above", "cross_below"], [3], NULLABLE_SEMANTICS, source.decode(), sha])
    manifest = {"series_runtime_version": SERIES_RUNTIME_VERSION, "nullable_runtime_identity": RUNTIME_IDENTITY, "supported_operations": ["sma", "cross_above", "cross_below"], "supported_sma_periods": [3], "source_filename": SERIES_SOURCE_FILENAME, "source_sha256": sha, "series_runtime_identity": identity}
    if (out/SERIES_SOURCE_FILENAME).exists() or (out/SERIES_MANIFEST_FILENAME).exists(): raise GenerationError("generated series runtime targets must not already exist")
    done = False
    try: _publish(out, SERIES_SOURCE_FILENAME, source); done = True; _publish(out, SERIES_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":"))+"\n").encode())
    except GenerationError:
        if done: (out/SERIES_SOURCE_FILENAME).unlink(missing_ok=True)
        (out/SERIES_MANIFEST_FILENAME).unlink(missing_ok=True); raise
    return {"ok": True, **manifest, "source_path": str(out/SERIES_SOURCE_FILENAME), "manifest_path": str(out/SERIES_MANIFEST_FILENAME)}

def generate_series_tester(evidence_path: str | os.PathLike[str], runtime_manifest_path: str | os.PathLike[str], condition_manifest_path: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    evidence = _validate_evidence(Path(evidence_path)); out = Path(output_dir)
    if not out.is_dir(): raise GenerationError("output directory must be an existing directory")
    runtime = json.loads(Path(runtime_manifest_path).read_text()); condition = json.loads(Path(condition_manifest_path).read_text())
    if runtime.get("series_runtime_identity") != generate_series_runtime_identity(): raise GenerationError("series runtime manifest identity mismatch")
    if condition.get("translation_identity") != CONDITION_IDENTITY or [x.get("original_series_name") for x in condition.get("series_bindings", [])] != ["close.cross_above.sma3", "sma3.cross_below.close", "sma3"]: raise GenerationError("condition manifest identity or series bindings mismatch")
    close = evidence["input_vector"]
    def nullable(name, values, row): return f"NoraNullableDoubleV1 {name}(const int row_index)\n{{\n   if(row_index < 0 || {name}_Null[row_index]) return NoraNumericNullV1();\n   return NoraNumericValueV1({name}_Values[row_index]);\n}}"
    source = _tester_source(close, evidence, condition).encode()
    sha = hashlib.sha256(source).hexdigest()
    identity = _identity(TESTER_DOMAIN, [TESTER_VERSION, RUNTIME_IDENTITY, runtime["series_runtime_identity"], CONDITION_IDENTITY, AST_IDENTITY, INPUT_IDENTITY, close, evidence["expected_sma"], evidence["expected_cross_above"], evidence["expected_cross_below"], evidence["expected_nullable_vector"], evidence["expected_trigger_vector"], CSV_COLUMNS, source.decode(), sha])
    manifest = {"tester_fixture_version": TESTER_VERSION, "nullable_runtime_identity": RUNTIME_IDENTITY, "series_runtime_identity": runtime["series_runtime_identity"], "condition_translation_identity": CONDITION_IDENTITY, "evaluation_ast_identity": AST_IDENTITY, "rust_source_data_identity": INPUT_IDENTITY, "rust_sma_artifact_identity": INDICATOR_IDENTITY, "rust_cross_artifact_identity": CROSS_IDENTITY, "input_series_name": "close", "raw_input_vector": close, "expected_sma_vector": evidence["expected_sma"], "expected_cross_above_vector": evidence["expected_cross_above"], "expected_cross_below_vector": evidence["expected_cross_below"], "expected_nullable_vector": evidence["expected_nullable_vector"], "expected_trigger_vector": evidence["expected_trigger_vector"], "csv_schema": CSV_COLUMNS, "source_filename": TESTER_SOURCE_FILENAME, "source_sha256": sha, "tester_fixture_identity": identity}
    if (out/TESTER_SOURCE_FILENAME).exists() or (out/TESTER_MANIFEST_FILENAME).exists(): raise GenerationError("generated series tester targets must not already exist")
    done=False
    try: _publish(out, TESTER_SOURCE_FILENAME, source); done=True; _publish(out, TESTER_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":"))+"\n").encode())
    except GenerationError:
        if done: (out/TESTER_SOURCE_FILENAME).unlink(missing_ok=True)
        (out/TESTER_MANIFEST_FILENAME).unlink(missing_ok=True); raise
    return {"ok": True, **manifest, "source_path": str(out/TESTER_SOURCE_FILENAME), "manifest_path": str(out/TESTER_MANIFEST_FILENAME)}

def generate_series_runtime_identity() -> str:
    source = _SERIES_SOURCE.encode(); sha=hashlib.sha256(source).hexdigest()
    return _identity(SERIES_DOMAIN, [SERIES_RUNTIME_VERSION, RUNTIME_IDENTITY, ["sma", "cross_above", "cross_below"], [3], NULLABLE_SEMANTICS, source.decode(), sha])

def _tester_source(close, e, condition):
    def nums(values): return ", ".join("0.0" if v is None else _literal(float(v)) for v in values)
    def tri(values): return ", ".join("NORA_BOOL_NULL_V1" if v is None else ("NORA_BOOL_TRUE_V1" if v else "NORA_BOOL_FALSE_V1") for v in values)
    def booleans(values): return ", ".join("true" if v else "false" for v in values)
    numeric = "const double NoraSeriesClose[12] = {"+nums(close)+"};\nconst bool NoraSeriesCloseNull[12] = {false, false, false, false, false, false, false, false, false, false, false, false};\n"
    expected = "const double NoraExpectedSma[12] = {"+nums(e["expected_sma"])+"};\nconst bool NoraExpectedSmaNull[12] = {true, true, false, false, false, false, false, false, false, false, false, false};\nconst NoraTriBoolV1 NoraExpectedAbove[12] = {"+tri(e["expected_cross_above"])+"};\nconst NoraTriBoolV1 NoraExpectedBelow[12] = {"+tri(e["expected_cross_below"])+"};\nconst NoraTriBoolV1 NoraExpectedNullable[12] = {"+tri([None if x=="null" else x=="true" for x in e["expected_nullable_vector"]])+"};\nconst bool NoraExpectedTrigger[12] = {"+booleans(e["expected_trigger_vector"])+"};\n"
    condition_name = condition["function_name"]
    trigger_name = condition["trigger_function_name"]
    args = "NoraSeriesCrossAbove[row_index], NoraSeriesCrossBelow[row_index], NoraSeriesSma(row_index)"
    return """#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2SeriesRuntimeV1.mqh"
#include "NoraPhase2ConditionV1.mqh"

#define NORA_PHASE2K_ROW_COUNT 12
""" + numeric + expected + r'''

NoraNullableDoubleV1 NoraSeriesCloseValue(const int row_index)
{
   if(row_index < 0 || row_index >= NORA_PHASE2K_ROW_COUNT || NoraSeriesCloseNull[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(NoraSeriesClose[row_index]);
}

NoraNullableDoubleV1 NoraSeriesSma(const int row_index)
{
   return NoraSma3V1(NoraSeriesClose, NoraSeriesCloseNull, row_index);
}

string NoraPhase2KNullableText(const NoraTriBoolV1 value)
{
   if(value == NORA_BOOL_NULL_V1) return "null";
   return value == NORA_BOOL_TRUE_V1 ? "true" : "false";
}

string NoraPhase2KNumericText(const NoraNullableDoubleV1 &value)
{
   if(value.is_null) return "null";
   return DoubleToString(value.value, 16);
}

int OnInit()
{
   const int handle = FileOpen("nora_phase2_series_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE) return INIT_FAILED;
   FileWrite(handle, "record_type", "row_index", "actual_sma", "expected_sma", "actual_cross_above", "expected_cross_above", "actual_cross_below", "expected_cross_below", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   NoraTriBoolV1 NoraSeriesCrossAbove[12];
   NoraTriBoolV1 NoraSeriesCrossBelow[12];
   for(int row_index = 0; row_index < NORA_PHASE2K_ROW_COUNT; row_index++)
   {
      NoraNullableDoubleV1 current_sma = NoraSeriesSma(row_index);
      NoraNullableDoubleV1 previous_sma = row_index == 0 ? NoraNumericNullV1() : NoraSeriesSma(row_index - 1);
      NoraNullableDoubleV1 current_close = NoraSeriesCloseValue(row_index);
      NoraNullableDoubleV1 previous_close = row_index == 0 ? NoraNumericNullV1() : NoraSeriesCloseValue(row_index - 1);
      NoraSeriesCrossAbove[row_index] = NoraCrossAboveV1(previous_close, previous_sma, current_close, current_sma);
      NoraSeriesCrossBelow[row_index] = NoraCrossBelowV1(previous_sma, previous_close, current_sma, current_close);
      NoraTriBoolV1 actual_nullable = ''' + condition_name + '''(''' + args + r''');
      bool actual_trigger = ''' + trigger_name + '''(''' + args + r''');
      bool row_pass = current_sma.is_null == NoraExpectedSmaNull[row_index] && (current_sma.is_null || MathAbs(current_sma.value - NoraExpectedSma[row_index]) < 0.000000000000001) && NoraSeriesCrossAbove[row_index] == NoraExpectedAbove[row_index] && NoraSeriesCrossBelow[row_index] == NoraExpectedBelow[row_index] && actual_nullable == NoraExpectedNullable[row_index] && actual_trigger == NoraExpectedTrigger[row_index];
      if(row_pass) passed_rows++; else failed_rows++;
      FileWrite(handle, "row", row_index, NoraPhase2KNumericText(current_sma), NoraExpectedSmaNull[row_index] ? "null" : DoubleToString(NoraExpectedSma[row_index], 16), NoraPhase2KNullableText(NoraSeriesCrossAbove[row_index]), NoraPhase2KNullableText(NoraExpectedAbove[row_index]), NoraPhase2KNullableText(NoraSeriesCrossBelow[row_index]), NoraPhase2KNullableText(NoraExpectedBelow[row_index]), NoraPhase2KNullableText(actual_nullable), NoraPhase2KNullableText(NoraExpectedNullable[row_index]), actual_trigger ? "true" : "false", NoraExpectedTrigger[row_index] ? "true" : "false", row_pass ? "true" : "false", "", "", "", "");
   }
   bool overall_pass = passed_rows == NORA_PHASE2K_ROW_COUNT && failed_rows == 0;
   FileWrite(handle, "summary", -1, "", "", "", "", "", "", "", "", "", "", overall_pass ? "true" : "false", NORA_PHASE2K_ROW_COUNT, passed_rows, failed_rows, overall_pass ? "true" : "false");
   FileFlush(handle);
   FileClose(handle);
   TesterStop();
   return overall_pass ? INIT_SUCCEEDED : INIT_FAILED;
}
'''
