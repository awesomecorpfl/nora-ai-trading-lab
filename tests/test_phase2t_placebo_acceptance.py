"""Phase-2T placebo/scrambled-data integrity admission contract."""
from __future__ import annotations

import json
from pathlib import Path

from lab.phase2_placebo import build_placebo_fixture, verify_placebo_fixture

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "tests/fixtures/phase2_remaining_parity_inventory.json"
FIXTURE = ROOT / "tests/fixtures/phase2_placebo_edge_fixture.json"
ITEM_ID = "integrity.placebo_scrambled_edge"


def _item() -> dict:
    value = json.loads(INVENTORY.read_text())
    return next(item for item in value["items"] if item["id"] == ITEM_ID)


def test_placebo_fixture_is_admitted_in_authoritative_inventory():
    item = _item()
    fixture = json.loads(FIXTURE.read_text())

    assert item["status"] == "accepted"
    assert item["rust"]["implementation"] == "implemented"
    assert "lab/phase2_placebo.py" in item["rust"]["source_paths"]
    assert "tests/test_phase2t_placebo_acceptance.py" in item["rust"]["tests"]
    assert item["mql5"]["generation"] == "out_of_scope"
    assert item["native"]["execution_evidence_paths"] == []
    assert "tests/fixtures/phase2_placebo_edge_fixture.json" in item["evidence_paths"]
    assert item["parity_result_identity"] == fixture["fixture_identity"]
    assert item["searchable"] is False
    assert item["missing_gate"] == "complete Phase-2 admission gate"


def test_placebo_fixture_contract_and_destruction_are_verified_before_admission():
    fixture = json.loads(FIXTURE.read_text())
    assert fixture == build_placebo_fixture()
    assert verify_placebo_fixture(fixture)
    assert fixture["canary"]["edge_statistic"] > fixture["contract"]["destruction_threshold"]
    assert fixture["scrambled"]["edge_statistic"] < fixture["contract"]["destruction_threshold"]
    assert fixture["destruction"]["destroyed"] is True
