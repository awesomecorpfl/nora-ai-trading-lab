import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "engine/target/debug/labengine"
BASE = {
    "task_version": 1,
    "task_type": "generate_named_rng_stream_v1",
    "experiment_id": "experiment-fixture-a",
    "stage_id": "phase2e",
    "task_id": "rng-fixture-001",
    "stream_name": "fixture.primary",
    "draw_count": 8,
}
EXPECTED_VALUES = [15683671983959346999, 17675346156240728563, 9059889430460492925,
                   17956420554887779641, 14995845127018178684, 324214738316669255,
                   1627427474117293339, 4198829781091559740]


class Phase2eRng(unittest.TestCase):
    def run_task(self, directory, task):
        task = dict(task)
        path = Path(directory) / "task.json"
        path.write_text(json.dumps(task))
        result = subprocess.run([str(BINARY), str(path)], capture_output=True, text=True)
        return result, task

    def test_baseline_repeat_prefix_and_draw_count(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            tasks = []
            for directory, task_name in [(first, "one"), (second, "two")]:
                task = {**BASE, "output_path": str(Path(directory) / task_name / "rng.parquet")}
                Path(task["output_path"]).parent.mkdir()
                result, _ = self.run_task(directory, task)
                self.assertEqual(result.returncode, 0, result.stderr)
                tasks.append((json.loads(result.stdout), pq.read_table(task["output_path"])))
            self.assertEqual(tasks[0][0]["seed_hex"], "ada6b7c486f979d5accb0edb4e5b57928f514985f0bfd5765bd426e183181c57")
            self.assertEqual(tasks[0][0]["stream_identity"], "e8c1364bca46d45610dca7db0c55776dfa2afb1bfd4550dc40c5fd37bbd8aa6e")
            self.assertEqual(tasks[0][1]["value_u64"].to_pylist(), EXPECTED_VALUES)
            self.assertEqual(tasks[0][1].to_pydict(), tasks[1][1].to_pydict())
            self.assertEqual({k: v for k, v in tasks[0][0].items() if k != "output_path"}, {k: v for k, v in tasks[1][0].items() if k != "output_path"})
            short_dir = Path(first) / "short"
            short_dir.mkdir()
            short = {**BASE, "draw_count": 4, "output_path": str(short_dir / "rng.parquet")}
            result, _ = self.run_task(short_dir, short)
            self.assertEqual(result.returncode, 0, result.stderr)
            short_summary = json.loads(result.stdout)
            self.assertEqual(short_summary["seed_hex"], tasks[0][0]["seed_hex"])
            self.assertNotEqual(short_summary["stream_identity"], tasks[0][0]["stream_identity"])
            self.assertEqual(pq.read_table(short["output_path"])["value_u64"].to_pylist(), EXPECTED_VALUES[:4])
            nine_dir = Path(first) / "nine"
            nine_dir.mkdir()
            nine = {**BASE, "draw_count": 9, "output_path": str(nine_dir / "rng.parquet")}
            result, _ = self.run_task(nine_dir, nine)
            self.assertEqual(result.returncode, 0, result.stderr)
            nine_summary = json.loads(result.stdout)
            self.assertEqual(nine_summary["seed_hex"], tasks[0][0]["seed_hex"])
            self.assertEqual(pq.read_table(nine["output_path"])["value_u64"].to_pylist()[:8], EXPECTED_VALUES)
            self.assertEqual(pq.read_table(nine["output_path"])["value_u64"].to_pylist()[8], 14340693636365067419)
            self.assertNotEqual(nine_summary["stream_identity"], tasks[0][0]["stream_identity"])

    def test_identity_field_mutations_and_atomic_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = {**BASE, "output_path": str(Path(directory) / "baseline.parquet")}
            result, _ = self.run_task(directory, baseline)
            self.assertEqual(result.returncode, 0, result.stderr)
            original = json.loads(result.stdout)
            for field in ("experiment_id", "stage_id", "task_id", "stream_name"):
                task = {**BASE, field: BASE[field] + "x", "output_path": str(Path(directory) / (field + ".parquet"))}
                result, _ = self.run_task(directory, task)
                self.assertEqual(result.returncode, 0, result.stderr)
                changed = json.loads(result.stdout)
                self.assertNotEqual(changed["seed_hex"], original["seed_hex"])
                self.assertNotEqual(changed["stream_identity"], original["stream_identity"])
                self.assertNotEqual(pq.read_table(task["output_path"])["value_u64"].to_pylist(), EXPECTED_VALUES)
            failures = [("empty", {**BASE, "stream_name": ""}), ("zero", {**BASE, "draw_count": 0}), ("unknown", {**BASE, "extra": "x"})]
            for name, task in failures:
                output = Path(directory) / (name + ".parquet")
                task["output_path"] = str(output)
                result, _ = self.run_task(directory, task)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertFalse(output.exists())
                self.assertNotIn("seed_hex", result.stderr)
                self.assertNotIn("stream_identity", result.stderr)

