import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from lab.core import State, ingest_csv, run_task, run_engine_task, validate_contract, validate_indicator_artifact, workflow

CONTRACT={"provider":"manual","acquisition_tool":"manual","source_symbol":"EURUSD","project_symbol":"EURUSD","source_timestamp_semantics":"broker_local","bar_timestamp_semantics":"start","timezone_identity":"america_new_york_plus_7_v1","dst_regime":"new_york_dst_v1","session_clock":"broker","strategy_clock":"broker","conversion_history":[]}
class Phase1(unittest.TestCase):
 def test_cross_boolean_rejected_by_numeric_transforms_cli(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; source=str(root/"engine/labengine/tests/fixtures/phase2_indicator_utc.parquet")
  with tempfile.TemporaryDirectory() as d:
   prefix=[{"name":"SMA","output":"sma3","period":3},{"name":"Cross","left":{"series":"close","type":"numeric"},"right":{"series":"sma3","type":"numeric"},"direction":"above","output":"flag"}]
   numeric={"series":"flag","type":"numeric"}
   tails=[{"name":"Slope","input":numeric,"lookback":1,"output":"bad"},{"name":"Percentile","input":numeric,"lookback":2,"output":"bad"},{"name":"DistanceAtr","input":numeric,"reference":{"series":"sma3","type":"numeric"},"atr":{"series":"sma3","type":"numeric"},"output":"bad"},{"name":"Cross","left":numeric,"right":{"series":"sma3","type":"numeric"},"direction":"above","output":"bad"}]
   for i,tail in enumerate(tails):
    task={"task_version":1,"task_type":"compute_indicators","input_path":source,"output_path":str(Path(d)/(f"bad{i}.parquet")),"indicators":prefix+[tail]}; p=Path(d)/(f"bad{i}.json"); p.write_text(json.dumps(task)); result=subprocess.run([str(binary),str(p)],capture_output=True,text=True); self.assertNotEqual(result.returncode,0); self.assertIn("type mismatch",result.stderr); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(result.stdout.strip())
 def test_committed_cross_fixture(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; task=json.loads((root/"engine/labengine/tests/fixtures/phase2_cross_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   task["input_path"]=str(root/task["input_path"]); task["output_path"]=str(Path(d)/"one.parquet"); Path(d,"one.json").write_text(json.dumps(task)); one=json.loads(subprocess.run([str(binary),str(Path(d)/"one.json")],check=True,capture_output=True,text=True).stdout); task["output_path"]=str(Path(d)/"two.parquet"); Path(d,"two.json").write_text(json.dumps(task)); two=json.loads(subprocess.run([str(binary),str(Path(d)/"two.json")],check=True,capture_output=True,text=True).stdout); self.assertEqual(one["output_semantic_content_identity"],two["output_semantic_content_identity"])
   import pyarrow.parquet as pq
   table=pq.read_table(task["output_path"]); self.assertEqual(table.num_rows,12); self.assertEqual(table.column_names,["timestamp","sma3","close.cross_above.sma3","sma3.cross_below.close"]); self.assertEqual(str(table.schema.field("close.cross_above.sma3").type),"bool"); self.assertEqual(table["close.cross_above.sma3"].to_pylist()[3],True); self.assertEqual(table["close.cross_above.sma3"].to_pylist()[0],None)
 def test_percentile_cli_acceptance_and_identity(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; source=str(root/"engine/labengine/tests/fixtures/phase2_indicator_utc.parquet"); fixture=json.loads((root/"engine/labengine/tests/fixtures/phase2_percentile_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   def spec(**change): return {"name":"Percentile","input":{"series":"close","type":"numeric"},"lookback":4,"output":"x",**change}
   bad=[{"input":None},{"lookback":None},{"output":None},{"bad":1},{"input":{"series":"close"}},{"input":{"type":"numeric"}},{"input":{"series":1,"type":"numeric"}},{"input":{"series":"close","type":"numeric","x":1}},{"input":{"series":"close","type":"boolean"}},{"lookback":0},{"lookback":1},{"lookback":1.5},{"input":{"series":"unknown","type":"numeric"}},{"input":{"series":"later","type":"numeric"}}]
   for i,change in enumerate(bad):
    item={k:v for k,v in spec(**change).items() if v is not None}; task={"task_version":1,"task_type":"compute_indicators","input_path":source,"output_path":str(Path(d)/(f"bad{i}.parquet")),"indicators":[item]}; p=Path(d)/(f"bad{i}.json"); p.write_text(json.dumps(task)); result=subprocess.run([str(binary),str(p)],capture_output=True,text=True); self.assertNotEqual(result.returncode,0); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(result.stdout.strip())
   duplicate={"task_version":1,"task_type":"compute_indicators","input_path":source,"output_path":str(Path(d)/"dup.parquet"),"indicators":[{"name":"SMA","output":"sma3","period":3},spec(output="sma3",input={"series":"sma3","type":"numeric"})]}; p=Path(d)/"dup.json"; p.write_text(json.dumps(duplicate)); result=subprocess.run([str(binary),str(p)],capture_output=True,text=True); self.assertNotEqual(result.returncode,0); self.assertFalse(Path(duplicate["output_path"]).exists()); self.assertFalse(result.stdout.strip())
   def run(task,name,raw=None): task["input_path"]=source; task["output_path"]=str(Path(d)/(name+".parquet")); p=Path(d)/(name+".json"); p.write_text(raw or json.dumps(task)); return json.loads(subprocess.run([str(binary),str(p)],check=True,capture_output=True,text=True).stdout),task
   baseline,_=run(json.loads(json.dumps(fixture)),"base"); self.assertEqual(baseline["output_semantic_content_identity"],"943765d83d115309867fa8da768fc2a69500e7292f6048ed87541f4e26e63775")
   equivalent=json.loads(json.dumps(fixture)); raw='{"indicators":'+json.dumps(equivalent["indicators"],separators=(",",":"))+',"task_type":"compute_indicators","task_version":1,"input_path":"'+source+'","output_path":"'+str(Path(d)/"same.parquet")+'"}'; same,_=run(equivalent,"same",raw); self.assertEqual(same["output_semantic_content_identity"],baseline["output_semantic_content_identity"])
   for name,field,value in [("lookback","lookback",3),("input","input",{"series":"close","type":"numeric"})]:
    variant=json.loads(json.dumps(fixture)); variant["indicators"][1][field]=value; result,_=run(variant,name); self.assertNotEqual(result["output_semantic_content_identity"],baseline["output_semantic_content_identity"])
   renamed=json.loads(json.dumps(fixture)); renamed["indicators"][1]["output"]="renamed.percentile"; renamed["indicators"][2]["input"]["series"]="renamed.percentile"; result,_=run(renamed,"renamed"); self.assertNotEqual(result["output_semantic_content_identity"],baseline["output_semantic_content_identity"])
 def test_committed_percentile_fixture(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; task=json.loads((root/"engine/labengine/tests/fixtures/phase2_percentile_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   task["input_path"]=str(root/task["input_path"]); task["output_path"]=str(Path(d)/"one.parquet"); Path(d,"one.json").write_text(json.dumps(task)); one=json.loads(subprocess.run([str(binary),str(Path(d)/"one.json")],check=True,capture_output=True,text=True).stdout); task["output_path"]=str(Path(d)/"two.parquet"); Path(d,"two.json").write_text(json.dumps(task)); two=json.loads(subprocess.run([str(binary),str(Path(d)/"two.json")],check=True,capture_output=True,text=True).stdout); self.assertEqual(one["output_semantic_content_identity"],"943765d83d115309867fa8da768fc2a69500e7292f6048ed87541f4e26e63775"); self.assertEqual(two["output_semantic_content_identity"],one["output_semantic_content_identity"])
   import pyarrow.parquet as pq
   table=pq.read_table(task["output_path"]); self.assertEqual(table.column_names,["timestamp","sma3","sma3.percentile4","sma3.percentile4.slope"]); self.assertEqual(table.num_rows,12); self.assertEqual(str(table.schema.field("sma3.percentile4").type),"double"); self.assertEqual(table["sma3.percentile4"].to_pylist()[:6],[None,None,None,None,None,1.0]); self.assertEqual(table["sma3.percentile4.slope"].to_pylist()[6],0.0)
 def test_distance_atr_duplicate_output_rejected_by_cli(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; source=str(root/"engine/labengine/tests/fixtures/phase2_indicator_utc.parquet")
  with tempfile.TemporaryDirectory() as d:
   task={"task_version":1,"task_type":"compute_indicators","input_path":source,"output_path":str(Path(d)/"duplicate.parquet"),"indicators":[{"name":"SMA","output":"sma3","period":3},{"name":"ATR","output":"atr3","period":3},{"name":"DistanceAtr","input":{"series":"close","type":"numeric"},"reference":{"series":"sma3","type":"numeric"},"atr":{"series":"atr3","type":"numeric"},"output":"sma3"}]}; path=Path(d)/"task.json"; path.write_text(json.dumps(task)); result=subprocess.run([str(binary),str(path)],capture_output=True,text=True); self.assertNotEqual(result.returncode,0); self.assertIn("duplicate output name",result.stderr); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(result.stdout.strip())
 def test_distance_atr_cli_failures_and_identity_sensitivity(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; source=str(root/"engine/labengine/tests/fixtures/phase2_indicator_utc.parquet"); fixture=json.loads((root/"engine/labengine/tests/fixtures/phase2_distance_atr_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   def invoke(task,name,raw=None):
    task["input_path"]=source; task["output_path"]=str(Path(d)/(name+".parquet")); p=Path(d)/(name+".json"); p.write_text(raw or json.dumps(task)); return subprocess.run([str(binary),str(p)],capture_output=True,text=True),task
   def distance(**changes): return {"name":"DistanceAtr","input":{"series":"close","type":"numeric"},"reference":{"series":"sma3","type":"numeric"},"atr":{"series":"atr3","type":"numeric"},"output":"x",**changes}
   bad=[{}, {"input":None}, {"reference":None}, {"atr":None}, {"output":None}, {"bad":1}, {"input":{"series":"close"}}, {"reference":{"type":"numeric"}}, {"atr":{"series":1,"type":"numeric"}}, {"input":{"series":"close","type":"numeric","extra":1}}, {"input":{"series":"close","type":"boolean"}}, {"input":{"series":"missing","type":"numeric"}}, {"reference":{"series":"missing","type":"numeric"}}, {"atr":{"series":"missing","type":"numeric"}}, {"input":{"series":"later","type":"numeric"}}]
   for i,change in enumerate(bad):
    spec=distance(**change); spec={k:v for k,v in spec.items() if v is not None}; task={"task_version":1,"task_type":"compute_indicators","input_path":source,"output_path":str(Path(d)/(f"bad{i}.parquet")),"indicators":[spec]}; p=Path(d)/(f"bad{i}.json"); p.write_text(json.dumps(task)); result=subprocess.run([str(binary),str(p)],capture_output=True,text=True); self.assertNotEqual(result.returncode,0); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(result.stdout.strip())
   base=json.loads(json.dumps(fixture)); result,base=invoke(base,"baseline"); baseline=json.loads(result.stdout)["output_semantic_content_identity"]; self.assertEqual(baseline,"c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad")
   equivalent=json.loads(json.dumps(fixture)); raw='{"indicators":'+json.dumps(equivalent["indicators"],separators=(",",":"))+',"task_version":1,"task_type":"compute_indicators","input_path":"'+source+'","output_path":"'+str(Path(d)/"equivalent.parquet")+'"}'; result,_=invoke(equivalent,"equivalent",raw); self.assertEqual(json.loads(result.stdout)["output_semantic_content_identity"],baseline)
   for name,field,series in [("input","input","sma3"),("reference","reference","atr3"),("atr","atr","sma3")]:
    variant=json.loads(json.dumps(fixture)); variant["indicators"][2][field]["series"]=series; result,variant=invoke(variant,name); identity=json.loads(result.stdout)["output_semantic_content_identity"]; self.assertNotEqual(identity,baseline)
   renamed=json.loads(json.dumps(fixture)); renamed["indicators"][2]["output"]="renamed.distance"; renamed["indicators"][3]["input"]["series"]="renamed.distance"; result,renamed=invoke(renamed,"renamed"); self.assertNotEqual(json.loads(result.stdout)["output_semantic_content_identity"],baseline)
 def test_committed_distance_atr_fixture(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; task=json.loads((root/"engine/labengine/tests/fixtures/phase2_distance_atr_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   task["input_path"]=str(root/task["input_path"]); task["output_path"]=str(Path(d)/"one.parquet"); Path(d,"one.json").write_text(json.dumps(task)); one=json.loads(subprocess.run([str(binary),str(Path(d)/"one.json")],check=True,capture_output=True,text=True).stdout); task["output_path"]=str(Path(d)/"two.parquet"); Path(d,"two.json").write_text(json.dumps(task)); two=json.loads(subprocess.run([str(binary),str(Path(d)/"two.json")],check=True,capture_output=True,text=True).stdout); self.assertEqual(one["output_semantic_content_identity"],"c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad"); self.assertEqual(two["output_semantic_content_identity"],one["output_semantic_content_identity"])
   import pyarrow.parquet as pq
   table=pq.read_table(task["output_path"]); self.assertEqual(table.num_rows,12); self.assertEqual(table.column_names,["timestamp","sma3","atr3","close_sma3.distance_atr","close_sma3.distance_atr.slope"]); self.assertEqual(str(table.schema.field("close_sma3.distance_atr").type),"double"); self.assertEqual(table["close_sma3.distance_atr"].to_pylist()[:4],[None,None,0.0,0.2999999999998062])
 def test_slope_identity_sensitivity_through_cli(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; base=json.loads((root/"engine/labengine/tests/fixtures/phase2_slope_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   def run(task,name,raw=None):
    task["input_path"]=str(root/task["input_path"]); task["output_path"]=str(Path(d)/(name+".parquet")); p=Path(d)/(name+".json"); p.write_text(raw if raw else json.dumps(task)); result=json.loads(subprocess.run([str(binary),str(p)],check=True,capture_output=True,text=True).stdout); return result,task
   baseline,_=run(json.loads(json.dumps(base)),"baseline")
   equivalent=json.loads(json.dumps(base)); raw='{"indicators":'+json.dumps(equivalent["indicators"],separators=(",",":"))+',"task_type":"compute_indicators","task_version":1,"output_path":"'+str(Path(d)/"equivalent.parquet")+'","input_path":"'+str(root/equivalent["input_path"])+'"}'
   same,_=run(equivalent,"equivalent",raw); self.assertEqual(same["output_semantic_content_identity"],baseline["output_semantic_content_identity"])
   cases=[]
   lookback=json.loads(json.dumps(base)); lookback["indicators"][1]["lookback"]=2; cases.append(("lookback",lookback))
   reference=json.loads(json.dumps(base)); reference["indicators"][2]["input"]["series"]="sma3"; cases.append(("reference",reference))
   renamed=json.loads(json.dumps(base)); renamed["indicators"][2]["output"]="renamed.delta"; cases.append(("output",renamed))
   for name,variant in cases:
    result,task=run(variant,name); self.assertNotEqual(result["output_semantic_content_identity"],baseline["output_semantic_content_identity"]); import pyarrow.parquet as pq; self.assertIn(task["indicators"][-1]["output"],pq.read_table(task["output_path"]).column_names)
 def test_slope_dispatch_failures_and_macd_component(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; source=str(root/"engine/labengine/tests/fixtures/phase2_indicator_utc.parquet")
  with tempfile.TemporaryDirectory() as d:
   base={"task_version":1,"task_type":"compute_indicators","input_path":source,"indicators":[{"name":"SMA","output":"sma3","period":3}]}
   bads=[{"name":"Slope","output":"x","lookback":1},{"name":"Slope","input":{"series":"close","type":"numeric"},"output":"x"},{"name":"Slope","input":{"series":"close","type":"numeric"},"lookback":1,"output":"x","bad":1},{"name":"Slope","input":{"series":"close"},"lookback":1,"output":"x"},{"name":"Slope","input":{"series":"nope","type":"numeric"},"lookback":1,"output":"x"},{"name":"Slope","input":{"series":"later","type":"numeric"},"lookback":1,"output":"x"},{"name":"Slope","input":{"series":"close","type":"boolean"},"lookback":1,"output":"x"},{"name":"Slope","input":{"series":"close","type":"numeric"},"lookback":0,"output":"x"},{"name":"Slope","input":{"series":"close","type":"numeric"},"lookback":1.5,"output":"x"}]
   for i,spec in enumerate(bads):
    task={**base,"output_path":str(Path(d)/f"bad{i}.parquet"),"indicators":[spec]}; p=Path(d)/f"bad{i}.json"; p.write_text(json.dumps(task)); result=subprocess.run([str(binary),str(p)],capture_output=True,text=True); self.assertNotEqual(result.returncode,0); self.assertFalse(Path(task["output_path"]).exists())
   duplicate={**base,"output_path":str(Path(d)/"duplicate.parquet"),"indicators":base["indicators"]+[{"name":"Slope","input":{"series":"close","type":"numeric"},"lookback":1,"output":"sma3"}]}; Path(d,"duplicate.json").write_text(json.dumps(duplicate)); self.assertNotEqual(subprocess.run([str(binary),str(Path(d,"duplicate.json"))],capture_output=True,text=True).returncode,0); self.assertFalse(Path(duplicate["output_path"]).exists())
   task=json.loads((root/"engine/labengine/tests/fixtures/phase2_macd_slope_task.json").read_text()); task["input_path"]=source; task["output_path"]=str(Path(d)/"macd.parquet"); p=Path(d)/"macd.json"; p.write_text(json.dumps(task)); one=json.loads(subprocess.run([str(binary),str(p)],check=True,capture_output=True,text=True).stdout); self.assertEqual(one["output_semantic_content_identity"],"c1d1d4a1003a3c0bc8f6b8b3d3ec736349db90082647a349cebf89b6dd07cb1e")
   import pyarrow.parquet as pq
   table=pq.read_table(task["output_path"]); self.assertEqual(table.column_names[-2:],["macd_histogram_slope","macd_histogram_slope_delta"]); self.assertEqual(table["macd_histogram_slope"].to_pylist()[6],-8.176790123456032e-05)
 def test_committed_slope_regression_fixture(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; task=json.loads((root/"engine"/"labengine"/"tests"/"fixtures"/"phase2_slope_task.json").read_text()); expected=json.loads((root/"engine"/"labengine"/"tests"/"fixtures"/"phase2_slope_expected.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   task["input_path"]=str(root/task["input_path"]); task["output_path"]=str(Path(d)/"one.parquet"); Path(d,"one.json").write_text(json.dumps(task)); one=json.loads(subprocess.run([str(binary),str(Path(d)/"one.json")],check=True,capture_output=True,text=True).stdout); task["output_path"]=str(Path(d)/"two.parquet"); Path(d,"two.json").write_text(json.dumps(task)); two=json.loads(subprocess.run([str(binary),str(Path(d)/"two.json")],check=True,capture_output=True,text=True).stdout); self.assertEqual(one["output_semantic_content_identity"],expected["semantic_identity"]); self.assertEqual(two["output_semantic_content_identity"],one["output_semantic_content_identity"])
 def test_committed_typed_indicator_regression_fixture(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"
  if not binary.exists(): subprocess.run(["cargo","build","--manifest-path",str(root/"engine"/"Cargo.toml")],check=True,cwd=root)
  task=json.loads((root/"engine"/"labengine"/"tests"/"fixtures"/"phase2_indicator_task.json").read_text()); expected=json.loads((root/"engine"/"labengine"/"tests"/"fixtures"/"phase2_indicator_expected.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   task["input_path"]=str(root/task["input_path"]); task["output_path"]=str(Path(d)/"out.parquet")
   first=json.loads(subprocess.run([str(binary),str(Path(d)/"task.json")],input=json.dumps(task),capture_output=True,text=True).stdout or "{}") if False else None
   Path(d,"task.json").write_text(json.dumps(task)); first=json.loads(subprocess.run([str(binary),str(Path(d)/"task.json")],check=True,capture_output=True,text=True).stdout); task["output_path"]=str(Path(d)/"out-second.parquet"); Path(d,"task-second.json").write_text(json.dumps(task)); second=json.loads(subprocess.run([str(binary),str(Path(d)/"task-second.json")],check=True,capture_output=True,text=True).stdout); self.assertEqual(first["output_semantic_content_identity"],expected["semantic_identity"]); self.assertEqual(second["output_semantic_content_identity"],first["output_semantic_content_identity"])
   import pyarrow.parquet as pq
   table=pq.read_table(task["output_path"]); self.assertEqual(table.num_rows,expected["rows"]); self.assertEqual([[f.name,str(f.type)] for f in table.schema],expected["columns"])
 def test_nullable_boolean_indicator_artifact_validation(self):
  import pyarrow as pa, pyarrow.parquet as pq
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"flags.parquet"; stamps=["a","b","c"]
   pq.write_table(pa.table({"timestamp":pa.array(stamps,type=pa.string()),"flag":pa.array([True,False,None],type=pa.bool_())}),p)
   self.assertEqual(validate_indicator_artifact(p,[("flag","boolean")],stamps).column("flag").to_pylist(),[True,False,None])
   for value in [pa.array([1,0,None],type=pa.float64()),pa.array(["true","false",None],type=pa.string())]:
    bad=Path(d)/"bad.parquet"; pq.write_table(pa.table({"timestamp":stamps,"flag":value}),bad)
    with self.assertRaises(ValueError): validate_indicator_artifact(bad,[("flag","boolean")],stamps)
   short=Path(d)/"short.parquet"; pq.write_table(pa.table({"timestamp":["a"],"flag":pa.array([True],type=pa.bool_())}),short)
   with self.assertRaises(ValueError): validate_indicator_artifact(short,[("flag","boolean")],stamps)
   with self.assertRaises(ValueError): validate_indicator_artifact(Path(d)/"missing.parquet",[("flag","boolean")],stamps)
   broken=Path(d)/"broken.parquet"; broken.write_bytes(b"PAR1")
   with self.assertRaises(ValueError): validate_indicator_artifact(broken,[("flag","boolean")],stamps)
 def test_contract_and_double_conversion(self):
  self.assertEqual(validate_contract(CONTRACT)["strategy_clock"],"broker")
  bad={**CONTRACT,"conversion_history":[{"target":"UTC"},{"target":"UTC"}]}
  with self.assertRaises(ValueError): validate_contract(bad)
 def test_idempotent_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   s=State(d); p=s.protocol("p",{"v":1}); e=s.experiment("x",p,{"x":1}); self.assertEqual(e,s.experiment("x",p,{"x":1}))
   workflow(s,d,e); final=s.conn.execute("SELECT result_hash FROM tasks WHERE status='succeeded' ORDER BY updated_at DESC LIMIT 1").fetchone()[0]
   workflow(s,d,e); self.assertEqual(final,s.conn.execute("SELECT result_hash FROM tasks WHERE status='succeeded' ORDER BY updated_at DESC LIMIT 1").fetchone()[0]); self.assertEqual(7,s.conn.execute("SELECT count(*) FROM tasks WHERE experiment_id=?",(e,)).fetchone()[0])
 def test_partial_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   s=State(d); p=s.protocol("p",{}); e=s.experiment("x",p,{}); st=s.stage(e,"x",0); t=s.task(e,st,{"stage":"x","kind":"shard","value":1})
   partial=Path(d)/"bad.partial"; partial.mkdir()
   with self.assertRaises(ValueError): s.publish(t,partial,{})
 def test_interrupted_resume_and_parquet(self):
  with tempfile.TemporaryDirectory() as d:
   s=State(d); p=s.protocol("p",{"v":1}); e=s.experiment("x",p,{"x":1})
   st=s.stage(e,"interrupt",0); t=s.task(e,st,{"stage":"interrupt","kind":"shard","value":1})
   run_task(s,d,t,interrupt=True); self.assertEqual(s.conn.execute("SELECT status FROM tasks WHERE id=?",(t,)).fetchone()[0],"interrupted")
   run_task(s,d,t); self.assertEqual(s.conn.execute("SELECT status FROM tasks WHERE id=?",(t,)).fetchone()[0],"succeeded")
   workflow(s,d,e); completed=s.conn.execute("SELECT count(*) FROM tasks WHERE status='succeeded'").fetchone()[0]
   self.assertEqual(completed,8); workflow(s,d,e); self.assertEqual(completed,s.conn.execute("SELECT count(*) FROM tasks WHERE status='succeeded'").fetchone()[0])
   csv_path=Path(d)/"bars.csv"; csv_path.write_text("Date,Time,Open,High,Low,Close,Volume\n2025.06.03,08:00,1,2,0.5,1.5,7\n2025.06.03,08:01,1.5,2.5,1,2,8\n")
   result=ingest_csv(csv_path,Path(d)/"bars.parquet",{"date":"Date","time":"Time","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"},CONTRACT)
   self.assertEqual(result["rows"],2)
   import pyarrow.parquet as pq
   self.assertEqual(pq.read_table(Path(d)/"bars.parquet").num_rows,2)
 def test_engine_json_tasks_publish_only_complete_artifacts(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"
  if not binary.exists(): subprocess.run(["cargo","build","--manifest-path",str(root/"engine"/"Cargo.toml")],check=True,cwd=root)
  with tempfile.TemporaryDirectory() as d:
   s=State(d); p=s.protocol("engine",{"version":1}); e=s.experiment("engine",p,{}) ; stage=s.stage(e,"engine",0)
   source=Path(d)/"source.parquet"; shutil.copy(root/"engine"/"labengine"/"tests"/"fixtures"/"phase1_utc_m1.parquet",source)
   validate={"stage":"engine","task_version":1,"task_type":"validate_dataset","input_path":str(source),"expected_contract_version":1}
   valid_task=s.task(e,stage,validate); self.assertEqual(run_engine_task(s,d,valid_task,binary,validate),valid_task)
   aggregate={"stage":"engine","task_version":1,"task_type":"aggregate_m1","input_path":str(source),"target_timeframe":"M5","completeness_policy":"omit_edge_partials_v1"}
   aggregate_task=s.task(e,stage,aggregate); self.assertEqual(run_engine_task(s,d,aggregate_task,binary,aggregate),aggregate_task)
   artifact=Path(s.conn.execute("SELECT artifact_path FROM tasks WHERE id=?",(aggregate_task,)).fetchone()[0]); self.assertTrue((artifact/"derived.parquet").is_file()); self.assertEqual(run_engine_task(s,d,aggregate_task,binary,aggregate),aggregate_task)
   indicators={"stage":"engine","task_version":1,"task_type":"compute_indicators","input_path":str(source),"indicators":[{"name":"SMA","output":"sma2","period":2}]}
   indicator_task=s.task(e,stage,indicators); self.assertEqual(run_engine_task(s,d,indicator_task,binary,indicators),indicator_task); indicator_artifact=Path(s.conn.execute("SELECT artifact_path FROM tasks WHERE id=?",(indicator_task,)).fetchone()[0]); self.assertTrue((indicator_artifact/"indicators.parquet").is_file())
   rejected={"stage":"engine","task_version":1,"task_type":"aggregate_m1","input_path":str(source),"target_timeframe":"bad","completeness_policy":"omit_edge_partials_v1"}
   bad=s.task(e,stage,rejected); self.assertIsNone(run_engine_task(s,d,bad,binary,rejected)); self.assertEqual(s.conn.execute("SELECT status FROM tasks WHERE id=?",(bad,)).fetchone()[0],"failed"); self.assertIsNone(s.conn.execute("SELECT artifact_path FROM tasks WHERE id=?",(bad,)).fetchone()[0])
if __name__=="__main__": unittest.main()
