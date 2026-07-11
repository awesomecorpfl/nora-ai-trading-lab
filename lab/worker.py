import json, sys
from pathlib import Path

spec=json.loads(Path(sys.argv[1]).read_text()); out=Path(sys.argv[2])
if spec["kind"]=="shard": result={"value":spec["value"],"checksum":spec["value"]*17}
elif spec["kind"]=="transform": result={"parent":spec["parent"],"value":len(spec["parent"]),"checksum":sum(map(ord,spec["parent"]))}
else: result={"parents":sorted(spec["parents"]),"checksum":sum(sum(map(ord,p)) for p in spec["parents"])}
(out/"result.json").write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
