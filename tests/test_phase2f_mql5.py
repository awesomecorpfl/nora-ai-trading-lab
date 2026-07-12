import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from lab.mql5gen import (
    MANIFEST_FILENAME,
    RUNTIME_VERSION,
    SOURCE_FILENAME,
    SUPPORTED_AST_NODES,
    SUPPORTED_OPERATORS,
    generate,
    runtime_identity_for_test,
)


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "engine/target/debug/labengine"
FIXTURE = json.loads((ROOT / "tests/fixtures/phase2f_mql5_nullable_semantics.json").read_text())


class Phase2fMql5Runtime(unittest.TestCase):
    def test_repeatability_inventory_sensitivity_and_manifest(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = generate(first)
            two = generate(second)
            header_one = Path(first, SOURCE_FILENAME).read_bytes()
            header_two = Path(second, SOURCE_FILENAME).read_bytes()
            self.assertEqual(header_one, header_two)
            self.assertFalse(header_one.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r\n", header_one)
            self.assertEqual(one["source_sha256"], two["source_sha256"])
            self.assertEqual(one["runtime_identity"], two["runtime_identity"])
            self.assertEqual(one["supported_ast_nodes"], SUPPORTED_AST_NODES)
            self.assertEqual(one["supported_operators"], SUPPORTED_OPERATORS)
            manifest_one = json.loads(Path(first, MANIFEST_FILENAME).read_text())
            manifest_two = json.loads(Path(second, MANIFEST_FILENAME).read_text())
            self.assertEqual(manifest_one, manifest_two)
            self.assertEqual(set(manifest_one), {"runtime_version", "source_filename", "supported_ast_nodes", "supported_operators", "source_sha256", "runtime_identity"})
            self.assertNotEqual(runtime_identity_for_test(source=header_one + b"\n"), one["runtime_identity"])
            self.assertNotEqual(runtime_identity_for_test(operators=SUPPORTED_OPERATORS + ["test_only"]), one["runtime_identity"])

    def test_atomic_generation_failures(self):
        with tempfile.TemporaryDirectory() as root:
            missing = Path(root) / "missing"
            result = subprocess.run([sys.executable, "-m", "lab.mql5gen", "--output-dir", str(missing)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("output directory must be", result.stderr)
            self.assertFalse(missing.exists())

            existing = Path(root) / "existing"
            existing.mkdir()
            (existing / SOURCE_FILENAME).write_text("incompatible")
            result = subprocess.run([sys.executable, "-m", "lab.mql5gen", "--output-dir", str(existing)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("targets must not already exist", result.stderr)
            self.assertFalse((existing / MANIFEST_FILENAME).exists())
            self.assertEqual((existing / SOURCE_FILENAME).read_text(), "incompatible")
            self.assertFalse(any(path.name.endswith(".partial") for path in existing.iterdir()))

            unknown = Path(root) / "unknown"
            unknown.mkdir()
            result = subprocess.run([sys.executable, "-m", "lab.mql5gen", "--output-dir", str(unknown), "--runtime-version", "unknown"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsupported runtime_version", result.stderr)
            self.assertEqual(list(unknown.iterdir()), [])

    def _run_rust(self, input_path, output_path, ast):
        task_path = output_path.with_suffix(".json")
        task_path.write_text(json.dumps({"task_version": 1, "task_type": "evaluate_ast", "input_path": str(input_path), "output_path": str(output_path), "output": "signal", "ast": ast}))
        result = subprocess.run([str(BINARY), str(task_path)], cwd=ROOT, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    @staticmethod
    def _values(path):
        return ["null" if value is None else ("true" if value else "false") for value in pq.read_table(path)["signal"].to_pylist()]

    def test_rust_evaluator_matches_nullable_runtime_fixture(self):
        if not BINARY.exists():
            subprocess.run(["cargo", "build", "--manifest-path", str(ROOT / "engine/Cargo.toml")], cwd=ROOT, check=True)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            bool_path = directory / "boolean.parquet"
            bool_table = pa.table({"timestamp": [f"2025.01.01 00:0{i}" for i in range(9)], "left": [None, None, None, False, False, False, True, True, True], "right": [None, False, True, None, False, True, None, False, True], "single": [None, False, True, None, False, True, None, False, True]})
            pq.write_table(bool_table, bool_path)
            not_path = directory / "not.parquet"
            not_ast = {"schema_version": 1, "root": {"kind": "not", "arg": {"kind": "boolean_series", "ref": {"series": "single", "type": "boolean"}}}}
            self._run_rust(bool_path, not_path, not_ast)
            self.assertEqual(self._values(not_path), [FIXTURE["not"][value] for value in ["null", "false", "true", "null", "false", "true", "null", "false", "true"]])
            for kind, expected in [("and", FIXTURE["and"]), ("or", FIXTURE["or"])]:
                output = directory / (kind + ".parquet")
                ast = {"schema_version": 1, "root": {"kind": kind, "args": [{"kind": "boolean_series", "ref": {"series": "left", "type": "boolean"}}, {"kind": "boolean_series", "ref": {"series": "right", "type": "boolean"}}]}}
                self._run_rust(bool_path, output, ast)
                expected_values = [expected[row][column] for row in range(3) for column in range(3)]
                self.assertEqual(self._values(output), expected_values)

            numeric_path = directory / "numeric.parquet"
            numeric_table = pa.table({"timestamp": [f"2025.01.01 00:0{i}" for i in range(5)], "left": [2.0, 1.0, None, 1.0, None], "right": [1.0, 2.0, 1.0, None, None]})
            pq.write_table(numeric_table, numeric_path)
            for operator in ("gt", "gte", "lt", "lte"):
                output = directory / (operator + ".parquet")
                ast = {"schema_version": 1, "root": {"kind": "compare", "op": operator, "left": {"kind": "numeric_series", "ref": {"series": "left", "type": "numeric"}}, "right": {"kind": "numeric_series", "ref": {"series": "right", "type": "numeric"}}}}
                self._run_rust(numeric_path, output, ast)
                self.assertEqual(self._values(output), FIXTURE["comparisons"][operator])

