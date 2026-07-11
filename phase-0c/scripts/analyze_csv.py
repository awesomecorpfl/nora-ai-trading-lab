#!/usr/bin/env python3
"""Bounded Phase-0C CSV quality/alignment analyzer; not Phase-1 ingestion."""
import argparse,csv,datetime as dt,hashlib,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--kind',choices=['m1','tick','spec'],required=True);p.add_argument('--time');p.add_argument('--open');p.add_argument('--high');p.add_argument('--low');p.add_argument('--close');p.add_argument('--bid');p.add_argument('--ask');p.add_argument('--delimiter',default=',');p.add_argument('--out',required=True);a=p.parse_args(); rows=list(csv.DictReader(open(a.path,newline=''),delimiter=a.delimiter)); times=[r.get(a.time,'') for r in rows] if a.time else []
 out={'kind':a.kind,'file':Path(a.path).name,'sha256':hashlib.sha256(Path(a.path).read_bytes()).hexdigest(),'rows':len(rows),'first_timestamp':times[0] if times else None,'last_timestamp':times[-1] if times else None,'duplicate_timestamps':len(times)-len(set(times)) if times else None,'out_of_order':sum(times[i]<times[i-1] for i in range(1,len(times))) if times else None,'columns':list(rows[0]) if rows else []}
 if a.kind=='m1' and rows:
  bad=sum(float(r[a.low])>min(float(r[a.open]),float(r[a.close]),float(r[a.high])) or float(r[a.high])<max(float(r[a.open]),float(r[a.close]),float(r[a.low])) for r in rows);out['malformed_ohlc']=bad
 if a.kind=='tick' and rows and a.bid and a.ask: out['crossed_quotes']=sum(float(r[a.bid])>float(r[a.ask]) for r in rows)
 Path(a.out).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
