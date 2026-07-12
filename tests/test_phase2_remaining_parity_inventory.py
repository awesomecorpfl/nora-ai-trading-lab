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
        self.assertEqual(value["evidence_package_completeness"], {
            "canary.condition_native": "legacy_committed_summary",
            "canary.sma_cross_native": "legacy_committed_summary",
            "canary.slope_native": "self_contained_raw_native",
        })
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

    def test_legacy_canaries_remain_accepted_with_less_complete_packages(self):
        items = {item["id"]: item for item in self.value["items"]}
        self.assertEqual(items["canary.condition_native"]["status"], "accepted")
        self.assertEqual(items["canary.condition_native"]["mql5"]["source_identity"], "583fe60539d2da2cb46f054d9800d7702efd577b6984d23757794ca91ab259e6")
        self.assertEqual(items["canary.condition_native"]["parity_result_identity"], "b66f60ad5ae4cc036d29197063e2dbe355cafac96085c359e92783ac74da74e4")
        self.assertEqual(items["canary.sma_cross_native"]["status"], "accepted")
        self.assertEqual(items["canary.sma_cross_native"]["mql5"]["source_identity"], "78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4")
        self.assertEqual(items["canary.sma_cross_native"]["parity_result_identity"], "ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687")
        self.assertEqual(items["canary.slope_native"]["status"], "accepted")

    def test_phase_2p_prerequisites_are_proven_and_not_already_parity_accepted(self):
        items = {item["id"]: item for item in self.value["items"]}
        for item_id in ("layer1.atr", "transform.distance_atr"):
            item = items[item_id]
            self.assertEqual(item["rust"]["implementation"], "implemented")
            self.assertIn("engine/labengine/src/indicators.rs", item["rust"]["source_paths"])
            self.assertEqual(item["mql5"]["generation"], "absent")
            self.assertFalse(item["native"]["execution_evidence_paths"])
        prerequisite = self.value["next_task"]["prerequisites"]
        fixture = "engine/labengine/tests/fixtures/phase2_distance_atr_task.json"
        self.assertIn(fixture, prerequisite["real_rust_fixture"])
        self.assertTrue((ROOT / fixture).exists())
        self.assertIn("c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad", prerequisite["real_rust_fixture"])

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
