import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lab.mql5gen import (
    CONDITION_MANIFEST_FILENAME,
    CONDITION_SOURCE_FILENAME,
    FIXTURE_MANIFEST_FILENAME,
    FIXTURE_SOURCE_FILENAME,
    RUNTIME_IDENTITY,
    generate_fixture_script,
)


ROOT = Path(__file__).resolve().parents[1]
CONDITION_MANIFEST = ROOT / "tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.manifest.json"
EVIDENCE_PATH = ROOT / "tests/fixtures/phase2g_translation_evidence.json"
FROZEN_DIR = ROOT / "tests/fixtures/phase2h_mql5_condition_fixture"
FROZEN_MANIFEST = json.loads((FROZEN_DIR / FIXTURE_MANIFEST_FILENAME).read_text())


class Phase2hMql5FixtureScript(unittest.TestCase):
    def test_repeatability_frozen_source_and_static_contract(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = generate_fixture_script(CONDITION_MANIFEST, EVIDENCE_PATH, first)
            two = generate_fixture_script(CONDITION_MANIFEST, EVIDENCE_PATH, second)
            source_one = Path(first, FIXTURE_SOURCE_FILENAME).read_bytes()
            source_two = Path(second, FIXTURE_SOURCE_FILENAME).read_bytes()
            self.assertEqual(source_one, source_two)
            self.assertEqual(source_one, (FROZEN_DIR / FIXTURE_SOURCE_FILENAME).read_bytes())
            self.assertEqual(one["source_sha256"], two["source_sha256"])
            self.assertEqual(one["fixture_identity"], two["fixture_identity"])
            self.assertEqual(json.loads(Path(first, FIXTURE_MANIFEST_FILENAME).read_text()), FROZEN_MANIFEST)
            source = source_one.decode()
            condition = json.loads(CONDITION_MANIFEST.read_text())
            self.assertEqual(source.count('#include "NoraPhase2RuntimeV1.mqh"'), 1)
            self.assertEqual(source.count('#include "NoraPhase2ConditionV1.mqh"'), 1)
            self.assertIn("void OnStart()", source)
            self.assertIn(condition["function_name"] + "(", source)
            self.assertIn(condition["trigger_function_name"] + "(", source)
            self.assertIn('"nora_phase2_condition_fixture_v1.csv"', source)
            lowered = source.lower()
            for forbidden in ("ordersend", "ctrade", "buy", "sell", "position", "market"):
                self.assertNotIn(forbidden, lowered)
            self.assertNotIn("202", source)
            self.assertNotIn("/tmp/", source)
            self.assertNotIn("\\", source)

    def test_mutations_change_source_and_fixture_identity(self):
        evidence = json.loads(EVIDENCE_PATH.read_text())
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            base_dir = directory / "base"; base_dir.mkdir()
            base = generate_fixture_script(CONDITION_MANIFEST, EVIDENCE_PATH, base_dir)
            expected_mutation = copy.deepcopy(evidence)
            expected_mutation["triggers"][0] = True
            expected_mutation["rows"][0]["trigger"] = True
            expected_path = directory / "expected.json"; expected_path.write_text(json.dumps(expected_mutation))
            expected_dir = directory / "expected"; expected_dir.mkdir()
            changed_expected = generate_fixture_script(CONDITION_MANIFEST, expected_path, expected_dir)
            self.assertNotEqual(changed_expected["source_sha256"], base["source_sha256"])
            self.assertNotEqual(changed_expected["fixture_identity"], base["fixture_identity"])
            input_mutation = copy.deepcopy(evidence)
            input_mutation["rows"][2]["bindings"]["sma3"] = 1.1007
            input_path = directory / "input.json"; input_path.write_text(json.dumps(input_mutation))
            input_dir = directory / "input"; input_dir.mkdir()
            changed_input = generate_fixture_script(CONDITION_MANIFEST, input_path, input_dir)
            self.assertNotEqual(changed_input["source_sha256"], base["source_sha256"])
            self.assertNotEqual(changed_input["fixture_identity"], base["fixture_identity"])
            self.assertIn("1.1007", (input_dir / FIXTURE_SOURCE_FILENAME).read_text())

    def test_atomic_failures(self):
        evidence = json.loads(EVIDENCE_PATH.read_text())
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            def invoke(manifest=CONDITION_MANIFEST, evidence_value=evidence, output=None):
                output = directory / "out" if output is None else output
                output.mkdir(exist_ok=True)
                manifest_path = directory / "condition.json"
                manifest_path.write_text(Path(manifest).read_text() if isinstance(manifest, Path) else json.dumps(manifest))
                evidence_path = directory / "evidence.json"
                evidence_path.write_text(json.dumps(evidence_value))
                result = subprocess.run([sys.executable, "-m", "lab.mql5gen", "fixture-script", "--condition-manifest", str(manifest_path), "--evidence", str(evidence_path), "--output-dir", str(output)], cwd=ROOT, capture_output=True, text=True)
                return result, output
            bad_manifest = json.loads(CONDITION_MANIFEST.read_text()); bad_manifest["translation_identity"] = "0" * 64
            result, output = invoke(manifest=bad_manifest)
            self.assertNotEqual(result.returncode, 0); self.assertFalse(result.stdout); self.assertFalse((output / FIXTURE_SOURCE_FILENAME).exists()); self.assertFalse((output / FIXTURE_MANIFEST_FILENAME).exists())
            missing_binding = copy.deepcopy(evidence); del missing_binding["rows"][0]["bindings"]["sma3"]
            result, output = invoke(evidence_value=missing_binding, output=directory / "missing-binding")
            self.assertNotEqual(result.returncode, 0); self.assertFalse((output / FIXTURE_SOURCE_FILENAME).exists()); self.assertFalse((output / FIXTURE_MANIFEST_FILENAME).exists())
            invalid_bool = copy.deepcopy(evidence); invalid_bool["rows"][0]["bindings"]["close.cross_above.sma3"] = "invalid"
            result, output = invoke(evidence_value=invalid_bool, output=directory / "invalid-bool")
            self.assertNotEqual(result.returncode, 0); self.assertFalse((output / FIXTURE_SOURCE_FILENAME).exists()); self.assertFalse((output / FIXTURE_MANIFEST_FILENAME).exists())
            existing = directory / "existing"; existing.mkdir(); (existing / FIXTURE_SOURCE_FILENAME).write_text("incompatible")
            result, _ = invoke(output=existing)
            self.assertNotEqual(result.returncode, 0); self.assertEqual((existing / FIXTURE_SOURCE_FILENAME).read_text(), "incompatible"); self.assertFalse((existing / FIXTURE_MANIFEST_FILENAME).exists())

