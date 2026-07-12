"""Phase-2S typed ATR3/Wilder and Distance/ATR feature-plan admission checks."""
import json
import tempfile
import unittest
from pathlib import Path

from lab.mql5gen import (
    ATR_DISTANCE_FEATURE_MANIFEST_FILENAME,
    ATR_DISTANCE_FEATURE_SOURCE_FILENAME,
    GenerationError,
    translate_atr_distance_feature_plan,
)


ROOT = Path(__file__).resolve().parents[1]
NATIVE_IDENTITY = "8a912bd9152d16c8e94b1a96210d2cc6917c5b2639f615b0ecd4931dac2669f2"


def document(period=3, method="wilder", reference="sma3"):
    atr = {"type": "atr", "high": {"type": "series", "name": "high"}, "low": {"type": "series", "name": "low"}, "close": {"type": "series", "name": "close"}, "period": period, "method": method}
    return {"schema_version": 1, "root": {"kind": "compare", "op": "gt", "left": {"type": "distance_atr", "value": {"type": "series", "name": "close"}, "reference": {"type": "series", "name": reference}, "atr": atr}, "right": {"kind": "number", "value": 0}}}


class Phase2SAtrDistanceAstAdmissionTests(unittest.TestCase):
    def _write(self, directory, value):
        path = Path(directory) / "ast.json"; path.write_text(json.dumps(value)); return path

    def test_deterministic_plan_uses_accepted_runtimes_without_formula_duplication(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one, two = Path(first), Path(second)
            result_one = translate_atr_distance_feature_plan(self._write(one, document()), one)
            result_two = translate_atr_distance_feature_plan(self._write(two, document()), two)
            source_one = (one / ATR_DISTANCE_FEATURE_SOURCE_FILENAME).read_bytes()
            self.assertEqual(source_one, (two / ATR_DISTANCE_FEATURE_SOURCE_FILENAME).read_bytes())
            self.assertEqual(result_one["translation_identity"], result_two["translation_identity"])
            self.assertEqual(result_one["features"], result_two["features"])
            source = source_one.decode()
            self.assertIn('#include "NoraPhase2AtrRuntimeV1.mqh"', source)
            self.assertIn('#include "NoraPhase2DistanceAtrRuntimeV1.mqh"', source)
            self.assertIn("NoraAtr3V1", source)
            self.assertIn("NoraDistanceAtrV1", source)
            self.assertNotIn("previous_atr", source)
            self.assertNotIn("high[row_index] - low[row_index]", source)
            self.assertEqual(len(result_one["features"]), 2)
            self.assertEqual(json.loads((one / ATR_DISTANCE_FEATURE_MANIFEST_FILENAME).read_text())["translation_identity"], result_one["translation_identity"])

    def test_invalid_and_mutated_nodes_fail_or_change_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            baseline = translate_atr_distance_feature_plan(self._write(directory, document()), directory)
            for name, value in (("period", document(period=2)), ("method", document(method="sma"))):
                out = directory / name; out.mkdir()
                with self.assertRaises(GenerationError): translate_atr_distance_feature_plan(self._write(out, value), out)
                self.assertFalse((out / ATR_DISTANCE_FEATURE_SOURCE_FILENAME).exists())
            out = directory / "mutated"; out.mkdir()
            mutated = translate_atr_distance_feature_plan(self._write(out, document(reference="sma4")), out)
            self.assertNotEqual(mutated["canonical_ast_identity"], baseline["canonical_ast_identity"])
            self.assertNotEqual(mutated["translation_identity"], baseline["translation_identity"])
            self.assertNotEqual(mutated["features"][-1]["identity"], baseline["features"][-1]["identity"])

    def test_committed_cross_layer_fixture_binds_native_parity(self):
        fixture = json.loads((ROOT / "tests/fixtures/phase2s_atr_distance_ast_admission.json").read_text())
        self.assertEqual(fixture["native_semantic_result_identity"], NATIVE_IDENTITY)
        self.assertEqual(fixture["admitted_period"], 3)
        self.assertEqual(fixture["admitted_method"], "wilder")
        self.assertFalse(fixture["search_authorized"])
