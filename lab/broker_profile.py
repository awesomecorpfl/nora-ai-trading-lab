"""Strict intake for StrategyQuantX broker/symbol exports.

The legacy export is treated as observed source material. Conflicting derived
values are retained under ``source_values`` and surfaced as warnings rather
than silently reconciled.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from lab.core import canon

SCHEMA = "nora.broker_profile_v1"
BOUNDARY_SCHEMA = "nora.broker_profile_boundary_v1"
UNBOUND_POLICY_FIELDS = (
    "spread_model",
    "commission_model",
    "slippage_model",
    "swap_model",
    "account_currency",
    "sizing",
    "leverage_margin",
    "session_policy",
)
EXPECTED_HEADER = [
    "Instrument", "Description", "Instrument Type", "Exchange", "Country", "Sector", "Execution Type", "Trading Conditions", "---", "Last Bid Price", "HowManyTicksAreIn1Pip", "---", "Calculations are based on", "Pip (Tick Size)", "Tick (Tick Step)", "1 Pip Worth", "", "1 Tick Worth", "", "Min Lot Size", "Max Lot Size", "Min Lot Step", "Instrument's Daily ATR (In Pips)", "", "", "Leverage", "Margin Requirement", "", "AccountMarginStopOutMode", "Margin Call at", "Stop Out at", "Spread (In Pips)", "", "", "Slippage (In Pips)", "", "", "Commission Type", "Commission Value", "", "Minimum SL/TP distance from market price (STOP_LEVEL) (In Pips)", "", "", "Minimum pending order distance from market price (FREEZE_LEVEL) (In Pips)", "", "", "Maximum open pending orders allowed", "Swap Type", "Swap Long", "", "", "Swap Short", "", "", "Triple Swap on", "Trading Sessions Times (TimeOffSet=0)", "Decimals", "Contract Size", "Point Value",
]
CSV_COLUMNS = {
    "symbol": 0, "description": 1, "instrument_type": 2, "exchange": 3,
    "country": 4, "sector": 5, "execution_type": 6, "trading_conditions": 7,
    "last_bid": 9, "pip_size": 13, "trade_tick_size": 14, "min_volume": 19,
    "max_volume": 20, "volume_step": 21, "leverage": 25,
    "margin_requirement": 26, "margin_call": 29, "stop_out": 30,
    "spread_pips": 31, "slippage_pips": 34, "commission_type": 37,
    "commission_value": 38, "stops_level_pips": 40, "freeze_level_pips": 43,
    "max_pending_orders": 46, "swap_type": 47, "swap_long": 48,
    "swap_short": 51, "triple_swap_day": 54, "sessions": 55, "digits": 56,
    "contract_size": 57, "point_value": 58,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _float(row: list[str], index: int, field: str) -> float:
    try:
        value = float(row[index].replace("_", ""))
    except (IndexError, ValueError) as exc:
        raise ValueError(f"invalid {field}") from exc
    if not math.isfinite(value):
        raise ValueError(f"non-finite {field}")
    return value


def _text(row: list[str], index: int) -> str:
    try:
        return row[index].strip()
    except IndexError as exc:
        raise ValueError(f"missing CSV column {index}") from exc


def _safe_xml_root(path: Path) -> ET.Element:
    """Parse the fixed export grammar after rejecting entity/doctype constructs.

    StrategyQuantX exports are simple local XML files; external entities and
    DTDs are not part of the accepted grammar and are rejected fail-closed.
    """
    raw = path.read_bytes()
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper or b"SYSTEM" in upper:
        raise ValueError(f"unsafe XML construct in {path.name}")
    return ET.fromstring(raw)


def _session_map(path: Path) -> dict[str, dict[str, Any]]:
    root = _safe_xml_root(path)
    result: dict[str, dict[str, Any]] = {}
    for session in root.findall("Session"):
        name = session.attrib["name"]
        if name in result:
            raise ValueError(f"duplicate session name: {name}")
        elements = [dict(item.attrib) for item in session.findall("Element")]
        result[name] = {"name": name, "elements": elements}
    return result


def _xml_map(path: Path) -> dict[str, dict[str, str]]:
    root = _safe_xml_root(path)
    result: dict[str, dict[str, str]] = {}
    for item in root.findall("InstrumentInfo"):
        symbol = item.attrib["instrument"]
        if symbol in result:
            raise ValueError(f"duplicate instrument name: {symbol}")
        result[symbol] = dict(item.attrib)
    return result


def _find_session(symbol: str, sessions: dict[str, dict[str, Any]]) -> str | None:
    matches = [name for name in sessions if symbol in name.split("_")]
    if len(matches) > 1:
        raise ValueError(f"ambiguous session mapping for {symbol}")
    return matches[0] if matches else None


def _embedded_attr(value: str, attribute: str) -> str | None:
    match = re.search(rf'{re.escape(attribute)}="([^"]*)"', value)
    return match.group(1) if match else None


def _embedded_param(value: str, key: str) -> str | None:
    match = re.search(rf'key="{re.escape(key)}"[^>]*>([^<]*)<', value)
    return match.group(1) if match else None


def _day(value: str) -> str:
    return {"mon": "monday", "tue": "tuesday", "wed": "wednesday", "thu": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday"}.get(value.strip().lower(), value.strip().lower())


def _instrument_family(source_csv: dict[str, str], source_xml: dict[str, str]) -> str:
    """Derive a coarse family from explicit source labels, never from symbol names."""
    sector = source_csv.get("sector", "").strip().lower()
    csv_description = source_csv.get("description", "").strip().lower()
    xml_description = source_xml.get("description", "").strip().lower()
    if sector == "currency" or "fx_" in xml_description:
        return "forex"
    if "commodit" in sector or "gold" in csv_description or "gold" in xml_description:
        return "metals_commodities"
    if sector == "indexes" or xml_description.startswith("index"):
        return "indices"
    if "stock" in xml_description or "etf" in csv_description or sector in {"financial", "equity"}:
        return "equity_etf"
    return "other"


def load_strategyquantx_export(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    csv_path = root / "sample.csv"
    sessions_path = root / "Sessions.xml"
    xml_path = root / "updated_instrument_information.xml"
    for path in (csv_path, sessions_path, xml_path):
        if not path.is_file():
            raise ValueError(f"missing export file: {path.name}")

    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2 or rows[0] != EXPECTED_HEADER:
        raise ValueError("unsupported StrategyQuantX CSV header")
    if any(len(row) != len(EXPECTED_HEADER) for row in rows[1:]):
        raise ValueError("ragged StrategyQuantX CSV")

    sessions = _session_map(sessions_path)
    xml_rows = _xml_map(xml_path)
    symbols: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    for row in rows[1:]:
        symbol = _text(row, CSV_COLUMNS["symbol"])
        if not symbol or symbol in {item["symbol"] for item in symbols}:
            raise ValueError(f"duplicate or empty symbol: {symbol!r}")
        if symbol not in xml_rows:
            raise ValueError(f"CSV/XML symbol mismatch: {symbol}")
        x = xml_rows[symbol]
        digits = int(_float(row, CSV_COLUMNS["digits"], "digits"))
        source_csv = {name: _text(row, index) for name, index in CSV_COLUMNS.items()}
        conflict_pairs = (
            ("pip_size", "tickSize"), ("trade_tick_size", "tickStep"),
            ("digits", "decimals"), ("spread_pips", "defaultSpread"),
            ("slippage_pips", "defaultSlippage"), ("volume_step", "orderSizeStep"),
            ("point_value", "pointValue"),
        )
        for csv_field, xml_field in conflict_pairs:
            csv_value = _float(row, CSV_COLUMNS[csv_field], csv_field)
            xml_value = float(x[xml_field])
            if not math.isclose(csv_value, xml_value, rel_tol=0.0, abs_tol=1e-12):
                warnings.append({"code": "SOURCE_VALUE_CONFLICT", "symbol": symbol, "field": csv_field})
        swap_xml = x.get("swap", "")
        swap_pairs = (("swap_long", "long"), ("swap_short", "short"), ("triple_swap_day", "tripleSwapOn"))
        for csv_field, xml_field in swap_pairs:
            csv_value = _day(_text(row, CSV_COLUMNS[csv_field])) if csv_field == "triple_swap_day" else _text(row, CSV_COLUMNS[csv_field]).lower()
            xml_value = (_embedded_attr(swap_xml, xml_field) or "").lower()
            if csv_value != (_day(xml_value) if csv_field == "triple_swap_day" else xml_value):
                warnings.append({"code": "SOURCE_VALUE_CONFLICT", "symbol": symbol, "field": csv_field})
        csv_swap_type = _text(row, CSV_COLUMNS["swap_type"]).lower().removeprefix("in ")
        xml_swap_type = (_embedded_attr(swap_xml, "type") or "").lower()
        if csv_swap_type != xml_swap_type:
            warnings.append({"code": "SOURCE_VALUE_CONFLICT", "symbol": symbol, "field": "swap_type"})
        commission_xml = _embedded_param(x.get("commissions", ""), "Commission")
        commission_type_xml = _embedded_attr(x.get("commissions", ""), "type")
        if commission_type_xml is not None and _text(row, CSV_COLUMNS["commission_type"]).lower() != commission_type_xml.lower():
            warnings.append({"code": "SOURCE_VALUE_CONFLICT", "symbol": symbol, "field": "commission_type"})
        if commission_xml is not None and not math.isclose(_float(row, CSV_COLUMNS["commission_value"], "commission_value"), float(commission_xml), rel_tol=0.0, abs_tol=1e-12):
            warnings.append({"code": "SOURCE_VALUE_CONFLICT", "symbol": symbol, "field": "commission_value"})
        session_name = _find_session(symbol, sessions)
        if session_name is None:
            warnings.append({"code": "MISSING_SESSION_MAPPING", "symbol": symbol, "field": "sessions"})
        source_xml = x
        symbols.append({
            "symbol": symbol,
            "source_values": {"csv": source_csv, "csv_header": list(EXPECTED_HEADER), "csv_row": list(row), "instrument_xml": source_xml},
            "identity": {
                "canonical_symbol": symbol,
                "broker_symbol": symbol,
                "instrument_type": _text(row, CSV_COLUMNS["instrument_type"]) or None,
                "sector": _text(row, CSV_COLUMNS["sector"]) or None,
                "instrument_family": _instrument_family(source_csv, source_xml),
            },
            "price": {
                "digits": digits,
                "point_size_derived": 10.0 ** -digits,
                "pip_size_observed": _float(row, CSV_COLUMNS["pip_size"], "pip_size"),
                "trade_tick_size_observed": _float(row, CSV_COLUMNS["trade_tick_size"], "trade_tick_size"),
                "last_bid_observed": _float(row, CSV_COLUMNS["last_bid"], "last_bid"),
            },
            "contract": {
                "contract_size_observed": _float(row, CSV_COLUMNS["contract_size"], "contract_size"),
                "volume_min_observed": _float(row, CSV_COLUMNS["min_volume"], "min_volume"),
                "volume_max_observed": _float(row, CSV_COLUMNS["max_volume"], "max_volume"),
                "volume_step_observed": _float(row, CSV_COLUMNS["volume_step"], "volume_step"),
            },
            "execution": {
                "execution_type": _text(row, CSV_COLUMNS["execution_type"]),
                "trading_conditions": _text(row, CSV_COLUMNS["trading_conditions"]),
                "stops_level_pips_observed": _float(row, CSV_COLUMNS["stops_level_pips"], "stops_level_pips"),
                "freeze_level_pips_observed": _float(row, CSV_COLUMNS["freeze_level_pips"], "freeze_level_pips"),
            },
            "costs": {
                "spread_pips_observed": _float(row, CSV_COLUMNS["spread_pips"], "spread_pips"),
                "slippage_pips_observed": _float(row, CSV_COLUMNS["slippage_pips"], "slippage_pips"),
                "commission_type_observed": _text(row, CSV_COLUMNS["commission_type"]),
                "commission_value_observed": _float(row, CSV_COLUMNS["commission_value"], "commission_value"),
                "swap_type_observed": _text(row, CSV_COLUMNS["swap_type"]),
                "swap_long_observed": _float(row, CSV_COLUMNS["swap_long"], "swap_long"),
                "swap_short_observed": _float(row, CSV_COLUMNS["swap_short"], "swap_short"),
                "triple_swap_day_observed": _text(row, CSV_COLUMNS["triple_swap_day"]),
            },
            "session_name": session_name,
        })

    if set(xml_rows) != {item["symbol"] for item in symbols}:
        raise ValueError("CSV/XML instrument sets differ")
    files = [{"path": path.name, "sha256": _sha(path), "bytes": path.stat().st_size} for path in (csv_path, sessions_path, xml_path)]
    value = {
        "schema_version": SCHEMA,
        "provenance": {"format": "StrategyQuantX_export", "files": files, "raw_preserved": True},
        "symbols": symbols,
        "sessions": sessions,
        "warnings": warnings,
    }
    value["profile_identity"] = hashlib.sha256(canon(value).encode()).hexdigest()
    return value


def load_canonical_profile(path: str | Path) -> dict[str, Any]:
    """Load and verify one canonical normalized broker-profile artifact."""
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid canonical profile: {path}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        raise ValueError("unsupported canonical profile schema")
    actual = value.get("profile_identity")
    if not isinstance(actual, str):
        raise ValueError("missing profile identity")
    body = dict(value)
    body.pop("profile_identity", None)
    expected = hashlib.sha256(canon(body).encode()).hexdigest()
    if actual != expected:
        raise ValueError("profile identity mismatch")
    return value


def write_strategyquantx_profile(root: str | Path, output: str | Path) -> dict[str, Any]:
    """Write one canonical, reproducible normalized profile artifact."""
    profile = load_strategyquantx_export(root)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".partial")
    try:
        partial.write_text(canon(profile) + "\n", encoding="utf-8", newline="\n")
        partial.replace(output)
    finally:
        if partial.exists():
            partial.unlink()
    return profile


def build_profile_boundary(profile: dict[str, Any]) -> dict[str, Any]:
    """Separate source observations from policy decisions that remain unbound."""
    if not isinstance(profile, dict) or profile.get("schema_version") != SCHEMA:
        raise ValueError("unsupported observed broker profile")
    profile_identity = profile.get("profile_identity")
    if not isinstance(profile_identity, str) or not profile_identity:
        raise ValueError("observed broker profile has no identity")
    body = dict(profile)
    body.pop("profile_identity", None)
    expected_identity = hashlib.sha256(canon(body).encode()).hexdigest()
    if profile_identity != expected_identity:
        raise ValueError("profile identity mismatch")
    return {
        "schema_version": BOUNDARY_SCHEMA,
        "source_profile_identity": profile_identity,
        "observed_profile": profile,
        "policy": {
            "status": "unbound",
            "bindings": {},
            "unbound_fields": list(UNBOUND_POLICY_FIELDS),
        },
    }
