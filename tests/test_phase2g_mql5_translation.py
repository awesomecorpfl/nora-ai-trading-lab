import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq

from lab.mql5gen import (
    CONDITION_MANIFEST_FILENAME,
    CONDITION_SOURCE_FILENAME,
    RUNTIME_IDENTITY,
    GenerationError,
    translate_condition,
)


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "engine/target/debug/labengine"
AST_PATH = ROOT / "engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json"
RUNTIME_MANIFEST = ROOT / "tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.manifest.json"
EVIDENCE = json.loads((ROOT / "tests/fixtures/phase2g_translation_evidence.json").read_text())


class Phase2gMql5Translation(unittest.TestCase):
    def test_accepted_fixture_repeatability_and_expression(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = translate_condition(AST_PATH, RUNTIME_MANIFEST, first)
            two = translate_condition(AST_PATH, RUNTIME_MANIFEST, second)
            source_one = Path(first, CONDITION_SOURCE_FILENAME).read_bytes()
            source_two = Path(second, CONDITION_SOURCE_FILENAME).read_bytes()
            self.assertEqual(source_one, source_two)
            frozen_dir = ROOT / "tests/fixtures/phase2g_mql5_condition"
            self.assertEqual(source_one, (frozen_dir / CONDITION_SOURCE_FILENAME).read_bytes())
            self.assertEqual(one["source_sha256"], two["source_sha256"])
            self.assertEqual(one["translation_identity"], two["translation_identity"])
            self.assertEqual(one["canonical_ast_identity"], "667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664")
            self.assertEqual(one["runtime_identity"], RUNTIME_IDENTITY)
            self.assertEqual(one["series_bindings"], [
                {"original_series_name": "close.cross_above.sma3", "series_type": "boolean", "parameter_name": "nora_bool_close_cross_above_sma3_47260c9c5e68"},
                {"original_series_name": "sma3.cross_below.close", "series_type": "boolean", "parameter_name": "nora_bool_sma3_cross_below_close_f82f2c17f999"},
                {"original_series_name": "sma3", "series_type": "numeric", "parameter_name": "nora_num_sma3_662a95a8677d"},
            ])
            source = source_one.decode()
            self.assertIn('#include "NoraPhase2RuntimeV1.mqh"', source)
            self.assertIn("NoraBoolAndV1(NoraCompareGtV1(nora_num_sma3_662a95a8677d, NoraNumericValueV1(1.1008)), NoraBoolOrV1(nora_bool_close_cross_above_sma3_47260c9c5e68, NoraBoolNotV1(nora_bool_sma3_cross_below_close_f82f2c17f999)))", source)
            self.assertNotIn("&&", source)
            self.assertNotIn("||", source)
            self.assertNotIn("!", source)
            self.assertEqual(json.loads(Path(first, CONDITION_MANIFEST_FILENAME).read_text()), json.loads(Path(second, CONDITION_MANIFEST_FILENAME).read_text()))
            self.assertEqual(json.loads(Path(first, CONDITION_MANIFEST_FILENAME).read_text()), json.loads((frozen_dir / CONDITION_MANIFEST_FILENAME).read_text()))

    def test_compact_operator_matrix_and_binding_conflict(self):
        operators = ("gt", "gte", "lt", "lte")
        with tempfile.TemporaryDirectory() as directory:
            for operator in operators:
                ast = {"schema_version": 1, "root": {"kind": "compare", "op": operator, "left": {"kind": "numeric_series", "ref": {"series": "price", "type": "numeric"}}, "right": {"kind": "number", "value": 2}}}
                out = Path(directory) / operator
                out.mkdir()
                result = translate_condition(ast_path=self._write_json(out, ast), runtime_manifest_path=RUNTIME_MANIFEST, output_dir=out)
                source = Path(result["header_path"]).read_text()
                self.assertIn(f"NoraCompare{operator.capitalize()}V1", source)
            nested = {"schema_version": 1, "root": {"kind": "or", "args": [{"kind": "and", "args": [{"kind": "boolean_series", "ref": {"series": "signal.a", "type": "boolean"}}, {"kind": "not", "arg": {"kind": "boolean_series", "ref": {"series": "signal.b", "type": "boolean"}}}]}, {"kind": "compare", "op": "lte", "left": {"kind": "numeric_series", "ref": {"series": "price", "type": "numeric"}}, "right": {"kind": "number", "value": 2.0}}]}}
            nested_dir = Path(directory) / "nested"
            nested_dir.mkdir()
            nested_result = translate_condition(self._write_json(nested_dir, nested), RUNTIME_MANIFEST, nested_dir)
            nested_source = Path(nested_result["header_path"]).read_text()
            self.assertIn("NoraBoolOrV1(NoraBoolAndV1(nora_bool_signal_a", nested_source)
            conflict = {"schema_version": 1, "root": {"kind": "and", "args": [{"kind": "boolean_series", "ref": {"series": "same", "type": "boolean"}}, {"kind": "compare", "op": "gt", "left": {"kind": "numeric_series", "ref": {"series": "same", "type": "numeric"}}, "right": {"kind": "number", "value": 1}}]}}
            conflict_dir = Path(directory) / "conflict"
            conflict_dir.mkdir()
            with self.assertRaisesRegex(GenerationError, "conflicting types"):
                translate_condition(self._write_json(conflict_dir, conflict), RUNTIME_MANIFEST, conflict_dir)

    def test_rust_evidence_and_mutations(self):
        self.assertEqual(EVIDENCE["nullable_results"], ["null", "null", "false", "true", "true", "true", "true", "true", "true", "true", "true", "true"])
        self.assertEqual(EVIDENCE["triggers"], [False, False, False, True, True, True, True, True, True, True, True, True])
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            baseline = json.loads(AST_PATH.read_text())["ast"]
            baseline_path = self._write_json(directory, baseline, "baseline.json")
            (directory / "base").mkdir()
            base_result = translate_condition(baseline_path, RUNTIME_MANIFEST, directory / "base")
            def rust_identity(ast, name):
                task_path = self._write_json(directory, {"task_version": 1, "task_type": "canonicalize_ast", "output_path": str(directory / (name + ".canonical.json")), "ast": ast}, name + ".task.json")
                result = subprocess.run([str(BINARY), str(task_path)], cwd=ROOT, capture_output=True, text=True, check=True)
                return json.loads(result.stdout)["ast_semantic_identity"]
            rust_base_identity = rust_identity(baseline, "rust-base")
            self.assertEqual(rust_base_identity, base_result["canonical_ast_identity"])
            changed_constant = json.loads(json.dumps(baseline)); changed_constant["root"]["args"][0]["right"]["value"] = 1.1009
            (directory / "constant").mkdir()
            constant_result = translate_condition(self._write_json(directory, changed_constant, "constant.json"), RUNTIME_MANIFEST, directory / "constant")
            self.assertNotEqual(rust_identity(changed_constant, "rust-constant"), rust_base_identity)
            self.assertNotEqual(constant_result["canonical_ast_identity"], base_result["canonical_ast_identity"])
            self.assertNotEqual(constant_result["source_sha256"], base_result["source_sha256"])
            self.assertNotEqual(constant_result["translation_identity"], base_result["translation_identity"])
            renamed = json.loads(json.dumps(baseline)); renamed["root"]["args"][0]["left"]["ref"]["series"] = "sma4"
            (directory / "renamed").mkdir()
            renamed_result = translate_condition(self._write_json(directory, renamed, "renamed.json"), RUNTIME_MANIFEST, directory / "renamed")
            self.assertNotEqual(rust_identity(renamed, "rust-renamed"), rust_base_identity)
            self.assertNotEqual(renamed_result["series_bindings"], base_result["series_bindings"])
            self.assertNotEqual(renamed_result["source_sha256"], base_result["source_sha256"])
            self.assertNotEqual(renamed_result["translation_identity"], base_result["translation_identity"])

    def test_cli_atomic_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            def invoke(ast, manifest=RUNTIME_MANIFEST, output=None):
                output = directory / "out" if output is None else output
                output.mkdir(exist_ok=True)
                ast_file = self._write_json(directory, ast, "failure.json")
                return subprocess.run([sys.executable, "-m", "lab.mql5gen", "condition", "--ast", str(ast_file), "--runtime-manifest", str(manifest), "--output-dir", str(output)], cwd=ROOT, capture_output=True, text=True), output
            unsupported = {"schema_version": 1, "root": {"kind": "future_node"}}
            result, output = invoke(unsupported)
            self.assertNotEqual(result.returncode, 0); self.assertFalse(result.stdout); self.assertFalse((output / CONDITION_SOURCE_FILENAME).exists()); self.assertFalse((output / CONDITION_MANIFEST_FILENAME).exists())
            conflict = {"schema_version": 1, "root": {"kind": "and", "args": [{"kind": "boolean_series", "ref": {"series": "same", "type": "boolean"}}, {"kind": "compare", "op": "gt", "left": {"kind": "numeric_series", "ref": {"series": "same", "type": "numeric"}}, "right": {"kind": "number", "value": 1}}]}}
            result, output = invoke(conflict, output=directory / "conflict")
            self.assertNotEqual(result.returncode, 0); self.assertFalse((output / CONDITION_SOURCE_FILENAME).exists()); self.assertFalse((output / CONDITION_MANIFEST_FILENAME).exists())
            bad_manifest = directory / "bad.manifest.json"; bad = json.loads(RUNTIME_MANIFEST.read_text()); bad["runtime_identity"] = "0" * 64; bad_manifest.write_text(json.dumps(bad)); result, output = invoke(json.loads(AST_PATH.read_text())["ast"], manifest=bad_manifest, output=directory / "bad-runtime")
            self.assertNotEqual(result.returncode, 0); self.assertFalse((output / CONDITION_SOURCE_FILENAME).exists()); self.assertFalse((output / CONDITION_MANIFEST_FILENAME).exists())
            existing = directory / "existing"; existing.mkdir(); (existing / CONDITION_SOURCE_FILENAME).write_text("incompatible")
            result, _ = invoke(json.loads(AST_PATH.read_text())["ast"], output=existing)
            self.assertNotEqual(result.returncode, 0); self.assertEqual((existing / CONDITION_SOURCE_FILENAME).read_text(), "incompatible"); self.assertFalse((existing / CONDITION_MANIFEST_FILENAME).exists())

    @staticmethod
    def _write_json(directory, value, name="ast.json"):
        path = Path(directory) / name
        path.write_text(json.dumps(value))
        return path
