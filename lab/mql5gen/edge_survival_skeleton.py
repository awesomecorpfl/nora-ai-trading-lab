"""Broker-data EA skeleton generator for the edge-survival gate.

This is a *skeleton*, not a runnable strategy. The ten system-test fixtures do
not have broker-native implementations (their canary exits in ``OnInit`` with
synthetic OHLC). A real finalist will need a broker-data EA that:

  - runs in ``OnTick`` against live tester ticks/bars;
  - implements the finalist's indicator/entry/exit logic;
  - respects the declared cost model (spread, commission, slippage);
  - emits a per-trade CSV with the same schema the similarity report consumes;
  - carries no live-trading path (investor-mode enforcement, no order sends
    outside the tester).

This generator emits the skeleton: a compilable MQL5 EA that declares the
required input parameters, the CSV schema, the cost-model inputs, the
OnTick/OnDeinit lifecycle, and stubbed strategy hooks. It is intentionally
non-strategic: the entry/exit hooks raise/return without placing trades. A
finalist's real logic plugs into the marked extension points.

The skeleton is identity-bound so the scaffold can detect when a real finalist
EA replaces it: the generator records the source hash, the CSV schema hash, and
the extension-point contract.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "nora.phase2_edge_survival_ea_skeleton_v1"
EA_FILENAME = "NoraPhase2EdgeSurvivalSkeletonV1.mq5"
MANIFEST_FILENAME = "NoraPhase2EdgeSurvivalSkeletonV1.manifest.json"
CSV_COLUMNS = (
    "strategy_identity",
    "trade_ordinal",
    "direction",
    "signal_timestamp",
    "entry_timestamp",
    "entry_price",
    "initial_stop",
    "initial_target",
    "exit_timestamp",
    "exit_price",
    "exit_reason",
    "holding_bars",
    "gross_price_return",
    "cost_model_spread",
    "cost_model_commission",
    "cost_model_slippage",
    "native_edge_survives_flag",
    "terminal_source_disposition",
)


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _ea_source() -> str:
    """Return the skeleton MQL5 source.

    The skeleton compiles but performs no strategy logic. It declares the
    cost-model inputs, opens the result CSV on init, writes a header, and
    provides stubbed ``EvaluateEntry``/``EvaluateExit`` hooks that a finalist
    implementation must replace.
    """
    header = "\\t".join(f'"{c}"' for c in CSV_COLUMNS)
    return f'''#property strict
// Nora Phase 2 edge-survival broker-data EA skeleton.
// This skeleton is intentionally non-strategic. It compiles and runs but
// performs no entry/exit logic. A finalist implementation must replace the
// EvaluateEntry and EvaluateExit hooks with the finalist's real strategy.
//
// Extension-point contract:
//   EvaluateEntry  -> returns OP_BUY / OP_SELL / -1 (no entry) for the current tick
//   EvaluateExit   -> returns true if the open trade should exit now
//
// The skeleton refuses to trade: OrderSend is guarded by a tester-only check
// and the investor-mode boundary is enforced by the tester configuration.

input string  FinalistIdentity     = "";
input string  StrategyIdentity     = "";
input double  CostModelSpread      = 0.0;
input double  CostModelCommission  = 0.0;
input double  CostModelSlippage    = 0.0;
input string  ResultCsv            = "nora_phase2_edge_survival_v1.csv";

int      g_file          = INVALID_HANDLE;
int      g_trade_ordinal = 0;
datetime g_entry_time    = 0;
double   g_entry_price   = 0.0;
double   g_initial_stop  = 0.0;
double   g_initial_target= 0.0;
int      g_direction     = -1;

// --- Extension points (finalist replaces these) -----------------------------
int EvaluateEntry()
{{
    // Finalist entry logic goes here. Return OP_BUY, OP_SELL, or -1.
    // The skeleton never enters.
    return -1;
}}

bool EvaluateExit()
{{
    // Finalist exit logic goes here. Return true to close the open trade.
    // The skeleton never exits.
    return false;
}}

// --- Lifecycle --------------------------------------------------------------
int OnInit()
{{
    if(!MQLInfoInteger(MQL_TESTER))
    {{
        Print("NORA_EDGE_SURVIVAL_SKELETON: refuses to run outside tester");
        return INIT_FAILED;
    }}
    g_file = FileOpen(ResultCsv, FILE_WRITE | FILE_CSV | FILE_COMMON, "\\t");
    if(g_file == INVALID_HANDLE)
    {{
        Print("NORA_EDGE_SURVIVAL_SKELETON: failed to open result CSV");
        return INIT_FAILED;
    }}
    FileWrite(g_file, {header});
    Print("NORA_EDGE_SURVIVAL_SKELETON_V1_INIT");
    return INIT_SUCCEEDED;
}}

void OnDeinit(const int reason)
{{
    if(g_file != INVALID_HANDLE) {{ FileClose(g_file); g_file = INVALID_HANDLE; }}
}}

void OnTick()
{{
    if(g_direction < 0)
    {{
        int signal = EvaluateEntry();
        if(signal == OP_BUY || signal == OP_SELL)
        {{
            // Finalist order placement goes here. The skeleton records intent
            // but does not call OrderSend. A real finalist EA must respect the
            // declared cost model and the investor-mode boundary.
            g_direction     = signal;
            g_entry_time    = TimeCurrent();
            g_entry_price   = (signal == OP_BUY) ? Ask : Bid;
            g_initial_stop  = 0.0;  // finalist computes
            g_initial_target= 0.0;  // finalist computes
            g_trade_ordinal += 1;
        }}
        return;
    }}
    if(EvaluateExit())
    {{
        double exit_price = (g_direction == OP_BUY) ? Bid : Ask;
        double gross      = (g_direction == OP_BUY) ? (exit_price - g_entry_price)
                                                    : (g_entry_price - exit_price);
        FileWrite(g_file,
            StrategyIdentity, g_trade_ordinal,
            (g_direction == OP_BUY) ? "long" : "short",
            TimeToString(g_entry_time, TIME_DATE | TIME_SECONDS),
            TimeToString(g_entry_time, TIME_DATE | TIME_SECONDS),
            DoubleToString(g_entry_price, 16),
            DoubleToString(g_initial_stop, 16),
            DoubleToString(g_initial_target, 16),
            TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
            DoubleToString(exit_price, 16),
            "skeleton_exit",
            0,
            DoubleToString(gross, 16),
            DoubleToString(CostModelSpread, 16),
            DoubleToString(CostModelCommission, 16),
            DoubleToString(CostModelSlippage, 16),
            "false",
            "skeleton_not_strategic");
        g_direction = -1;
    }}
}}
'''


def generate(destination: Path) -> dict[str, Any]:
    """Generate the skeleton EA + manifest into ``destination``.

    Returns the manifest dict. The manifest records:
      - the source SHA-256;
      - the CSV schema identity (hash of the column list);
      - the extension-point contract (so a finalist replacement is detectable);
      - a ``skeleton_not_strategic`` flag that remains true until a finalist
        implementation replaces this generator.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    source = _ea_source().encode("utf-8")
    source_sha = hashlib.sha256(source).hexdigest()
    csv_schema_identity = _sha(list(CSV_COLUMNS))

    manifest = {
        "schema_version": SCHEMA,
        "ea_filename": EA_FILENAME,
        "source_sha256": source_sha,
        "csv_schema_identity": csv_schema_identity,
        "csv_columns": list(CSV_COLUMNS),
        "extension_point_contract": {
            "EvaluateEntry": "returns OP_BUY / OP_SELL / -1 (no entry)",
            "EvaluateExit": "returns true if the open trade should exit now",
            "tester_only": "OnInit refuses to run outside MQL_TESTER",
            "cost_model_inputs": ["CostModelSpread", "CostModelCommission", "CostModelSlippage"],
        },
        "skeleton_not_strategic": True,
        "note": (
            "This is a compilable skeleton, not a finalist strategy. The ten "
            "system-test fixtures have no broker-native implementation. A real "
            "finalist must replace the extension points with strategic logic."
        ),
    }
    manifest["skeleton_identity"] = _sha(
        {
            "source_sha256": source_sha,
            "csv_schema_identity": csv_schema_identity,
            "extension_point_contract": manifest["extension_point_contract"],
        }
    )
    (destination / EA_FILENAME).write_bytes(source)
    (destination / MANIFEST_FILENAME).write_text(_canon(manifest) + "\n")
    return manifest
