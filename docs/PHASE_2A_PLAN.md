# Phase 2A plan

- Extend `engine/labengine` into `data`, `time`, `indicators`, `transforms`, `sim`, `metrics`, and `rng` modules, retaining `labengine <task.json>` JSON/file invocation.
- Canonical input is M1 OHLCV plus optional spread and immutable contract metadata. Rust validates the contract’s timezone/DST/session/strategy clocks and rejects UTC-only or repeated conversion history; it does not convert timestamps implicitly.
- The broker-time model is a versioned named contract, including `america_new_york_plus_7_v1`; trading-day aggregation anchors to the declared local session clock. M5/M15/H1 aggregation uses local minute buckets, explicit incomplete bars, summed volume and last spread.
- Indicators implement completed-bar vectors with `None` warmup values; transforms consume completed indices only. Tests use hand-checkable paths.
- The simulator has one position, completed-bar signal / next-open entry, initial stop/target, pessimistic same-M1-bar ambiguity, gap-at-open fills, time/signal exits and deterministic cost interfaces.
- Named RNG streams derive from stable identifiers. Metrics use balance-equity trade ledger semantics and define zero-denominator behavior.
- Fixtures cover DST/time rules, aggregation, execution mechanics, deterministic replay and scrambled-data integrity. No AST/search/MQL5/MT5 campaign is included.
