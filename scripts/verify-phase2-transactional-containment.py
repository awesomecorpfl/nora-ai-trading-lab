#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab.phase2_transactional_containment_verifier import verify
p=argparse.ArgumentParser(); p.add_argument("artifact"); p.add_argument("--root",default="."); a=p.parse_args()
try: print(json.dumps(verify(Path(a.artifact),Path(a.root).resolve()),sort_keys=True)); sys.exit(0)
except Exception as e: print(json.dumps({"verdict":"FAIL","error":str(e)},sort_keys=True)); sys.exit(1)
