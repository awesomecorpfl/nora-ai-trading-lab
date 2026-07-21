import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ENGINE=ROOT/'engine/target/debug/labengine';FIXTURE=ROOT/'tests/fixtures/phase2_kama_scenarios.json'
def test_kama_rust_contract():
 task={'task_version':1,'task_type':'layer1_parity_v1','scenarios':json.loads(FIXTURE.read_text())['scenarios']}
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'task.json';p.write_text(json.dumps(task));r=subprocess.run([str(ENGINE),str(p)],capture_output=True,text=True)
 assert r.returncode==0,r.stderr;rows=json.loads(r.stdout)['rows'];assert len(rows)==15
 trend=[x for x in rows if x['scenario_id']=='adaptive_trend'];assert all(x['value'] is None for x in trend[:3]);assert all(x['classification']=='steady_state' for x in trend[3:])
 flat=[x for x in rows if x['scenario_id']=='flat_series'];assert all(abs(x['value']-7.0)<1e-12 for x in flat if x['classification']=='steady_state');assert any(x['reason_code']=='invalid_period' for x in rows)
def test_kama_package_deterministic_and_closed():
 from lab.mql5gen.kama_batch import generate
 e=json.loads((ROOT/'tests/fixtures/phase2_kama_local_evidence/rust_evidence.json').read_text())
 with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:x=generate(Path(a),e);y=generate(Path(b),e)
 assert x==y;assert x['package_identity']=='fb71c6dc42804640aad5f5956520682d3dd6cde29ade2aa7b4f532e9efdde008';assert x['native_execution_attempted'] is False and x['native_parity_accepted'] is False;assert x['grammar_admitted'] is False and x['searchable'] is False;assert json.loads((ROOT/'tests/fixtures/phase2_kama_native/phase2_kama_executable_package.json').read_text())==x
