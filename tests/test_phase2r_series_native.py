"""Phase-2R durable native evidence upgrade for the SMA/cross (series) canary.

This test defines the acceptance boundary for bringing
``canary.sma_cross_native`` from ``legacy_committed_summary`` up to
``self_contained_raw_native`` evidence-package completeness — the same
standard Phase-2N slope, Phase-2Q ATR/Distance-ATR, and Phase-2R condition
already meet.

The package must be self-contained: compile evidence (log + EX5 + manifest),
two independent native tester runs (each with lifecycle.jsonl, redacted
tester.ini, tester.log, tester-journal.log, CSV, execution_manifest), and a
top-level ``native_evidence_manifest.json`` index binding every artifact hash
and proving the two runs are semantically identical.

Legacy raw evidence lived in pre-reboot ``/tmp`` and is gone. Phase 2R produces
fresh durable evidence under the Phase-2N contract; it does not re-accept, does
not add functionality, and does not authorize search.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_ROOT = ROOT / "tests/fixtures/phase2r_mql5_sma_cross_native"
NATIVE_INDEX = NATIVE_ROOT / "native_evidence_manifest.json"

# Frozen identities inherited from the accepted legacy series canary.
# The durable package must reproduce these exactly, not invent new ones.
SERIES_TESTER_IDENTITY = "78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4"
SERIES_TESTER_SOURCE_SHA256 = "bc62801db8965d268e192d3dadb8ba7b11a7c5e3d5a432fbadd3f2241a4d2757"
LEGACY_SEMANTIC_RESULT_IDENTITY = "ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687"
# Frozen vectors as the reconciliation parser returns them from the CSV —
# strings, not native Python types, because the CSV stores them as text and
# the parser preserves that representation. The semantic identity binds these
# exact strings, so the test must assert against the same representation.
SMA_VECTOR = ["null", "null", "1.1006000000000000", "1.1009333333333335", "1.1009666666666667", "1.1013333333333335", "1.1013666666666666", "1.1017333333333335", "1.1017666666666666", "1.1021333333333334", "1.1021666666666665", "1.1025333333333334"]
CROSS_ABOVE_VECTOR = ["null", "null", "null", "true", "false", "false", "false", "false", "false", "false", "false", "false"]
CROSS_BELOW_VECTOR = ["null", "null", "null", "true", "false", "false", "false", "false", "false", "false", "false", "false"]
NULLABLE_VECTOR = ["null", "null", "false", "true", "true", "true", "true", "true", "true", "true", "true", "true"]
TRIGGER_VECTOR = [False, False, False, True, True, True, True, True, True, True, True, True]

REQUIRED_LAUNCH_STAGES = (
    "tester_configuration_loaded",
    "testing_agent_started",
    "ea_loaded",
    "ea_initialized",
    "fixture_execution_started",
    "result_csv_written",
    "fixture_execution_completed",
    "tester_completed",
    "terminal_shutdown",
)

REQUIRED_LIFECYCLE_EVENTS = {
    "tester_configuration_loaded",
    "terminal_process_started",
    "tester_completed",
    "terminal_shutdown",
    "result_csv_written",
    "fixture_execution_started",
    "fixture_execution_completed",
    "testing_agent_started",
    "ea_loaded",
    "ea_initialized",
}


class Phase2RSeriesNativeEvidenceStructuralTests(unittest.TestCase):
    """Require a self-contained durable package to exist and be internally consistent."""

    def test_native_evidence_directory_and_index_exist(self):
        self.assertTrue(NATIVE_ROOT.is_dir(), f"{NATIVE_ROOT} must exist as a directory")
        self.assertTrue(NATIVE_INDEX.is_file(), f"{NATIVE_INDEX} must exist")

    def test_index_schema_is_self_contained_raw_native(self):
        index = json.loads(NATIVE_INDEX.read_text())
        self.assertEqual(index["evidence_version"], "nora.phase2r.native_evidence_v2")
        self.assertEqual(index["scope"], "frozen native series (SMA/cross) canary only")
        for key in ("compile", "compile_log", "ex5"):
            self.assertIn(key, index, f"index missing compile artifact key {key!r}")
        for key in ("run1", "run2", "run1_csv", "run2_csv"):
            self.assertIn(key, index, f"index missing run artifact key {key!r}")
        for key in ("ex5_sha256", "csv_sha256", "semantic_result_identity"):
            self.assertIn(key, index, f"index missing identity key {key!r}")
        self.assertIn("source_hashes", index)
        self.assertIn("series_tester_sha256", index["source_hashes"])
        self.assertIn("runs_semantically_identical", index)

    def test_all_referenced_artifact_paths_exist_under_root(self):
        index = json.loads(NATIVE_INDEX.read_text())
        path_keys = ("compile", "compile_log", "ex5", "run1", "run2", "run1_csv", "run2_csv",
                     "run1_journal", "run2_journal", "run1_lifecycle", "run2_lifecycle",
                     "run1_tester_ini", "run2_tester_ini")
        for key in path_keys:
            self.assertIn(key, index, f"index missing path key {key!r}")
            path = NATIVE_ROOT / index[key]
            self.assertTrue(path.is_file(), f"referenced artifact {key}={index[key]} does not exist")

    def test_index_hashes_match_actual_file_bytes(self):
        index = json.loads(NATIVE_INDEX.read_text())
        ex5_path = NATIVE_ROOT / index["ex5"]
        actual_ex5 = hashlib.sha256(ex5_path.read_bytes()).hexdigest()
        self.assertEqual(actual_ex5, index["ex5_sha256"], "EX5 hash mismatch between index and bytes")
        for csv_key in ("run1_csv", "run2_csv"):
            csv_path = NATIVE_ROOT / index[csv_key]
            actual_csv = hashlib.sha256(csv_path.read_bytes()).hexdigest()
            self.assertEqual(actual_csv, index["csv_sha256"], f"CSV hash mismatch for {csv_key}")

    def test_frozen_series_tester_source_hash_is_bound_and_matches(self):
        index = json.loads(NATIVE_INDEX.read_text())
        self.assertEqual(
            index["source_hashes"]["series_tester_sha256"],
            SERIES_TESTER_SOURCE_SHA256,
            "durable package must bind the frozen series tester source hash, not a new one",
        )


class Phase2RSeriesNativeCompileTests(unittest.TestCase):
    """Compile evidence must be self-contained and freshness-bound."""

    def setUp(self):
        if not NATIVE_INDEX.is_file():
            self.skipTest("Phase 2R series native evidence not yet produced")
        self.index = json.loads(NATIVE_INDEX.read_text())
        self.compile = json.loads((NATIVE_ROOT / self.index["compile"]).read_text())

    def test_compile_manifest_reports_zero_errors_and_bound_ex5(self):
        native = self.compile["native_evidence"]
        self.assertEqual(native["error_count"], 0)
        self.assertEqual(self.compile["error_count"], 0)
        self.assertEqual(native["ex5_sha256"], self.index["ex5_sha256"])
        self.assertIn("MetaEditor64.exe", native["rendered_command"])
        self.assertFalse(native["output_ex5_existed_immediately_before"])
        self.assertFalse(native["source_ex5_existed_immediately_before"])

    def test_compile_log_is_committed_and_nonempty(self):
        log_path = NATIVE_ROOT / self.index["compile_log"]
        self.assertGreater(log_path.stat().st_size, 0)

    def test_series_tester_source_hash_bound_in_compile(self):
        self.assertEqual(self.compile["series_tester_source_sha256"], SERIES_TESTER_SOURCE_SHA256)


class Phase2RSeriesNativeRunTests(unittest.TestCase):
    """Each run must be fresh, complete, redacted, and reconcilable."""

    def setUp(self):
        if not NATIVE_INDEX.is_file():
            self.skipTest("Phase 2R series native evidence not yet produced")
        self.index = json.loads(NATIVE_INDEX.read_text())
        self.runs = [
            json.loads((NATIVE_ROOT / self.index[name]).read_text())
            for name in ("run1", "run2")
        ]

    def test_each_run_completed_all_required_launch_stages(self):
        for number, run in enumerate(self.runs, 1):
            self.assertEqual(
                run["launch_stages"],
                {stage: True for stage in REQUIRED_LAUNCH_STAGES},
                f"run{number} missing required launch stages",
            )

    def test_each_run_lifecycle_jsonl_records_all_events(self):
        for number in (1, 2):
            lifecycle_path = NATIVE_ROOT / self.index[f"run{number}_lifecycle"]
            lifecycle = [
                json.loads(line)
                for line in lifecycle_path.read_text(encoding="utf-8-sig").splitlines()
                if line.strip()
            ]
            self.assertEqual(
                {item["event"] for item in lifecycle},
                REQUIRED_LIFECYCLE_EVENTS,
                f"run{number} lifecycle events do not match required set",
            )

    def test_each_run_tester_ini_is_redacted(self):
        for number in (1, 2):
            config = (NATIVE_ROOT / self.index[f"run{number}_tester_ini"]).read_text()
            self.assertIn("Login=<redacted>", config, f"run{number} tester.ini Login not redacted")
            self.assertIn("Server=<redacted>", config, f"run{number} tester.ini Server not redacted")

    def test_each_run_tester_log_is_committed_and_nonempty(self):
        for number in (1, 2):
            run_name = self.index[f"run{number}"].split("/")[0]
            log_path = NATIVE_ROOT / run_name / "tester.log"
            self.assertTrue(log_path.is_file(), f"run{number} tester.log missing")
            self.assertGreater(log_path.stat().st_size, 0, f"run{number} tester.log empty")

    def test_each_run_reconciles_to_frozen_series_vectors(self):
        for number, run in enumerate(self.runs, 1):
            self.assertEqual(run["row_count"], 12, f"run{number} row_count is not 12")
            # SMA vector reconciliation (string "null" for leading warmup rows)
            self.assertEqual(
                run["sma_vector"],
                SMA_VECTOR,
                f"run{number} sma_vector diverges from frozen fixture",
            )
            self.assertEqual(
                run["cross_above_vector"],
                CROSS_ABOVE_VECTOR,
                f"run{number} cross_above_vector diverges from frozen fixture",
            )
            self.assertEqual(
                run["cross_below_vector"],
                CROSS_BELOW_VECTOR,
                f"run{number} cross_below_vector diverges from frozen fixture",
            )
            self.assertEqual(
                run["nullable_vector"],
                NULLABLE_VECTOR,
                f"run{number} nullable_vector diverges from frozen fixture",
            )
            self.assertEqual(
                [bool(x) for x in run["trigger_vector"]],
                [bool(x) for x in TRIGGER_VECTOR],
                f"run{number} trigger_vector diverges from frozen fixture",
            )


class Phase2RSeriesNativeDeterminismTests(unittest.TestCase):
    """The two runs must prove semantic determinism."""

    def setUp(self):
        if not NATIVE_INDEX.is_file():
            self.skipTest("Phase 2R series native evidence not yet produced")
        self.index = json.loads(NATIVE_INDEX.read_text())
        self.runs = [
            json.loads((NATIVE_ROOT / self.index[name]).read_text())
            for name in ("run1", "run2")
        ]

    def test_index_declares_runs_semantically_identical(self):
        self.assertTrue(self.index["runs_semantically_identical"])

    def test_both_runs_share_semantic_result_identity(self):
        self.assertEqual(
            self.runs[0]["semantic_result_identity"],
            self.runs[1]["semantic_result_identity"],
        )

    def test_both_runs_share_result_csv_sha256(self):
        self.assertEqual(
            self.runs[0]["result_csv_sha256"],
            self.runs[1]["result_csv_sha256"],
        )

    def test_semantic_identity_is_bound_in_index(self):
        self.assertEqual(
            self.runs[0]["semantic_result_identity"],
            self.index["semantic_result_identity"],
        )

    def test_semantic_identity_reconciles_with_legacy_acceptance(self):
        """The durable package must reproduce the accepted legacy semantic identity.

        Phase 2R is an evidence-package upgrade, not re-acceptance. The semantic
        result must match the frozen legacy identity; a divergence would mean the
        canary itself changed, which is out of scope.
        """
        self.assertEqual(
            self.index["semantic_result_identity"],
            LEGACY_SEMANTIC_RESULT_IDENTITY,
            "durable semantic identity diverges from accepted legacy — canary contract changed",
        )


if __name__ == "__main__":
    unittest.main()
