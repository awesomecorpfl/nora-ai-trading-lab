import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ENGINE=ROOT/'engine/target/debug/labengine';FIXTURE=ROOT/'tests/fixtures/phase2_linear_regression_scenarios.json'
def test_linear_regression_rust_contract():
 task={'task_version':1,'task_type':'layer1_parity_v1','scenarios':json.loads(FIXTURE.read_text())['scenarios']}
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'task.json';p.write_text(json.dumps(task));r=subprocess.run([str(ENGINE),str(p)],capture_output=True,text=True)
 assert r.returncode==0,r.stderr;rows=json.loads(r.stdout)['rows'];assert len(rows)==19
 value=[x for x in rows if x['scenario_id']=='rising_line' and x['output']=='value'];slope=[x for x in rows if x['scenario_id']=='rising_line' and x['output']=='slope'];assert all(x['value'] is None for x in value[:2]);assert all(abs(x['value']-(2+2*x['row']))<1e-12 for x in value[2:]);assert all(abs(x['value']-2.0)<1e-12 for x in slope[2:]);assert any(x['reason_code']=='invalid_period' for x in rows)
def test_linear_regression_package_deterministic_and_closed():
 from lab.mql5gen.linear_regression_batch import generate
 e=json.loads((ROOT/'tests/fixtures/phase2_linear_regression_local_evidence/rust_evidence.json').read_text())
 with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:x=generate(Path(a),e);y=generate(Path(b),e)
 assert x==y;assert x['package_identity']=='54f4218f2e6bbdccb42a8c6a6d6faa6ff7b46a53724b59f9ee8b9e797248f1c9';assert x['native_execution_attempted'] is False and x['native_parity_accepted'] is False;assert x['grammar_admitted'] is False and x['searchable'] is False;assert json.loads((ROOT/'tests/fixtures/phase2_linear_regression_native/phase2_linear_regression_executable_package.json').read_text())==x
