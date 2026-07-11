import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from lab.core import State, ingest_csv, run_task, run_engine_task, validate_contract, validate_indicator_artifact, workflow

CONTRACT={"provider":"manual","acquisition_tool":"manual","source_symbol":"EURUSD","project_symbol":"EURUSD","source_timestamp_semantics":"broker_local","bar_timestamp_semantics":"start","timezone_identity":"america_new_york_plus_7_v1","dst_regime":"new_york_dst_v1","session_clock":"broker","strategy_clock":"broker","conversion_history":[]}
class Phase1(unittest.TestCase):
 def test_entry_intent_cli_closure_variants_and_failures(self):
  import pyarrow as pa, pyarrow.parquet as pq
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; cross=json.loads((root/"engine/labengine/tests/fixtures/phase2_cross_task.json").read_text()); eva=json.loads((root/"engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json").read_text()); base=json.loads((root/"engine/labengine/tests/fixtures/phase2_entry_intent_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   def call(task,name):
    task=json.loads(json.dumps(task)); task["output_path"]=str(Path(d)/(name+".parquet")); p=Path(d)/(name+".json");p.write_text(json.dumps(task));return subprocess.run([str(binary),str(p)],capture_output=True,text=True),task
   cross["input_path"]=str(root/cross["input_path"]);r,cross=call(cross,"cross");eva["input_path"]=cross["output_path"];r,eva=call(eva,"eva");base["input_path"]=eva["output_path"];r,base=call(base,"base");self.assertEqual(r.returncode,0);a=json.loads(r.stdout);cid=a["condition_semantic_identity"];iid=a["entry_intent_semantic_identity"]
   equivalent=json.loads(json.dumps(base));equivalent["condition"]=json.loads('{"entry":'+json.dumps(base["condition"]["entry"],separators=(",",":"))+',"side":"long","schema_version":1}');r,_=call(equivalent,"equivalent");self.assertEqual((json.loads(r.stdout)["condition_semantic_identity"],json.loads(r.stdout)["entry_intent_semantic_identity"]),(cid,iid))
   short=json.loads(json.dumps(base));short["condition"]["side"]="short";r,_=call(short,"short");self.assertNotEqual(json.loads(r.stdout)["condition_semantic_identity"],cid);self.assertNotEqual(json.loads(r.stdout)["entry_intent_semantic_identity"],iid);self.assertEqual(json.loads(r.stdout)["side"],"short")
   renamed=json.loads(json.dumps(base));renamed["output"]="renamed_intent";r,t=call(renamed,"renamed");self.assertEqual(json.loads(r.stdout)["condition_semantic_identity"],cid);self.assertNotEqual(json.loads(r.stdout)["entry_intent_semantic_identity"],iid);self.assertEqual(pq.read_table(t["output_path"]).column_names,["timestamp","renamed_intent"])
   table=pq.read_table(eva["output_path"]);v=table["entry_signal"].to_pylist();v[3]=False;changed=Path(d)/"changed.parquet";pq.write_table(table.set_column(1,"entry_signal",pa.array(v,type=pa.bool_())),changed);mut=json.loads(json.dumps(base));mut["input_path"]=str(changed);r,t=call(mut,"mut-out");self.assertEqual(json.loads(r.stdout)["condition_semantic_identity"],cid);self.assertNotEqual(json.loads(r.stdout)["entry_intent_semantic_identity"],iid);self.assertFalse(pq.read_table(t["output_path"])["entry_intent"].to_pylist()[4])
   badconds=[{}, {"schema_version":2,"side":"long","entry":base["condition"]["entry"]},{"schema_version":"1","side":"long","entry":base["condition"]["entry"]},{"schema_version":1,"side":"x","entry":base["condition"]["entry"]},{"schema_version":1,"side":"long","entry":{}},{"schema_version":1,"side":"long","entry":{"signal":{"series":"entry_signal","type":"numeric"},"timing":"next_open"}},{"schema_version":1,"side":"long","entry":{"signal":{"series":"entry_signal","type":"boolean","x":1},"timing":"next_open"}},{"schema_version":1,"side":"long","entry":{"signal":{"series":"entry_signal","type":"boolean"},"timing":"now"}}]
   for n,c in enumerate(badconds):task={"task_version":1,"task_type":"build_entry_intents","input_path":eva["output_path"],"output":"x","condition":c};r,t=call(task,"bad"+str(n));self.assertNotEqual(r.returncode,0);self.assertFalse(Path(t["output_path"]).exists());self.assertFalse(r.stdout.strip())
 def test_entry_intent_committed_cli_chain(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; tasks=[json.loads((root/f).read_text()) for f in ["engine/labengine/tests/fixtures/phase2_cross_task.json","engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json","engine/labengine/tests/fixtures/phase2_entry_intent_task.json"]]
  with tempfile.TemporaryDirectory() as d:
   paths=[Path(d)/x for x in ["cross.parquet","signal.parquet","intent.parquet"]]
   tasks[0]["input_path"]=str(root/tasks[0]["input_path"]); tasks[0]["output_path"]=str(paths[0]); tasks[1]["input_path"]=str(paths[0]); tasks[1]["output_path"]=str(paths[1]); tasks[2]["input_path"]=str(paths[1]); tasks[2]["output_path"]=str(paths[2])
   summaries=[]
   for i,task in enumerate(tasks):p=Path(d)/(str(i)+".json");p.write_text(json.dumps(task)); summaries.append(json.loads(subprocess.run([str(binary),str(p)],check=True,capture_output=True,text=True).stdout))
   import pyarrow.parquet as pq
   table=pq.read_table(paths[2]); self.assertEqual(table.column_names,["timestamp","entry_intent"]); self.assertEqual(table["entry_intent"].to_pylist(),[None,None,None,False,True,True,True,True,True,True,True,True]); self.assertEqual([summaries[-1]["intent_true"],summaries[-1]["intent_false"],summaries[-1]["intent_null"]],[8,1,3]); self.assertEqual(summaries[-1]["terminal_source_signal"],True); self.assertEqual(summaries[-1]["condition_semantic_identity"],"6649fde8f30650966ef241396024d163b08432ba12ec5aab7e2f570b10e2f832")
 def test_ast_evaluate_cli_runtime_closure(self):
  import pyarrow as pa, pyarrow.parquet as pq
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; cross=json.loads((root/"engine/labengine/tests/fixtures/phase2_cross_task.json").read_text()); base=json.loads((root/"engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   def call(task,name):
    task=json.loads(json.dumps(task)); task["output_path"]=str(Path(d)/(name+".parquet")); p=Path(d)/(name+".json"); p.write_text(json.dumps(task)); return subprocess.run([str(binary),str(p)],capture_output=True,text=True),task
   cross["input_path"]=str(root/cross["input_path"]); r,cross=call(cross,"cross"); self.assertEqual(r.returncode,0); base["input_path"]=cross["output_path"]; r,baseline=call(base,"baseline"); self.assertEqual(r.returncode,0); summary=json.loads(r.stdout); aid=summary["ast_semantic_identity"]; eid=summary["evaluated_artifact_semantic_identity"]
   equivalent=json.loads(json.dumps(base)); equivalent["ast"]=json.loads('{"root":'+json.dumps(base["ast"]["root"],separators=(",",":"))+',"schema_version":1}'); r,_=call(equivalent,"equivalent"); self.assertEqual((json.loads(r.stdout)["ast_semantic_identity"],json.loads(r.stdout)["evaluated_artifact_semantic_identity"]),(aid,eid))
   renamed=json.loads(json.dumps(base)); renamed["output"]="renamed_signal"; r,task=call(renamed,"renamed"); s=json.loads(r.stdout); self.assertEqual(s["ast_semantic_identity"],aid); self.assertNotEqual(s["evaluated_artifact_semantic_identity"],eid); self.assertEqual(pq.read_table(task["output_path"]).column_names,["timestamp","renamed_signal"])
   source=pq.read_table(cross["output_path"]); values=source["sma3"].to_pylist(); values[3]=1.0; changed=Path(d)/"changed.parquet"; pq.write_table(source.set_column(source.schema.get_field_index("sma3"),"sma3",pa.array(values,type=pa.float64())),changed); mutated=json.loads(json.dumps(base)); mutated["input_path"]=str(changed); r,task=call(mutated,"changed-output"); s=json.loads(r.stdout); self.assertEqual(s["ast_semantic_identity"],aid); self.assertNotEqual(s["evaluated_artifact_semantic_identity"],eid); self.assertEqual(pq.read_table(task["output_path"])["entry_signal"].to_pylist()[3],False)
   missing=Path(d)/"not-found.parquet"; invalid=Path(d)/"invalid.parquet"; invalid.write_text("not parquet"); no_time=Path(d)/"no-time.parquet"; pq.write_table(pa.table({"n":pa.array([1.0])}),no_time); wrong_time=Path(d)/"wrong-time.parquet"; pq.write_table(pa.table({"timestamp":pa.array([1]),"n":pa.array([1.0])}),wrong_time)
   cases=[("missing",str(missing),base["ast"]),("invalid",str(invalid),base["ast"]),("no-time",str(no_time),base["ast"]),("wrong-time",str(wrong_time),base["ast"]),("unknown-numeric",cross["output_path"],{"schema_version":1,"root":{"kind":"compare","op":"gt","left":{"kind":"numeric_series","ref":{"series":"missing","type":"numeric"}},"right":{"kind":"number","value":1}}}),("unknown-boolean",cross["output_path"],{"schema_version":1,"root":{"kind":"boolean_series","ref":{"series":"missing","type":"boolean"}}}),("bool-as-num",cross["output_path"],{"schema_version":1,"root":{"kind":"compare","op":"gt","left":{"kind":"numeric_series","ref":{"series":"close.cross_above.sma3","type":"numeric"}},"right":{"kind":"number","value":1}}}),("num-as-bool",cross["output_path"],{"schema_version":1,"root":{"kind":"boolean_series","ref":{"series":"sma3","type":"boolean"}}})]
   for name,path,ast in cases:
    bad={"task_version":1,"task_type":"evaluate_ast","input_path":path,"output":"x","ast":ast}; r,task=call(bad,"failure-"+name); self.assertNotEqual(r.returncode,0); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(r.stdout.strip()); self.assertNotIn("evaluated_artifact_semantic_identity",r.stdout)
 def test_ast_evaluate_cli_fixture_and_failures(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; cross=json.loads((root/"engine/labengine/tests/fixtures/phase2_cross_task.json").read_text()); evaluate=json.loads((root/"engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   def invoke(task,name):
    task=json.loads(json.dumps(task)); task["output_path"]=str(Path(d)/(name+".parquet")); path=Path(d)/(name+".json"); path.write_text(json.dumps(task)); return subprocess.run([str(binary),str(path)],capture_output=True,text=True),task
   cross["input_path"]=str(root/cross["input_path"]); result,cross=invoke(cross,"cross"); self.assertEqual(result.returncode,0); evaluate["input_path"]=cross["output_path"]; first,one=invoke(evaluate,"one"); second,two=invoke(evaluate,"two"); self.assertEqual(first.returncode,0); self.assertEqual(second.returncode,0); a=json.loads(first.stdout); b=json.loads(second.stdout); self.assertEqual(a["ast_semantic_identity"],"667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664"); self.assertEqual(a["evaluated_artifact_semantic_identity"],b["evaluated_artifact_semantic_identity"]); self.assertEqual([a["true_count"],a["false_count"],a["null_count"]],[9,1,2]); self.assertEqual(sum([a["true_count"],a["false_count"],a["null_count"]]),12)
   import pyarrow.parquet as pq
   table=pq.read_table(one["output_path"]); self.assertEqual(table.column_names,["timestamp","entry_signal"]); self.assertEqual(str(table.schema.field("entry_signal").type),"bool"); self.assertEqual(table["entry_signal"].to_pylist(),[None,None,False,True,True,True,True,True,True,True,True,True]); self.assertEqual(table["timestamp"].to_pylist(),pq.read_table(cross["output_path"])["timestamp"].to_pylist())
   bads=[{}, {"input_path":cross["output_path"]}, {"output_path":str(Path(d)/"x.parquet")}, {"input_path":cross["output_path"],"output_path":str(Path(d)/"y.parquet"),"output":"timestamp","ast":evaluate["ast"]}, {"input_path":cross["output_path"],"output_path":str(Path(d)/"z.parquet"),"output":"entry_signal"}, {"input_path":cross["output_path"],"output_path":str(Path(d)/"bad.parquet"),"output":"sma3","ast":evaluate["ast"]}, {"input_path":cross["output_path"],"output_path":str(Path(d)/"strict.parquet"),"output":"x","ast":{"schema_version":1,"root":{"kind":"number","value":1}}}]
   for i,extra in enumerate(bads):
    task={"task_version":1,"task_type":"evaluate_ast",**extra}; path=Path(d)/(f"bad{i}.json"); path.write_text(json.dumps(task)); r=subprocess.run([str(binary),str(path)],capture_output=True,text=True); self.assertNotEqual(r.returncode,0); self.assertFalse(r.stdout.strip()); self.assertNotIn("evaluated_artifact_semantic_identity",r.stdout)
 def test_ast_cli_fixture_canonicalization_and_failures(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; fixture=json.loads((root/"engine/labengine/tests/fixtures/phase2_ast_task.json").read_text()); expected='{"root":{"args":[{"kind":"compare","left":{"kind":"numeric_series","ref":{"series":"rsi14","type":"numeric"}},"op":"gt","right":{"kind":"number","value":50.0}},{"args":[{"kind":"boolean_series","ref":{"series":"close.cross_above.sma3","type":"boolean"}},{"arg":{"kind":"boolean_series","ref":{"series":"rollover_blocked","type":"boolean"}},"kind":"not"}],"kind":"or"}],"kind":"and"},"schema_version":1}'
  with tempfile.TemporaryDirectory() as d:
   def invoke(ast,name):
    task={"task_version":1,"task_type":"canonicalize_ast","output_path":str(Path(d)/(name+".json")),"ast":ast}; path=Path(d)/(name+".task.json"); path.write_text(json.dumps(task)); return subprocess.run([str(binary),str(path)],capture_output=True,text=True),task
   first,one=invoke(fixture["ast"],"one"); second,two=invoke(fixture["ast"],"two"); self.assertEqual(first.returncode,0); self.assertEqual(second.returncode,0); a=json.loads(first.stdout); b=json.loads(second.stdout); self.assertEqual(a["schema_version"],1); self.assertEqual(a["root_type"],"boolean"); self.assertEqual(a["ast_semantic_identity"],"7f6898acef2fb8a2cfa2d07f951931dd68834e6729e2d1c57952dd3f5f5f0afd"); self.assertEqual(a["ast_semantic_identity"],b["ast_semantic_identity"]); canonical=Path(one["output_path"]).read_text(); self.assertEqual(canonical,expected); roundtrip,_=invoke(json.loads(canonical),"roundtrip"); self.assertEqual(json.loads(roundtrip.stdout)["ast_semantic_identity"],a["ast_semantic_identity"])
   bad=[{}, {"schema_version":2,"root":fixture["ast"]["root"]}, {"schema_version":"1","root":fixture["ast"]["root"]}, {"schema_version":1,"root":{"kind":"numeric_series","ref":{"series":"x","type":"numeric"}}}, {"schema_version":1,"root":{"kind":"boolean_series","ref":{"series":"x","type":"numeric"}}}, {"schema_version":1,"root":{"kind":"number","value":"x"}}, {"schema_version":1,"root":{"kind":"compare","left":{"kind":"number","value":1},"right":{"kind":"number","value":2}}}, {"schema_version":1,"root":{"kind":"compare","op":"eq","left":{"kind":"number","value":1},"right":{"kind":"number","value":2}}}, {"schema_version":1,"root":{"kind":"compare","op":"gt","left":{"kind":"boolean_series","ref":{"series":"x","type":"boolean"}},"right":{"kind":"number","value":2}}}, {"schema_version":1,"root":{"kind":"and","args":[]}}, {"schema_version":1,"root":{"kind":"or","args":[{"kind":"boolean_series","ref":{"series":"x","type":"boolean"}}]}}, {"schema_version":1,"root":{"kind":"not","arg":{"kind":"number","value":1}}}, {"schema_version":1,"root":{"kind":"boolean_series","ref":{"series":1,"type":"boolean","extra":1}}}, {"schema_version":1,"root":{"kind":"unknown"}}]
   for i,ast in enumerate(bad):
    result,task=invoke(ast,"bad"+str(i)); self.assertNotEqual(result.returncode,0); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(result.stdout.strip()); self.assertNotIn("ast_semantic_identity",result.stdout)
 def test_ast_identity_mutations_cli(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; base=json.loads((root/"engine/labengine/tests/fixtures/phase2_ast_task.json").read_text())["ast"]
  with tempfile.TemporaryDirectory() as d:
   def run(ast,name):
    task={"task_version":1,"task_type":"canonicalize_ast","output_path":str(Path(d)/(name+".json")),"ast":ast}; path=Path(d)/(name+".task.json"); path.write_text(json.dumps(task)); return json.loads(subprocess.run([str(binary),str(path)],check=True,capture_output=True,text=True).stdout)["ast_semantic_identity"]
   baseline=run(base,"base"); self.assertEqual(baseline,"7f6898acef2fb8a2cfa2d07f951931dd68834e6729e2d1c57952dd3f5f5f0afd")
   variants=[]
   for name,value in [("op","lte"),("threshold",51),("series","rsi13")]:
    item=json.loads(json.dumps(base)); target=item["root"]["args"][0]; target["op"] = value if name=="op" else target["op"]; target["right"]["value"] = value if name=="threshold" else target["right"]["value"]; target["left"]["ref"]["series"] = value if name=="series" else target["left"]["ref"]["series"]; variants.append((name,item))
   boolean=json.loads(json.dumps(base)); boolean["root"]["kind"]="or"; variants.append(("kind",boolean)); order=json.loads(json.dumps(base)); order["root"]["args"].reverse(); variants.append(("order",order)); wrapped=json.loads(json.dumps(base)); wrapped["root"]={"kind":"not","arg":wrapped["root"]}; variants.append(("not",wrapped))
   for name,item in variants:self.assertNotEqual(run(item,name),baseline)
 def test_cross_cli_closure_and_identity(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; source=str(root/"engine/labengine/tests/fixtures/phase2_indicator_utc.parquet"); fixture=json.loads((root/"engine/labengine/tests/fixtures/phase2_cross_task.json").read_text())
  with tempfile.TemporaryDirectory() as d:
   def spec(**c): return {"name":"Cross","left":{"series":"close","type":"numeric"},"right":{"series":"close","type":"numeric"},"direction":"above","output":"x",**c}
   bad=[{"left":None},{"right":None},{"direction":None},{"output":None},{"bad":1},{"left":{"series":"close"}},{"right":{"type":"numeric"}},{"left":{"series":1,"type":"numeric"}},{"left":{"series":"close","type":"numeric","x":1}},{"left":{"series":"close","type":"boolean"}},{"direction":"sideways"},{"direction":1},{"left":{"series":"unknown","type":"numeric"}},{"right":{"series":"unknown","type":"numeric"}},{"left":{"series":"later","type":"numeric"}}]
   for i,c in enumerate(bad):
    item={k:v for k,v in spec(**c).items() if v is not None}; task={"task_version":1,"task_type":"compute_indicators","input_path":source,"output_path":str(Path(d)/(f"bad{i}.parquet")),"indicators":[item]}; p=Path(d)/(f"bad{i}.json"); p.write_text(json.dumps(task)); result=subprocess.run([str(binary),str(p)],capture_output=True,text=True); self.assertNotEqual(result.returncode,0); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(result.stdout.strip())
   def run(task,name): task["input_path"]=source; task["output_path"]=str(Path(d)/(name+".parquet")); p=Path(d)/(name+".json"); p.write_text(json.dumps(task)); return json.loads(subprocess.run([str(binary),str(p)],check=True,capture_output=True,text=True).stdout)
   baseline=run(json.loads(json.dumps(fixture)),"base"); self.assertEqual(baseline["output_semantic_content_identity"],"274e22b09159252cc2a964cf08623de8dd9743c3152fea672a0c9ead749ff814")
   for name,field,value in [("direction","direction","below"),("left","left",{"series":"sma3","type":"numeric"}),("right","right",{"series":"close","type":"numeric"}),("output","output","renamed.cross")]:
    variant=json.loads(json.dumps(fixture)); variant["indicators"][1][field]=value; self.assertNotEqual(run(variant,name)["output_semantic_content_identity"],baseline["output_semantic_content_identity"])
 def test_cross_duplicate_output_rejected_by_cli(self):
  root=Path(__file__).resolve().parents[1]; binary=root/"engine"/"target"/"debug"/"labengine"; source=str(root/"engine/labengine/tests/fixtures/phase2_indicator_utc.parquet")
  with tempfile.TemporaryDirectory() as d:
   task={"task_version":1,"task_type":"compute_indicators","input_path":source,"output_path":str(Path(d)/"duplicate.parquet"),"indicators":[{"name":"SMA","output":"sma3","period":3},{"name":"Cross","left":{"series":"close","type":"numeric"},"right":{"series":"sma3","type":"numeric"},"direction":"above","output":"sma3"}]}
   path=Path(d)/"task.json"; path.write_text(json.dumps(task)); result=subprocess.run([str(binary),str(path)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0); self.assertIn("duplicate output name",result.stderr); self.assertFalse(Path(task["output_path"]).exists()); self.assertFalse(result.stdout.strip()); self.assertNotIn("output_semantic_content_identity",result.stdout)
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
