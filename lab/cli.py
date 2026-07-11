import argparse, json, os, time
from pathlib import Path
from .core import State, ingest_csv, validate_contract, workflow

def emit(value, args): print(json.dumps(value,default=dict,indent=2 if args.json else None) if args.json else value)
def state(args): return State(args.root)
def main():
 p=argparse.ArgumentParser(prog="lab"); p.add_argument("--root",default="."); p.add_argument("--json",action="store_true"); sub=p.add_subparsers(dest="cmd",required=True)
 e=sub.add_parser("experiment"); es=e.add_subparsers(dest="action",required=True)
 for a in ("create","launch","resume","show","status"):
  q=es.add_parser(a); q.add_argument("name")
 t=sub.add_parser("task"); t.add_argument("action",choices=["list"]); t.add_argument("experiment")
 for noun in ("event","artifact"):
  q=sub.add_parser(noun); q.add_argument("action",choices=["list"]); q.add_argument("experiment")
 q=sub.add_parser("protocol"); q.add_argument("action",choices=["show"]); q.add_argument("id")
 q=sub.add_parser("provenance"); q.add_argument("action",choices=["show"]); q.add_argument("id")
 ing=sub.add_parser("ingest"); ins=ing.add_subparsers(dest="action",required=True); q=ins.add_parser("validate"); q.add_argument("contract")
 sup=sub.add_parser("supervisor"); sup.add_argument("--once",action="store_true")
 a=p.parse_args(); s=state(a)
 if a.cmd=="experiment":
  protocol=s.protocol("phase1-dummy",{"version":1,"purpose":"foundation"}); eid=s.experiment(a.name,protocol,{"workflow":"dummy-v1"})
  if a.action in {"launch","resume"}: workflow(s,a.root,eid)
  if a.action in {"show","status"}: emit(dict(s.conn.execute("SELECT * FROM experiments WHERE id=?",(eid,)).fetchone()),a)
  else: emit({"experiment":eid,"action":a.action},a)
 elif a.cmd in {"task","event","artifact"}:
  table={"task":"tasks","event":"events","artifact":"artifacts"}[a.cmd]; col="experiment_id"; emit([dict(x) for x in s.conn.execute(f"SELECT * FROM {table} WHERE {col}=? ORDER BY 1",(a.experiment,))],a)
 elif a.cmd=="protocol": emit(dict(s.conn.execute("SELECT * FROM protocols WHERE id=?",(a.id,)).fetchone()),a)
 elif a.cmd=="provenance": emit(dict(s.conn.execute("SELECT * FROM provenance WHERE id=?",(a.id,)).fetchone()),a)
 elif a.cmd=="ingest": emit(validate_contract(json.loads(Path(a.contract).read_text())),a)
 else:
  while True:
   s.reconcile()
   if a.once: break
   time.sleep(5)
if __name__=="__main__": main()
