import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.mt5 import ExecutionError, reconcile_series_csv, _require_launch_evidence


ROOT = Path(__file__).resolve().parents[1]
TESTER_MANIFEST = ROOT / "tests/fixtures/phase2k_mql5_sma_cross/tester/NoraPhase2SeriesTesterCanaryV1.manifest.json"
SCHEMA = ["record_type", "row_index", "actual_sma", "expected_sma", "actual_cross_above", "expected_cross_above", "actual_cross_below", "expected_cross_below", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]
EXPECTED_SMA = [None, None, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334]
EXPECTED_ABOVE = [None, None, None, True, False, False, False, False, False, False, False, False]
EXPECTED_BELOW = [None, None, None, True, False, False, False, False, False, False, False, False]
EXPECTED_NULLABLE = ["null", "null", "false", "true", "true", "true", "true", "true", "true", "true", "true", "true"]
EXPECTED_TRIGGER = [False, False, False, True, True, True, True, True, True, True, True, True]


def write_csv(path: Path, *, mutate: bool = False) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SCHEMA)
        for index, (sma, above, below, nullable, trigger) in enumerate(zip(EXPECTED_SMA, EXPECTED_ABOVE, EXPECTED_BELOW, EXPECTED_NULLABLE, EXPECTED_TRIGGER)):
            if mutate and index == 3:
                sma = 1.0
            expected_sma = str(sma) if sma is not None else "null"
            expected_above = str(above).lower() if above is not None else "null"
            expected_below = str(below).lower() if below is not None else "null"
            writer.writerow(["row", index, expected_sma, expected_sma, expected_above, expected_above, expected_below, expected_below, nullable, nullable, "true" if trigger else "false", "true" if trigger else "false", "true", "", "", "", ""])
        writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])


class Phase2LSeriesTesterCanaryTests(unittest.TestCase):
    def test_valid_csv_reconciles_strictly(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            write_csv(result)
            parsed = reconcile_series_csv(result, TESTER_MANIFEST)
            self.assertEqual(parsed["sma_vector"], [str(x) if x is not None else "null" for x in EXPECTED_SMA])
            self.assertEqual(parsed["cross_above_vector"], [str(x).lower() if x is not None else "null" for x in EXPECTED_ABOVE])
            self.assertEqual(parsed["cross_below_vector"], [str(x).lower() if x is not None else "null" for x in EXPECTED_BELOW])
            self.assertEqual(parsed["nullable_vector"], EXPECTED_NULLABLE)
            self.assertEqual(parsed["trigger_vector"], [False, False, False, True, True, True, True, True, True, True, True, True])
            self.assertEqual(parsed["summary"]["passed_rows"], 12)

    def test_malformed_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            write_csv(result, mutate=True)
            with self.assertRaisesRegex(ExecutionError, "row expected value disagrees"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_missing_columns_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["record_type", "row_index"])
                writer.writerow(["row", 0, "null", "null", "null", "null", "null", "null", "null", "null", "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "header does not match"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_invalid_nullable_token_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SCHEMA)
                for index in range(12):
                    writer.writerow(["row", index, "null", "null", "null", "null", "null", "null", "invalid", "false", "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "invalid nullable token"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_invalid_numeric_token_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SCHEMA)
                for index in range(12):
                    writer.writerow(["row", index, "not_a_number", "null", "null", "null", "null", "null", "null", "null", "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "invalid numeric token"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_invalid_cross_token_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SCHEMA)
                for index in range(12):
                    writer.writerow(["row", index, "null", "null", "invalid_cross", "null", "null", "null", "null", "null", "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "invalid cross token"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_duplicate_row_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SCHEMA)
                for index in range(11):
                    writer.writerow(["row", index, "null", "null", "null", "null", "null", "null", "null", "null", "false", "false", "true", "", "", "", ""])
                writer.writerow(["row", 11, "null", "null", "null", "null", "null", "null", "null", "null", "false", "false", "true", "", "", "", ""])
                writer.writerow(["row", 11, "null", "null", "null", "null", "null", "null", "null", "null", "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "exactly 12 rows"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_wrong_row_count_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            with result.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(SCHEMA)
                for index in range(13):
                    writer.writerow(["row", index, "null", "null", "null", "null", "null", "null", "null", "null", "false", "false", "true", "", "", "", ""])
                writer.writerow(["summary", -1, "", "", "", "", "", "", "", "", "", "", "true", 12, 12, 0, "true"])
            with self.assertRaisesRegex(ExecutionError, "exactly 12 rows"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_summary_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            write_csv(result)
            with result.open("r", newline="", encoding="utf-8") as stream:
                lines = stream.readlines()
            lines[-1] = "summary,-1,,,,,,,,,,,,true,12,11,1,false\n"
            with result.open("w", newline="", encoding="utf-8") as stream:
                stream.writelines(lines)
            with self.assertRaisesRegex(ExecutionError, "summary record is malformed"):
                reconcile_series_csv(result, TESTER_MANIFEST)

    def test_launch_evidence_incomplete(self):
        evidence = {"stages": {"tester_configuration_loaded": True, "testing_agent_started": False, "ea_loaded": False, "ea_initialized": False, "fixture_execution_started": False, "result_csv_written": False, "fixture_execution_completed": False, "tester_completed": False, "terminal_shutdown": False}}
        with self.assertRaisesRegex(ExecutionError, "missing stages"):
            _require_launch_evidence(evidence)

    def test_launch_evidence_missing_terminal_shutdown(self):
        evidence = {"stages": {"tester_configuration_loaded": True, "testing_agent_started": True, "ea_loaded": True, "ea_initialized": True, "fixture_execution_started": True, "result_csv_written": True, "fixture_execution_completed": True, "tester_completed": True, "terminal_shutdown": False}}
        with self.assertRaisesRegex(ExecutionError, "terminal_shutdown"):
            _require_launch_evidence(evidence)


if __name__ == "__main__":
    unittest.main()