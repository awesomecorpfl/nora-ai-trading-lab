import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_session_ohlc_local_evidence():
 x=json.loads((ROOT/'tests/fixtures/phase2_session_ohlc_local_evidence.json').read_text());assert x['ok'] and len(x['rows'])==20
 assert [r['value'] for r in x['rows'] if r['output']=='open']==[10,10,10,20,20]
 assert [r['value'] for r in x['rows'] if r['output']=='high']==[12,14,14,22,25]
 assert [r['value'] for r in x['rows'] if r['output']=='low']==[8,8,7,18,18]
 assert [r['value'] for r in x['rows'] if r['output']=='close']==[11,13,10,21,24]
