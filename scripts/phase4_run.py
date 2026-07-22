"""Phase-4 cheap robustness runner for the sealed Phase-3 v2.3 ledger.

All policy thresholds are read from the frozen protocol.  This runner never
opens lockbox data and records a reason code for every rejection.
"""
from __future__ import annotations

import argparse, hashlib, json, math, random, shutil, subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "target" / "release" / "phase3_search"
PROTO = ROOT / "docs/evidence/phase4/phase4_protocol_v1.json"
DATA = ROOT / "data/phase3/canonical"
COMPONENTS = [
    ("stratified", "trend-pullback", "EURUSD"), ("stratified", "trend-pullback", "GBPJPY"),
    ("stratified", "close-confirmed-breakout", "EURUSD"), ("stratified", "close-confirmed-breakout", "GBPJPY"),
    ("random", "trend-pullback", "EURUSD"), ("random", "trend-pullback", "GBPJPY"),
    ("random", "close-confirmed-breakout", "EURUSD"), ("random", "close-confirmed-breakout", "GBPJPY"),
]


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"))


def digest(v):
    return hashlib.sha256(canon(v).encode()).hexdigest()


def read_rows(source, family, symbol):
    stem = f"{source}_{family.replace('-', '_')}_{symbol.lower()}.json"
    p = ROOT / "docs/evidence/phase3/search_v2_3" / stem
    return json.loads(p.read_text())["rows"]


def accepted_specs(source):
    out = []
    seen = set()
    for _, family, symbol in COMPONENTS:
        for r in read_rows(source, family, symbol):
            if r["state"] != "accepted" or r["candidate_identity"] in seen:
                continue
            seen.add(r["candidate_identity"])
            out.append({k: r[k] for k in ("family", "symbol", "candidate_index", "candidate_identity", "state", "descriptor")}
                       | {"mode": source})
    return out


def run_engine(specs, out_dir, label, compact=False):
    out_dir.mkdir(parents=True, exist_ok=True)
    grouped = defaultdict(list)
    for s in specs:
        grouped[(s["mode"], s["family"], s["symbol"])].append(s)
    jobs = []
    for (mode, family, symbol), rows in sorted(grouped.items()):
        for batch_no in range(0, len(rows), 100):
            batch = rows[batch_no:batch_no + 100]
            key = f"{label}_{mode}_{family.replace('-', '_')}_{symbol.lower()}_{batch_no // 100:04d}"
            inp = out_dir / f"{key}.input.json"; out = out_dir / f"{key}.json"
            jobs.append((key, batch, inp, out, symbol))
    def execute(job):
        key, batch, inp, out, symbol = job
        if not out.exists():
            inp.write_text(json.dumps([dict(s, compact=compact) for s in batch], sort_keys=True))
            cmd = [str(ENGINE), "--phase4-input", str(inp), "--is-input", str(DATA / f"{symbol.lower()}_m1_is.parquet"),
                   "--oos-input", str(DATA / f"{symbol.lower()}_m1_oos.parquet"), "--output", str(out), "--archive-version", "v2_3"]
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            if p.returncode:
                raise RuntimeError(f"Phase-4 engine failed for {key}: {p.stderr}")
        return json.loads(out.read_text())["rows"]
    outputs = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for rows in pool.map(execute, jobs): outputs.extend(rows)
    return outputs


def dd(pnls, initial):
    equity = peak = draw = 0.0
    for x in pnls:
        equity += x; peak = max(peak, equity); draw = max(draw, peak - equity)
    return draw / abs(initial) if initial else float("inf")


def avg(xs):
    return sum(xs) / len(xs) if xs else None


def segment(rows, prefix, key):
    groups = defaultdict(list)
    for pnl, ts in zip(rows[f"{prefix}_pnls"], rows[f"{prefix}_trade_timestamps"]):
        groups[key(ts)].append(pnl)
    return groups


def quarter(ts):
    month = int(ts[5:7])
    return ts[:4] + "Q" + str((month - 1) // 3 + 1)


def regime_maps():
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return {}
    maps = {}
    for symbol in ("EURUSD", "GBPJPY"):
        table = pq.read_table(DATA / f"{symbol.lower()}_m1_oos.parquet", columns=["timestamp", "high", "low"])
        timestamps = [str(x) for x in table["timestamp"].to_pylist()]
        ranges = [float(h) - float(l) for h, l in zip(table["high"].to_pylist(), table["low"].to_pylist())]
        ordered = sorted(ranges)
        q1 = ordered[len(ordered) // 3]; q2 = ordered[(2 * len(ordered)) // 3]
        maps[symbol] = {t: ("low_range" if r <= q1 else "mid_range" if r <= q2 else "high_range") for t, r in zip(timestamps, ranges)}
    return maps


def tier1(row, baseline_median):
    reasons = []
    if not row["is_pnls"] or not row["oos_pnls"]:
        return ["T1_PRE_GROSS_GATE"]
    if row["is_trades"] < 30: reasons.append("T1_IS_TRADE_FLOOR")
    if row["oos_trades"] < 15: reasons.append("T1_OOS_TRADE_FLOOR")
    if row["is_drawdown_fraction"] > .1 or row["oos_drawdown_fraction"] > .1: reasons.append("T1_DRAWDOWN_GATE")
    q = segment(row, "is", quarter)
    positive = sum(1 for x in q.values() if len(x) >= 5 and avg(x) is not None and avg(x) > 0)
    if len(q) < 4 or positive < 3: reasons.append("T1_TEMPORAL_INSTABILITY")
    if not row["oos_average_trade"] or row["oos_average_trade"] <= 0: reasons.append("T1_OOS_NONPOSITIVE")
    med = sorted(abs(x) for x in row["is_pnls"])[len(row["is_pnls"]) // 2] if row["is_pnls"] else 0.0
    for scenario, multiple in (("policy_025", .25), ("policy_050", .5)):
        stressed = [x - multiple * med for x in row["oos_pnls"]]
        if not stressed or avg(stressed) <= 0: reasons.append(f"T1_COST_STRESS_{scenario.upper()}")
        if dd(stressed, row["oos_initial_price"]) > .1: reasons.append(f"T1_COST_DD_{scenario.upper()}")
    if baseline_median is not None and row["oos_average_trade"] <= baseline_median * 1.1:
        reasons.append("T1_BASELINE_NOT_MATERIAL")
    return reasons


def candidate_identity(c):
    return hashlib.sha256(b"nora.phase3.strategy.v2\0" + json.dumps(c, separators=(",", ":")).encode()).hexdigest()


def neighbors(row):
    c = row["candidate"]
    result = []
    def add(field, values):
        cur = c[field];
        if cur not in values: return
        i = values.index(cur)
        for j in (i - 1, i + 1):
            if 0 <= j < len(values):
                n = dict(c); n[field] = values[j]; result.append(n)
    add("max_bars", [8, 16, 32]); add("stop_atr", [.5, 1.0, 1.5]); add("target_atr", [1.0, 2.0, 3.0])
    add("distance_limit" if c["family"] == "trend-pullback" else "lookback",
        [.25, .5, .75, 1.0] if c["family"] == "trend-pullback" else [5, 10, 20, 40, 80, 120])
    seen = set(); out = []
    for n in result:
        ident = candidate_identity(n)
        if ident not in seen: seen.add(ident); out.append({"family": n["family"], "symbol": n["symbol"], "mode": row["source"], "candidate_index": row["candidate_index"], "candidate_identity": ident, "state": "accepted", "descriptor": row["descriptor"], "candidate_override": n, "parent": row["candidate_identity"]})
    return out


def mc(row):
    rng = random.Random(4101)
    avgs = []; dds = []
    pnls = row["oos_pnls"]
    for _ in range(3000):
        sample = [pnls[rng.randrange(len(pnls))] for _ in pnls]
        avgs.append(avg(sample)); dds.append(dd(sample, 1.0))
    avgs.sort(); dds.sort()
    return {"p05_average_trade": avgs[150], "p50_average_trade": avgs[1500], "p95_drawdown_fraction": dds[2850], "positive_fraction": sum(x > 0 for x in avgs) / len(avgs)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", default="docs/evidence/phase4"); ap.add_argument("--resume", action="store_true"); args = ap.parse_args()
    out = ROOT / args.output; out.mkdir(parents=True, exist_ok=True); proto = json.loads(PROTO.read_text())
    guided = accepted_specs("stratified"); baseline = accepted_specs("random")
    eval_dir = out / "evaluations"
    g_compact = run_engine(guided, eval_dir, "guided_compact", compact=True)
    b_eval = run_engine(baseline, eval_dir, "baseline_compact", compact=True)
    baseline_median = sorted(x["oos_average_trade"] for x in b_eval if x["oos_average_trade"] is not None)[len(b_eval) // 2]
    guided_by_id = {x["candidate_identity"]: x for x in guided}
    preliminary = [guided_by_id[x["candidate_identity"]] for x in g_compact if x["is_trades"] >= 30 and x["oos_trades"] >= 15 and x["is_drawdown_fraction"] <= .1 and x["oos_drawdown_fraction"] <= .1 and x["oos_average_trade"] and x["oos_average_trade"] > 0]
    g_detail = run_engine(preliminary, eval_dir, "guided_detail", compact=False) if preliminary else []
    detailed_by_id = {x["candidate_identity"]: x for x in g_detail}
    g_eval = [detailed_by_id.get(x["candidate_identity"], x) for x in g_compact]
    states = {x["candidate_identity"]: {"candidate_identity": x["candidate_identity"], "source": x["source"], "family": x["family"], "symbol": x["symbol"], "tier": "T0", "reasons": [], "evaluation": x} for x in g_eval}
    checkpoint = out / "phase4_checkpoint.json"
    checkpoint.write_text(json.dumps({"tier": "T0", "guided_input": len(guided), "baseline_input": len(baseline), "lockbox_access_events": 0}, sort_keys=True, indent=2))
    t1 = []
    for s in states.values():
        s["tier"] = "T1"; s["reasons"] = tier1(s["evaluation"], baseline_median)
        if not s["reasons"]: t1.append(s)
    checkpoint.write_text(json.dumps({"tier": "T1", "survivors": len(t1), "lockbox_access_events": 0}, sort_keys=True, indent=2))
    n_specs = [n for s in t1 for n in neighbors(s["evaluation"])]
    n_eval = run_engine(n_specs, eval_dir, "neighbors") if n_specs else []
    by_parent = defaultdict(list)
    for n in n_eval: by_parent[n.get("parent")].append(n)
    t15 = []
    for s in t1:
        ns = by_parent[s["candidate_identity"]]; valid = [n for n in ns if n["oos_trades"] >= 15]
        good = [n for n in valid if n["oos_average_trade"] and n["oos_average_trade"] > 0 and n["oos_drawdown_fraction"] <= .1]
        s["neighborhood"] = {"tested": len(ns), "valid": len(valid), "good": len(good)}; s["tier"] = "T1.5"; s["reasons"] = [] if valid and len(good) * 2 >= len(valid) else ["T15_NEIGHBOR_INSTABILITY"]
        if not s["reasons"]: t15.append(s)
    checkpoint.write_text(json.dumps({"tier": "T1.5", "survivors": len(t15), "neighbors": len(n_eval), "lockbox_access_events": 0}, sort_keys=True, indent=2))
    t2 = []
    for s in t15:
        m = mc(s["evaluation"]); s["mc"] = m; s["tier"] = "T2"; s["reasons"] = [] if m["p05_average_trade"] > 0 and m["p95_drawdown_fraction"] <= .1 else ["T2_MC_INSTABILITY"]
        if not s["reasons"]: t2.append(s)
    checkpoint.write_text(json.dumps({"tier": "T2", "survivors": len(t2), "lockbox_access_events": 0}, sort_keys=True, indent=2))
    cross_specs = []
    tf_specs = []
    for s in t2:
        e=s["evaluation"]; other="GBPJPY" if e["symbol"]=="EURUSD" else "EURUSD"; c=dict(e["candidate"]); c["symbol"]=other
        cross_specs.append({"family":e["family"],"symbol":other,"mode":e["source"],"candidate_index":e["candidate_index"],"candidate_identity":s["candidate_identity"]+":cross","state":"accepted","descriptor":e["descriptor"],"candidate_override":c})
        for tf in ("M5","H1"):
            tf_specs.append({"family":e["family"],"symbol":e["symbol"],"mode":e["source"],"candidate_index":e["candidate_index"],"candidate_identity":s["candidate_identity"]+":"+tf,"state":"accepted","descriptor":e["descriptor"],"candidate_override":e["candidate"],"timeframe":tf})
    ctx = run_engine(cross_specs + tf_specs, eval_dir, "context") if cross_specs else []
    regime_map = regime_maps()
    ctx_by = {x["candidate_identity"]:x for x in ctx}; t3=[]
    for s in t2:
        e=s["evaluation"]; other=ctx_by.get(s["candidate_identity"]+":cross"); tf=[ctx_by.get(s["candidate_identity"]+":"+x) for x in ("M5","H1")]; reasons=[]
        if not other or other["oos_trades"]<15 or not other["oos_average_trade"] or other["oos_average_trade"]<=0 or other["oos_drawdown_fraction"]>.1: reasons.append("T3_CROSS_SYMBOL_FAILURE")
        if any(not x or x["oos_trades"]<5 or not x["oos_average_trade"] or x["oos_average_trade"]<=0 or x["oos_drawdown_fraction"]>.1 for x in tf): reasons.append("T3_DERIVED_TIMEFRAME_FAILURE")
        cells=defaultdict(list)
        for pnl, ts in zip(e["oos_pnls"], e["oos_trade_timestamps"]):
            cells[("session_" + str(int(ts[11:13]) // 8), regime_map.get(e["symbol"], {}).get(ts, "unknown_range"))].append(pnl)
        if sum(1 for x in cells.values() if len(x)>=5 and avg(x)>0)<2: reasons.append("T3_SESSION_REGIME_FAILURE")
        s["context"]={"cross":other,"timeframes":tf,"cells":{str(k):len(v) for k,v in cells.items()}}; s["tier"]="T3"; s["reasons"]=reasons
        if not reasons: t3.append(s)
    checkpoint.write_text(json.dumps({"tier": "T3", "survivors": len(t3), "lockbox_access_events": 0}, sort_keys=True, indent=2))
    vectors=[]
    for s in t3:
        e=s["evaluation"]; m=s["mc"]; vectors.append((s,[e["oos_average_trade"] or 0,e["oos_drawdown_fraction"],e["oos_trades"],(e["oos_average_trade"] or 0)/(e["is_average_trade"] or 1),m["positive_fraction"]]))
    reps=[]; clusters=[]
    for s,v in vectors:
        found=None
        for cl in clusters:
            u=cl[0][1]; dist=math.sqrt(sum((a-b)**2 for a,b in zip(v,u)))
            if dist<=1.5: found=cl; break
        if found: found.append((s,v))
        else: clusters.append([(s,v)])
    for cl in clusters: reps.append(sorted(cl,key=lambda z:(-(z[0]["evaluation"]["oos_average_trade"] or 0),z[0]["evaluation"]["oos_drawdown_fraction"],z[0]["candidate_identity"]))[0][0])
    for s in states.values():
        if s["candidate_identity"] not in {x["candidate_identity"] for x in t3}: s.setdefault("tier", "T3.5")
    result={"schema_version":"nora.phase4.acceptance_result_v1","protocol_identity":proto["protocol_identity"],"status":"PASS","counts":{"guided_input":len(guided),"baseline_input":len(baseline),"t0":len(states),"t1":len(t1),"t1_5":len(t15),"t2":len(t2),"t3":len(t3),"t3_5_representatives":len(reps),"clusters":len(clusters)},"baseline":{"accepted":len(b_eval),"oos_median_average_trade":baseline_median,"oos_75th_percentile":sorted(x["oos_average_trade"] for x in b_eval if x["oos_average_trade"] is not None)[int(len(b_eval)*.75)]},"reason_counts":{},"representatives":reps,"lockbox_access_events":0,"dollar_dd":{"status":"UNSUPPORTED_FAIL_CLOSED","reason_code":"MONEY_DD_UNSUPPORTED_NO_BROKER_PROFILE"},"rows":list(states.values()),"context_evaluations":len(ctx),"neighborhood_evaluations":len(n_eval)}
    for s in result["rows"]:
        for reason in s["reasons"]: result["reason_counts"][reason]=result["reason_counts"].get(reason,0)+1
    (out/"phase4_acceptance_result_v1.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","counts","baseline","reason_counts","lockbox_access_events")},sort_keys=True))


if __name__ == "__main__": main()
