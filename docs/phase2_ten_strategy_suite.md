# Phase 2 ten-strategy parity suite

This local-only contract freezes the five committed trend-pullback designs and five committed close-confirmed breakout designs as `nora.phase2_ten_strategy_suite_v1`. It is a canary suite for deterministic trade-ledger parity; it is not broad grammar admission, searchability, strategy search, or proof that Phase 2 is complete.

Trend-pullback uses only accepted EMA, Slope, ATR, Distance/ATR, and Cross semantics. Close-confirmed breakout uses only accepted Highest, Lowest, and Cross semantics, with the level window ending one completed bar before the decision bar. All decisions use completed bars, entries occur at the next open, positions cannot overlap, terminal source signals are not executed, and accepted execution precedence remains `gap → signal → time → intrabar` with pessimistic dual-touch handling.

The committed fixtures are synthetic embedded OHLC vectors. No external market data, terminal history, timestamp conversion, account state, or trading operation is part of this suite. Native compilation and execution remain pending after this local tranche.
