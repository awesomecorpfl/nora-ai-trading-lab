import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'tests/fixtures/phase2_keltner_native'
def test_keltner_native_acceptance():
 m=json.loads((BASE/'native_evidence_manifest.json').read_text());assert m['compile']['error_count']==0 and m['compile']['warning_count']==0 and len(m['contexts'])==4 and m['journal_completion_marker_count']==4 and m['cross_context_csv_identity'] and m['rust_native_reconciliation']=='exact'
 exp=json.loads((ROOT/'tests/fixtures/phase2_keltner_local_evidence.json').read_text())['output']['rows'];em={(x['scenario_id'],x['output'],x['row']):x for x in exp}
 for c in m['contexts']:
  rows=list(csv.DictReader((BASE/'runs'/c['run_id']/'nora_phase2_keltner_v1.csv').open(encoding='utf-8-sig'),delimiter='\t'));assert len(rows)==19
  for x in rows:
   e=em[(x['scenario_id'],x['output'],None if x['row']=='NULL' else int(x['row']))];nv=None if x['value']=='NULL' else float(x['value']);assert (nv is None)==(e['value'] is None) and (nv is None or abs(nv-e['value'])<1e-12)
