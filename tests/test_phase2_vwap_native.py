import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'tests/fixtures/phase2_vwap_native'

def test_vwap_native_acceptance():
    m = json.loads((BASE / 'native_evidence.json').read_text())
    assert m['parity'] == 'exact'
    assert m['completion_count'] == 4
    assert m['failure_count'] == 0
    assert m['run_rows'] == {'VWAP-A1-1': 5, 'VWAP-A2-2': 5, 'VWAP-B1-3': 5, 'VWAP-B2-4': 5}
    for rid in m['run_ids']:
        p = BASE / 'runs' / rid / 'nora_phase2_vwap_v1.csv'
        rows = []
        with open(p, newline='', encoding='utf-8-sig') as f:
            r = csv.DictReader(f, delimiter='\t')
            rows = list(r)
        assert len(rows) == 5
    rust = json.loads((ROOT / 'tests/fixtures/phase2_vwap_local_evidence.json').read_text())['rows']
    for rid in m['run_ids']:
        p = BASE / 'runs' / rid / 'nora_phase2_vwap_v1.csv'
        rows = []
        with open(p, newline='', encoding='utf-8-sig') as f:
            r = csv.DictReader(f, delimiter='\t')
            rows = list(r)
        for a, b in zip(rows, rust):
            assert a['scenario_id'] == b['scenario_id']
            assert a['output'] == b['output']
            assert int(a['row']) == b['row']
            assert abs(float(a['value']) - float(b['value'])) < 1e-12