"""Phase-2N native slope canary regression tests."""
import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from lab.mt5 import (
    SLOPE_CSV_SCHEMA,
    SLOPE_EXPECTED_VECTOR,
    SLOPE_RUNTIME_IDENTITY,
    SLOPE_RUNTIME_SOURCE_SHA256,
    SLOPE_TESTER_IDENTITY,
    SLOPE_TESTER_SOURCE_SHA256,
    CompileError,
    ExecutionError,
    reconcile_slope_csv,
)

ROOT = Path(__file__).resolve().parents[1]
TESTER_MANIFEST = ROOT / "tests/fixtures/phase2m_mql5_slope/NoraPhase2SlopeTesterCanaryV1.manifest.json"
RUNTIME_SOURCE = ROOT / "tests/fixtures/phase2m_mql5_slope/NoraPhase2SlopeRuntimeV1.mqh"
TESTER_SOURCE = ROOT / "tests/fixtures/phase2m_mql5_slope/NoraPhase2SlopeTesterCanaryV1.mq5"
NATIVE_ROOT = ROOT / "tests/fixtures/phase2n_mql5_slope_native"
NATIVE_INDEX = NATIVE_ROOT / "native_evidence_manifest.json"
REQUIRED_STAGES = ("tester_configuration_loaded", "testing_agent_started", "ea_loaded", "ea_initialized", "fixture_execution_started", "result_csv_written", "fixture_execution_completed", "tester_completed", "terminal_shutdown")


def _slope_text(value):
    if value is None:
        return "null"
    return format(float(value), ".16f")

def _make_valid_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SLOPE_CSV_SCHEMA)
        for index, expected in enumerate(SLOPE_EXPECTED_VECTOR):
            sv = _slope_text(expected)
            writer.writerow(["row", index, sv, sv, "true", "", "", "", ""])
        writer.writerow(["summary", -1, "", "", "true", 12, 12, 0, "true"])


class Phase2NSlopeNativeEvidenceTests(unittest.TestCase):
    def test_source_hashes_match_accepted_fixtures(self):
        self.assertEqual(hashlib.sha256(RUNTIME_SOURCE.read_bytes()).hexdigest(), SLOPE_RUNTIME_SOURCE_SHA256)
        self.assertEqual(hashlib.sha256(TESTER_SOURCE.read_bytes()).hexdigest(), SLOPE_TESTER_SOURCE_SHA256)

    def test_tester_manifest_matches_accepted_contract(self):
        manifest = json.loads(TESTER_MANIFEST.read_text())
        self.assertEqual(manifest["slope_tester_version"], "nora_mql5_slope_tester_canary_v1")
        self.assertEqual(manifest["slope_tester_identity"], SLOPE_TESTER_IDENTITY)
        self.assertEqual(manifest["source_sha256"], SLOPE_TESTER_SOURCE_SHA256)
        self.assertEqual(manifest["source_filename"], "NoraPhase2SlopeTesterCanaryV1.mq5")
        self.assertEqual(manifest["nullable_runtime_identity"], "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d")
        self.assertEqual(manifest["slope_runtime_identity"], SLOPE_RUNTIME_IDENTITY)
        self.assertEqual(manifest["lookback"], 1)
        self.assertEqual(manifest["row_count"], 12)
        self.assertEqual(manifest["result_filename"], "nora_phase2_slope_tester_v1.csv")
        self.assertEqual(manifest["rust_input_identity"], "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383")
        self.assertEqual(manifest["rust_slope_identity"], "45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499")

    def test_frozen_expected_slope_matches_manifest(self):
        manifest = json.loads(TESTER_MANIFEST.read_text())
        manifest_vector = manifest["expected_slope_vector"]
        self.assertEqual(len(SLOPE_EXPECTED_VECTOR), 12)
        self.assertEqual(len(manifest_vector), 12)

    def test_null_positions_correct(self):
        null_positions = [i for i, v in enumerate(SLOPE_EXPECTED_VECTOR) if v is None]
        self.assertEqual(null_positions, [0, 1, 2])

    def test_lookback_2_is_not_postulated_as_a_variant(self):
        from lab.mql5gen.slope import LOOKBACK as MQL5GEN_LOOKBACK
        self.assertEqual(MQL5GEN_LOOKBACK, 1)

    def test_valid_csv_reconciles_strictly(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            _make_valid_csv(result)
            parsed = reconcile_slope_csv(result, TESTER_MANIFEST)
            self.assertEqual(parsed["summary"]["passed_rows"], 12)
            self.assertEqual(parsed["summary"]["failed_rows"], 0)
            self.assertTrue(parsed["summary"]["overall_pass"])
            for i in [0, 1, 2]:
                self.assertEqual(parsed["slope_vector"][i], "null")
            for i in range(3, 12):
                self.assertNotEqual(parsed["slope_vector"][i], "null")

    def test_wrong_slope_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SLOPE_CSV_SCHEMA)
                for index, expected in enumerate(SLOPE_EXPECTED_VECTOR):
                    sv = "0.9999" if index == 5 else _slope_text(expected)
                    writer.writerow(["row", index, sv, sv, "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "disagrees|reconciliation"):
                reconcile_slope_csv(result, TESTER_MANIFEST)

    def test_null_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SLOPE_CSV_SCHEMA)
                for index, expected in enumerate(SLOPE_EXPECTED_VECTOR):
                    sv = "0.5" if expected is None else _slope_text(expected)
                    writer.writerow(["row", index, sv, sv, "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "disagrees|reconciliation"):
                reconcile_slope_csv(result, TESTER_MANIFEST)

    def test_wrong_row_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SLOPE_CSV_SCHEMA)
                for index in range(13):
                    writer.writerow(["row", index, "null", "null", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "true", 13, 13, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "13|exactly 12"):
                reconcile_slope_csv(result, TESTER_MANIFEST)

    def test_missing_columns_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["record_type", "row_index"])
                for _ in range(12):
                    writer.writerow(["row", 0, "null", "null", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "header"):
                reconcile_slope_csv(result, TESTER_MANIFEST)

    def test_invalid_slope_token_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SLOPE_CSV_SCHEMA)
                for index in range(12):
                    sv = "not_a_number" if index == 3 else _slope_text(SLOPE_EXPECTED_VECTOR[index])
                    writer.writerow(["row", index, sv, sv, "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "invalid numeric token"):
                reconcile_slope_csv(result, TESTER_MANIFEST)

    def test_failed_summary_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            _make_valid_csv(result)
            text = result.read_text()
            text = text.replace("true,12,12,0,true", "false,12,11,1,false")
            result.write_text(text)
            with self.assertRaisesRegex(ExecutionError, "summary"):
                reconcile_slope_csv(result, TESTER_MANIFEST)


class Phase2NSlopeSemanticIdentityTests(unittest.TestCase):
    def test_canonical_semantic_identity_is_deterministic(self):
        from lab.mt5 import _identity
        slope_vec = [_slope_text(v) for v in SLOPE_EXPECTED_VECTOR]
        semantic_id = _identity("nora.mt5.slope_semantic_result_v1.semantic.v1", [
            SLOPE_TESTER_IDENTITY,
            "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383",
            "45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499",
            "MetaTrader 5",
            "5.0.0.5836",
            json.dumps(slope_vec, separators=(",", ":")),
            json.dumps([True] * 12, separators=(",", ":")),
            json.dumps({"row_count": 12, "passed_rows": 12, "failed_rows": 0, "overall_pass": True}, sort_keys=True, separators=(",", ":")),
        ])
        self.assertEqual(semantic_id, "221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f")

    def test_lookback_2_is_not_a_variant(self):
        manifest = json.loads(TESTER_MANIFEST.read_text())
        self.assertEqual(manifest["lookback"], 1)


class Phase2NCommittedNativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.index = json.loads(NATIVE_INDEX.read_text())
        self.compile = json.loads((NATIVE_ROOT / self.index["compile"]).read_text())
        self.runs = [json.loads((NATIVE_ROOT / self.index[name]).read_text()) for name in ("run1", "run2")]

    def test_committed_paths_and_hashes(self):
        self.assertEqual(self.index["identities"]["slope_runtime"], SLOPE_RUNTIME_IDENTITY)
        self.assertEqual(self.index["identities"]["slope_tester"], SLOPE_TESTER_IDENTITY)
        self.assertEqual(self.index["identities"]["rust_slope"], "45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499")
        self.assertEqual(self.index["source_hashes"]["slope_runtime_sha256"], SLOPE_RUNTIME_SOURCE_SHA256)
        self.assertEqual(self.index["source_hashes"]["tester_sha256"], SLOPE_TESTER_SOURCE_SHA256)
        self.assertEqual(hashlib.sha256((NATIVE_ROOT / self.index["ex5"]).read_bytes()).hexdigest(), self.index["ex5_sha256"])
        for name in ("run1_csv", "run2_csv"):
            self.assertEqual(hashlib.sha256((NATIVE_ROOT / self.index[name]).read_bytes()).hexdigest(), self.index["csv_sha256"])
        self.assertEqual(self.compile["native_evidence"]["ex5_sha256"], self.index["ex5_sha256"])
        self.assertEqual(self.compile["slope_runtime_source_sha256"], SLOPE_RUNTIME_SOURCE_SHA256)
        self.assertEqual(self.compile["tester_source_sha256"], SLOPE_TESTER_SOURCE_SHA256)

    def test_compile_command_timestamps_and_freshness(self):
        native = self.compile["native_evidence"]
        self.assertIn("MetaEditor64.exe", native["rendered_command"])
        self.assertIn("/compile:\"C:\\Users\\Gasper\\NoraPhase2N\\", native["rendered_command"])
        self.assertIn("/log:\"C:\\Users\\Gasper\\NoraPhase2N\\", native["rendered_command"])
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

    def test_each_run_is_fresh_complete_and_redacted(self):
        for number, run in enumerate(self.runs, 1):
            native = run["native_evidence"]
            self.assertIn("terminal64.exe /config:\"C:\\Users\\Gasper\\NoraPhase2N\\", native["terminal_rendered_command"])
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
            self.assertEqual(run["null_positions"], [0, 1, 2])
            self.assertEqual(run["max_finite_abs_difference"], 4.83554168928535e-17)

    def test_runs_are_semantically_identical_and_mutation_is_detectable(self):
        self.assertTrue(self.index["runs_semantically_identical"])
        self.assertEqual(self.runs[0]["semantic_result_identity"], self.runs[1]["semantic_result_identity"])
        self.assertEqual(self.runs[0]["result_csv_sha256"], self.runs[1]["result_csv_sha256"])
        mutated = dict(self.runs[0])
        mutated["semantic_result_identity"] = "mutated"
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated["semantic_result_identity"], self.index["semantic_result_identity"])


if __name__ == "__main__":
    unittest.main()
