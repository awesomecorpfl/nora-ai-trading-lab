"""Deterministic Phase-2P ATR and Distance/ATR canary generation.

This module intentionally generates source only.  It neither invokes an MT5
tool nor treats generated artifacts as native-parity evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from . import GenerationError, _publish

ATR_RUNTIME_VERSION = "nora_mql5_atr_runtime_v1"
DISTANCE_RUNTIME_VERSION = "nora_mql5_distance_atr_runtime_v1"
TESTER_VERSION = "nora_mql5_atr_distance_tester_canary_v1"
EVIDENCE_VERSION = "nora_phase2p_rust_atr_distance_evidence_v1"
ATR_SOURCE_FILENAME = "NoraPhase2AtrRuntimeV1.mqh"
ATR_MANIFEST_FILENAME = "NoraPhase2AtrRuntimeV1.manifest.json"
DISTANCE_SOURCE_FILENAME = "NoraPhase2DistanceAtrRuntimeV1.mqh"
DISTANCE_MANIFEST_FILENAME = "NoraPhase2DistanceAtrRuntimeV1.manifest.json"
TESTER_SOURCE_FILENAME = "NoraPhase2AtrDistanceTesterCanaryV1.mq5"
TESTER_MANIFEST_FILENAME = "NoraPhase2AtrDistanceTesterCanaryV1.manifest.json"
EVIDENCE_FILENAME = "phase2p_atr_distance_rust_evidence.json"
ROW_COUNT = 12
ATR_PERIOD = 3
NULLABLE_RUNTIME_IDENTITY = "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d"
RUST_TASK_IDENTITY = "c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad"
RUST_INPUT_IDENTITY = "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383"
RUST_TASK_PATH = "engine/labengine/tests/fixtures/phase2_distance_atr_task.json"
RUST_INPUT_PATH = "engine/labengine/tests/fixtures/phase2_indicator_utc.parquet"
RUST_TASK_COMMAND = "engine/target/debug/labengine engine/labengine/tests/fixtures/phase2_distance_atr_task.json"
RUST_TASK_JSON = {"task_version": 1, "task_type": "compute_indicators", "input_path": RUST_INPUT_PATH, "output_path": "/tmp/phase2_distance_atr_output.parquet", "indicators": [{"name": "SMA", "output": "sma3", "period": 3}, {"name": "ATR", "output": "atr3", "period": 3}, {"name": "DistanceAtr", "input": {"series": "close", "type": "numeric"}, "reference": {"series": "sma3", "type": "numeric"}, "atr": {"series": "atr3", "type": "numeric"}, "output": "close_sma3.distance_atr"}, {"name": "Slope", "input": {"series": "close_sma3.distance_atr", "type": "numeric"}, "lookback": 1, "output": "close_sma3.distance_atr.slope"}]}
CSV_COLUMNS = ["record_type", "row_index", "timestamp", "open", "high", "low", "close", "previous_close", "actual_atr", "expected_atr", "distance_numerator", "actual_distance_atr", "expected_distance_atr", "atr_nullable", "distance_atr_nullable", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]


def _part(hasher, value: bytes) -> None:
    hasher.update(len(value).to_bytes(8, "big"))
    hasher.update(value)


def identity(domain: str, *values: object) -> str:
    digest = hashlib.sha256()
    _part(digest, domain.encode("utf-8"))
    for value in values:
        _part(digest, json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _literal(value: float) -> str:
    return format(value, ".17g")


def _nullable_positions(values: list[float | None]) -> list[int]:
    return [index for index, value in enumerate(values) if value is None]


def _finite_vector(values: list[float], name: str) -> None:
    if len(values) != ROW_COUNT or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
        raise GenerationError(f"{name} must contain {ROW_COUNT} finite values")


def derive_atr(high: list[float], low: list[float], close: list[float], period: int = ATR_PERIOD) -> tuple[list[float], list[float | None]]:
    """Mirror `indicators::atr`: TR then a Wilder seed and recurrence."""
    if period != ATR_PERIOD:
        raise GenerationError("only frozen ATR period 3 is supported")
    for name, values in (("high", high), ("low", low), ("close", close)):
        _finite_vector(values, name)
    true_range = []
    for index in range(ROW_COUNT):
        if index == 0:
            value = high[index] - low[index]
        else:
            value = max(high[index] - low[index], abs(high[index] - close[index - 1]), abs(low[index] - close[index - 1]))
        if not math.isfinite(value):
            raise GenerationError("ATR true range is non-finite")
        true_range.append(value)
    atr: list[float | None] = [None] * ROW_COUNT
    value = sum(true_range[:period]) / period
    atr[period - 1] = value
    for index in range(period, ROW_COUNT):
        value = (value * (period - 1) + true_range[index]) / period
        atr[index] = value
    return true_range, atr


def derive_distance_atr(input_values: list[float | None], reference: list[float | None], atr: list[float | None]) -> tuple[list[float | None], list[float | None]]:
    """Mirror `transform_distance_atr` including its positive-denominator rule."""
    if any(len(values) != ROW_COUNT for values in (input_values, reference, atr)):
        raise GenerationError("distance/ATR vectors must have the frozen row count")
    numerator: list[float | None] = []
    output: list[float | None] = []
    for input_value, reference_value, denominator in zip(input_values, reference, atr):
        if input_value is None or reference_value is None:
            numerator.append(None)
            output.append(None)
            continue
        delta = input_value - reference_value
        numerator.append(delta if math.isfinite(delta) else None)
        if denominator is None or not math.isfinite(denominator) or denominator <= 0 or not math.isfinite(delta):
            output.append(None)
            continue
        value = delta / denominator
        output.append(value if math.isfinite(value) else None)
    return numerator, output


def _evidence_identities(evidence: dict[str, object]) -> tuple[str, str, str]:
    atr_identity = identity("nora.phase2p.rust_atr_evidence.v1", evidence["rust_input_identity"], evidence["timestamps"], evidence["high"], evidence["low"], evidence["close"], evidence["true_range"], evidence["atr_vector"], ATR_PERIOD)
    distance_identity = identity("nora.phase2p.rust_distance_atr_evidence.v1", evidence["rust_task_output_semantic_identity"], evidence["close"], evidence["sma3_vector"], evidence["atr_vector"], evidence["distance_numerator"], evidence["distance_atr_vector"])
    package_identity = identity("nora.phase2p.atr_distance_fixture_package.v1", EVIDENCE_VERSION, atr_identity, distance_identity, evidence["row_count"], evidence["timestamps"])
    return atr_identity, distance_identity, package_identity


def evidence_from_vectors(*, timestamps: list[str], open_values: list[float], high: list[float], low: list[float], close: list[float], sma3: list[float | None], rust_task_output_semantic_identity: str = RUST_TASK_IDENTITY, rust_input_identity: str = RUST_INPUT_IDENTITY) -> dict[str, object]:
    if len(timestamps) != ROW_COUNT or timestamps != sorted(timestamps) or len(set(timestamps)) != ROW_COUNT:
        raise GenerationError("timestamps must be 12 strictly ordered UTC fixture labels")
    _finite_vector(open_values, "open")
    true_range, atr = derive_atr(high, low, close)
    numerator, distance = derive_distance_atr(close, sma3, atr)
    evidence: dict[str, object] = {
        "evidence_version": EVIDENCE_VERSION,
        "rust_task_command": RUST_TASK_COMMAND,
        "rust_task_fixture_path": RUST_TASK_PATH,
        "rust_task_json": RUST_TASK_JSON,
        "rust_input_fixture_path": RUST_INPUT_PATH,
        "rust_task_output_semantic_identity": rust_task_output_semantic_identity,
        "rust_input_identity": rust_input_identity,
        "timestamp_clock": "UTC fixture labels; no conversion or broker-time transformation",
        "row_count": ROW_COUNT,
        "timestamps": timestamps,
        "open": open_values,
        "high": high,
        "low": low,
        "close": close,
        "sma3_vector": sma3,
        "true_range": true_range,
        "atr_period": ATR_PERIOD,
        "atr_method": "Wilder seed mean followed by (previous*(period-1)+true_range)/period",
        "atr_vector": atr,
        "distance_numerator": numerator,
        "distance_atr_vector": distance,
        "atr_null_positions": _nullable_positions(atr),
        "distance_atr_null_positions": _nullable_positions(distance),
    }
    atr_identity, distance_identity, package_identity = _evidence_identities(evidence)
    evidence["rust_atr_evidence_identity"] = atr_identity
    evidence["rust_distance_atr_evidence_identity"] = distance_identity
    evidence["fixture_package_identity"] = package_identity
    return evidence


def _validate_evidence(path: Path) -> dict[str, object]:
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError("ATR/Distance evidence is unreadable or malformed") from error
    required = {"evidence_version", "rust_task_command", "rust_task_fixture_path", "rust_task_json", "rust_input_fixture_path", "rust_task_output_semantic_identity", "rust_input_identity", "timestamp_clock", "row_count", "timestamps", "open", "high", "low", "close", "sma3_vector", "true_range", "atr_period", "atr_method", "atr_vector", "distance_numerator", "distance_atr_vector", "atr_null_positions", "distance_atr_null_positions", "rust_atr_evidence_identity", "rust_distance_atr_evidence_identity", "fixture_package_identity"}
    if set(evidence) != required:
        raise GenerationError("ATR/Distance evidence fields are inconsistent")
    if evidence["evidence_version"] != EVIDENCE_VERSION or evidence["rust_task_command"] != RUST_TASK_COMMAND:
        raise GenerationError("ATR/Distance evidence version or task command is not frozen")
    if evidence["rust_task_fixture_path"] != RUST_TASK_PATH or evidence["rust_input_fixture_path"] != RUST_INPUT_PATH:
        raise GenerationError("ATR/Distance evidence fixture paths are not normalized")
    if evidence["rust_task_json"] != RUST_TASK_JSON:
        raise GenerationError("ATR/Distance evidence task JSON is not frozen")
    if evidence["rust_task_output_semantic_identity"] != RUST_TASK_IDENTITY or evidence["rust_input_identity"] != RUST_INPUT_IDENTITY:
        raise GenerationError("Rust fixture identity does not match the accepted Distance/ATR fixture")
    if evidence["row_count"] != ROW_COUNT or evidence["atr_period"] != ATR_PERIOD:
        raise GenerationError("ATR/Distance evidence row count or period is unsupported")
    canonical = evidence_from_vectors(timestamps=evidence["timestamps"], open_values=evidence["open"], high=evidence["high"], low=evidence["low"], close=evidence["close"], sma3=evidence["sma3_vector"], rust_task_output_semantic_identity=evidence["rust_task_output_semantic_identity"], rust_input_identity=evidence["rust_input_identity"])
    for key in ("true_range", "atr_vector", "distance_numerator", "distance_atr_vector", "atr_null_positions", "distance_atr_null_positions", "rust_atr_evidence_identity", "rust_distance_atr_evidence_identity", "fixture_package_identity"):
        if evidence[key] != canonical[key]:
            raise GenerationError(f"ATR/Distance evidence {key} does not match frozen Rust semantics")
    return evidence


_ATR_SOURCE = r'''#ifndef NORA_PHASE2_ATR_RUNTIME_V1_MQH
#define NORA_PHASE2_ATR_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraAtr3V1(const double &high_values[], const double &low_values[], const double &close_values[], const int row_index)
{
   if(row_index < 0 || !MathIsValidNumber(high_values[row_index]) || !MathIsValidNumber(low_values[row_index]) || !MathIsValidNumber(close_values[row_index]))
      return NoraNumericNullV1();
   double tr_sum = 0.0;
   double atr_value = 0.0;
   for(int index = 0; index <= row_index; index++)
   {
      if(!MathIsValidNumber(high_values[index]) || !MathIsValidNumber(low_values[index]) || !MathIsValidNumber(close_values[index]))
         return NoraNumericNullV1();
      double true_range = high_values[index] - low_values[index];
      if(index > 0)
         true_range = MathMax(true_range, MathMax(MathAbs(high_values[index] - close_values[index - 1]), MathAbs(low_values[index] - close_values[index - 1])));
      if(!MathIsValidNumber(true_range))
         return NoraNumericNullV1();
      if(index < 3)
      {
         tr_sum += true_range;
         if(index == 2)
            atr_value = tr_sum / 3.0;
      }
      else
         atr_value = (atr_value * 2.0 + true_range) / 3.0;
   }
   if(row_index < 2 || !MathIsValidNumber(atr_value))
      return NoraNumericNullV1();
   return NoraNumericValueV1(atr_value);
}

#endif
'''

_DISTANCE_SOURCE = r'''#ifndef NORA_PHASE2_DISTANCE_ATR_RUNTIME_V1_MQH
#define NORA_PHASE2_DISTANCE_ATR_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraDistanceAtrV1(const NoraNullableDoubleV1 &input_value, const NoraNullableDoubleV1 &reference_value, const NoraNullableDoubleV1 &atr_value)
{
   if(input_value.is_null || reference_value.is_null || atr_value.is_null || !MathIsValidNumber(input_value.value) || !MathIsValidNumber(reference_value.value) || !MathIsValidNumber(atr_value.value) || atr_value.value <= 0.0)
      return NoraNumericNullV1();
   double numerator = input_value.value - reference_value.value;
   double result = numerator / atr_value.value;
   if(!MathIsValidNumber(numerator) || !MathIsValidNumber(result))
      return NoraNumericNullV1();
   return NoraNumericValueV1(result);
}

#endif
'''


def _runtime_manifest(version: str, filename: str, source: str, domain: str, semantics: dict[str, object]) -> dict[str, object]:
    source_sha = _sha(source)
    runtime_identity = identity(domain, version, NULLABLE_RUNTIME_IDENTITY, semantics, source, source_sha)
    key = "atr_runtime_identity" if version == ATR_RUNTIME_VERSION else "distance_atr_runtime_identity"
    return {"runtime_version": version, "nullable_runtime_identity": NULLABLE_RUNTIME_IDENTITY, "semantics": semantics, "source_filename": filename, "source_sha256": source_sha, key: runtime_identity}


def atr_runtime_manifest() -> dict[str, object]:
    return _runtime_manifest(ATR_RUNTIME_VERSION, ATR_SOURCE_FILENAME, _ATR_SOURCE, "nora.mql5.atr_runtime.v1", {"period": 3, "true_range": "row0=high-low; later=max(high-low,abs(high-previous_close),abs(low-previous_close))", "method": "Wilder seed mean then recurrence", "warmup": "null before row index 2", "finite_input_policy": "null on non-finite input or result", "row_order": "input order"})


def distance_runtime_manifest() -> dict[str, object]:
    return _runtime_manifest(DISTANCE_RUNTIME_VERSION, DISTANCE_SOURCE_FILENAME, _DISTANCE_SOURCE, "nora.mql5.distance_atr_runtime.v1", {"formula": "(input-reference)/atr", "alignment": "same row", "null_policy": "null if input, reference, or atr is null", "denominator_policy": "null unless finite atr > 0", "finite_output_policy": "null on non-finite numerator or result", "row_order": "input order"})


def _write_files(output: Path, files: list[tuple[str, bytes]]) -> None:
    if not output.is_dir():
        raise GenerationError("output directory must be an existing directory")
    targets = [output / filename for filename, _ in files]
    if any(target.exists() for target in targets):
        raise GenerationError("generated ATR/Distance targets must not already exist")
    published: list[Path] = []
    try:
        for filename, payload in files:
            _publish(output, filename, payload)
            published.append(output / filename)
    except Exception:
        for target in published:
            target.unlink(missing_ok=True)
        raise


def _numbers(values: list[float | None]) -> str:
    return ", ".join("0.0" if value is None else _literal(float(value)) for value in values)


def _nulls(values: list[float | None]) -> str:
    return ", ".join("true" if value is None else "false" for value in values)


def _tester_source(evidence: dict[str, object]) -> str:
    arrays = []
    for name in ("open", "high", "low", "close", "sma3_vector", "atr_vector", "distance_atr_vector"):
        variable = {"sma3_vector": "Sma3", "atr_vector": "ExpectedAtr", "distance_atr_vector": "ExpectedDistanceAtr"}.get(name, name.title())
        values = evidence[name]
        arrays.append(f"const double Nora{variable}_Values[12] = {{" + _numbers(values) + "};")
        arrays.append(f"const bool Nora{variable}_NullMask[12] = {{" + _nulls(values) + "};")
    timestamps = ", ".join('"' + value + '"' for value in evidence["timestamps"])
    return """#property strict

#include \"NoraPhase2RuntimeV1.mqh\"
#include \"NoraPhase2AtrRuntimeV1.mqh\"
#include \"NoraPhase2DistanceAtrRuntimeV1.mqh\"

#define NORA_PHASE2P_ROW_COUNT 12

const string NoraTimestamp_Values[12] = {""" + timestamps + "};\n" + "\n".join(arrays) + r'''

NoraNullableDoubleV1 NoraPhase2PValue(const double &values[], const bool &null_mask[], const int row_index)
{
   if(row_index < 0 || row_index >= NORA_PHASE2P_ROW_COUNT || null_mask[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(values[row_index]);
}

string NoraPhase2PNullableText(const NoraNullableDoubleV1 &value)
{
   if(value.is_null)
      return "null";
   return DoubleToString(value.value, 16);
}

int OnInit()
{
   const int handle = FileOpen("nora_phase2_atr_distance_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
      return INIT_FAILED;
   FileWrite(handle, "record_type", "row_index", "timestamp", "open", "high", "low", "close", "previous_close", "actual_atr", "expected_atr", "distance_numerator", "actual_distance_atr", "expected_distance_atr", "atr_nullable", "distance_atr_nullable", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   for(int row_index = 0; row_index < NORA_PHASE2P_ROW_COUNT; row_index++)
   {
      NoraNullableDoubleV1 actual_atr = NoraAtr3V1(NoraHigh_Values, NoraLow_Values, NoraClose_Values, row_index);
      NoraNullableDoubleV1 close_value = NoraPhase2PValue(NoraClose_Values, NoraClose_NullMask, row_index);
      NoraNullableDoubleV1 sma_value = NoraPhase2PValue(NoraSma3_Values, NoraSma3_NullMask, row_index);
      NoraNullableDoubleV1 actual_distance = NoraDistanceAtrV1(close_value, sma_value, actual_atr);
      NoraNullableDoubleV1 expected_atr = NoraPhase2PValue(NoraExpectedAtr_Values, NoraExpectedAtr_NullMask, row_index);
      NoraNullableDoubleV1 expected_distance = NoraPhase2PValue(NoraExpectedDistanceAtr_Values, NoraExpectedDistanceAtr_NullMask, row_index);
      NoraNullableDoubleV1 numerator = (close_value.is_null || sma_value.is_null) ? NoraNumericNullV1() : NoraNumericValueV1(close_value.value - sma_value.value);
      bool atr_pass = actual_atr.is_null == expected_atr.is_null && (actual_atr.is_null || MathAbs(actual_atr.value - expected_atr.value) < 0.000000000000001);
      bool distance_pass = actual_distance.is_null == expected_distance.is_null && (actual_distance.is_null || MathAbs(actual_distance.value - expected_distance.value) < 0.000000000000001);
      bool row_pass = atr_pass && distance_pass;
      if(row_pass)
         passed_rows++;
      else
         failed_rows++;
      string previous_close = row_index == 0 ? "null" : DoubleToString(NoraClose_Values[row_index - 1], 16);
      FileWrite(handle, "row", row_index, NoraTimestamp_Values[row_index], DoubleToString(NoraOpen_Values[row_index], 16), DoubleToString(NoraHigh_Values[row_index], 16), DoubleToString(NoraLow_Values[row_index], 16), DoubleToString(NoraClose_Values[row_index], 16), previous_close, NoraPhase2PNullableText(actual_atr), NoraPhase2PNullableText(expected_atr), NoraPhase2PNullableText(numerator), NoraPhase2PNullableText(actual_distance), NoraPhase2PNullableText(expected_distance), actual_atr.is_null ? "true" : "false", actual_distance.is_null ? "true" : "false", row_pass ? "true" : "false", "", "", "", "");
   }
   bool overall_pass = passed_rows == NORA_PHASE2P_ROW_COUNT && failed_rows == 0;
   FileWrite(handle, "summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", overall_pass ? "true" : "false", NORA_PHASE2P_ROW_COUNT, passed_rows, failed_rows, overall_pass ? "true" : "false");
   FileFlush(handle);
   FileClose(handle);
   TesterStop();
   return overall_pass ? INIT_SUCCEEDED : INIT_FAILED;
}
'''


def generate_package(evidence_path: str | os.PathLike[str], output_dir: str | os.PathLike[str], repository_root: str | os.PathLike[str] | None = None) -> dict[str, object]:
    evidence = _validate_evidence(Path(evidence_path))
    root = Path.cwd() if repository_root is None else Path(repository_root)
    if not (root / RUST_INPUT_PATH).is_file():
        raise GenerationError("frozen Rust input fixture is missing")
    try:
        task_json = json.loads((root / RUST_TASK_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError("frozen Rust task fixture is missing or malformed") from error
    if task_json != RUST_TASK_JSON:
        raise GenerationError("frozen Rust task fixture differs from evidence")
    atr_manifest = atr_runtime_manifest()
    distance_manifest = distance_runtime_manifest()
    source = _tester_source(evidence)
    source_sha = _sha(source)
    tester_identity = identity("nora.mql5.atr_distance_tester.v1", TESTER_VERSION, NULLABLE_RUNTIME_IDENTITY, atr_manifest["atr_runtime_identity"], distance_manifest["distance_atr_runtime_identity"], evidence["rust_atr_evidence_identity"], evidence["rust_distance_atr_evidence_identity"], CSV_COLUMNS, source, source_sha)
    tester_manifest = {"tester_version": TESTER_VERSION, "nullable_runtime_identity": NULLABLE_RUNTIME_IDENTITY, "atr_runtime_identity": atr_manifest["atr_runtime_identity"], "distance_atr_runtime_identity": distance_manifest["distance_atr_runtime_identity"], "rust_atr_evidence_identity": evidence["rust_atr_evidence_identity"], "rust_distance_atr_evidence_identity": evidence["rust_distance_atr_evidence_identity"], "fixture_package_identity": evidence["fixture_package_identity"], "row_count": ROW_COUNT, "result_filename": "nora_phase2_atr_distance_tester_v1.csv", "csv_columns": CSV_COLUMNS, "source_filename": TESTER_SOURCE_FILENAME, "source_sha256": source_sha, "tester_identity": tester_identity}
    files = [(ATR_SOURCE_FILENAME, _ATR_SOURCE.encode()), (ATR_MANIFEST_FILENAME, (json.dumps(atr_manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()), (DISTANCE_SOURCE_FILENAME, _DISTANCE_SOURCE.encode()), (DISTANCE_MANIFEST_FILENAME, (json.dumps(distance_manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()), (TESTER_SOURCE_FILENAME, source.encode()), (TESTER_MANIFEST_FILENAME, (json.dumps(tester_manifest, sort_keys=True, separators=(",", ":")) + "\n").encode())]
    out = Path(output_dir)
    _write_files(out, files)
    return {"ok": True, **tester_manifest}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(prog="python -m lab.mql5gen.atr_distance")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(generate_package(args.evidence, args.output_dir), sort_keys=True, separators=(",", ":")))
    except GenerationError as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True, separators=(",", ":")), file=os.sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
