import json
import tempfile
import unittest
from pathlib import Path

from lab.mql5gen import GenerationError
from lab.mql5gen.series import (
    CONDITION_IDENTITY, SERIES_SOURCE_FILENAME, TESTER_SOURCE_FILENAME,
    generate_series_runtime, generate_series_tester,
)

ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/fixtures/phase2k_mql5_sma_cross/series_evidence.json"
CONDITION = ROOT / "tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.manifest.json"


class Phase2KSeriesCanaryTests(unittest.TestCase):
    def make_runtime(self, root):
        root.mkdir(parents=True, exist_ok=True)
        out = root / "runtime"
        out.mkdir()
        result = generate_series_runtime(out)
        return out, result

    def make_tester(self, root, evidence=EVIDENCE):
        runtime, manifest = self.make_runtime(root)
        out = root / "tester"
        out.mkdir()
        result = generate_series_tester(evidence, runtime / "NoraPhase2SeriesRuntimeV1.manifest.json", CONDITION, out)
        return out, result

    def test_generation_is_byte_identical_and_manifest_has_no_paths(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"; b = Path(td) / "b"; a.mkdir(); b.mkdir()
            ar, at = self.make_tester(a); br, bt = self.make_tester(b)
            self.assertEqual((ar.parent / "runtime" / SERIES_SOURCE_FILENAME).read_bytes(), (br.parent / "runtime" / SERIES_SOURCE_FILENAME).read_bytes())
            self.assertEqual((at := (ar.parent / "runtime" / "NoraPhase2SeriesRuntimeV1.manifest.json").read_bytes()), (br.parent / "runtime" / "NoraPhase2SeriesRuntimeV1.manifest.json").read_bytes())
            self.assertEqual((ar / TESTER_SOURCE_FILENAME).read_bytes(), (br / TESTER_SOURCE_FILENAME).read_bytes())
            self.assertEqual(json.loads((ar / "NoraPhase2SeriesTesterCanaryV1.manifest.json").read_text()), json.loads((br / "NoraPhase2SeriesTesterCanaryV1.manifest.json").read_text()))
            self.assertNotIn(str(a).encode(), at)

    def test_input_mutation_changes_source_and_identity(self):
        with tempfile.TemporaryDirectory() as td:
            base = json.loads(EVIDENCE.read_text()); changed = dict(base); changed["input_vector"] = list(base["input_vector"]); changed["input_vector"][3] += 0.0001
            mutation = Path(td) / "mutated.json"; mutation.write_text(json.dumps(changed))
            _, first = self.make_tester(Path(td) / "first")
            _, second = self.make_tester(Path(td) / "second", mutation)
            self.assertNotEqual(first["source_sha256"], second["source_sha256"])
            self.assertNotEqual(first["tester_fixture_identity"], second["tester_fixture_identity"])

    def test_period_four_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bad = json.loads(EVIDENCE.read_text()); bad["sma_period"] = 4
            path = Path(td) / "bad.json"; path.write_text(json.dumps(bad))
            with self.assertRaises(GenerationError): self.make_tester(Path(td) / "run", path)

    def test_atomic_contract_failures(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"; root.mkdir(); out, _ = self.make_runtime(root)
            with self.assertRaises(GenerationError): generate_series_runtime(out)
            bad = json.loads(EVIDENCE.read_text()); bad["input_vector"][0] = float("nan")
            path = Path(td) / "nan.json"; path.write_text(json.dumps(bad))
            tester = Path(td) / "tester"; tester.mkdir()
            with self.assertRaises(GenerationError): generate_series_tester(path, out / "NoraPhase2SeriesRuntimeV1.manifest.json", CONDITION, tester)
            self.assertFalse((tester / TESTER_SOURCE_FILENAME).exists())

    def test_mismatched_rust_artifact_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bad = json.loads(EVIDENCE.read_text()); bad["rust_cross_artifact_identity"] = "0" * 64
            path = Path(td) / "bad.json"; path.write_text(json.dumps(bad))
            root = Path(td) / "run"
            with self.assertRaises(GenerationError): self.make_tester(root, path)
            self.assertFalse((root / "tester" / TESTER_SOURCE_FILENAME).exists())

    def test_static_no_market_data_or_trading_contract(self):
        with tempfile.TemporaryDirectory() as td:
            out, _ = self.make_tester(Path(td) / "run")
            text = ((out / TESTER_SOURCE_FILENAME).read_text() + (Path(td) / "run" / "runtime" / SERIES_SOURCE_FILENAME).read_text()).lower()
            for forbidden in ["ima", "copybuffer", "copyrates", "copyclose", "symbolinfotick", "bid", "ask", "spread", "ordersend", "ctrade", "buy", "sell", "positionopen", "positionclose", "account"]:
                import re
                self.assertIsNone(re.search(r"(?<![a-z0-9_])" + forbidden + r"(?![a-z0-9_])", text))
            self.assertIn('#include "noraphase2seriesruntimev1.mqh"', text)

    def test_contract_constants_remain_frozen(self):
        self.assertEqual(CONDITION_IDENTITY, "1fa3d6613348a2fa532c4393e2a95795546c9cc5e2c86d010ee30fa9fe9632af")


if __name__ == "__main__": unittest.main()
