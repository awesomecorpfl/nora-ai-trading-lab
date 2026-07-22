"""Prepare the approved Phase-3 canonical datasets and immutable split records."""
from __future__ import annotations

import argparse, hashlib, json, os, shutil, stat
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "phase-0c" / "staged" / "qdm"
PROVENANCE = ROOT / "phase-0c" / "provenance"


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identity(domain: str, value) -> str:
    return hashlib.sha256((domain + "\0" + canon(value)).encode()).hexdigest()


def read_raw(path: Path):
    timestamps, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    previous = None
    with path.open(newline="") as f:
        for number, line in enumerate(f, 1):
            fields = line.rstrip("\n").split(",")
            if len(fields) != 7:
                raise ValueError(f"{path}: row {number}: expected 7 fields")
            stamp = f"{fields[0]} {fields[1]}"
            dt = datetime.strptime(stamp, "%Y.%m.%d %H:%M")
            if previous is not None and dt <= previous:
                raise ValueError(f"{path}: non-monotonic timestamp at row {number}")
            previous = dt
            values = [float(x) for x in fields[2:]]
            o, h, l, c, v = values
            if not all(map(lambda x: x == x and abs(x) != float("inf"), values)):
                raise ValueError(f"{path}: non-finite OHLCV at row {number}")
            if l > min(o, h, c) or h < max(o, l, c):
                raise ValueError(f"{path}: malformed OHLC at row {number}")
            timestamps.append(stamp); opens.append(o); highs.append(h); lows.append(l); closes.append(c); volumes.append(v)
    return timestamps, opens, highs, lows, closes, volumes


def write_parquet(path: Path, contract: dict, rows):
    ts, op, hi, lo, cl, vol = rows
    table = pa.table({
        "timestamp": pa.array(ts, type=pa.string()),
        "open": pa.array(op, type=pa.float64()),
        "high": pa.array(hi, type=pa.float64()),
        "low": pa.array(lo, type=pa.float64()),
        "close": pa.array(cl, type=pa.float64()),
        "volume": pa.array(vol, type=pa.float64()),
        "spread": pa.array([None] * len(ts), type=pa.float64()),
    })
    metadata = dict(table.schema.metadata or {})
    metadata.update({
        b"nora.contract": canon(contract).encode(),
        b"nora.source_sha256": contract["source_sha256"].encode(),
        b"nora.timeframe": b"M1",
    })
    pq.write_table(table.replace_schema_metadata(metadata), path, compression="zstd")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(ROOT / "data" / "phase3"))
    args = ap.parse_args()
    out = Path(args.output).resolve()
    canonical = out / "canonical"
    splits = out / "splits"
    lockbox = out / "lockbox"
    canonical.mkdir(parents=True, exist_ok=True); splits.mkdir(parents=True, exist_ok=True); lockbox.mkdir(parents=True, exist_ok=True)
    lockbox_identity = None
    lockbox_records = []
    dataset_records = []
    split_records = []
    for symbol in ("EURUSD", "GBPJPY"):
        raw = RAW / f"long_{symbol}-M1-No Session.csv"
        prov_path = PROVENANCE / f"{symbol}_M1_2024-2025.json"
        prov = json.loads(prov_path.read_text())
        raw_hash = sha256(raw)
        if raw_hash != prov["file_sha256"]:
            raise ValueError(f"{symbol}: raw hash does not match committed provenance")
        rows = read_raw(raw)
        if len(rows[0]) != prov["row_count"] or rows[0][0] != prov["first_timestamp"] or rows[0][-1] != prov["last_timestamp"]:
            raise ValueError(f"{symbol}: rows/endpoints do not match committed provenance")
        contract = {
            "schema_version": "nora.phase3.dataset_contract_v1",
            "provider": "Dukascopy",
            "acquisition_tool": "Quant Data Manager",
            "acquisition_tool_version": "125.2692",
            "source_symbol": symbol,
            "project_symbol": symbol,
            "timeframe": "M1",
            "source_timestamp_semantics": "UTC provider label",
            "bar_timestamp_semantics": "start-of-bar",
            "timezone_identity": "UTC",
            "dst_regime": "none in source export",
            "session_clock": "UTC source clock; session gaps preserved",
            "strategy_clock": "UTC source clock; no conversion",
            "conversion_history": [],
            "source_sha256": raw_hash,
            "source_range": ["2024-01-01", "2025-12-31"],
            "parent_provenance": str(prov_path.relative_to(ROOT)),
        }
        dataset_id = identity("nora.phase3.dataset.v1", contract)
        contract["dataset_identity"] = dataset_id
        dataset_path = canonical / f"{symbol.lower()}_m1.parquet"
        if not dataset_path.exists():
            write_parquet(dataset_path, contract, rows)
        dataset_sha = sha256(dataset_path)
        dataset_records.append({"symbol": symbol, "path": str(dataset_path.relative_to(ROOT)), "dataset_identity": dataset_id, "source_sha256": raw_hash, "parquet_sha256": dataset_sha, "rows": len(rows[0]), "contract": contract})
        dates = (("is", "2024-01-01", "2024-12-31", canonical / f"{symbol.lower()}_m1_is.parquet"), ("oos", "2025-01-01", "2025-06-30", canonical / f"{symbol.lower()}_m1_oos.parquet"), ("lockbox", "2025-07-01", "2025-12-31", lockbox / f"{symbol.lower()}_m1_lockbox.parquet"))
        for name, start, end, dest in dates:
            selected = [i for i, stamp in enumerate(rows[0]) if start <= stamp[:10].replace(".", "-") <= end]
            if not selected: raise ValueError(f"{symbol}/{name}: empty split")
            split = tuple([v[i] for i in selected] for v in rows)
            split_contract = {"schema_version": "nora.phase3.split_contract_v1", "parent_dataset_identity": dataset_id, "symbol": symbol, "timeframe": "M1", "role": name, "inclusive_date_range": [start, end], "source_timestamp_semantics": "UTC provider label", "bar_timestamp_semantics": "start-of-bar", "conversion_history": []}
            split_id = identity("nora.phase3.split.v1", split_contract); split_contract["split_identity"] = split_id
            if name != "lockbox":
                if not dest.exists(): write_parquet(dest, {**contract, **split_contract, "source_sha256": raw_hash}, split)
            else:
                if not dest.exists(): write_parquet(dest, {**contract, **split_contract, "source_sha256": raw_hash}, split)
                os.chmod(dest, stat.S_IRUSR | stat.S_IRGRP)
            record = {"symbol": symbol, "role": name, "path": str(dest.relative_to(ROOT)), "split_identity": split_id, "parent_dataset_identity": dataset_id, "date_range": [start, end], "rows": len(selected), "sha256": sha256(dest), "contract": split_contract}
            split_records.append(record)
            if name == "lockbox": lockbox_records.append({"symbol": symbol, "split_identity": split_id, "sha256": record["sha256"]})
    lockbox_identity = identity("nora.phase3.lockbox.v1", lockbox_records)
    manifest = {"schema_version": "nora.phase3.data_manifest_v1", "datasets": dataset_records, "splits": split_records, "lockbox_identity": lockbox_identity, "lockbox_policy": {"human_gated": True, "readable_by_phase3": False, "access_log": "data/phase3/lockbox_access.log", "phase3_evaluator_may_open": False}}
    (out / "data_manifest.json").write_text(canon(manifest) + "\n")
    (out / "lockbox_access.log").write_text(canon({"schema_version": "nora.phase3.lockbox_access_log_v1", "events": []}) + "\n")
    os.chmod(out / "lockbox_access.log", stat.S_IRUSR | stat.S_IWUSR)
    print(canon({"ok": True, "manifest": str((out / "data_manifest.json").relative_to(ROOT)), "lockbox_identity": lockbox_identity, "datasets": [{"symbol": x["symbol"], "identity": x["dataset_identity"], "rows": x["rows"]} for x in dataset_records], "splits": [{"symbol": x["symbol"], "role": x["role"], "identity": x["split_identity"], "rows": x["rows"]} for x in split_records]}))


if __name__ == "__main__": main()
