import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_bollinger_local_evidence():
 f=json.loads((ROOT/'tests/fixtures/phase2_bollinger_scenarios.json').read_text());e=json.loads((ROOT/'tests/fixtures/phase2_bollinger_local_evidence/rust_evidence.json').read_text());o=e['output'];assert f['schema_version']=='nora.phase2_bollinger_scenarios_v1';assert o['ok'] and len(o['rows'])==23;assert any(r['reason_code']=='invalid_period' for r in o['rows']);assert any(r['output']=='width' and r['value']==0.0 for r in o['rows'] if r['value'] is not None)
