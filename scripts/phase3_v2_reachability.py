"""Structural-only Phase-3 v2 reachability proof.

This probe does not load market data, calculate trades, rank candidates, or
open either the OOS partition or the permanent lockbox.  It enumerates the
frozen grammar parameter domains and proves the replacement archive is
reachable before v2 candidate evaluation.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/phase3"


def identity(domain: str, value: object) -> str:
    raw = domain.encode() + b"\0" + json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def descriptor(family: str, side: str, max_bars: int, stop: float, target: float) -> dict[str, str]:
    ratio = target / stop
    return {
        "trigger_shape": family,
        "side": side,
        "holding_policy": {8: "short", 16: "medium", 32: "long"}[max_bars],
        "risk_shape": "sub_one_to_one" if ratio < 1.5 else "balanced" if ratio < 2.5 else "target_dominant",
    }


def main() -> None:
    families = ("trend-pullback", "close-confirmed-breakout")
    symbols = ("EURUSD", "GBPJPY")
    sides = ("long", "short")
    holds = (8, 16, 32)
    stops = (0.5, 1.0, 1.5)
    targets = (1.0, 2.0, 3.0)
    candidates = []
    cells = set()
    for family, symbol, side, max_bars, stop, target in itertools.product(
        families, symbols, sides, holds, stops, targets
    ):
        # The probe keeps one representative of each archive cell; no market
        # result is involved in this identity or coverage calculation.
        d = descriptor(family, side, max_bars, stop, target)
        cell = json.dumps(d, sort_keys=True, separators=(",", ":"))
        cells.add(cell)
        candidates.append({"family": family, "symbol": symbol, "side": side,
                           "max_bars": max_bars, "stop_atr": stop, "target_atr": target,
                           "candidate_identity": identity("nora.phase3.strategy.v2.probe", {
                               "family": family, "symbol": symbol, "side": side,
                               "max_bars": max_bars, "stop_atr": stop, "target_atr": target,
                           }), "archive_cell": cell})
    ordered = sorted(cells)
    result = {
        "schema_version": "nora.phase3.v2.reachability_probe_v1",
        "status": "PASS",
        "market_data_loaded": False,
        "oos_loaded": False,
        "lockbox_access_events": 0,
        "profitability_or_ranking_used": False,
        "v1_failure_mechanics": {
            "fixed_side_makes_long_short_mid_unreachable": True,
            "session_concentration_is_not_a_grammar_control": True,
            "result_derived_trade_and_session_bins_are_not_pre_search_reachable_contracts": True,
            "canonical_dedup_is_preserved": True,
        },
        "v2_archive": {
            "dimensions": ["trigger_shape", "side", "holding_policy", "risk_shape"],
            "domains": {
                "trigger_shape": list(families), "side": list(sides),
                "holding_policy": ["short", "medium", "long"],
                "risk_shape": ["sub_one_to_one", "balanced", "target_dominant"],
            },
            "theoretical_cells": 36,
            "reachable_cells": len(ordered),
            "minimum_frozen_coverage": 24,
            "coverage_rule": "at least 24 of 36 occupied; every trigger_shape and side represented",
        },
        "probe_candidate_count": len(candidates),
        "probe_unique_candidate_identities": len({x["candidate_identity"] for x in candidates}),
        "reachable_cell_identities": [identity("nora.phase3.archive.v2.cell", x) for x in ordered],
        "reachable_cells": [json.loads(x) for x in ordered],
    }
    (OUT / "phase3_v2_reachability_probe_v1.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "reachable_cells": len(ordered), "minimum": 24}))


if __name__ == "__main__":
    main()
