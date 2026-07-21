import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/'engine/target/debug/labengine'
FIXTURE=ROOT/'tests/fixtures/phase2_er_scenarios.json'

def test_er_rust_rows_and_boundary_contract():
    task={"task_version":1,"task_type":"layer1_parity_v1","scenarios":json.loads(FIXTURE.read_text())["scenarios"]}
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'task.json';p.write_text(json.dumps(task));r=subprocess.run([str(ENGINE),str(p)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    rows=json.loads(r.stdout)["rows"]
    assert len(rows)==18
    trend=[x for x in rows if x['scenario_id']=='steady_trend'];assert all(x['value'] is None for x in trend[:3]);assert all(abs(x['value']-1.5)<1e-12 for x in trend[3:])
    zero=[x for x in rows if x['scenario_id']=='zero_volatility'];assert all(x['value']==0.0 for x in zero if x['classification']=='steady_state')
    assert any(x['reason_code']=='invalid_period' for x in rows)

def test_er_package_is_deterministic_and_closed():
    from lab.mql5gen.er_batch import generate
    e=json.loads((ROOT/'tests/fixtures/phase2_er_local_evidence/rust_evidence.json').read_text())
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        x=generate(Path(a),e);y=generate(Path(b),e)
    assert x==y
    assert x['package_identity']=='a67a1901cca6af3f06c763f25f187ce3a1cfe993aebca434791552e8ef530b4a'
    assert x['native_execution_attempted'] is False and x['native_parity_accepted'] is False
    assert x['grammar_admitted'] is False and x['searchable'] is False
    assert json.loads((ROOT/'tests/fixtures/phase2_er_native/phase2_er_executable_package.json').read_text())==x
