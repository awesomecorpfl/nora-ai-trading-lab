# Phase 2 execution-model native canary: authoritative scenario audit

This audit freezes evidence only; it does not alter `simulate_market_v1`. The executable source of truth remains `engine/labengine/src/simulator.rs`, with the ordering implemented for a carried position as: gap-open bracket, signal exit, due maximum-bars exit, then intrabar bracket. An entry is evaluated only while flat, at that row open; it cannot be closed on the entry row.

The canonical fixed-path task set is intentionally compact. Each scenario uses long, one unit, `leave_open`, fixed offset bracket (`SL=1`, `TP=2`) unless stated, and UTC-like synthetic labels `2040.01.01 00:0N`. `E` and `X` mean nullable entry and exit intent. The Stage-2 artifacts materialize each row as a real `labengine <task.json>` input and bind the returned simulator identity.

| Scenario | OHLC rows / E / X | Time | Expected ledger or no-trade | Rules demonstrated |
|---|---|---|---|---|
| `completed_next_open` | r0 10/10/10, F/F; r1 11/11/11, T/F; r2 12/12/12, F/T | — | entry r1 11; exit r2 12 signal | completed-bar intent boundary, next-open entry, ordered ledger |
| `entry_row_excluded_terminal` | r0 10/13/8, T/T | — | no trade; terminal open r0 10 | no same-bar entry/exit, terminal source not executed |
| `gap_stop_over_signal_time` | r0 10/10/10, T/F; r1 8.5/10/8, T/T | 1 | entry r0 10; exit r1 8.5 `initial_stop_gap` | entry-price gap, stop gap, gap over signal/time, no reopen |
| `gap_target` | r0 10/10/10, T/F; r1 12.5/13/12, F/F | — | entry r0 10; exit r1 12.5 `initial_target_gap` | supported take-profit gap |
| `signal_over_time_intrabar` | r0 10/10/10, T/F; r1 10/13/8, T/T | 1 | entry r0 10; exit r1 10 `signal` | signal over due time and ambiguous intrabar |
| `time_over_intrabar` | r0 10/10/10, T/F; r1 10.5/12.5/10, F/F | 1 | entry r0 10; exit r1 10.5 `max_bars_held` | time over intrabar |
| `pessimistic_dual_touch` | r0 10/10/10, T/F; r1 10/12/9, F/F | — | entry r0 10; exit r1 9 `initial_stop_pessimistic` | pessimistic SL/TP ambiguity |
| `nonambiguous_stop` | r0 10/10/10, T/F; r1 10/11/9, F/F | — | entry r0 10; exit r1 9 `initial_stop` | non-ambiguous stop |
| `nonambiguous_target` | r0 10/10/10, T/F; r1 10/12/9.5, F/F | — | entry r0 10; exit r1 12 `initial_target` | non-ambiguous target |
| `signal_exit` | r0 10/10/10, T/F; r1 10.5/11/10, F/T | — | entry r0 10; exit r1 10.5 `signal` | signal exit |
| `time_exit` | r0 10/10/10, T/F; r1 10.5/11/10, F/F | 1 | entry r0 10; exit r1 10.5 `max_bars_held` | time exit |
| `terminal_no_trade` | r0 10/10/10, F/F; r1 11/11/11, F/T | — | no trade; exit ignored while flat | null/terminal-source handling, no pending entry |

`signal` is the canonical evidence reason for a signal close even though the current Rust ledger has no explicit reason field; the evidence assembler derives it from the returned summary/event artifacts. Bracket reasons come from the bracket event artifact and time reason from the time event artifact. The Stage-2 ledger schema binds the derived reason with the returned trade row, so no zero-valued placeholder is used for a null/no-trade result.

Existing supporting fixture families are `phase2_market_simulator_*`, `phase2_initial_bracket_*`, and `phase2_time_exit_*`; combined ordering is sealed by `tests/test_phase1.py` and `docs/phase2c_minimal_market_simulator.md`. The canonical canary adds only the missing fixed task paths needed to run the whole matrix through the real command boundary.
