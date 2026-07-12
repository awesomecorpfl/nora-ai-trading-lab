"""Phase-2P deterministic local ATR and Distance/ATR generator checks."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.mql5gen import GenerationError
from lab.mql5gen import atr_distance as subject

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2p_mql5_atr_distance"
EVIDENCE_PATH = FIXTURE / subject.EVIDENCE_FILENAME
FILES = [subject.ATR_SOURCE_FILENAME, subject.ATR_MANIFEST_FILENAME, subject.DISTANCE_SOURCE_FILENAME, subject.DISTANCE_MANIFEST_FILENAME, subject.TESTER_SOURCE_FILENAME, subject.TESTER_MANIFEST_FILENAME]


class Phase2PAtrDistanceGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads(EVIDENCE_PATH.read_text())

    def vectors(self, change=None):
        values = {"timestamps": self.evidence["timestamps"], "open_values": self.evidence["open"], "high": self.evidence["high"], "low": self.evidence["low"], "close": self.evidence["close"], "sma3": self.evidence["sma3_vector"]}
        values = copy.deepcopy(values)
        if change:
            change(values)
        return subject.evidence_from_vectors(**values)

    def write_evidence(self, path: Path, value=None):
        path.write_text(json.dumps(self.evidence if value is None else value, sort_keys=True, separators=(",", ":")) + "\n")

    def test_committed_rust_evidence_is_exact_and_has_separate_identities(self):
        self.assertEqual(self.evidence["rust_task_command"], "engine/target/debug/labengine engine/labengine/tests/fixtures/phase2_distance_atr_task.json")
        self.assertEqual(self.evidence["rust_task_output_semantic_identity"], "c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad")
        self.assertEqual(self.evidence["rust_input_identity"], "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383")
        self.assertEqual(self.evidence["row_count"], 12)
        self.assertEqual(self.evidence["timestamps"], sorted(self.evidence["timestamps"]))
        self.assertEqual(self.evidence["atr_null_positions"], [0, 1])
        self.assertEqual(self.evidence["distance_atr_null_positions"], [0, 1])
        self.assertEqual(self.evidence["rust_atr_evidence_identity"], "26363cfb22ba13fdd5f922173373d56f6aff5b57c3e66604dbec28908b68708d")
        self.assertEqual(self.evidence["rust_distance_atr_evidence_identity"], "f4964fe1ecba67ab79654e59069ca5110e8330956b02b381517cf37bccf17f1f")
        self.assertNotEqual(self.evidence["rust_atr_evidence_identity"], self.evidence["rust_distance_atr_evidence_identity"])
        self.assertEqual(self.evidence, subject._validate_evidence(EVIDENCE_PATH))

    def test_evidence_is_reproduced_by_the_frozen_rust_task(self):
        with tempfile.TemporaryDirectory() as temp:
            task = json.loads((ROOT / subject.RUST_TASK_PATH).read_text())
            task["input_path"] = str(ROOT / subject.RUST_INPUT_PATH)
            task["output_path"] = str(Path(temp) / "output.parquet")
            task_path = Path(temp) / "task.json"; task_path.write_text(json.dumps(task))
            result = subprocess.run([str(ROOT / "engine/target/debug/labengine"), str(task_path)], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(result.stdout)["output_semantic_content_identity"], subject.RUST_TASK_IDENTITY)
            import pyarrow.parquet as pq
            output = pq.read_table(task["output_path"])
            source = pq.read_table(ROOT / subject.RUST_INPUT_PATH)
            for key in ("timestamp", "open", "high", "low", "close"):
                evidence_key = "timestamps" if key == "timestamp" else key
                self.assertEqual(output[key].to_pylist() if key == "timestamp" else source[key].to_pylist(), self.evidence[evidence_key])
            self.assertEqual(output["atr3"].to_pylist(), self.evidence["atr_vector"])
            self.assertEqual(output["close_sma3.distance_atr"].to_pylist(), self.evidence["distance_atr_vector"])

    def test_generated_hashes_identities_and_tester_contract(self):
        atr = json.loads((FIXTURE / subject.ATR_MANIFEST_FILENAME).read_text())
        distance = json.loads((FIXTURE / subject.DISTANCE_MANIFEST_FILENAME).read_text())
        tester = json.loads((FIXTURE / subject.TESTER_MANIFEST_FILENAME).read_text())
        self.assertEqual(atr["source_sha256"], "aa88f1627a016c20859b8eb4ecf7717b3d922ab879adeb63f3f460fa8d2c478c")
        self.assertEqual(atr["atr_runtime_identity"], "80445d259d9ac9bcf3a15bf6ec12a160594237ee469b2ee53c46d22f99370194")
        self.assertEqual(distance["source_sha256"], "80dada0eb19f53672e90009bce8d39fc74e18eaaed530e0725715be0fa417a19")
        self.assertEqual(distance["distance_atr_runtime_identity"], "008c2f3a1824a8a22b03c6b447e3ae1a06cdd6c852381d96c8ca7eefba730c12")
        self.assertEqual(tester["source_sha256"], "490a0c37f1d611c48f57e50dfb533265790950fa76b0e0a08edd915c91f05f0a")
        self.assertEqual(tester["tester_identity"], "38c4e578079fd42ec31c390c84e78162d120b67a7bad48fb7859eb350dbad51e")
        source = (FIXTURE / subject.TESTER_SOURCE_FILENAME).read_text()
        for column in subject.CSV_COLUMNS:
            self.assertIn('"' + column + '"', source)
        self.assertIn("NoraTimestamp_Values", source)
        self.assertIn("previous_close", source)
        self.assertNotIn(str(ROOT), source)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            subject.generate_package(EVIDENCE_PATH, output, ROOT)
            for filename in FILES:
                self.assertEqual((output / filename).read_bytes(), (FIXTURE / filename).read_bytes())

    def test_repeat_generation_is_byte_identical_including_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / "first", root / "second"
            first.mkdir(); second.mkdir()
            for output in (first, second):
                self.write_evidence(output / subject.EVIDENCE_FILENAME)
                subject.generate_package(output / subject.EVIDENCE_FILENAME, output, ROOT)
            for filename in [subject.EVIDENCE_FILENAME, *FILES]:
                self.assertEqual((first / filename).read_bytes(), (second / filename).read_bytes())
                self.assertNotIn(str(first).encode(), (first / filename).read_bytes())
                self.assertNotIn(str(second).encode(), (second / filename).read_bytes())

    def test_mutations_change_exact_semantic_positions_and_identities(self):
        baseline = self.evidence
        high = self.vectors(lambda values: values["high"].__setitem__(4, values["high"][4] + 0.0005))
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["true_range"], high["true_range"])) if a != b], [4])
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["atr_vector"], high["atr_vector"])) if a != b], list(range(4, 12)))
        self.assertNotEqual(baseline["rust_atr_evidence_identity"], high["rust_atr_evidence_identity"])
        low = self.vectors(lambda values: values["low"].__setitem__(5, values["low"][5] - 0.0005))
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["true_range"], low["true_range"])) if a != b], [5])
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["atr_vector"], low["atr_vector"])) if a != b], list(range(5, 12)))
        self.assertNotEqual(baseline["rust_atr_evidence_identity"], low["rust_atr_evidence_identity"])
        gap = self.vectors(lambda values: values["close"].__setitem__(3, values["close"][3] - 0.002))
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["true_range"], gap["true_range"])) if a != b], [4])
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["atr_vector"], gap["atr_vector"])) if a != b], list(range(4, 12)))
        self.assertNotEqual(baseline["rust_atr_evidence_identity"], gap["rust_atr_evidence_identity"])
        numerator = self.vectors(lambda values: values["sma3"].__setitem__(7, values["sma3"][7] + 0.01))
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["distance_numerator"], numerator["distance_numerator"])) if a != b], [7])
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["distance_atr_vector"], numerator["distance_atr_vector"])) if a != b], [7])
        self.assertNotEqual(baseline["rust_distance_atr_evidence_identity"], numerator["rust_distance_atr_evidence_identity"])
        nullable = self.vectors(lambda values: values["sma3"].__setitem__(2, None))
        self.assertEqual(nullable["distance_atr_null_positions"], [0, 1, 2])
        self.assertEqual([index for index, (a, b) in enumerate(zip(baseline["distance_atr_vector"], nullable["distance_atr_vector"])) if a != b], [2])
        self.assertNotEqual(baseline["rust_distance_atr_evidence_identity"], nullable["rust_distance_atr_evidence_identity"])
        self.assertNotEqual(baseline["fixture_package_identity"], nullable["fixture_package_identity"])

    def test_atomic_failures_leave_no_partial_package(self):
        cases = []
        missing_root = Path(tempfile.mkdtemp())
        cases.append(("missing Rust input fixture", self.evidence, missing_root))
        for name, mutate in (
            ("incorrect frozen Rust fixture identity", lambda value: value.__setitem__("rust_task_output_semantic_identity", "0" * 64)),
            ("incorrect ATR expected-vector length", lambda value: value.__setitem__("atr_vector", value["atr_vector"][:-1])),
            ("incorrect Distance/ATR expected-vector length", lambda value: value.__setitem__("distance_atr_vector", value["distance_atr_vector"][:-1])),
            ("non-finite input", lambda value: value["high"].__setitem__(4, float("inf"))),
            ("unsupported ATR period", lambda value: value.__setitem__("atr_period", 4)),
        ):
            value = copy.deepcopy(self.evidence); mutate(value); cases.append((name, value, ROOT))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index, (name, value, repository_root) in enumerate(cases):
                output = root / str(index); output.mkdir()
                evidence = output / "input.json"; self.write_evidence(evidence, value)
                with self.assertRaises(GenerationError, msg=name):
                    subject.generate_package(evidence, output, repository_root)
                self.assertEqual([path.name for path in output.iterdir()], ["input.json"], name)
            self.assertEqual(subject.derive_distance_atr([1.0], [0.0], [0.0]) if False else subject.derive_distance_atr([1.0] * 12, [0.0] * 12, [0.0] * 12)[1], [None] * 12)
            output = root / "preexisting"; output.mkdir(); evidence = output / "input.json"; self.write_evidence(evidence)
            (output / subject.ATR_SOURCE_FILENAME).write_text("sentinel")
            with self.assertRaises(GenerationError): subject.generate_package(evidence, output, ROOT)
            self.assertEqual((output / subject.ATR_SOURCE_FILENAME).read_text(), "sentinel")
            self.assertEqual(sorted(path.name for path in output.iterdir()), [subject.ATR_SOURCE_FILENAME, "input.json"])

    def test_publish_failure_rolls_back_all_stages(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp); evidence = output / "input.json"; self.write_evidence(evidence)
            original = subject._publish
            calls = 0
            def failing_publish(directory, filename, payload):
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise GenerationError("simulated publish failure")
                return original(directory, filename, payload)
            with patch.object(subject, "_publish", failing_publish):
                with self.assertRaises(GenerationError):
                    subject.generate_package(evidence, output, ROOT)
            self.assertEqual([path.name for path in output.iterdir()], ["input.json"])


if __name__ == "__main__":
    unittest.main()
