import copy
import json
from pathlib import Path
import pytest
from lab.numeric_parity import *
from lab.phase2_placebo import build_placebo_fixture, verify_placebo_fixture

def test_protocol_and_failure_identities_are_frozen_and_budget_mutates_identity():
 p=protocol();assert p['parity_protocol_identity']==protocol()['parity_protocol_identity'];assert set(EXACT_FIELDS)==set(p['exact_fields'])
 assert set(failure_vocabulary()['codes'])==set(FAILURES)
 a={'EMA':{'value':{'absolute':1e-12,'relative':0.0,'ulp':10000}}};b=copy.deepcopy(a);b['EMA']['value']['absolute']=2e-12
 assert budget_identity(a)!=budget_identity(b)

def test_measurement_records_exact_errors_percentiles_ulp_and_phase():
 exact=measure([1.0,2.0],[1.0,2.0],['warmup','steady_state']);assert exact['exact'] and exact['first_divergence'] is None
 changed=measure([1.0,2.0],[1.0,2.0+1e-13],['warmup','steady_state']);assert not changed['exact'] and changed['first_divergence']['row']==1
 assert changed['maximum_error']['absolute']>0 and changed['points'][1]['ulp_distance']>0
 assert within_budget(changed,{'absolute':1e-12,'relative':0.0,'ulp':10000})
 assert not within_budget(changed,{'absolute':1e-14,'relative':0.0,'ulp':1})
 with pytest.raises(ValueError,match='ROW_COUNT'):measure([1.0],[1.0,2.0],['steady_state'])


def test_placebo_fixture_captures_and_destroys_the_planted_edge():
    fixture = build_placebo_fixture()
    assert verify_placebo_fixture(fixture)
    assert fixture["canary"]["edge_statistic"] > fixture["contract"]["destruction_threshold"]
    assert fixture["scrambled"]["edge_statistic"] < fixture["contract"]["destruction_threshold"]
    assert fixture["destruction"]["destroyed"] is True


def test_placebo_fixture_matches_committed_canonical_bytes():
    path = Path(__file__).resolve().parents[1] / "tests/fixtures/phase2_placebo_edge_fixture.json"
    committed = json.loads(path.read_text())
    assert committed == build_placebo_fixture()
    assert verify_placebo_fixture(committed)


def test_placebo_verifier_rejects_contract_mutation():
    fixture = build_placebo_fixture()
    fixture["contract"]["scramble_seed"] += 1
    with pytest.raises(ValueError, match="contract mismatch"):
        verify_placebo_fixture(fixture)
