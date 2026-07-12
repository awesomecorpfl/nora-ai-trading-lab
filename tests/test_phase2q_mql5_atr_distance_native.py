"""Phase-2Q native ATR and Distance/ATR canary regression tests."""
import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from lab.mt5 import (
    ATR_DISTANCE_CSV_SCHEMA,
    ATR_DISTANCE_TESTER_IDENTITY,
    ATR_DISTANCE_TESTER_SOURCE_SHA256,
    ATR_EXPECTED_VECTOR,
    ATR_RUNTIME_IDENTITY,
    ATR_RUNTIME_SOURCE_SHA256,
    DISTANCE_ATR_EXPECTED_VECTOR,
    DISTANCE_ATR_RUNTIME_IDENTITY,
    DISTANCE_ATR_RUNTIME_SOURCE_SHA256,
    FIXTURE_PACKAGE_IDENTITY,
    RUST_ATR_IDENTITY,
    RUST_DISTANCE_ATR_IDENTITY,
    CompileError,
    ExecutionError,
    reconcile_atr_distance_csv,
)

ROOT = Path(__file__).resolve().parents[1]
TESTER_MANIFEST = ROOT / "tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2AtrDistanceTesterCanaryV1.manifest.json"
ATR_RUNTIME_SOURCE = ROOT / "tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2AtrRuntimeV1.mqh"
DISTANCE_ATR_RUNTIME_SOURCE = ROOT / "tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2DistanceAtrRuntimeV1.mqh"
TESTER_SOURCE = ROOT / "tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2AtrDistanceTesterCanaryV1.mq5"
NATIVE_ROOT = ROOT / "tests/fixtures/phase2q_mql5_atr_distance_native"
NATIVE_INDEX = NATIVE_ROOT / "native_evidence_manifest.json"
REQUIRED_STAGES = ("tester_configuration_loaded", "testing_agent_started", "ea_loaded", "ea_initialized", "fixture_execution_started", "result_csv_written", "fixture_execution_completed", "tester_completed", "terminal_shutdown")


def _numeric_text(value):
    if value is None:
        return "null"
    return format(float(value), ".16f")


def _make_valid_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(ATR_DISTANCE_CSV_SCHEMA)
        for index in range(12):
            atr = _numeric_text(ATR_EXPECTED_VECTOR[index])
            distance = _numeric_text(DISTANCE_ATR_EXPECTED_VECTOR[index])
            writer.writerow(["row", index, "", "", "", "", "", "", atr, atr, _numeric_text(0.0 if ATR_EXPECTED_VECTOR[index] is None else 0.0003666666666666263), distance, distance, "true" if ATR_EXPECTED_VECTOR[index] is None else "false", "true" if DISTANCE_ATR_EXPECTED_VECTOR[index] is None else "false", "true", "", "", "", ""])
        writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])


class Phase2QSourceHashTests(unittest.TestCase):
    def test_atr_source_hash_matches_frozen(self):
        self.assertEqual(hashlib.sha256(ATR_RUNTIME_SOURCE.read_bytes()).hexdigest(), ATR_RUNTIME_SOURCE_SHA256)

    def test_distance_atr_source_hash_matches_frozen(self):
        self.assertEqual(hashlib.sha256(DISTANCE_ATR_RUNTIME_SOURCE.read_bytes()).hexdigest(), DISTANCE_ATR_RUNTIME_SOURCE_SHA256)

    def test_tester_source_hash_matches_frozen(self):
        self.assertEqual(hashlib.sha256(TESTER_SOURCE.read_bytes()).hexdigest(), ATR_DISTANCE_TESTER_SOURCE_SHA256)

    def test_tester_manifest_contract(self):
        manifest = json.loads(TESTER_MANIFEST.read_text())
        self.assertEqual(manifest["tester_version"], "nora_mql5_atr_distance_tester_canary_v1")
        self.assertEqual(manifest["tester_identity"], ATR_DISTANCE_TESTER_IDENTITY)
        self.assertEqual(manifest["source_sha256"], ATR_DISTANCE_TESTER_SOURCE_SHA256)
        self.assertEqual(manifest["source_filename"], "NoraPhase2AtrDistanceTesterCanaryV1.mq5")
        self.assertEqual(manifest["nullable_runtime_identity"], "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d")
        self.assertEqual(manifest["atr_runtime_identity"], ATR_RUNTIME_IDENTITY)
        self.assertEqual(manifest["distance_atr_runtime_identity"], DISTANCE_ATR_RUNTIME_IDENTITY)
        self.assertEqual(manifest["fixture_package_identity"], FIXTURE_PACKAGE_IDENTITY)
        self.assertEqual(manifest["rust_atr_evidence_identity"], RUST_ATR_IDENTITY)
        self.assertEqual(manifest["rust_distance_atr_evidence_identity"], RUST_DISTANCE_ATR_IDENTITY)
        self.assertEqual(manifest["row_count"], 12)
        self.assertEqual(manifest["result_filename"], "nora_phase2_atr_distance_tester_v1.csv")

    def test_frozen_atr_vector_format(self):
        self.assertEqual(len(ATR_EXPECTED_VECTOR), 12)
        self.assertEqual(ATR_EXPECTED_VECTOR[0], None)
        self.assertEqual(ATR_EXPECTED_VECTOR[1], None)
        for i in range(2, 12):
            self.assertIsNotNone(ATR_EXPECTED_VECTOR[i])

    def test_frozen_distance_atr_vector_format(self):
        self.assertEqual(len(DISTANCE_ATR_EXPECTED_VECTOR), 12)
        self.assertEqual(DISTANCE_ATR_EXPECTED_VECTOR[0], None)
        self.assertEqual(DISTANCE_ATR_EXPECTED_VECTOR[1], None)
        for i in range(2, 12):
            self.assertIsNotNone(DISTANCE_ATR_EXPECTED_VECTOR[i])


class Phase2QReconciliationTests(unittest.TestCase):
    def test_valid_csv_reconciles(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            _make_valid_csv(result)
            parsed = reconcile_atr_distance_csv(result, TESTER_MANIFEST)
            self.assertEqual(parsed["summary"]["passed_rows"], 12)
            self.assertEqual(parsed["summary"]["failed_rows"], 0)
            self.assertTrue(parsed["summary"]["overall_pass"])
            for i in [0, 1]:
                self.assertEqual(parsed["atr_vector"][i], "null")
                self.assertEqual(parsed["distance_atr_vector"][i], "null")
            for i in range(2, 12):
                self.assertNotEqual(parsed["atr_vector"][i], "null")
                self.assertNotEqual(parsed["distance_atr_vector"][i], "null")

    def test_wrong_atr_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(ATR_DISTANCE_CSV_SCHEMA)
                for index in range(12):
                    atr = _numeric_text(ATR_EXPECTED_VECTOR[index])
                    distance = _numeric_text(DISTANCE_ATR_EXPECTED_VECTOR[index])
                    if index == 5:
                        atr = "0.9999"
                    writer.writerow(["row", index, "", "", "", "", "", "", atr, atr, _numeric_text(0), distance, distance, "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "disagrees|reconciliation"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)

    def test_wrong_distance_atr_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(ATR_DISTANCE_CSV_SCHEMA)
                for index in range(12):
                    atr = _numeric_text(ATR_EXPECTED_VECTOR[index])
                    distance = _numeric_text(DISTANCE_ATR_EXPECTED_VECTOR[index])
                    if index == 5:
                        distance = "0.9999"
                    writer.writerow(["row", index, "", "", "", "", "", "", atr, atr, _numeric_text(0), distance, distance, "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "disagrees|reconciliation"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)

    def test_atr_null_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(ATR_DISTANCE_CSV_SCHEMA)
                for index in range(12):
                    atr = "0.5" if ATR_EXPECTED_VECTOR[index] is None else _numeric_text(ATR_EXPECTED_VECTOR[index])
                    distance = _numeric_text(DISTANCE_ATR_EXPECTED_VECTOR[index])
                    writer.writerow(["row", index, "", "", "", "", "", "", atr, atr, _numeric_text(0), distance, distance, "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "disagrees|reconciliation"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)

    def test_distance_atr_null_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(ATR_DISTANCE_CSV_SCHEMA)
                for index in range(12):
                    atr = _numeric_text(ATR_EXPECTED_VECTOR[index])
                    distance = "0.5" if DISTANCE_ATR_EXPECTED_VECTOR[index] is None else _numeric_text(DISTANCE_ATR_EXPECTED_VECTOR[index])
                    writer.writerow(["row", index, "", "", "", "", "", "", atr, atr, _numeric_text(0), distance, distance, "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "disagrees|reconciliation"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)

    def test_wrong_row_count_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(ATR_DISTANCE_CSV_SCHEMA)
                for index in range(13):
                    writer.writerow(["row", index, "", "", "", "", "", "", "null", "null", "", "null", "null", "true", "true", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", "true", 13, 13, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "13|exactly 12"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)

    def test_failed_summary_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            _make_valid_csv(result)
            text = result.read_text()
            text = text.replace("true,12,12,0,true", "false,12,11,1,false")
            result.write_text(text)
            with self.assertRaisesRegex(ExecutionError, "summary"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)

    def test_invalid_numeric_token_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(ATR_DISTANCE_CSV_SCHEMA)
                for index in range(12):
                    atr = "not_a_number" if index == 3 else _numeric_text(ATR_EXPECTED_VECTOR[index])
                    distance = _numeric_text(DISTANCE_ATR_EXPECTED_VECTOR[index])
                    writer.writerow(["row", index, "", "", "", "", "", "", atr, atr, _numeric_text(0), distance, distance, "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "invalid numeric token"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)

    def test_row_pass_must_be_true(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            _make_valid_csv(result)
            text = result.read_text()
            # row_pass is column index 15. Replace the first true in row_pass position with false
            lines = [line.strip() for line in text.splitlines()]
            parts = lines[1].split(",")
            self.assertEqual(parts[15], "true")
            parts[15] = "false"
            lines[1] = ",".join(parts)
            result.write_text("\n".join(lines) + "\n")
            with self.assertRaisesRegex(ExecutionError, "row_pass is false"):
                reconcile_atr_distance_csv(result, TESTER_MANIFEST)


class Phase2QSpatialSemanticIdentityTests(unittest.TestCase):
    def test_canonical_semantic_identity_deterministic(self):
        from lab.mt5 import _identity
        run1 = json.loads((NATIVE_ROOT / "run1/execution_manifest.json").read_text())
        atr_vec = run1["atr_vector"]
        distance_vec = run1["distance_atr_vector"]
        rowpass = run1["row_pass_vector"]
        semantic_id = _identity("nora.mt5.atr_distance_semantic_result_v1.semantic.v1", [
            ATR_DISTANCE_TESTER_IDENTITY,
            FIXTURE_PACKAGE_IDENTITY,
            RUST_ATR_IDENTITY,
            RUST_DISTANCE_ATR_IDENTITY,
            "MetaTrader 5",
            "5.0.0.5836",
            json.dumps(atr_vec, separators=(",", ":")),
            json.dumps(distance_vec, separators=(",", ":")),
            json.dumps(rowpass, separators=(",", ":")),
            json.dumps({"row_count": 12, "passed_rows": 12, "failed_rows": 0, "overall_pass": True}, sort_keys=True, separators=(",", ":")),
        ])
        self.assertEqual(semantic_id, "8a912bd9152d16c8e94b1a96210d2cc6917c5b2639f615b0ecd4931dac2669f2")

    def test_semantic_identity_is_sensitive_to_atr_vector(self):
        from lab.mt5 import _identity
        run1 = json.loads((NATIVE_ROOT / "run1/execution_manifest.json").read_text())
        atr_vec = run1["atr_vector"]
        distance_vec = run1["distance_atr_vector"]
        rowpass = run1["row_pass_vector"]
        mutated_atr = list(atr_vec)
        mutated_atr[5] = "0.9999"
        id1 = _identity("nora.mt5.atr_distance_semantic_result_v1.semantic.v1", [
            ATR_DISTANCE_TESTER_IDENTITY,
            FIXTURE_PACKAGE_IDENTITY,
            RUST_ATR_IDENTITY,
            RUST_DISTANCE_ATR_IDENTITY,
            "MetaTrader 5",
            "5.0.0.5836",
            json.dumps(atr_vec, separators=(",", ":")),
            json.dumps(distance_vec, separators=(",", ":")),
            json.dumps(rowpass, separators=(",", ":")),
            json.dumps({"row_count": 12, "passed_rows": 12, "failed_rows": 0, "overall_pass": True}, sort_keys=True, separators=(",", ":")),
        ])
        id2 = _identity("nora.mt5.atr_distance_semantic_result_v1.semantic.v1", [
            ATR_DISTANCE_TESTER_IDENTITY,
            FIXTURE_PACKAGE_IDENTITY,
            RUST_ATR_IDENTITY,
            RUST_DISTANCE_ATR_IDENTITY,
            "MetaTrader 5",
            "5.0.0.5836",
            json.dumps(mutated_atr, separators=(",", ":")),
            json.dumps(distance_vec, separators=(",", ":")),
            json.dumps(rowpass, separators=(",", ":")),
            json.dumps({"row_count": 12, "passed_rows": 12, "failed_rows": 0, "overall_pass": True}, sort_keys=True, separators=(",", ":")),
        ])
        self.assertNotEqual(id1, id2)

    def test_semantic_identity_is_sensitive_to_distance_vector(self):
        from lab.mt5 import _identity
        run1 = json.loads((NATIVE_ROOT / "run1/execution_manifest.json").read_text())
        atr_vec = run1["atr_vector"]
        distance_vec = run1["distance_atr_vector"]
        rowpass = run1["row_pass_vector"]
        mutated_distance = list(distance_vec)
        mutated_distance[5] = "0.9999"
        id1 = _identity("nora.mt5.atr_distance_semantic_result_v1.semantic.v1", [
            ATR_DISTANCE_TESTER_IDENTITY,
            FIXTURE_PACKAGE_IDENTITY,
            RUST_ATR_IDENTITY,
            RUST_DISTANCE_ATR_IDENTITY,
            "MetaTrader 5",
            "5.0.0.5836",
            json.dumps(atr_vec, separators=(",", ":")),
            json.dumps(distance_vec, separators=(",", ":")),
            json.dumps(rowpass, separators=(",", ":")),
            json.dumps({"row_count": 12, "passed_rows": 12, "failed_rows": 0, "overall_pass": True}, sort_keys=True, separators=(",", ":")),
        ])
        id2 = _identity("nora.mt5.atr_distance_semantic_result_v1.semantic.v1", [
            ATR_DISTANCE_TESTER_IDENTITY,
            FIXTURE_PACKAGE_IDENTITY,
            RUST_ATR_IDENTITY,
            RUST_DISTANCE_ATR_IDENTITY,
            "MetaTrader 5",
            "5.0.0.5836",
            json.dumps(atr_vec, separators=(",", ":")),
            json.dumps(mutated_distance, separators=(",", ":")),
            json.dumps(rowpass, separators=(",", ":")),
            json.dumps({"row_count": 12, "passed_rows": 12, "failed_rows": 0, "overall_pass": True}, sort_keys=True, separators=(",", ":")),
        ])
        self.assertNotEqual(id1, id2)


class Phase2QCommittedNativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.index = json.loads(NATIVE_INDEX.read_text())
        self.compile = json.loads((NATIVE_ROOT / self.index["compile"]).read_text())
        self.runs = [json.loads((NATIVE_ROOT / self.index[name]).read_text()) for name in ("run1", "run2")]

    def test_committed_paths_and_hashes(self):
        self.assertEqual(self.index["identities"]["atr_runtime"], ATR_RUNTIME_IDENTITY)
        self.assertEqual(self.index["identities"]["distance_atr_runtime"], DISTANCE_ATR_RUNTIME_IDENTITY)
        self.assertEqual(self.index["identities"]["atr_distance_tester"], ATR_DISTANCE_TESTER_IDENTITY)
        self.assertEqual(self.index["identities"]["fixture_package"], FIXTURE_PACKAGE_IDENTITY)
        self.assertEqual(self.index["identities"]["rust_atr"], RUST_ATR_IDENTITY)
        self.assertEqual(self.index["identities"]["rust_distance_atr"], RUST_DISTANCE_ATR_IDENTITY)
        self.assertEqual(self.index["source_hashes"]["atr_runtime_sha256"], ATR_RUNTIME_SOURCE_SHA256)
        self.assertEqual(self.index["source_hashes"]["distance_atr_runtime_sha256"], DISTANCE_ATR_RUNTIME_SOURCE_SHA256)
        self.assertEqual(self.index["source_hashes"]["tester_sha256"], ATR_DISTANCE_TESTER_SOURCE_SHA256)
        self.assertEqual(hashlib.sha256((NATIVE_ROOT / self.index["ex5"]).read_bytes()).hexdigest(), self.index["ex5_sha256"])
        for name in ("run1_csv", "run2_csv"):
            self.assertEqual(hashlib.sha256((NATIVE_ROOT / self.index[name]).read_bytes()).hexdigest(), self.index["csv_sha256"])
        self.assertEqual(self.compile["native_evidence"]["ex5_sha256"], self.index["ex5_sha256"])
        self.assertEqual(self.compile["atr_runtime_source_sha256"], ATR_RUNTIME_SOURCE_SHA256)
        self.assertEqual(self.compile["distance_atr_runtime_source_sha256"], DISTANCE_ATR_RUNTIME_SOURCE_SHA256)
        self.assertEqual(self.compile["tester_source_sha256"], ATR_DISTANCE_TESTER_SOURCE_SHA256)

    def test_compile_command_timestamps_and_freshness(self):
        native = self.compile["native_evidence"]
        self.assertIn("MetaEditor64.exe", native["rendered_command"])
        self.assertIn("/compile:\"C:\\Users\\Gasper\\NoraPhase2Q\\", native["rendered_command"])
        self.assertIn("/log:\"C:\\Users\\Gasper\\NoraPhase2Q\\", native["rendered_command"])
        self.assertFalse(native["source_ex5_existed_immediately_before"])
        self.assertFalse(native["output_ex5_existed_immediately_before"])
        start = datetime.fromisoformat(native["compile_start_utc"].replace("Z", "+00:00"))
        complete = datetime.fromisoformat(native["compile_completion_utc"].replace("Z", "+00:00"))
        ex5_time = datetime.fromisoformat(native["ex5_last_write_time_utc"].replace("Z", "+00:00"))
        self.assertGreaterEqual(ex5_time, start)
        self.assertLessEqual(ex5_time, complete)
        self.assertEqual(native["native_process_exit_status"], 1)
        self.assertEqual(native["error_count"], 0)
        self.assertEqual(native["warning_count"], 0)
        self.assertTrue(native["diagnostic_lines"])
        self.assertIn("NoraPhase2AtrDistanceTesterCanaryV1.ex5", native["ex5_filename"])

    def test_each_run_is_fresh_complete_and_redacted(self):
        for number, run in enumerate(self.runs, 1):
            native = run["native_evidence"]
            self.assertIn("terminal64.exe /config:\"C:\\Users\\Gasper\\NoraPhase2Q\\", native["terminal_rendered_command"])
            self.assertFalse(native["csv_existed_immediately_before"])
            start = datetime.fromisoformat(native["run_start_utc"].replace("Z", "+00:00"))
            complete = datetime.fromisoformat(native["run_completion_utc"].replace("Z", "+00:00"))
            csv_time = datetime.fromisoformat(native["csv_last_write_time_utc"].replace("Z", "+00:00"))
            self.assertGreaterEqual(csv_time, start)
            self.assertEqual(native["native_process_exit_status"], 0)
            self.assertTrue(native["result_fresh"])
            self.assertEqual(run["launch_stages"], {stage: True for stage in REQUIRED_STAGES})
            lifecycle = [json.loads(line) for line in (NATIVE_ROOT / f"run{number}" / "lifecycle.jsonl").read_text(encoding="utf-8-sig").splitlines()]
            self.assertEqual({item["event"] for item in lifecycle}, {"tester_configuration_loaded", "terminal_process_started", "tester_completed", "terminal_shutdown", "result_csv_written", "fixture_execution_started", "fixture_execution_completed", "testing_agent_started", "ea_loaded", "ea_initialized"})
            self.assertTrue((NATIVE_ROOT / f"run{number}" / "tester.log").stat().st_size > 0)
            for boundary in native["native_journal_boundaries"]["ending_files"]:
                self.assertLess(boundary["start_offset_bytes"], boundary["end_offset_bytes"])
            self.assertLessEqual(start, complete)
            config = (NATIVE_ROOT / f"run{number}" / "tester.ini").read_text()
            self.assertIn("Login=<redacted>", config)
            self.assertIn("Server=<redacted>", config)
            self.assertNotIn("4000094575", config)
            self.assertEqual(run["row_count"], 12)
            self.assertEqual(run["atr_null_positions"], [0, 1])
            self.assertEqual(run["distance_atr_null_positions"], [0, 1])
            self.assertEqual(run["max_atr_abs_difference"], 4.2500725161431774e-17)
            self.assertEqual(run["max_distance_atr_abs_difference"], 5.551115123125783e-17)
            self.assertEqual(run["passed_rows"], 12)
            self.assertEqual(run["failed_rows"], 0)
            self.assertTrue(run["overall_pass"])

    def test_runs_are_semantically_identical(self):
        self.assertTrue(self.index["runs_semantically_identical"])
        self.assertTrue(self.index["csv_byte_identical"])
        self.assertEqual(self.runs[0]["semantic_result_identity"], self.runs[1]["semantic_result_identity"])
        self.assertEqual(self.runs[0]["result_csv_sha256"], self.runs[1]["result_csv_sha256"])
        self.assertEqual(self.runs[0]["semantic_result_identity"], self.index["semantic_result_identity"])

    def test_mutation_of_semantic_identity_detectable(self):
        mutated = dict(self.runs[0])
        mutated["semantic_result_identity"] = "mutated"
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated["semantic_result_identity"], self.index["semantic_result_identity"])

    def test_atr_manifest_identities_and_hashes(self):
        atr_manifest = json.loads((ROOT / "tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2AtrRuntimeV1.manifest.json").read_text())
        self.assertEqual(atr_manifest["atr_runtime_identity"], ATR_RUNTIME_IDENTITY)
        self.assertEqual(atr_manifest["source_sha256"], ATR_RUNTIME_SOURCE_SHA256)
        self.assertEqual(atr_manifest["nullable_runtime_identity"], "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d")

    def test_distance_atr_manifest_identities_and_hashes(self):
        dist_manifest = json.loads((ROOT / "tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2DistanceAtrRuntimeV1.manifest.json").read_text())
        self.assertEqual(dist_manifest["distance_atr_runtime_identity"], DISTANCE_ATR_RUNTIME_IDENTITY)
        self.assertEqual(dist_manifest["source_sha256"], DISTANCE_ATR_RUNTIME_SOURCE_SHA256)
        self.assertEqual(dist_manifest["nullable_runtime_identity"], "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d")

    def test_orchestration_command_fields_present(self):
        self.assertIn("orchestration_command", self.compile)
        self.assertIn("working_directory", self.compile)
        self.assertIn("orchestration_start_utc", self.compile)
        self.assertIn("orchestration_completion_utc", self.compile)
        self.assertEqual(self.compile["orchestration_exit_status"], 0)
        for run in self.runs:
            self.assertIn("orchestration_command", run)
            self.assertIn("working_directory", run)
            self.assertIn("orchestration_start_utc", run)
            self.assertIn("orchestration_completion_utc", run)
            self.assertEqual(run["orchestration_exit_status"], 0)

    def test_compiler_diagnostic_zero_errors_warnings(self):
        self.assertEqual(self.compile["error_count"], 0)
        self.assertEqual(self.compile["warning_count"], 0)
        self.assertEqual(self.compile["compiler_exit_code"], 1)
        self.assertIn("0 errors, 0 warnings", self.compile["native_evidence"]["diagnostic_lines"][0])

    def test_ex5_and_csv_absence_before_execution(self):
        self.assertFalse(self.compile["native_evidence"]["output_ex5_existed_before"])
        self.assertFalse(self.compile["native_evidence"]["output_ex5_existed_immediately_before"])
        for run in self.runs:
            self.assertFalse(run["native_evidence"]["csv_existed_immediately_before"])

    def test_raw_csv_hashes(self):
        self.assertEqual(self.runs[0]["result_csv_sha256"], "3fd319613374e0b22ac80cf1fea1cb34c2a37069ee3778cf9f154ac86a1eaccf")
        self.assertEqual(self.runs[1]["result_csv_sha256"], "3fd319613374e0b22ac80cf1fea1cb34c2a37069ee3778cf9f154ac86a1eaccf")

    def test_ex5_sha256(self):
        self.assertEqual(self.compile["ex5_sha256"], "a948b4c4c4c386e14706fbafe610dfc4a4445e645a851f47780cf6a15acd770c")

    def test_execution_identities_match(self):
        self.assertEqual(self.runs[0]["execution_identity"], self.runs[1]["execution_identity"])


if __name__ == "__main__":
    unittest.main()