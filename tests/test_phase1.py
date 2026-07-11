import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from lab.core import State, ingest_csv, run_task, run_engine_task, validate_contract, validate_indicator_artifact, workflow

CONTRACT={"provider":"manual","acquisition_tool":"manual","source_symbol":"EURUSD","project_symbol":"EURUSD","source_timestamp_semantics":"broker_local","bar_timestamp_semantics":"start","timezone_identity":"america_new_york_plus_7_v1","dst_regime":"new_york_dst_v1","session_clock":"broker","strategy_clock":"broker","conversion_history":[]}
class Phase1(unittest.TestCase):
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
