import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.mt5 import ExecutionError, reconcile_condition_csv, execute_condition_canary, _require_launch_evidence


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_MANIFEST = ROOT / "tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.manifest.json"
COMPILE_MANIFEST = Path("/tmp/phase2i-repair-run1/compile_manifest.json")
EX5 = Path("/tmp/phase2i-repair-run1/NoraPhase2ConditionFixtureV1.ex5")
SCHEMA = ["record_type", "row_index", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass"]
NULLABLE = ["null", "null", "false", "true", "true", "true", "true", "true", "true", "true", "true", "true"]
TRIGGER = [False, False, False, True, True, True, True, True, True, True, True, True]


def write_csv(path: Path, *, mutate: bool = False) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SCHEMA)
        for index, (nullable, trigger) in enumerate(zip(NULLABLE, TRIGGER)):
            if mutate and index == 3:
                trigger = False
            writer.writerow(["row", index, nullable, nullable, "true" if trigger else "false", "true" if TRIGGER[index] else "false", "true", "", "", "", ""])
        writer.writerow(["summary", -1, "", "", "", "", "true", 12, 12, 0, "true"])


class Phase2jExecutionCanary(unittest.TestCase):
    def test_valid_csv_reconciles_strictly(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            write_csv(result)
            parsed = reconcile_condition_csv(result, FIXTURE_MANIFEST)
            self.assertEqual(parsed["nullable_vector"], NULLABLE)
            self.assertEqual(parsed["trigger_vector"], TRIGGER)
            self.assertEqual(parsed["summary"]["passed_rows"], 12)

    def test_malformed_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.csv"
            write_csv(result, mutate=True)
            with self.assertRaisesRegex(ExecutionError, "reconciliation"):
                reconcile_condition_csv(result, FIXTURE_MANIFEST)

    def test_contract_mismatch_fails_before_ssh(self):
        if not COMPILE_MANIFEST.is_file() or not EX5.is_file():
            self.skipTest("Phase 2I compile evidence is not available")
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            compile_manifest = json.loads(COMPILE_MANIFEST.read_text())
            compile_manifest["fixture_identity"] = "0" * 64
            mutated = directory / "compile_manifest.json"
            mutated.write_text(json.dumps(compile_manifest))
            with patch("lab.mt5._ssh", side_effect=AssertionError("SSH must not be reached")):
                with self.assertRaisesRegex(ExecutionError, "compile contract mismatch"):
                    execute_condition_canary(mutated, EX5, FIXTURE_MANIFEST, directory / "output")
            self.assertFalse((directory / "output" / "execution_manifest.json").exists())

    def test_unavailable_symbol_evidence_cannot_pass(self):
        evidence = {"stages": {"terminal_started": True, "startup_configuration_loaded": True, "requested_symbol": "NOT_A_SYMBOL"}}
        with self.assertRaisesRegex(ExecutionError, "launch evidence"):
            _require_launch_evidence(evidence)

    def test_stale_process_evidence_cannot_pass(self):
        evidence = {"status": "failed", "error": "unrelated terminal process already owns installation", "stages": {}}
        with self.assertRaisesRegex(ExecutionError, "launch evidence"):
            _require_launch_evidence(evidence)

    def test_chart_timeout_evidence_cannot_pass(self):
        evidence = {"stages": {"terminal_started": True, "startup_configuration_loaded": True, "chart_opened": False, "script_loaded": False, "script_started": False, "result_csv_created": False, "script_completed": False, "terminal_shutdown": True}}
        with self.assertRaisesRegex(ExecutionError, "chart_opened"):
            _require_launch_evidence(evidence)

    def test_script_never_loaded_evidence_cannot_pass(self):
        evidence = {"stages": {"terminal_started": True, "startup_configuration_loaded": True, "chart_opened": True, "script_loaded": False, "script_started": False, "result_csv_created": False, "script_completed": False, "terminal_shutdown": True}}
        with self.assertRaisesRegex(ExecutionError, "script_loaded"):
            _require_launch_evidence(evidence)


if __name__ == "__main__":
    unittest.main()
