import json, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ENGINE=ROOT/'engine/target/debug/labengine';FIXTURE=ROOT/'tests/fixtures/phase2_roc_scenarios.json'
def test_rust_layer1_task_emits_deterministic_roc_rows():
 source=json.loads(FIXTURE.read_text());task={'task_version':1,'task_type':'layer1_parity_v1','scenarios':source['scenarios']}
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'task.json';p.write_text(json.dumps(task));r=subprocess.run([str(ENGINE),str(p)],capture_output=True,text=True)
 assert r.returncode==0,r.stderr;out=json.loads(r.stdout);assert out['ok'] is True;assert {x['node'] for x in out['rows']}=={'ROC'};assert any(x['classification']=='steady_state' for x in out['rows']);assert any(x['reason_code']=='invalid_period' for x in out['rows'])
