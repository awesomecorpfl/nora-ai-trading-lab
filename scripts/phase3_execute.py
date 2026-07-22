"""Run the frozen Phase-3 population with a bounded process pool and merge evidence."""
from __future__ import annotations

import argparse, hashlib, json, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "target" / "release" / "phase3_search"
CASES = [(f, s) for f in ("trend-pullback", "close-confirmed-breakout") for s in ("EURUSD", "GBPJPY")]


def run_one(spec):
    family, symbol, mode, output, checkpoint, protocol_version = spec
    inp = ROOT / "data" / "phase3" / "canonical" / f"{symbol.lower()}_m1_is.parquet"
    if "lockbox" in str(inp).lower():
        raise RuntimeError("lockbox path entered evaluator")
    sampled, refinement = (2000, 500) if mode == "stratified" else (2500, 0)
    cmd = [str(ENGINE), "--input", str(inp), "--family", family, "--symbol", symbol, "--mode", mode,
           "--trials", "2500", "--sampled-trials", str(sampled), "--refinement-trials", str(refinement),
           "--batch-size", "250", "--checkpoint", str(checkpoint), "--output", str(output),
           "--archive-version", protocol_version]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{family}/{symbol}/{mode} failed: {result.stderr}")
    return json.loads(Path(output).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", default="docs/evidence/phase3/search"); ap.add_argument("--protocol-version", default="v1", choices=("v1", "v2")); args = ap.parse_args()
    out = ROOT / args.output; out.mkdir(parents=True, exist_ok=True)
    specs = []
    for mode in ("stratified", "random"):
        for family, symbol in CASES:
            stem = f"{mode}_{family.replace('-', '_')}_{symbol.lower()}"
        specs.append((family, symbol, mode, out / f"{stem}.json", out / f"{stem}.checkpoint.json", args.protocol_version))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_one, specs))
    grouped = {}
    for result in results: grouped.setdefault(result["mode"], []).append(result)
    merged = {"schema_version": f"nora.phase3.execution_result_{args.protocol_version}", "protocol": f"docs/evidence/phase3/phase3_protocol_{args.protocol_version}.json", "workers": 4, "batch_size": 250, "guided": {}, "matched_random_baseline": {}, "lockbox_touched": False}
    for mode, items in grouped.items():
        rows = [row for item in items for row in item["rows"]]
        accepted = [row for row in rows if row["state"] == "accepted"]
        merged["guided" if mode == "stratified" else "matched_random_baseline"] = {
            "trials": sum(x["trials"] for x in items),
            "unique_evaluated": sum(x["unique_evaluated"] for x in items),
            "duplicate_rejected": sum(x["duplicate_rejected"] for x in items),
            "accepted": len(accepted),
            "archive_cells": len({row["archive_cell"] for row in accepted}),
            "best_average_trade": max((row["average_trade"] for row in accepted if row["average_trade"] is not None), default=None),
            "distribution": {f"{x['family']}/{x['symbol']}": x["trials"] for x in items},
            "component_result_sha256": {f"{x['family']}/{x['symbol']}": digest(next(p for p in out.glob(f"{mode}_{x['family'].replace('-', '_')}_{x['symbol'].lower()}.json"))) for x in items},
        }
    minimum = 20 if args.protocol_version == "v1" else 24
    merged["coverage_assessment"] = {"declared_minimum_cells": minimum, "observed_cells": merged["guided"]["archive_cells"], "passes": merged["guided"]["archive_cells"] >= minimum}
    (out / f"phase3_execution_result_{args.protocol_version}.json").write_text(json.dumps(merged, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: merged[k] for k in ("guided", "matched_random_baseline", "coverage_assessment", "lockbox_touched")}, sort_keys=True))


if __name__ == "__main__": main()
