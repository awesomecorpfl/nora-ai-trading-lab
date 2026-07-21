import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_vwap_local_evidence():
 x=json.loads((ROOT/'tests/fixtures/phase2_vwap_local_evidence.json').read_text());assert x['ok'] and len(x['rows'])==5
 assert [r['value'] for r in x['rows']]==[10.333333333333334,11.0,10.5,20.333333333333332,21.11111111111111]