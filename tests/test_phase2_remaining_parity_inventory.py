"""Schema and admission checks for the frozen Phase-2 remaining-parity inventory."""
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "tests/fixtures/phase2_remaining_parity_inventory.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT = re.compile(r"^[0-9a-f]{40}$")
STATUSES = {"accepted", "partially_proven", "implemented_but_unproved", "absent", "deferred", "out_of_scope"}


class Phase2RemainingParityInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = INVENTORY_PATH.read_text(encoding="utf-8")
        cls.value = json.loads(cls.raw)

    def test_schema_and_deterministic_serialization(self):
        value = self.value
        self.assertEqual(value["schema_version"], 1)
        self.assertEqual(value["phase"], "2")
        self.assertFalse(value["search_authorized"])
        self.assertEqual(set(value["status_values"]), STATUSES)
        canonical_a = json.dumps(value, sort_keys=True, separators=(",", ":"))
        canonical_b = json.dumps(json.loads(canonical_a), sort_keys=True, separators=(",", ":"))
        self.assertEqual(canonical_a, canonical_b)
        self.assertEqual(hashlib.sha256(canonical_a.encode()).hexdigest(), hashlib.sha256(canonical_b.encode()).hexdigest())

    def test_items_are_unique_and_complete(self):
        required = {"id", "category", "name", "status", "rust", "mql5", "native", "parity_result_identity", "evidence_paths", "commits", "searchable", "missing_gate"}
        items = self.value["items"]
        self.assertEqual(len(items), 50)
        self.assertEqual(len({item["id"] for item in items}), len(items))
        for item in items:
            self.assertEqual(set(item), required)
            self.assertIn(item["status"], STATUSES)
            self.assertTrue(item["missing_gate"])
            self.assertEqual(set(item["rust"]), {"implementation", "source_paths", "identity", "tests"})
            self.assertEqual(set(item["mql5"]), {"generation", "source_identity"})
            self.assertEqual(set(item["native"]), {"compile_evidence_paths", "execution_evidence_paths"})

    def test_claimed_evidence_paths_and_identities_are_valid(self):
        for item in self.value["items"]:
            for path in [*item["evidence_paths"], *item["native"]["compile_evidence_paths"], *item["native"]["execution_evidence_paths"]]:
                self.assertFalse(Path(path).is_absolute())
                self.assertTrue((ROOT / path).exists(), f"missing evidence path {path}")
            for identity in (item["rust"]["identity"], item["mql5"]["source_identity"], item["parity_result_identity"]):
                if identity is not None:
                    self.assertRegex(identity, SHA256)
            for commit in item["commits"]:
                self.assertRegex(commit, GIT_OBJECT)

    def test_search_admission_and_phase_three_are_closed(self):
        self.assertFalse(self.value["search_authorized"])
        for item in self.value["items"]:
            if item["searchable"]:
                self.assertEqual(item["rust"]["implementation"], "implemented")
                self.assertEqual(item["mql5"]["generation"], "generated")
                self.assertTrue(item["native"]["execution_evidence_paths"])
                self.assertIsNotNone(item["parity_result_identity"])
            self.assertNotIn("phase3", item["id"].lower())
            self.assertNotIn("search", item["category"].lower())

    def test_acceptance_requirement_schema_and_next_task(self):
        requirements = self.value["acceptance_requirements"]
        self.assertEqual(len(requirements), 6)
        self.assertEqual({entry["status"] for entry in requirements}, {"partial", "blocked"})
        for entry in requirements:
            self.assertTrue(entry["blocks_phase2"])
            self.assertTrue(entry["smallest_next_task"])
        next_task = self.value["next_task"]
        self.assertEqual(next_task["phase_label"], "Phase 2P")
        self.assertEqual(next_task["execution_boundary"], "local-only")
        self.assertNotIn("search", next_task["scope"].lower())


if __name__ == "__main__":
    unittest.main()
