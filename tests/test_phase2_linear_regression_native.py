import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'tests/fixtures/phase2_linear_regression_native'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def test_linear_regression_native_evidence_is_complete_and_exact():
 m=json.loads((BASE/'native_evidence_manifest.json').read_text());exp=json.loads((ROOT/'tests/fixtures/phase2_linear_regression_local_evidence/rust_evidence.json').read_text())['rust_output']['rows'];hashes=[]
 assert m['acceptance']=='PASS_EXACT' and m['native_parity_accepted'] is True;assert m['compiled']['errors']==0 and m['compiled']['warnings']==0;assert h(BASE/m['compiled']['ex5_path'])==m['compiled']['ex5_sha256'];assert h(BASE/'compile/linear-regression-compile.log')==m['compiled']['compile_log_sha256']
 for c in m['contexts'].values():
  d=BASE/'runs'/c['run_id'];ex=json.loads((d/'execution.json').read_text(encoding='utf-8-sig'));rows=list(csv.DictReader((d/'nora_phase2_linear_regression_v1.csv').open(encoding='utf-8-sig'),delimiter='\t'));assert ex['status']=='completed' and ex['native_process_exit_status']==0 and ex['completion_marker_present'] is True and ex['failure_marker_present'] is False;assert len(rows)==len(exp)==19;assert h(d/'execution.json')==c['execution_sha256'];assert h(d/'tester.ini.normalized')==c['tester_ini_normalized_sha256'];assert h(d/'nora_phase2_linear_regression_v1.csv')==c['csv_sha256'];hashes.append(c['csv_sha256'])
  for g,w in zip(rows,exp):
   assert g['scenario_id']==w['scenario_id'] and g['output']==w['output'] and g['row']==('NULL' if w['row'] is None else str(w['row'])) and g['timestamp']==('NULL' if w['timestamp'] is None else w['timestamp']) and g['null']==str(w['null']).lower()
   if w['value'] is None:assert g['value']=='NULL'
   else:assert abs(float(g['value'])-w['value'])<=1e-12
 assert len(set(hashes))==1 and m['cross_context_csv_sha256_equal'] is True
