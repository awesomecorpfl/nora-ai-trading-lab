#!/usr/bin/env python3
"""Bounded Phase-0C CSV quality analyzer; not Phase-1 ingestion.

Accepts normal headered CSVs and QDM's headerless Date,Time,OHLC,Volume export.
The optional interval is inclusive, intentionally making one source export usable for
the long, DST, and weekend checks without creating derivative raw files.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def parse_time(value):
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in ("%Y.%m.%d %H:%M:%S.%f", "%Y.%m.%d %H:%M:%S",
                "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def percentiles(values):
    if not values:
        return {"count": 0, "min": None, "median": None, "p95": None, "max": None}
    values.sort()
    return {"count": len(values), "min": values[0],
            "median": values[(len(values) - 1) // 2],
            "p95": values[math.floor((len(values) - 1) * .95)], "max": values[-1]}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def field(row, name):
    return row.get(name, "") if name is not None else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--kind", choices=["m1", "tick", "spec"], required=True)
    parser.add_argument("--time", help="single timestamp column")
    parser.add_argument("--date-column", help="date column for split QDM timestamps")
    parser.add_argument("--clock-column", help="time column for split QDM timestamps")
    parser.add_argument("--open")
    parser.add_argument("--high")
    parser.add_argument("--low")
    parser.add_argument("--close")
    parser.add_argument("--volume")
    parser.add_argument("--bid")
    parser.add_argument("--ask")
    parser.add_argument("--delimiter", default=",")
    parser.add_argument("--no-header", action="store_true")
    parser.add_argument("--start", help="inclusive UTC-like local timestamp")
    parser.add_argument("--end", help="inclusive UTC-like local timestamp")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if bool(args.time) == bool(args.date_column or args.clock_column):
        parser.error("provide --time or both --date-column and --clock-column")
    if bool(args.date_column) != bool(args.clock_column):
        parser.error("split timestamps require both date and clock columns")
    start, end = (parse_time(args.start) if args.start else None,
                  parse_time(args.end) if args.end else None)
    if (args.start and not start) or (args.end and not end):
        parser.error("unparseable --start or --end")

    with open(args.path, newline="") as source:
        if args.no_header:
            reader = csv.reader(source, delimiter=args.delimiter)
            columns = [str(i) for i in range(len(next(reader, [])))]
            source.seek(0)
            reader = (dict(zip(columns, row)) for row in csv.reader(source, delimiter=args.delimiter))
        else:
            reader = csv.DictReader(source, delimiter=args.delimiter)
            columns = reader.fieldnames or []

        rows = parseable = unparseable = duplicate = out_of_order = 0
        malformed = nonnumeric_ohlc = zero_volume = nonnumeric_volume = 0
        weekend_rows = timestamp_not_minute_aligned = 0
        bid_missing = ask_missing = nonnumeric_quote = crossed = 0
        first_raw = last_raw = None
        seen, gaps, quote_deltas, spreads, session_gaps, suspicious = set(), [], [], [], [], []
        previous = None
        for row in reader:
            raw_time = field(row, args.time) if args.time else f"{field(row, args.date_column)} {field(row, args.clock_column)}"
            stamp = parse_time(raw_time)
            if stamp is None:
                unparseable += 1
                continue
            if start and stamp < start or end and stamp > end:
                continue
            rows += 1
            parseable += 1
            first_raw = first_raw or raw_time
            last_raw = raw_time
            if raw_time in seen:
                duplicate += 1
            seen.add(raw_time)
            if stamp.second or stamp.microsecond:
                timestamp_not_minute_aligned += 1
            if stamp.weekday() >= 5:
                weekend_rows += 1
            if previous is not None:
                delta = (stamp - previous).total_seconds()
                if delta < 0:
                    out_of_order += 1
                if args.kind == "m1" and delta > 60:
                    gaps.append(delta)
                    event = {"from": previous.isoformat(sep=" "), "to": stamp.isoformat(sep=" "), "seconds": delta}
                    if previous.weekday() == 4 and stamp.weekday() >= 6:
                        session_gaps.append(event)
                    elif delta > 3600:
                        suspicious.append(event)
                if args.kind == "tick" and delta > 0:
                    quote_deltas.append(delta)
            previous = stamp

            if args.kind == "m1":
                values = [number(field(row, col)) for col in (args.open, args.high, args.low, args.close)]
                if any(v is None for v in values):
                    nonnumeric_ohlc += 1
                else:
                    o, h, l, c = values
                    if l > min(o, h, c) or h < max(o, l, c):
                        malformed += 1
                if args.volume:
                    volume = number(field(row, args.volume))
                    nonnumeric_volume += volume is None
                    zero_volume += volume == 0 if volume is not None else 0
            elif args.kind == "tick":
                bid, ask = number(field(row, args.bid)), number(field(row, args.ask))
                bid_missing += bid is None
                ask_missing += ask is None
                if bid is None or ask is None:
                    nonnumeric_quote += 1
                else:
                    spreads.append(ask - bid)
                    crossed += bid > ask

    out = {"kind": args.kind, "file": Path(args.path).name, "sha256": sha256(args.path),
           "interval": {"start": args.start, "end": args.end}, "rows": rows, "columns": columns,
           "first_timestamp": first_raw, "last_timestamp": last_raw,
           "parseable_timestamps": parseable, "unparseable_timestamps": unparseable,
           "duplicate_timestamps": duplicate, "out_of_order": out_of_order,
           "weekend_rows": weekend_rows}
    if args.kind == "m1":
        out.update({"timestamp_not_minute_aligned": timestamp_not_minute_aligned,
                    "malformed_ohlc": malformed, "non_numeric_ohlc": nonnumeric_ohlc,
                    "zero_volume_rows": zero_volume, "non_numeric_volume_rows": nonnumeric_volume,
                    "missing_minutes_between_adjacent_rows": sum(round(x / 60) - 1 for x in gaps),
                    "gap_seconds": percentiles(gaps),
                    "gap_buckets": dict(Counter("over_1h" if x > 3600 else "over_5m" if x > 300 else "over_1m" for x in gaps)),
                    "weekend_session_gaps": session_gaps, "suspicious_discontinuities": suspicious})
    elif args.kind == "tick":
        out.update({"bid_missing": bid_missing, "ask_missing": ask_missing,
                    "non_numeric_bid_or_ask": nonnumeric_quote, "crossed_quotes": crossed,
                    "spread": percentiles(spreads), "quote_gap_seconds": percentiles([x for x in quote_deltas if x > 1]),
                    "timestamp_resolution_seconds": percentiles(quote_deltas)})
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
