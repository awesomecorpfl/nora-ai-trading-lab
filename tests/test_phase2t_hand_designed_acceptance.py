"""Phase-2T hand-designed ten-strategy acceptance boundary."""
from __future__ import annotations

import json
from pathlib import Path

from lab.phase2_ten_strategy import strategy_suite

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "tests/fixtures/phase2_remaining_parity_inventory.json"
CORRECTED_FINAL = ROOT / "tests/fixtures/phase2_ten_strategy_suite/native_corrected_final"
ITEM_ID = "strategy.hand_designed_suite_10"


def _item() -> dict:
    value = json.loads(INVENTORY.read_text())
    return next(item for item in value["items"] if item["id"] == ITEM_ID)


def test_hand_designed_suite_has_frozen_ten_case_contract_before_native_gate():
    suite = strategy_suite()
    assert suite["schema_version"] == "nora.phase2_ten_strategy_suite_v1"
    assert len(suite["strategies"]) == 10
    assert sum(case["family"] == "trend-pullback" for case in suite["strategies"]) == 5
    assert sum(case["family"] == "close-confirmed breakout" for case in suite["strategies"]) == 5
    assert suite["searchable"] is False


def test_hand_designed_suite_requires_formal_durable_native_acceptance():
    item = _item()
    final_batch = json.loads((CORRECTED_FINAL / "final_batch.json").read_text())

    assert item["status"] == "accepted"
    assert item["rust"]["implementation"] == "implemented"
    assert "lab/phase2_ten_strategy.py" in item["rust"]["source_paths"]
    assert "tests/test_phase2t_hand_designed_acceptance.py" in item["rust"]["tests"]
    assert item["parity_result_identity"] is not None
    assert item["native"]["execution_evidence_paths"]
    assert final_batch["complete_phase2_gate"] is True
    assert item["searchable"] is False
