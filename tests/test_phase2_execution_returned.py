import copy
import json
import tempfile
from pathlib import Path

import pytest

from lab.phase2_execution_returned import ingest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "tests/fixtures/phase2_execution_native_accepted"


@pytest.mark.skipif(not NATIVE.exists(), reason="native returned packages are external until acceptance import")
def test_native_returned_packages_are_independent_exact_and_host_neutral():
    final = ROOT / "tests/fixtures/phase2_execution_native_final_v4"
    packet = json.loads((final / "execution_packet.json").read_text())
    batch = json.loads((final / "final_batch.json").read_text())
    evidence = json.loads((ROOT / "tests/fixtures/phase2_execution_rust_evidence.json").read_text())
    cases = [("A1", "GDAXI"), ("A2", "GDAXI"), ("B1", "AUDCAD"), ("B2", "AUDCAD")]
    results = [ingest(NATIVE / case.lower(), packet, batch, evidence,
                      f"exec-0c13771-{case}", symbol) for case, symbol in cases]
    assert {x["classification"] for x in results} == {"PASS_EXACT"}
    assert len({x["returned_package_identity"] for x in results}) == 4
    assert len({x["returned_inventory_identity"] for x in results}) == 4
    assert len({x["execution_record_identity"] for x in results}) == 4
    assert len({x["journal_segment_identity"] for x in results}) == 4
    assert len({x["semantic_ledger_identity"] for x in results}) == 1


@pytest.mark.skipif(not NATIVE.exists(), reason="native returned packages are external until acceptance import")
def test_native_ingestion_fails_closed_on_decision_and_inventory_mutation():
    final = ROOT / "tests/fixtures/phase2_execution_native_final_v4"
    packet = json.loads((final / "execution_packet.json").read_text())
    batch = json.loads((final / "final_batch.json").read_text())
    evidence = json.loads((ROOT / "tests/fixtures/phase2_execution_rust_evidence.json").read_text())
    with tempfile.TemporaryDirectory() as temporary:
        source = NATIVE / "a1"; target = Path(temporary) / "package"
        import shutil; shutil.copytree(source, target)
        (target / "nora_phase2_execution_tester_v1.csv").write_text("corrupt\n")
        with pytest.raises(ValueError): ingest(target, packet, batch, evidence, "exec-0c13771-A1", "GDAXI")


def test_execution_acceptance_does_not_open_grammar_search_or_phase2_gate():
    acceptance = json.loads((NATIVE / "native_acceptance.json").read_text())
    assert acceptance["native_execution_attempted"] is True
    assert acceptance["native_result_returned"] is True
    assert acceptance["native_reconciliation_passed"] is True
    assert acceptance["native_parity_evidence_available"] is True
    assert acceptance["native_parity_accepted"] is True
    assert acceptance["grammar_admitted"] is False
    assert acceptance["searchable"] is False
    assert acceptance["complete_phase2_gate"] is False
