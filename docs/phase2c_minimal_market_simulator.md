# Phase 2C minimal stateful market simulator

`simulate_market_v1` accepts `{task_version, task_type, market_path, entry_intent_path, exit_intent_path, output_path, config}`. Config version `1` permits only `side: long|short`, `price_column: open`, `position_policy: one_at_a_time`, and `terminal_policy: leave_open`; all task and config fields are strict.

Market data must have aligned UTF-8 `timestamp` and finite non-null Float64 `open`. Both intent artifacts must have exactly aligned timestamps and their configured native nullable Boolean columns. No joins, timestamp conversion, filling, or coercion occurs.

At each open, an open position exits on true exit intent and ignores that row's entry intent. Otherwise it remains open and true entry is ignored. When flat, true entry opens and that row's exit intent is ignored; otherwise true exit is ignored. There is no same-row close/reopen. Null means no action. Quantity is one; long P&L is exit minus entry, short P&L is entry minus exit, and closed `bars_held` is exit index minus entry index. A final open position is left open and excluded from the ledger.

The atomic closed-trade ledger has `trade_id`, entry/exit timestamps and indices, entry/exit prices, `bars_held`, and `gross_pnl_per_unit`. Identity uses `nora-market-simulator-v1-semantic-v1` over typed config, market/intents, closed ledger, and terminal state; paths do not affect it. Failures publish no final ledger or successful identity summary.

The committed chain produces four long trades, rows `4→5`, `6→7`, `8→9`, and `10→11`, all held one bar. Entry prices are `1.1013, 1.1017, 1.1021, 1.1025`; exits are `1.1010, 1.1014, 1.1018, 1.1022`; gross P&Ls are approximately `-0.0003` each, totaling `-0.0012`. It opens and closes four trades, ignores four exits while flat and four entries while open, and ends flat. Its identity is `f913e382d93cfc125ae57171cfcf0bb28a5f8a7abaa77c3dab13eda6bd023c17`.

This is not the complete v1 simulator. No SL/TP, intrabar path or ambiguity, costs, sizing, trailing, time exits, pending orders, partial exits, MQL5, parity, or searchable grammar exists. Phase 3 remains blocked.
