#!/usr/bin/env bash
set -euo pipefail
p=$(cd "$(dirname "${BASH_SOURCE[0]}")/.."&&pwd); cd "$p"; cargo build --release
out="results/$(date -u +%Y%m%dT%H%M%SZ).jsonl"; for w in 1 4 6 8 10 12; do for r in 1 2; do /usr/bin/time -f '{"workers":'$w',"repeat":'$r',"max_rss_kib":%M}' -o /tmp/time.json ./target/release/phase0b-throughput "$w" 1000 > /tmp/run.json; python3 -c 'import json; a=json.load(open("/tmp/run.json"));a.update(json.load(open("/tmp/time.json")));print(json.dumps(a))' >> "$out"; done; done; echo "$out"
