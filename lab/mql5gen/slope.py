"""Deterministic Phase-2M slope source generation."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from . import GenerationError, _publish

SLOPE_RUNTIME_VERSION = "nora_mql5_slope_runtime_v1"
SLOPE_SOURCE_FILENAME = "NoraPhase2SlopeRuntimeV1.mqh"
SLOPE_MANIFEST_FILENAME = "NoraPhase2SlopeRuntimeV1.manifest.json"
SLOPE_DOMAIN = "nora.mql5.slope_runtime_v1.semantic.v1"
TESTER_VERSION = "nora_mql5_slope_tester_canary_v1"
TESTER_SOURCE_FILENAME = "NoraPhase2SlopeTesterCanaryV1.mq5"
TESTER_MANIFEST_FILENAME = "NoraPhase2SlopeTesterCanaryV1.manifest.json"
TESTER_DOMAIN = "nora.mql5.slope_tester_canary_v1.semantic.v1"
RUNTIME_IDENTITY = "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d"
CSV_COLUMNS = ["record_type", "row_index", "actual_slope", "expected_slope", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]

# Frozen evidence values
INPUT_IDENTITY = "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383"
SLOPE_IDENTITY = "45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499"
INPUT_SERIES_NAME = "sma3"
INPUT_VECTOR = [None, None, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334]
INPUT_NULL_POSITIONS = [0, 1]
LOOKBACK = 1
EXPECTED_SLOPE = [None, None, None, 0.00033333333333351867, 3.333333333310762e-05, 0.00036666666666684833, 3.333333333310762e-05, 0.00036666666666684833, 3.333333333310762e-05, 0.00036666666666684833, 3.333333333310762e-05, 0.00036666666666684833]

_SLOPE_SOURCE = r'''#ifndef NORA_PHASE2_SLOPE_RUNTIME_V1_MQH
#define NORA_PHASE2_SLOPE_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraSlopeLookback1V1(
   const NoraNullableDoubleV1 &current_value,
   const NoraNullableDoubleV1 &previous_value
)
{
   if(current_value.is_null || previous_value.is_null)
      return NoraNumericNullV1();
   double v = (current_value.value - previous_value.value) / 1.0;
   if(!MathIsValidNumber(v))
      return NoraNumericNullV1();
   return NoraNumericValueV1(v);
}

#endif
'''

def _part(h, value: bytes) -> None:
    h.update(len(value).to_bytes(8, "big"))
    h.update(value)

def _identity(domain: str, values: list[object]) -> str:
    h = hashlib.sha256()
    _part(h, domain.encode())
    for value in values:
        _part(h, json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
    return h.hexdigest()

def _literal(value: float) -> str:
    return format(value, ".17g")

def _text(value):
    if value is None:
        return "null"
    return format(float(value), ".16f")

def _validate_evidence(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise GenerationError("slope evidence is unreadable or malformed") from e
    required = {"rust_input_identity", "rust_slope_identity", "input_series_name", "input_vector", "input_null_positions", "lookback", "expected_slope_vector", "rust_task_command"}
    if set(data) != required:
        raise GenerationError("slope evidence fields are inconsistent")
    if data["input_series_name"] != INPUT_SERIES_NAME or data["lookback"] != LOOKBACK:
        raise GenerationError("slope evidence is not the accepted sma3/slope fixture")
    if data["rust_input_identity"] != INPUT_IDENTITY or data["rust_slope_identity"] != SLOPE_IDENTITY:
        raise GenerationError("Rust slope artifact identity does not match the accepted fixture")
    vectors = [data["input_vector"], data["expected_slope_vector"]]
    if any(len(v) != 12 for v in vectors):
        raise GenerationError("slope evidence vectors must have length 12")
    if data["input_null_positions"] != INPUT_NULL_POSITIONS:
        raise GenerationError("input null positions do not match the accepted fixture")
    for v in data["input_vector"]:
        if v is not None and (not isinstance(v, (int, float)) or not math.isfinite(float(v))):
            raise GenerationError("input values must be finite or null")
    return data

def generate_slope_runtime(output_dir: str | os.PathLike[str]) -> dict[str, object]:
    out = Path(output_dir)
    if not out.is_dir():
        raise GenerationError("output directory must be an existing directory")
    source = _SLOPE_SOURCE.encode()
    sha = hashlib.sha256(source).hexdigest()
    identity = _identity(SLOPE_DOMAIN, [
        SLOPE_RUNTIME_VERSION,
        RUNTIME_IDENTITY,
        ["slope"],
        [1],
        {"formula": "(current - previous) / lookback", "null_policy": "null if either endpoint is null", "finite_policy": "null if non-finite"},
        source.decode(),
        sha
    ])
    manifest = {
        "slope_runtime_version": SLOPE_RUNTIME_VERSION,
        "nullable_runtime_identity": RUNTIME_IDENTITY,
        "supported_operations": ["slope"],
        "supported_lookbacks": [1],
        "formula": "(current - previous) / lookback",
        "source_filename": SLOPE_SOURCE_FILENAME,
        "source_sha256": sha,
        "slope_runtime_identity": identity
    }
    if (out / SLOPE_SOURCE_FILENAME).exists() or (out / SLOPE_MANIFEST_FILENAME).exists():
        raise GenerationError("generated slope runtime targets must not already exist")
    done = False
    try:
        _publish(out, SLOPE_SOURCE_FILENAME, source)
        done = True
        _publish(out, SLOPE_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode())
    except GenerationError:
        if done:
            (out / SLOPE_SOURCE_FILENAME).unlink(missing_ok=True)
        (out / SLOPE_MANIFEST_FILENAME).unlink(missing_ok=True)
        raise
    return {"ok": True, **manifest, "source_path": str(out / SLOPE_SOURCE_FILENAME), "manifest_path": str(out / SLOPE_MANIFEST_FILENAME)}

def generate_slope_tester(evidence_path: str | os.PathLike[str], runtime_manifest_path: str | os.PathLike[str], output_dir: str | os.PathLike[str]) -> dict[str, object]:
    evidence = _validate_evidence(Path(evidence_path))
    out = Path(output_dir)
    if not out.is_dir():
        raise GenerationError("output directory must be an existing directory")
    runtime = json.loads(Path(runtime_manifest_path).read_text())
    if runtime.get("slope_runtime_identity") != generate_slope_runtime_identity():
        raise GenerationError("slope runtime manifest identity mismatch")

    close = evidence["input_vector"]
    expected = evidence["expected_slope_vector"]

    def nums(values):
        return ", ".join("0.0" if v is None else _literal(float(v)) for v in values)

    def tri(values):
        return ", ".join("NORA_BOOL_NULL_V1" if v is None else ("NORA_BOOL_TRUE_V1" if v else "NORA_BOOL_FALSE_V1") for v in values)

    numeric = (
        "const double NoraSlopeInput_Values[12] = {" + nums(close) + "};\n"
        "const bool NoraSlopeInput_NullMask[12] = {" + ", ".join("true" if v is None else "false" for v in close) + "};\n"
    )
    expected_block = (
        "const double NoraExpectedSlope_Values[12] = {" + nums(expected) + "};\n"
        "const bool NoraExpectedSlope_NullMask[12] = {" + ", ".join("true" if v is None else "false" for v in expected) + "};\n"
    )

    source_text = """#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2SlopeRuntimeV1.mqh"

#define NORA_PHASE2M_ROW_COUNT 12

""" + numeric + expected_block + r'''

NoraNullableDoubleV1 NoraSlopeInputValue(const int row_index)
{
   if(row_index < 0 || row_index >= NORA_PHASE2M_ROW_COUNT || NoraSlopeInput_NullMask[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(NoraSlopeInput_Values[row_index]);
}

string NoraPhase2MNullableText(const NoraNullableDoubleV1 &value)
{
   if(value.is_null)
      return "null";
   return DoubleToString(value.value, 16);
}

int OnInit()
{
   const int handle = FileOpen("nora_phase2_slope_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
      return INIT_FAILED;
   FileWrite(handle, "record_type", "row_index", "actual_slope", "expected_slope", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   for(int row_index = 0; row_index < NORA_PHASE2M_ROW_COUNT; row_index++)
   {
      NoraNullableDoubleV1 current = NoraSlopeInputValue(row_index);
      NoraNullableDoubleV1 previous = row_index == 0 ? NoraNumericNullV1() : NoraSlopeInputValue(row_index - 1);
      NoraNullableDoubleV1 actual_slope = NoraSlopeLookback1V1(current, previous);
      bool current_null = actual_slope.is_null;
      bool expected_null = NoraExpectedSlope_NullMask[row_index];
      bool row_pass = false;
      if(current_null && expected_null)
         row_pass = true;
      else if(!current_null && !expected_null)
         row_pass = MathAbs(actual_slope.value - NoraExpectedSlope_Values[row_index]) < 0.000000000000001;
      if(row_pass)
         passed_rows++;
      else
         failed_rows++;
      FileWrite(handle, "row", row_index, NoraPhase2MNullableText(actual_slope), expected_null ? "null" : DoubleToString(NoraExpectedSlope_Values[row_index], 16), row_pass ? "true" : "false", "", "", "", "");
   }
   bool overall_pass = passed_rows == NORA_PHASE2M_ROW_COUNT && failed_rows == 0;
   FileWrite(handle, "summary", -1, "", "", overall_pass ? "true" : "false", NORA_PHASE2M_ROW_COUNT, passed_rows, failed_rows, overall_pass ? "true" : "false");
   FileFlush(handle);
   FileClose(handle);
   TesterStop();
   return overall_pass ? INIT_SUCCEEDED : INIT_FAILED;
}
'''
    source = source_text.encode("utf-8")
    sha = hashlib.sha256(source).hexdigest()
    identity = _identity(TESTER_DOMAIN, [
        TESTER_VERSION,
        RUNTIME_IDENTITY,
        runtime["slope_runtime_identity"],
        INPUT_IDENTITY,
        SLOPE_IDENTITY,
        LOOKBACK,
        close,
        expected,
        CSV_COLUMNS,
        "nora_phase2_slope_tester_v1.csv",
        source_text,
        sha
    ])
    manifest = {
        "slope_tester_version": TESTER_VERSION,
        "nullable_runtime_identity": RUNTIME_IDENTITY,
        "slope_runtime_identity": runtime["slope_runtime_identity"],
        "rust_input_identity": INPUT_IDENTITY,
        "rust_slope_identity": SLOPE_IDENTITY,
        "lookback": LOOKBACK,
        "row_count": 12,
        "input_vector": [v if v is not None else None for v in close],
        "expected_slope_vector": [v if v is not None else None for v in expected],
        "result_filename": "nora_phase2_slope_tester_v1.csv",
        "source_filename": TESTER_SOURCE_FILENAME,
        "source_sha256": sha,
        "slope_tester_identity": identity
    }
    if (out / TESTER_SOURCE_FILENAME).exists() or (out / TESTER_MANIFEST_FILENAME).exists():
        raise GenerationError("generated slope tester targets must not already exist")
    done = False
    try:
        _publish(out, TESTER_SOURCE_FILENAME, source)
        done = True
        _publish(out, TESTER_MANIFEST_FILENAME, (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode())
    except GenerationError:
        if done:
            (out / TESTER_SOURCE_FILENAME).unlink(missing_ok=True)
        (out / TESTER_MANIFEST_FILENAME).unlink(missing_ok=True)
        raise
    return {"ok": True, **manifest, "source_path": str(out / TESTER_SOURCE_FILENAME), "manifest_path": str(out / TESTER_MANIFEST_FILENAME)}

def generate_slope_runtime_identity() -> str:
    source = _SLOPE_SOURCE.encode()
    sha = hashlib.sha256(source).hexdigest()
    return _identity(SLOPE_DOMAIN, [
        SLOPE_RUNTIME_VERSION,
        RUNTIME_IDENTITY,
        ["slope"],
        [1],
        {"formula": "(current - previous) / lookback", "null_policy": "null if either endpoint is null", "finite_policy": "null if non-finite"},
        source.decode(),
        sha
    ])

def main():
    import sys
    argv = sys.argv[1:]
    if not argv or argv[0] not in {"slope-runtime", "slope-tester"}:
        print("Usage: python -m lab.mql5gen.slope {slope-runtime|slope-tester} --output-dir <dir> [--evidence <path> --runtime-manifest <path>]", file=sys.stderr)
        sys.exit(2)
    mode = argv[0]
    if mode == "slope-runtime":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--output-dir", required=True)
        args = parser.parse_args(argv[1:])
        result = generate_slope_runtime(args.output_dir)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    elif mode == "slope-tester":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--evidence", required=True)
        parser.add_argument("--runtime-manifest", required=True)
        parser.add_argument("--output-dir", required=True)
        args = parser.parse_args(argv[1:])
        result = generate_slope_tester(args.evidence, args.runtime_manifest, args.output_dir)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
