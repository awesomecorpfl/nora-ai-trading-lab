"""Durable Phase 1 state, contracts, ingestion, and dummy workflow."""
from __future__ import annotations

import csv, hashlib, json, os, sqlite3, subprocess, sys, tempfile
from datetime import UTC, datetime
from pathlib import Path

TERMINAL = {"succeeded", "failed", "cancelled"}
ALLOWED = {"pending": {"running", "cancelled"}, "running": {"succeeded", "failed", "interrupted"}, "interrupted": {"pending", "cancelled"}, "failed": {"pending", "cancelled"}, "succeeded": set(), "cancelled": set()}
REQUIRED_CONTRACT = {"provider", "acquisition_tool", "source_symbol", "project_symbol", "source_timestamp_semantics", "bar_timestamp_semantics", "timezone_identity", "dst_regime", "session_clock", "strategy_clock", "conversion_history"}

def now(): return datetime.now(UTC).isoformat()
def canon(value): return json.dumps(value, sort_keys=True, separators=(",", ":"))
def digest(value): return hashlib.sha256(value if isinstance(value, bytes) else canon(value).encode()).hexdigest()
def ident(kind, value): return f"{kind}_{digest(value)[:16]}"
def file_hash(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

class State:
    def __init__(self, root):
        self.root=Path(root)/"state"; self.root.mkdir(parents=True,exist_ok=True); self.db=self.root/"state.sqlite3"; self.conn=sqlite3.connect(self.db); self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL"); self.conn.execute("PRAGMA foreign_keys=ON"); self.migrate(); self.reconcile()
    def migrate(self):
        done={r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")}
        if not done:
            sql=(Path(__file__).parent/"migrations/001_initial.sql").read_text(); self.conn.executescript(sql); self.conn.execute("INSERT INTO schema_migrations VALUES(1,?)",(now(),)); self.conn.commit()
    def event(self, typ, severity="info", *, experiment=None, stage=None, task=None, payload=None, key=None):
        self.conn.execute("INSERT OR IGNORE INTO events(event_key,timestamp,type,severity,experiment_id,stage_id,task_id,payload_json) VALUES(?,?,?,?,?,?,?,?)",(key,now(),typ,severity,experiment,stage,task,canon(payload or {}))); self.conn.commit()
    def reconcile(self):
        rows=self.conn.execute("SELECT id FROM tasks WHERE status='running'").fetchall()
        for row in rows: self.transition(row["id"],"interrupted",{"reason":"controller_restart"})
    def close(self): self.conn.close()
    def protocol(self, name, content):
        h=digest(content); row=self.conn.execute("SELECT id FROM protocols WHERE content_hash=?",(h,)).fetchone()
        if row:return row["id"]
        pid=ident("protocol",content); self.conn.execute("INSERT INTO protocols VALUES(?,?,?,?,?)",(pid,name,canon(content),h,now())); self.conn.commit(); self.event("protocol_registered",payload={"protocol":pid},key=f"protocol:{pid}"); return pid
    def experiment(self,name,protocol_id,config):
        key={"name":name,"protocol":protocol_id,"config":config}; eid=ident("experiment",key); row=self.conn.execute("SELECT id FROM experiments WHERE id=?",(eid,)).fetchone()
        if not row:self.conn.execute("INSERT INTO experiments VALUES(?,?,?,?,?,?,?)",(eid,name,protocol_id,canon(config),digest(config),"created",now())); self.conn.commit(); self.event("experiment_created",experiment=eid,key=f"experiment:{eid}")
        return eid
    def stage(self,eid,name,ordinal):
        sid=ident("stage",{"experiment":eid,"name":name}); self.conn.execute("INSERT OR IGNORE INTO stages VALUES(?,?,?,?,?)",(sid,eid,name,ordinal,"pending")); self.conn.commit(); return sid
    def task(self,eid,sid,spec):
        h=digest(spec); row=self.conn.execute("SELECT id FROM tasks WHERE experiment_id=? AND stage_id=? AND spec_hash=?",(eid,sid,h)).fetchone()
        if row:return row["id"]
        tid=ident("task",{"experiment":eid,"stage":sid,"spec":spec}); self.conn.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?)",(tid,eid,sid,canon(spec),h,"pending",None,None,now(),now())); self.conn.commit(); self.event("task_created",experiment=eid,stage=sid,task=tid,key=f"task:{tid}"); return tid
    def transition(self,tid,target,detail=None):
        row=self.conn.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone(); old=row["status"]
        if old==target:return False
        if target not in ALLOWED[old]: raise ValueError(f"invalid transition {old}->{target}")
        self.conn.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?",(target,now(),tid))
        attempt=self.conn.execute("SELECT COALESCE(MAX(attempt),0) FROM task_attempts WHERE task_id=?",(tid,)).fetchone()[0]
        if target=="running": self.conn.execute("INSERT INTO task_attempts(task_id,attempt,state,started_at,detail_json) VALUES(?,?,?,?,?)",(tid,attempt+1,target,now(),canon(detail or {})))
        else:self.conn.execute("UPDATE task_attempts SET state=?,ended_at=?,detail_json=? WHERE task_id=? AND attempt=?",(target,now(),canon(detail or {}),tid,attempt))
        self.conn.commit(); self.event("task_"+target,experiment=row["experiment_id"],stage=row["stage_id"],task=tid,payload=detail,key=f"transition:{tid}:{target}:{attempt}"); return True
    def publish(self,tid,path,metadata):
        path=Path(path)
        if not path.is_dir() or path.name.endswith(".partial") or not (path/"result.json").is_file(): raise ValueError("only complete published directories may be registered")
        h=file_hash(path/"result.json"); row=self.conn.execute("SELECT id FROM artifacts WHERE path=?",(str(path),)).fetchone()
        task=self.conn.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
        aid=ident("artifact",{"task":tid,"hash":h})
        if not row:self.conn.execute("INSERT INTO artifacts VALUES(?,?,?,?,?,?,?,?)",(aid,task["experiment_id"],tid,str(path),h,"complete",canon(metadata),now())); self.conn.commit()
        self.conn.execute("UPDATE tasks SET artifact_path=?,result_hash=?,updated_at=? WHERE id=?",(str(path),h,now(),tid)); self.conn.commit()
        record={"artifact":aid,"task":tid,"experiment":task["experiment_id"],"protocol":self.conn.execute("SELECT protocol_id FROM experiments WHERE id=?",(task["experiment_id"],)).fetchone()[0],"content_hash":h,"parents":metadata.get("parents",[])}
        ph=digest(record); self.conn.execute("INSERT OR IGNORE INTO provenance VALUES(?,?,?,?,?,?,?,?)",(ident("prov",record),aid,tid,task["experiment_id"],canon(record["parents"]),canon(record),ph,now())); self.conn.commit(); return aid
    def checkpoint(self,eid,sid,tid,state):
        h=digest(state); self.conn.execute("INSERT OR IGNORE INTO checkpoints VALUES(?,?,?,?,?,?,?)",(ident("checkpoint",{"task":tid,"hash":h}),eid,sid,tid,canon(state),h,now())); self.conn.commit()

def validate_contract(contract):
    missing=REQUIRED_CONTRACT-set(contract)
    if missing: raise ValueError("missing contract fields: "+", ".join(sorted(missing)))
    history=contract["conversion_history"]
    if not isinstance(history,list): raise ValueError("conversion_history must be a list")
    targets=[x.get("target") for x in history if isinstance(x,dict)]
    if len(targets)!=len(set(targets)): raise ValueError("double conversion: a target clock appears more than once")
    if contract["timezone_identity"].startswith("UTC") and contract["strategy_clock"]!=contract["timezone_identity"] and not history: raise ValueError("clock mismatch requires explicit conversion provenance")
    return contract

def ingest_csv(source, destination, mapping, contract):
    validate_contract(contract); source=Path(source); rows=[]; seen=set(); previous=None
    with source.open(newline="") as f:
        for row in csv.DictReader(f):
            stamp=(row[mapping["date"]]+" "+row[mapping["time"]]) if "date" in mapping else row[mapping["timestamp"]]
            if stamp in seen: raise ValueError("duplicate timestamp")
            seen.add(stamp); parsed=datetime.fromisoformat(stamp.replace(".","-",2)) if "T" in stamp else datetime.strptime(stamp, mapping.get("timestamp_format","%Y.%m.%d %H:%M"))
            if previous and parsed<=previous: raise ValueError("non-monotonic timestamp")
            previous=parsed; o,h,l,c=(float(row[mapping[x]]) for x in ("open","high","low","close"))
            if l>min(o,h,c) or h<max(o,l,c): raise ValueError("malformed OHLC")
            rows.append({"timestamp":stamp,"open":o,"high":h,"low":l,"close":c,"volume":float(row[mapping["volume"]]) if mapping.get("volume") else None,"spread":float(row[mapping["spread"]]) if mapping.get("spread") else None})
    import pyarrow as pa, pyarrow.parquet as pq
    meta={b"nora.contract":canon(contract).encode(),b"nora.source_sha256":file_hash(source).encode(),b"nora.timeframe":mapping.get("timeframe","M1").encode()}
    table=pa.Table.from_pylist(rows).replace_schema_metadata(meta); destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True); pq.write_table(table,destination)
    return {"rows":len(rows),"first_timestamp":rows[0]["timestamp"],"last_timestamp":rows[-1]["timestamp"],"file_hash":file_hash(destination),"source_hash":file_hash(source)}

def run_task(state, root, tid, interrupt=False):
    task=state.conn.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
    if task["status"]=="succeeded": return task["result_hash"]
    if task["status"] in {"interrupted","failed"}: state.transition(tid,"pending",{"reason":"resume"})
    state.transition(tid,"running"); spec=json.loads(task["spec_json"]); out=Path(root)/"artifacts"/task["experiment_id"]/spec["stage"]/tid; partial=out.with_name(out.name+".partial")
    if out.is_dir() and (out/"result.json").is_file():
        aid=state.publish(tid,out,{"parents":spec.get("parents",[]),"spec_hash":task["spec_hash"],"recovered_existing":True}); state.transition(tid,"succeeded",{"artifact":aid,"recovered_existing":True}); return task["id"]
    partial.mkdir(parents=True,exist_ok=True)
    specfile=partial/"task.json"; specfile.write_text(canon(spec)); proc=subprocess.Popen([sys.executable,"-m","lab.worker",str(specfile),str(partial)])
    if interrupt: proc.terminate(); proc.wait(); state.transition(tid,"interrupted",{"reason":"controlled_interrupt"}); return None
    code=proc.wait()
    if code: state.transition(tid,"failed",{"exit_code":code}); return None
    os.replace(partial,out); aid=state.publish(tid,out,{"parents":spec.get("parents",[]),"spec_hash":task["spec_hash"]}); state.transition(tid,"succeeded",{"artifact":aid}); state.checkpoint(task["experiment_id"],task["stage_id"],tid,{"artifact":aid,"status":"succeeded"}); return task["id"]

def run_engine_task(state, root, tid, engine, engine_spec):
    """Run a versioned labengine task and publish only its complete artifact directory."""
    task=state.conn.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
    if task["status"]=="succeeded": return task["id"]
    if task["status"] in {"interrupted","failed"}: state.transition(tid,"pending",{"reason":"resume"})
    state.transition(tid,"running")
    out=Path(root)/"artifacts"/task["experiment_id"]/engine_spec["stage"]/tid
    partial=out.with_name(out.name+".partial"); partial.mkdir(parents=True,exist_ok=True)
    spec={k:v for k,v in engine_spec.items() if k!="stage"}
    if spec.get("task_type")=="aggregate_m1": spec["output_path"]=str(partial/"derived.parquet")
    specfile=partial/"task.json"; specfile.write_text(canon(spec))
    proc=subprocess.run([str(engine),str(specfile)],capture_output=True,text=True)
    try: summary=json.loads(proc.stdout) if proc.stdout else None
    except json.JSONDecodeError: summary=None
    expected=partial/"derived.parquet" if spec.get("task_type")=="aggregate_m1" else None
    if proc.returncode or not isinstance(summary,dict) or not summary.get("ok") or (expected and not expected.is_file()):
        state.transition(tid,"failed",{"exit_code":proc.returncode,"engine_error":proc.stderr.strip(),"summary":summary})
        return None
    (partial/"result.json").write_text(canon(summary)+"\n")
    os.replace(partial,out)
    aid=state.publish(tid,out,{"parents":engine_spec.get("parents",[]),"spec_hash":task["spec_hash"],"engine_task":spec})
    state.transition(tid,"succeeded",{"artifact":aid,"engine_task_type":spec["task_type"]})
    state.checkpoint(task["experiment_id"],task["stage_id"],tid,{"artifact":aid,"status":"succeeded"})
    return task["id"]

def workflow(state, root, eid, interrupt_task=None):
    stages=[("shards",0),("transform",1),("aggregate",2)]; sids={n:state.stage(eid,n,o) for n,o in stages}; created=[]
    for i in range(3): created.append(state.task(eid,sids["shards"],{"stage":"shards","kind":"shard","index":i,"value":i+1}))
    for tid in created: run_task(state,root,tid,tid==interrupt_task)
    done=[r for r in state.conn.execute("SELECT id,result_hash FROM tasks WHERE stage_id=? AND status='succeeded'",(sids["shards"],))]
    trans=[state.task(eid,sids["transform"],{"stage":"transform","kind":"transform","parent":r["id"],"parents":[r["id"]]}) for r in done]
    for tid in trans: run_task(state,root,tid,tid==interrupt_task)
    done=[r for r in state.conn.execute("SELECT id,result_hash FROM tasks WHERE stage_id=? AND status='succeeded'",(sids["transform"],))]
    if len(done)==3:
        aggregate=state.task(eid,sids["aggregate"],{"stage":"aggregate","kind":"aggregate","parents":[r["id"] for r in done]}); run_task(state,root,aggregate,aggregate==interrupt_task)
    return state.conn.execute("SELECT * FROM tasks WHERE experiment_id=? ORDER BY created_at",(eid,)).fetchall()
