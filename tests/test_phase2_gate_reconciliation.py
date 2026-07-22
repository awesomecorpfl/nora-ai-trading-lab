"""Stage-7 Phase-2 gate and identity-boundary regression tests."""
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "tests/fixtures/phase2_gate_reconciliation.json"
INVENTORY = ROOT / "tests/fixtures/phase2_remaining_parity_inventory.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Phase2GateReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text())
        cls.inventory = json.loads(INVENTORY.read_text())
        cls.items = {item["id"]: item for item in cls.inventory["items"]}

    def test_matrix_resolves_every_phase2_item_and_has_required_fields(self):
        self.assertEqual(len(self.matrix["records"]), 51)
        self.assertEqual(set(self.matrix["records"]), set(self.items))
        self.assertEqual(len(self.matrix["record_schema"]), 18)
        for identifier in self.matrix["records"]:
            item = self.items[identifier]
            self.assertIn(item["status"], self.inventory["status_values"])
            self.assertTrue(item["missing_gate"])
            self.assertIn("rust", item)
            self.assertIn("mql5", item)
            self.assertIn("native", item)

    def test_native_acceptance_does_not_admit_grammar_or_search(self):
        self.assertFalse(self.matrix["grammar_admitted"])
        self.assertFalse(self.matrix["searchable"])
        for identifier in ("layer1.macd", "transform.percentile", "canary.execution_model_native"):
            item = self.items[identifier]
            self.assertTrue(item["native"]["parity_accepted"])
            self.assertFalse(item.get("grammar_admitted", False))
            self.assertFalse(item["searchable"])
            self.assertTrue(self.matrix["accepted_native_nodes"][identifier]["native_parity_accepted"])
        trade = self.matrix["accepted_native_nodes"]["strategy.trade_by_trade_reconciliation"]
        self.assertTrue(trade["native_parity_accepted"])
        self.assertFalse(trade["grammar_admitted"])
        self.assertFalse(trade["searchable"])
        self.assertEqual(
            trade["acceptance_evidence"],
            "tests/fixtures/phase2_ten_strategy_suite/trade_reconciliation_manifest.json",
        )
        budget = self.matrix["accepted_native_nodes"]["strategy.provisional_parity_budget"]
        self.assertTrue(budget["native_parity_accepted"])
        self.assertFalse(budget["grammar_admitted"])
        self.assertFalse(budget["searchable"])
        self.assertEqual(
            budget["acceptance_evidence"],
            "tests/fixtures/phase2_ten_strategy_suite/strategy_provisional_parity_budget.json",
        )

    def test_phase2_completion_closes_only_the_six_frozen_criteria(self):
        trade = self.matrix["accepted_native_nodes"]["strategy.trade_by_trade_reconciliation"]
        self.assertIn("embedded ten-strategy suite only", trade["semantic_restriction"])
        self.assertIn("not finalist edge proof", trade["semantic_restriction"])
        self.assertEqual(self.matrix["binding_requirements"]["strategy.trade_by_trade_reconciliation"], "ACCEPTED")
        self.assertEqual(self.matrix["binding_requirements"]["strategy.provisional_parity_budget"], "ACCEPTED")
        self.assertEqual(self.matrix["binding_requirements"]["strategy.finalist_edge_survival"], "DEFERRED")
        self.assertEqual(self.matrix["next_critical_path"], "phase7.finalist_validation")
        self.assertTrue(self.matrix["complete_phase2_gate"])
        self.assertEqual(set(self.matrix["phase2_completion_basis"]), {
            "synthetic_execution_fixtures",
            "layer1_parity",
            "time_rule_parity",
            "hand_designed_strategy_trade_reconciliation",
            "repeated_linux_execution",
            "placebo_scrambled_edge_destruction",
        })
        self.assertEqual(self.matrix["deferred_later_phase_gates"]["strategy.finalist_edge_survival"]["phase"], "7")

    def test_complete_gate_is_true_with_later_phase_requirements_deferred(self):
        self.assertTrue(self.matrix["complete_phase2_gate"])
        self.assertEqual(self.inventory["inventory_summary"]["phase2_acceptance_gate"], "accepted")
        self.assertEqual(self.matrix["binding_requirements"]["indicators.remaining_layer1_targets"], "DEFERRED")

    def test_superseded_identities_are_never_current(self):
        history = self.matrix["identity_history"]
        pct = history["percentile_executable_sources"]
        self.assertNotEqual(pct["stale_package"], pct["current_package"])
        self.assertNotEqual(pct["historical_scaffold_runtime"], pct["current_runtime"])
        self.assertNotEqual(pct["historical_scaffold_tester"], pct["current_tester"])
        self.assertTrue(HEX64.fullmatch(pct["current_package"]))
        self.assertTrue(HEX64.fullmatch(history["batches"]["current"]))

    def test_accepted_contracts_are_exact_and_phase_boundaries_closed(self):
        macd = self.matrix["accepted_native_nodes"]["layer1.macd"]["semantic_restriction"]
        pct = self.matrix["accepted_native_nodes"]["transform.percentile"]["semantic_restriction"]
        for text in (macd, pct):
            self.assertIn("CSV V3", text)
            self.assertIn("GDAXI/M1", text)
            self.assertIn("AUDCAD/M1", text)
        self.assertIn("EMA fast 2", macd)
        self.assertIn("lookback 4", pct)
        self.assertEqual(self.matrix["closed_boundaries"], ["search", "phase_3", "new_grammar_admission", "searchability_enablement", "deployment"])

    def test_binding_status_vocabulary_is_exact(self):
        self.assertEqual(set(self.matrix["binding_requirements"].values()), {"ACCEPTED", "DEFERRED"})
        self.assertEqual(set(self.matrix["status_values"]), {"ACCEPTED", "PARTIAL", "IMPLEMENTED_UNPROVED", "ABSENT", "DEFERRED", "BLOCKED"})


if __name__ == "__main__":
    unittest.main()
