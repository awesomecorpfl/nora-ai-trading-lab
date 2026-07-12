import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.mt5 import CompileError, compile_condition_canary


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.mqh"
CONDITION = ROOT / "tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.mqh"
SCRIPT = ROOT / "tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.mq5"


class Phase2iCompileCanary(unittest.TestCase):
    def test_source_hash_mismatch_fails_before_ssh(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            mutated = directory / RUNTIME.name
            mutated.write_bytes(RUNTIME.read_bytes() + b"\n")
            (directory / "NoraPhase2RuntimeV1.manifest.json").write_text((RUNTIME.parent / "NoraPhase2RuntimeV1.manifest.json").read_text())
            with patch("lab.mt5._ssh", side_effect=AssertionError("SSH must not be reached")):
                with self.assertRaisesRegex(CompileError, "frozen source hash mismatch"):
                    compile_condition_canary(mutated, CONDITION, SCRIPT, directory / "output")
            self.assertFalse((directory / "output" / "compile_manifest.json").exists())

    def test_frozen_contract_values_are_present(self):
        manifest = json.loads((ROOT / "tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.manifest.json").read_text())
        self.assertEqual(manifest["runtime_identity"], "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d")
        self.assertEqual(manifest["row_count"], 12)
        self.assertEqual(len(manifest["expected_nullable_vector"]), 12)
        self.assertEqual(len(manifest["expected_trigger_vector"]), 12)
