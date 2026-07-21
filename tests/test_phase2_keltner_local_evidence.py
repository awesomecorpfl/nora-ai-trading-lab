import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_keltner_local_evidence():
 e=json.loads((ROOT/'tests/fixtures/phase2_keltner_local_evidence.json').read_text());assert e['output']['ok'];assert len(e['output']['rows'])==19;assert any(x['reason_code']=='invalid_period' for x in e['output']['rows'])
