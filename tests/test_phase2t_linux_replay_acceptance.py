"""Phase-2T complete Linux replay admission contract."""
from __future__ import annotations

import json
from pathlib import Path

from lab.phase2_linux_replay import run_linux_replay, verify_linux_replay

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "tests/fixtures/phase2_remaining_parity_inventory.json"
FIXTURE = ROOT / "tests/fixtures/phase2_linux_replay_fixture.json"
ITEM_ID = "determinism.linux_replay"


def _item() -> dict:
    value = json.loads(INVENTORY.read_text())
    return next(item for item in value["items"] if item["id"] == ITEM_ID)


def test_complete_linux_replay_is_admitted_in_authoritative_inventory():
    item = _item()
    fixture = json.loads(FIXTURE.read_text())

    assert item["status"] == "accepted"
    assert item["rust"]["implementation"] == "implemented"
    assert "lab/phase2_linux_replay.py" in item["rust"]["source_paths"]
    assert "tests/test_phase2_linux_replay.py" in item["rust"]["tests"]
    assert "tests/test_phase2t_linux_replay_acceptance.py" in item["rust"]["tests"]
    assert item["mql5"]["generation"] == "out_of_scope"
    assert item["native"]["compile_evidence_paths"] == []
    assert item["native"]["execution_evidence_paths"] == []
    assert "tests/fixtures/phase2_linux_replay_fixture.json" in item["evidence_paths"]
    assert item["parity_result_identity"] == fixture["replay_identity"]
    assert item["searchable"] is False
    assert item["missing_gate"] == "complete Phase-2 admission gate"


def test_committed_replay_fixture_is_complete_and_identity_verified_before_admission():
    fixture = json.loads(FIXTURE.read_text())
    assert fixture == run_linux_replay()
    assert verify_linux_replay(fixture)
    assert fixture["classification"] == "PASS_LINUX_EXPERIMENT_REPLAY"
    assert set(fixture["stages"]) == {
        "ingestion",
        "aggregation",
        "indicators",
        "ast_intents",
        "simulation",
        "metrics",
    }
    assert fixture["trades"]["trade_count"] >= 1
