#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab.phase2_transactional_containment import ContractError, build_candidate, canonical, publish, verify_document

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    for name in ("verify","publish"):
        q=sub.add_parser(name); q.add_argument("--root",default=".")
        if name == "verify": q.add_argument("--timestamp",default="2026-07-17T00:00:00Z"); q.add_argument("--publication-id",default="read-only")
        else: q.add_argument("--publication-id",required=True); q.add_argument("--timestamp",required=True)
    a=p.parse_args(); root=Path(a.root).resolve()
    try:
        if a.command == "verify":
            d=build_candidate(root,a.timestamp,a.publication_id); print(json.dumps({"candidate":d,"verdict":"PASS"},sort_keys=True)); return 0
        print(publish(root,a.publication_id,a.timestamp)); return 0
    except Exception as e:
        print(json.dumps({"verdict":"FAIL","error":str(e)},sort_keys=True)); return 1
if __name__ == "__main__": sys.exit(main())
