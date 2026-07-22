import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'tests/fixtures/phase2_session_ohlc_native'
def test_session_ohlc_native_acceptance():
 m=json.loads((BASE/'native_evidence.json').read_text());assert m['parity']=='exact';assert m['completion_count']==4;assert m['failure_count']==0;assert m['run_rows']=={'SESSION-A1-1':20,'SESSION-A2-2':20,'SESSION-B1-3':20,'SESSION-B2-4':20}
 for rid in m['run_ids']:
  c=csv.reader((BASE/'runs'/rid/'nora_phase2_session_ohlc_v1.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter='\t');h=next(c);assert h[0]=='scenario_id' and h[3]=='row'
  rows=list(c);assert len(rows)==20
 rust=json.loads((ROOT/'tests/fixtures/phase2_session_ohlc_local_evidence.json').read_text())['rows']
 rv={(r['node'],r['output'],r['row']):r['value'] for r in rust}
 for rid in m['run_ids']:
  c=csv.reader((BASE/'runs'/rid/'nora_phase2_session_ohlc_v1.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter='\t');next(c)
  for r in c:
   val=float(r[5]) if r[4]!='NULL' else None
   assert rv[(r[1],r[2],int(r[3]))]==val