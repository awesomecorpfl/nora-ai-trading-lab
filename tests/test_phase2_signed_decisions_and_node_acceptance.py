"""Independent validation of the signed D1-D7 packet and seven-node binding."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "docs/evidence/phase2/frt3-gate-closure/phase2_gate_decisions_v1.json"
NODES = ROOT / "docs/evidence/phase2/frt3-gate-closure/phase2_initial_v1_ast_condition_acceptance_v1.json"
INVENTORY = ROOT / "tests/fixtures/phase2_remaining_parity_inventory.json"
MATRIX = ROOT / "tests/fixtures/phase2_gate_reconciliation.json"


def test_signed_decisions_are_explicit_and_d8_is_unsigned():
    value = json.loads(DECISIONS.read_text())
    assert value["operator"] == "Gasper"
    assert value["repository"]["bound_head"] == "86d1fde"
    assert value["signed_decision_count"] == 7
    assert [d["id"] for d in value["decisions"]] == ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]
    assert all(d["signed"] for d in value["decisions"])
    assert value["d8"] == {"signed": False, "phase3_authorized": False, "note": value["d8"]["note"]}
    assert value["search_authorized"] is False
    assert value["grammar_admitted"] is False
    assert value["phase3_authorized"] is False
    for identity in value["decision_identities"].values():
        assert len(identity) == 64
        int(identity, 16)


def test_node_acceptance_binds_all_required_layers_and_contexts():
    value = json.loads(NODES.read_text())
    expected = {"ast.and", "ast.boolean_series", "ast.compare", "ast.not", "ast.number", "ast.numeric_series", "ast.or"}
    assert set(value["node_bindings"]) == expected
    assert value["native_contexts"] == ["A1 GDAXI/M1", "A2 GDAXI/M1", "B1 AUDCAD/M1", "B2 AUDCAD/M1"]
    assert value["native_acceptance"]["compile_errors"] == 0
    assert value["native_acceptance"]["compile_warnings"] == 0
    assert value["native_acceptance"]["condition_semantic_identity_stable"] is True
    assert value["native_acceptance"]["runtime_csv_identity_stable"] is True
    assert all(all(binding.values()) for binding in value["node_bindings"].values())
    assert value["grammar_admitted"] is False
    assert value["searchable"] is False


def test_inventory_and_gate_are_closed_by_evidence_not_by_deletion():
    inventory = json.loads(INVENTORY.read_text())
    matrix = json.loads(MATRIX.read_text())
    nodes = {item["id"]: item for item in inventory["items"]}
    required = {"ast.and", "ast.boolean_series", "ast.compare", "ast.not", "ast.number", "ast.numeric_series", "ast.or"}
    assert all(nodes[node]["status"] == "accepted" for node in required)
    assert all(nodes[node]["missing_gate"].startswith("none for bounded initial-v1") for node in required)
    assert inventory["inventory_summary"]["status_counts"]["partially_proven"] == 0
    assert inventory["inventory_summary"]["phase2_acceptance_gate"] == "accepted"
    assert matrix["complete_phase2_gate"] is True
    assert matrix["binding_requirements"]["strategy.finalist_edge_survival"] == "DEFERRED"
    assert matrix["phase3_authorized"] is False
