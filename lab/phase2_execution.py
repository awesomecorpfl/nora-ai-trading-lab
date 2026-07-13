"""Frozen Phase-2 execution-canary scenarios and local Rust evidence assembler."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

VERSION="nora.phase2.execution_canary_rust_v1"
SCHEMA=["scenario_id","ledger_row_index","entry_index","entry_price","exit_index","exit_price","side","stop_price","target_price","exit_reason","expected_state","pass"]
PRECEDENCE=["gap","signal","time","intrabar"]

def canon(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def sha(value): return hashlib.sha256(canon(value).encode()).hexdigest()
def _s(identifier,bars,entry,exit,reason,expected,*,time=None):
 return {"id":identifier,"bars":bars,"entry":entry,"exit":exit,"side":"long","stop_offset":1.0,"target_offset":2.0,"time_exit":time,"expected_reason":reason,"expected":expected}

SCENARIOS=[
 _s("completed_next_open",[[10,10,10],[11,11,11],[12,12,12]],[False,True,False],[False,False,True],"signal",{"entry_index":1,"entry_price":11.,"exit_index":2,"exit_price":12.}),
 _s("entry_row_excluded_terminal",[[10,13,8]],[True],[True],"no_trade",None),
 _s("gap_stop_over_signal_time",[[10,10,10],[8.5,10,8]],[True,True],[False,True],"initial_stop_gap",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":8.5},time=1),
 _s("gap_target",[[10,10,10],[12.5,13,12]],[True,False],[False,False],"initial_target_gap",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":12.5}),
 _s("signal_over_time_intrabar",[[10,10,10],[10,13,8]],[True,True],[False,True],"signal",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":10.},time=1),
 _s("time_over_intrabar",[[10,10,10],[10.5,12.5,10]],[True,False],[False,False],"max_bars_held",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":10.5},time=1),
 _s("pessimistic_dual_touch",[[10,10,10],[10,12,9]],[True,False],[False,False],"initial_stop_pessimistic",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":9.}),
 _s("nonambiguous_stop",[[10,10,10],[10,11,9]],[True,False],[False,False],"initial_stop",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":9.}),
 _s("nonambiguous_target",[[10,10,10],[10,12,9.5]],[True,False],[False,False],"initial_target",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":12.}),
 _s("signal_exit",[[10,10,10],[10.5,11,10]],[True,False],[False,True],"signal",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":10.5}),
 _s("time_exit",[[10,10,10],[10.5,11,10]],[True,False],[False,False],"max_bars_held",{"entry_index":0,"entry_price":10.,"exit_index":1,"exit_price":10.5},time=1),
 _s("terminal_no_trade",[[10,10,10],[11,11,11]],[False,False],[False,True],"no_trade",None),
]

def scenario_identity(s): return sha({k:s[k] for k in ("id","bars","entry","exit","side","stop_offset","target_offset","time_exit","expected_reason","expected")})
def plan_identity(): return sha({"version":VERSION,"ordering":[s["id"] for s in SCENARIOS],"scenarios":[scenario_identity(s) for s in SCENARIOS],"schema":SCHEMA,"reasons":["no_trade","signal","max_bars_held","initial_stop_gap","initial_target_gap","initial_stop_pessimistic","initial_stop","initial_target"],"precedence":PRECEDENCE})

def materialize(s,root):
 root=Path(root); root.mkdir(parents=True,exist_ok=True); ts=[f"2040.01.01 00:{i:02d}" for i in range(len(s["bars"]))]
 pq.write_table(pa.table({"timestamp":ts,"open":pa.array([float(x[0]) for x in s["bars"]],type=pa.float64()),"high":pa.array([float(x[1]) for x in s["bars"]],type=pa.float64()),"low":pa.array([float(x[2]) for x in s["bars"]],type=pa.float64())}),root/"market.parquet")
 pq.write_table(pa.table({"timestamp":ts,"entry_intent":pa.array(s["entry"],type=pa.bool_())}),root/"entry.parquet")
 pq.write_table(pa.table({"timestamp":ts,"exit_intent":pa.array(s["exit"],type=pa.bool_())}),root/"exit.parquet")
 cfg={"schema_version":1,"side":"long","price_column":"open","entry_column":"entry_intent","exit_column":"exit_intent","position_policy":"one_at_a_time","terminal_policy":"leave_open","initial_bracket":{"model":"fixed_price_offsets_v1","stop_offset":s["stop_offset"],"target_offset":s["target_offset"],"output_path":str(root/"brackets.parquet")},"initial_bracket_execution":{"model":"ohlc_pessimistic_gap_v1","event_output_path":str(root/"bracket_events.parquet")}}
 if s["time_exit"] is not None: cfg["time_exit"]={"model":"max_bars_held_v1","max_bars_held":s["time_exit"],"event_output_path":str(root/"time_events.parquet")}
 task={"task_version":1,"task_type":"simulate_market_v1","market_path":str(root/"market.parquet"),"entry_intent_path":str(root/"entry.parquet"),"exit_intent_path":str(root/"exit.parquet"),"output_path":str(root/"trades.parquet"),"config":cfg}
 (root/"task.json").write_text(canon(task)+"\n"); return task

def _reason(root,summary):
 b=Path(root)/"bracket_events.parquet"; t=Path(root)/"time_events.parquet"
 if b.exists() and pq.read_table(b).num_rows: return pq.read_table(b).to_pylist()[0]["exit_reason"]
 if t.exists() and pq.read_table(t).num_rows: return "max_bars_held"
 return "signal" if summary["trades_closed"] else "no_trade"

def run_one(s,binary,root):
 task=materialize(s,root); p=subprocess.run([str(binary),str(Path(root)/"task.json")],capture_output=True,text=True); assert p.returncode==0,p.stderr
 summary=json.loads(p.stdout); rows=pq.read_table(task["output_path"]).to_pylist(); reason=_reason(root,summary)
 expected=s["expected"]; assert reason==s["expected_reason"],(s["id"],reason)
 if expected is None: assert rows==[],(s["id"],rows)
 else:
  assert len(rows)==1; r=rows[0]
  for key,value in expected.items(): assert r[key]==value,(s["id"],key,r[key],value)
 ledger=None if not rows else {"entry_index":rows[0]["entry_index"],"entry_price":rows[0]["entry_price"],"exit_index":rows[0]["exit_index"],"exit_price":rows[0]["exit_price"],"side":rows[0]["side"],"bars_held":rows[0]["bars_held"],"gross_pnl_per_unit":rows[0]["gross_pnl_per_unit"]}
 return {"scenario_id":s["id"],"scenario_identity":scenario_identity(s),"task_fixture":s,"task_fixture_identity":scenario_identity(s),"input_bar_identity":sha(s["bars"]),"signal_intention_identity":sha({"entry":s["entry"],"exit":s["exit"]}),"task_output_semantic_identity":summary["simulator_semantic_identity"],"simulator_contract_version":"simulate_market_v1","expected_trade_ledger_rows":[] if ledger is None else [ledger],"exit_reason":reason,"precedence":PRECEDENCE,"expected_null_no_trade":ledger is None,"isolated_scenario_identity":sha({"scenario":scenario_identity(s),"ledger":ledger,"reason":reason,"summary":summary["simulator_semantic_identity"]})}

def evidence(binary):
 with tempfile.TemporaryDirectory(prefix="nora-phase2-execution-") as d: records=[run_one(s,binary,Path(d)/s["id"]) for s in SCENARIOS]
 return {"schema_version":VERSION,"execution_csv_schema":SCHEMA,"precedence_contract":PRECEDENCE,"scenario_order":[s["id"] for s in SCENARIOS],"scenarios":records,"execution_plan_identity":plan_identity()}
