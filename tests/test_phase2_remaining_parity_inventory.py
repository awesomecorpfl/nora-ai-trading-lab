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
            "canary.atr_distance_native": "self_contained_raw_native",
            "canary.execution_model_native": "self_contained_raw_native_returned_contract_v2",
        })
        canonical_a = json.dumps(value, sort_keys=True, separators=(",", ":"))
        canonical_b = json.dumps(json.loads(canonical_a), sort_keys=True, separators=(",", ":"))
        self.assertEqual(canonical_a, canonical_b)
        self.assertEqual(hashlib.sha256(canonical_a.encode()).hexdigest(), hashlib.sha256(canonical_b.encode()).hexdigest())

    def test_items_are_unique_and_complete(self):
        required = {"id", "category", "name", "status", "rust", "mql5", "native", "parity_result_identity", "evidence_paths", "commits", "searchable", "missing_gate"}
        items = self.value["items"]
        self.assertEqual(len(items), 51)
        self.assertEqual(len({item["id"] for item in items}), len(items))
        for item in items:
            self.assertTrue(set(item) in (required, required | {"grammar_admitted"}))
            self.assertIn(item["status"], STATUSES)
            self.assertTrue(item["missing_gate"])
            self.assertEqual(set(item["rust"]), {"implementation", "source_paths", "identity", "tests"})
            self.assertTrue({"generation", "source_identity"}.issubset(item["mql5"]))
            self.assertTrue({"compile_evidence_paths", "execution_evidence_paths"}.issubset(item["native"]))

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

    def test_atr_distance_native_acceptance_is_self_contained(self):
        items = {item["id"]: item for item in self.value["items"]}
        for item_id, rust_identity, runtime_identity in (
            ("layer1.atr", "26363cfb22ba13fdd5f922173373d56f6aff5b57c3e66604dbec28908b68708d", "80445d259d9ac9bcf3a15bf6ec12a160594237ee469b2ee53c46d22f99370194"),
            ("transform.distance_atr", "f4964fe1ecba67ab79654e59069ca5110e8330956b02b381517cf37bccf17f1f", "008c2f3a1824a8a22b03c6b447e3ae1a06cdd6c852381d96c8ca7eefba730c12"),
        ):
            item = items[item_id]
            self.assertEqual(item["status"], "accepted")
            self.assertEqual(item["rust"]["identity"], rust_identity)
            self.assertEqual(item["mql5"]["source_identity"], runtime_identity)
            self.assertEqual(item["parity_result_identity"], "8a912bd9152d16c8e94b1a96210d2cc6917c5b2639f615b0ecd4931dac2669f2")
            self.assertEqual(item["grammar_admitted"], True)
            self.assertEqual(len(item["native"]["compile_evidence_paths"]), 2)
            self.assertGreaterEqual(len(item["native"]["execution_evidence_paths"]), 10)
            self.assertEqual(item["commits"], ["a73ed6912c8dc354c36a7475dfe595d622e66d01", "021ac6d45e0624dd379be79a099022d22c12abd9", "fc363988af9ee7b80f9ad4f071868a922628ccd6"])

    def test_grammar_admission_requires_all_fields(self):
        rule = self.value["grammar_admission_rule"]
        self.assertEqual(set(rule["required_fields"]), {"typed_ast_schema_node_registration", "rust_evaluation_path", "canonicalization_support", "hashing_support", "mql5_translation", "native_parity_fixture"})
        self.assertFalse(rule["search_authorized"])
        self.assertFalse(rule["phase3_authorized"])
        admitted = [item["id"] for item in self.value["items"] if item.get("grammar_admitted")]
        self.assertEqual(admitted, ["layer1.atr", "transform.distance_atr"])

    def test_legacy_canaries_remain_accepted_with_less_complete_packages(self):
        items = {item["id"]: item for item in self.value["items"]}
        self.assertEqual(items["canary.condition_native"]["status"], "accepted")
        self.assertEqual(items["canary.condition_native"]["mql5"]["source_identity"], "583fe60539d2da2cb46f054d9800d7702efd577b6984d23757794ca91ab259e6")
        self.assertEqual(items["canary.condition_native"]["parity_result_identity"], "b66f60ad5ae4cc036d29197063e2dbe355cafac96085c359e92783ac74da74e4")
        self.assertEqual(items["canary.sma_cross_native"]["status"], "accepted")
        self.assertEqual(items["canary.sma_cross_native"]["mql5"]["source_identity"], "78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4")
        self.assertEqual(items["canary.sma_cross_native"]["parity_result_identity"], "ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687")
        self.assertEqual(items["canary.slope_native"]["status"], "accepted")

    def test_phase_2q_acceptance_and_next_task_prerequisites(self):
        items = {item["id"]: item for item in self.value["items"]}
        for item_id in ("layer1.atr", "transform.distance_atr"):
            item = items[item_id]
            self.assertEqual(item["rust"]["implementation"], "implemented")
            self.assertIn("engine/labengine/src/indicators.rs", item["rust"]["source_paths"])
            self.assertEqual(item["mql5"]["generation"], "generated")
            self.assertTrue(item["native"]["execution_evidence_paths"])
        next_task = self.value["next_task"]
        self.assertEqual(next_task["task_id"], "time_broker_clock_native_fixtures")
        self.assertNotIn(next_task["task_id"], items)
        self.assertNotIn(next_task["phase_label"].lower(), {item["status"] for item in items.values()})
        self.assertFalse(next_task["search_authorized"])
        self.assertFalse(next_task["phase3_authorized"])

    def test_acceptance_requirement_schema_and_next_task(self):
        requirements = self.value["acceptance_requirements"]
        self.assertEqual(len(requirements), 6)
        self.assertEqual({entry["status"] for entry in requirements}, {"accepted", "partial", "blocked"})
        for entry in requirements:
            self.assertEqual(entry["blocks_phase2"], entry["status"] != "accepted")
            self.assertTrue(entry["smallest_next_task"])
        next_task = self.value["next_task"]
        self.assertEqual(next_task["phase_label"], "Phase 2")
        self.assertEqual(next_task["execution_boundary"], "native canary preparation and validation")
        self.assertIn("search", next_task["scope"].lower())
        self.assertIn("clock", next_task["why_next"])

    def test_inventory_summary_matches_items(self):
        from collections import Counter
        counts = Counter({status: 0 for status in STATUSES})
        counts.update(item["status"] for item in self.value["items"])
        summary = self.value["inventory_summary"]
        self.assertEqual(summary["item_count"], len(self.value["items"]))
        self.assertEqual(summary["status_counts"], dict(counts))
        self.assertEqual(summary["accepted_native_canary_count"], 5)
        self.assertEqual(summary["grammar_admitted_node_count"], 2)
        self.assertEqual(summary["phase2_acceptance_gate"], "blocked")

    def test_accepted_macd_and_percentile_remain_narrow_and_non_searchable(self):
        items = {item["id"]: item for item in self.value["items"]}
        for item_id in ("layer1.macd", "transform.percentile"):
            item = items[item_id]
            self.assertEqual(item["status"], "accepted")
            self.assertEqual(item["mql5"]["generation"], "generated")
            self.assertTrue(item["mql5"]["executable_translation_generated"])
            self.assertEqual(set(item["mql5"]["historical_scaffold_identities"]), {"runtime", "tester", "package"})
            self.assertTrue(item["native"]["handoff_ready"])
            self.assertTrue(item["native"]["execution_attempted"])
            self.assertTrue(item["native"]["parity_accepted"])
            self.assertFalse(item.get("grammar_admitted", False))
            self.assertFalse(item["searchable"])


if __name__ == "__main__":
    unittest.main()
