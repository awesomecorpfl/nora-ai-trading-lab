import json, tempfile, unittest
from pathlib import Path
from lab.core import State, ingest_csv, run_task, validate_contract, workflow

CONTRACT={"provider":"manual","acquisition_tool":"manual","source_symbol":"EURUSD","project_symbol":"EURUSD","source_timestamp_semantics":"broker_local","bar_timestamp_semantics":"start","timezone_identity":"america_new_york_plus_7_v1","dst_regime":"new_york_dst_v1","session_clock":"broker","strategy_clock":"broker","conversion_history":[]}
class Phase1(unittest.TestCase):
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
if __name__=="__main__": unittest.main()
