import copy
import tempfile
import unittest
from pathlib import Path

from lab.phase2_execution_batch import FAILURES, ROOT, build, classify_synthetic, load, preflight, preflight_batch, stage


class ExecutionBatch(unittest.TestCase):
    def test_generated_current_chain_is_the_only_accepted_chain(self):
        current = load()
        self.assertEqual(current, build())
        self.assertEqual(preflight_batch(current), "ok")
        self.assertEqual(preflight()["status"], "PASS")
        self.assertEqual(current["staged_inventory_definition"], "nora.phase2x.execution_roles_paths_v1")
        execution=current["execution"]
        self.assertTrue(execution["precompile_ready"])
        self.assertTrue(execution["compile_evidence_pending"])
        self.assertFalse(execution["compile_evidence_imported"])
        self.assertFalse(execution["final_packet_ready"])
        self.assertFalse(execution["native_execution_attempted"])
        self.assertFalse(execution["native_parity_accepted"])

    def test_old_mixed_and_stale_chains_fail_closed(self):
        for mutate in (
            lambda v: v["execution"].__setitem__("tester_identity", "c09086906c22972b384970cbd66fd6d78c757e74d618499ec1f4e8ece81cd188"),
            lambda v: v["execution"].__setitem__("package_identity", "00e87549f0d08843a2ab35c7d4342d498f293bac488d553b018104370ee25258"),
            lambda v: v.__setitem__("batch_identity", "44be335b8f517fbdfb4de7d9d4b5e1f42f80e0d7dd636659dfd1c4f2b98f458c"),
            lambda v: v["execution"]["files"][2].__setitem__("sha256", "0" * 64),
        ):
            value = copy.deepcopy(load())
            mutate(value)
            self.assertEqual(preflight_batch(value), "stale_or_mixed_identity_chain")

    def test_two_directory_staging_is_byte_identical(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            first, second = stage(root / "first"), stage(root / "second")
            self.assertEqual(first, second)
            files_a = sorted(p.relative_to(root / "first") for p in (root / "first").rglob("*") if p.is_file())
            files_b = sorted(p.relative_to(root / "second") for p in (root / "second").rglob("*") if p.is_file())
            self.assertEqual(files_a, files_b)
            for rel in files_a:
                self.assertEqual((root / "first" / rel).read_bytes(), (root / "second" / rel).read_bytes())

    def test_all_synthetic_failure_classes_are_sealed(self):
        self.assertEqual(classify_synthetic("unknown"), "exact_pass")
        for kind in FAILURES:
            self.assertEqual(classify_synthetic(kind), kind)
