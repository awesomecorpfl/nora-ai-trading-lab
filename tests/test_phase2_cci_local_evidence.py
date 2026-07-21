import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_cci_local_evidence_contract():
    fixture=json.loads((ROOT/'tests/fixtures/phase2_cci_scenarios.json').read_text())
    evidence=json.loads((ROOT/'tests/fixtures/phase2_cci_local_evidence/rust_evidence.json').read_text())
    rows=evidence['rust_output']['rows']
    assert len(rows)==11
    assert [r for r in rows if r['reason_code']=='invalid_period'][0]['null'] is True
    linear=[r for r in rows if r['scenario_id']=='linear_typical_price']
    assert all(r['null'] for r in linear[:2])
    assert all(r['value']==0.0 for r in rows if r['scenario_id']=='flat_market' and not r['null'])
    assert fixture['contract']['zero_deviation']=='0.0'
    assert evidence['rust_evidence_identity']
    assert evidence['expected_vector_identity']
