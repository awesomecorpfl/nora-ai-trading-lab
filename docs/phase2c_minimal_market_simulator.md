# Phase 2C minimal stateful market simulator

`simulate_market_v1` accepts `{task_version, task_type, market_path, entry_intent_path, exit_intent_path, output_path, config}`. Config version `1` permits only `side: long|short`, `price_column: open`, `position_policy: one_at_a_time`, and `terminal_policy: leave_open`; all task and config fields are strict.

Market data must have aligned UTF-8 `timestamp` and finite non-null Float64 `open`. Both intent artifacts must have exactly aligned timestamps and their configured native nullable Boolean columns. No joins, timestamp conversion, filling, or coercion occurs.

## Frozen state order and economics

At each current open, the simulator performs exactly this ordering:

1. If open and exit is `true`, close at that current open; a same-row entry `true` is ignored and counted.
2. If open and exit is not `true`, a true entry is ignored and counted.
3. If flat and entry is `true`, open at that current open; a same-row exit `true` is ignored and counted.
4. If flat and entry is not `true`, a true exit is ignored and counted.

`null` does nothing. There is no same-row close/reopen. One unit is modeled: long gross P&L is `exit_price - entry_price`; short gross P&L is `entry_price - exit_price`; `bars_held` is `exit_index - entry_index`. `leave_open` creates no artificial terminal close.

## Final closed-trade ledger schema

The atomically published Parquet ledger has these required non-null typed fields: `trade_id: UInt64`, `side: Utf8` (`long` or `short` only), `entry_timestamp: Utf8`, `exit_timestamp: Utf8`, `entry_index: UInt64`, `exit_index: UInt64`, `entry_price: Float64`, `exit_price: Float64`, `bars_held: UInt64`, and `gross_pnl_per_unit: Float64`. Terminal-open reporting includes `state`, `side`, `entry_index`, `entry_timestamp`, `entry_price`, and `bars_open_through_final_row`.

## Committed-chain evidence

The long chain produces the following ledger (zero-based rows):

| trade | side | entry row / price | exit row / price | bars | gross P&L |
| --- | --- | --- | --- | --- | --- |
| 1 | long | 4 / 1.1013 | 5 / 1.1010 | 1 | -0.0003 |
| 2 | long | 6 / 1.1017 | 7 / 1.1014 | 1 | -0.0003 |
| 3 | long | 8 / 1.1021 | 9 / 1.1018 | 1 | -0.0003 |
| 4 | long | 10 / 1.1025 | 11 / 1.1022 | 1 | -0.0003 |

Counts are four entries, four closes, four ignored exits while flat, four ignored entries while open, and terminal `flat`; total gross P&L per unit is `-0.0012`. Its frozen simulator identity is `7b39a70d2fe5312a5dc1970254c50a350012309a50c7a3610992c225efa5a5b1`.

The committed short fixture (`phase2_market_simulator_short_*`) opens short at index 0 / `2030.01.02 00:00` at `10.0`, closes at index 2 / `2030.01.02 00:02` at `8.0`, has `bars_held = 2`, ledger `side = short`, gross P&L `10.0 - 8.0 = 2.0`, and ends flat.

The committed leave-open fixture (`phase2_market_simulator_leave_open_*`) opens long at index 1 / `2030.01.03 00:01` at `21.0`, creates zero closed trades, and reports `{state: open, side: long, entry_index: 1, entry_timestamp: 2030.01.03 00:01, entry_price: 21.0, bars_open_through_final_row: 1}`. Its task explicitly sets `terminal_policy: leave_open`.

## Identity and failed-publication evidence

The domain-separated identity protocol is `nora.market_simulator.simulate_market_v1.semantic.v2.ledger_side_v1`. It binds typed config (including side and terminal policy), the canonical market timestamps and open values, nullable entry and exit intent values, final ledger schema/content (including side), and terminal state. Paths and Parquet container bytes are deliberately not identity inputs.

Running identical short-fixture inputs twice yielded `2dedf9984a2e09ec91602b6819fee8474f9ea6b69e1fa20cd428c8e9927cb8ad` both times; ledger and summary semantics matched. The independent deterministic mutations yielded: side `3d38e45e34ae977fad93729c8401644562269dc94b3c223c77b3b693882e28ee`; one market open `7ac5de22b10872be6f12cb19eaeffdd560c8006d0cc9c419edf0eb635163700b`; entry intent `799b8176167f7edb34304be15971aebc5c8cda6421cc7cd2d5c97594464d22ed`; exit intent `3c6e27b5bcf24ad4a4912e8f1d91222353ac3c177b02a8250b49c2035e3f47ad`.

A fresh-output CLI run with a one-row, timestamp-misaligned entry artifact exited `2`, wrote the deterministic stderr JSON error `{"ok":false,"error":"simulator timestamps must match exactly"}`, emitted no stdout success summary, and published neither the requested final ledger nor a `.partial` artifact.

Commands executed (the two named Python tests execute real `labengine <task.json>` subprocesses, including the repeat, mutations, fixtures, and failure):

```bash
cargo build --manifest-path engine/Cargo.toml
.venv/bin/python -m unittest tests.test_phase1.Phase1.test_market_simulator_committed_cli_chain tests.test_phase1.Phase1.test_market_simulator_short_leave_open_identity_and_failure_evidence
cargo test --manifest-path engine/Cargo.toml
.venv/bin/python -m unittest discover -s tests
```

This remains the minimal simulator: no SL/TP, intrabar path or ambiguity, spread, commission, slippage, swap, sizing, trailing, pending orders, partial exits, RNG, MQL5, parity, searchable grammar, or Phase 3 work.

## Optional initial bracket construction

`config.initial_bracket` may be absent or `null`, preserving the simulator behavior and frozen committed-chain simulator identity `7b39a70d2fe5312a5dc1970254c50a350012309a50c7a3610992c225efa5a5b1`. When present it is strict and has `{model: "fixed_price_offsets_v1", stop_offset: Float64, target_offset: Float64, output_path: String}`. Unknown fields and models are rejected; both offsets must be finite and strictly greater than zero. This only constructs and publishes initial price levels: it does not execute stop-loss or take-profit levels.

For an actual long opening at `P`, stop is `P - stop_offset` and target is `P + target_offset`. For an actual short opening at `P`, stop is `P + stop_offset` and target is `P - target_offset`. A bracket row is constructed only when the state machine actually opens a position—not for false/null entries, exit-only rows, or entries ignored while already open. A terminal `leave_open` position remains unclosed and still receives its one initial bracket row.

The immutable bracket Parquet schema is `entry_id: UInt64`, `side: Utf8`, `entry_timestamp: Utf8`, `entry_index: UInt64`, `entry_price: Float64`, `initial_stop_price: Float64`, `initial_target_price: Float64`. `entry_id` starts at one and follows actual-open order. The closed-trade ledger schema and contents are unchanged.

Bracket identity is separately domain-separated as `nora.initial_bracket.fixed_price_offsets_v1.semantic.v1.schema.v1`. It binds the protocol/schema, accepted simulator identity, actual opening sequence, side, entry timestamps/indices/prices, both offsets, and canonical bracket rows; it never replaces the simulator identity.

Committed CLI fixtures prove: long `10.0 → stop 9.0 / target 12.0`; short `10.0 → stop 11.0 / target 8.0`; collision inputs yield one actual entry, one ignored entry while open, and one bracket row; terminal leave-open at `21.0` yields one bracket row `20.0 / 23.0` with zero closed trades.

Two identical short bracket runs produced `ece1581fec67637f24283f0c0c76a343688d214d7522dce41333e20c0a82c52d` and semantically identical rows. Independent mutations yielded: side `aab6d61cf6aedd6541a8be5235f097645e56c37d5727610950a691e89a53d445`; entry price `ff1ef22ee16b6e93a221dd3e88c5b7bdcdf279819954c237c16999b803bbeaab`; stop offset `87ee9a01152d1a6cc5bbd9084cb0628cdc95a4d0f39d5d495abdf2db1ad456e2`; target offset `a8ebda35b1275f528060d80e2d9588d1d652c771b1dfcd99c7fcbaa28840f948`.

The representative invalid zero-offset CLI task exited `2`, emitted `{"ok":false,"error":"initial_bracket offsets must be finite and strictly greater than zero"}` to stderr, emitted no stdout success summary, and published neither its trade ledger nor bracket artifact.

Additional executed CLI evidence command:

```bash
.venv/bin/python -m unittest tests.test_phase1.Phase1.test_initial_bracket_cli_evidence
```

## Optional initial bracket execution

`config.initial_bracket_execution` is strict and optional: `{model: "ohlc_unambiguous_v1", event_output_path: String}`. It requires `initial_bracket`; absence or `null` remains construction-only and preserves all prior simulator and bracket identities. Execution requires finite Float64 `open`, `high`, and `low` with `low <= open <= high`.

Only a carried position is eligible. Its later-row open must be strictly inside the initial bracket or the run fails closed as an unsupported gap/open-level event. A true signal exit closes at that open before OHLC evaluation. Otherwise long hits are `low <= stop` and `high >= target`; short hits are `high >= stop` and `low <= target`. Exactly one hit closes at its bracket level; both hits fail closed as an unsupported ambiguous bracket bar. An entry-row bracket is never evaluated, and a same-row entry following any carried-position close is ignored.

Bracket event Parquet rows are `trade_id: UInt64`, `entry_id: UInt64`, `side: Utf8`, `exit_timestamp: Utf8`, `exit_index: UInt64`, `exit_reason: Utf8`, `exit_price: Float64`, `bar_open: Float64`, `bar_high: Float64`, `bar_low: Float64`; reasons are only `initial_stop` or `initial_target`. Signal exits have no event row. Execution has its own domain-separated identity binding execution protocol/model, simulator identity, bracket identity, canonical eligible OHLC, event rows, and resulting trade outcomes.

The CLI matrix freezes long stop `9.0/-1.0`, long target `12.0/+2.0`, short stop `11.0/-1.0`, and short target `8.0/+2.0`, each at index 1 after a `10.0` entry with one bar held. The entry row deliberately crosses both levels yet remains open until the next row. Signal precedence closes at the carried-row open, emits no event, ignores same-row entry, and does not reopen; a bracket-close collision emits one event and likewise ignores its same-row entry. Ambiguous dual-touch and open-at-level gap tasks exit 2 with the explicit unsupported errors and publish neither ledger nor event artifact.

`ohlc_pessimistic_v1` is a separate strict execution model. It preserves all ordering, signal precedence, entry-row exclusion, and gap failure rules of `ohlc_unambiguous_v1`; only a later non-gap bar touching both inclusive levels differs. It always closes at the initial stop, for both long and short, and emits `initial_stop_pessimistic`. The close increments both `initial_stop_closes` and `pessimistic_ambiguity_resolutions` exactly once. The original unambiguous model continues to fail such bars.

Executed sealing command:

```bash
.venv/bin/python -m unittest tests.test_phase1.Phase1.test_unambiguous_bracket_execution_cli_matrix
```
