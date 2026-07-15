# Nora AI Trading Lab — Implementation Status

**Evidence snapshot:** `main` at `ab989628390f027ebc32ef749b8ffb8b6bfcb319`  
**Independent test result at review:** Python `359 passed, 1 skipped`; Rust `49 passed`.

This document states what is implemented. It does not authorize future phases.

## Status vocabulary

- `VERIFIED` — code, tests, and committed evidence inspected.
- `VERIFIED_NARROW` — verified within a deliberately restricted contract.
- `CONDITIONAL` — usable with documented bounded gaps.
- `PENDING_NATIVE` — local/compiler evidence exists; required native acceptance does not.
- `NOT_IMPLEMENTED` — planned but absent.
- `DEFERRED` — intentionally outside the current phase.

## Phase summary

| Area | Status | Evidence summary | Remaining gap |
|---|---|---|---|
| Phase 0A MT5 harness | CONDITIONAL | repository-owned SSH/MT5 harness; two pinned runs; semantic equality | tester-kill/VM-restart recovery and finalist-scale hardening |
| Phase 0B throughput | VERIFIED | 5,256,000 synthetic M1 bars; 1,000 candidates; 168.53 candidate-backtests/sec at four workers; about 290 MiB peak RSS | production workload calibration during authorized Phase 3 |
| Phase 0C data characterization | CONDITIONAL | Dukascopy/QDM M1 characterization and data-contract evidence | later Darwinex broker-reference exports and production datasets |
| Phase 1 foundation | CONDITIONAL | SQLite WAL state, task identities, guarded transitions, artifacts, checkpoints, idempotent registration, dummy resume workflow | no worker pool; service lifecycle and backup procedures deferred |
| Phase 2 local engine | VERIFIED_NARROW | ingestion, time, aggregation, indicators, AST, intents, simulator, metrics, RNG | grammar completion, full admission chains, replay/placebo gates |
| Phase 2 MQL5/compiler | VERIFIED_NARROW | deterministic generation and corrected v2 compiler evidence | four corrected native suite runs and exact reconciliation |
| Phase 2 complete | FALSE | repository gate remains false | E1–E5 and D1–D7 in `PHASE2_COMPLETION_GATE.md` |
| Phase 3 | UNAUTHORIZED | no search module or active grammar; all searchable flags false | separate signed authorization after Phase-2 closure |

## Implemented foundation

### Data ingestion

The Rust reader validates canonical M1 Parquet fail-closed:

- required metadata and source hash;
- declared timeframe and time contract;
- schema and numeric types;
- strictly increasing timestamps;
- duplicate rejection;
- OHLC sanity and finite values;
- semantic content identity.

### Time and aggregation

Implemented and tested:

- explicit dataset clock and DST identities;
- New York plus seven hours with New York DST behavior;
- gap/fold rejection;
- conversion history and double-conversion protection;
- declared session and strategy clocks;
- M5 and H1 aggregation anchored to the declared contract;
- leading/trailing partial-window handling;
- internal-gap rejection.

### Indicator kernels

Rust kernels exist for the planned Layer-1 set, including:

- SMA, EMA, Wilder smoothing, ATR, RSI, ROC, ER, KAMA;
- MACD, Highest, Lowest, CCI, Stochastic;
- Bollinger, Keltner, Linear Regression, ADX;
- Session OHLC and VWAP.

Multi-output indicators use named outputs. Kernel implementation does not imply AST admission, MQL5 translation, native parity, or searchability.

### Typed transforms

Implemented as typed series transforms:

- Cross;
- Slope;
- DistanceAtr;
- Percentile.

Important gap: Cross and Slope do not yet exist as typed AST nodes. The initial proposed family grammars are therefore not yet expressible through the canonical AST.

### Typed AST and identities

The canonical AST currently supports a narrow set including numeric/Boolean series, ATR, DistanceAtr, EMA, Highest, Lowest, comparisons, AND, OR, and NOT. It provides:

- strict parsing and typing;
- canonical JSON;
- stable domain-separated SHA-256 identities;
- deterministic evaluation;
- entry- and exit-intent tasks.

### Execution simulator

`simulate_market_v1` is natively accepted within its frozen contract:

- completed-bar decisions;
- next-open entries;
- one position;
- fixed stop/target brackets;
- gap handling at bar open;
- signal and time exits;
- pessimistic same-bar ambiguity;
- precedence: gap → signal → time → intrabar;
- per-unit gross ledger.

There is no account-currency cost or sizing model yet.

### Execution-policy divergence

Two versionable exit-price conventions currently coexist:

1. `simulate_market_v1`: signal and time exits at the current bar open.
2. ten-strategy suite: signal/time/Friday exits at the decision-bar close.

Both are internally identified; Phase-3 grammars must bind one explicit execution-policy identity. The recommended Phase-3 default is the natively accepted bar-open convention.

### Metrics

Current code implements narrow closed-trade metrics:

- trade counts;
- gross and net per-unit result;
- average trade;
- win rate;
- average win/loss;
- profit factor with null when undefined.

Not yet implemented as a complete production protocol:

- account-currency costs;
- money equity and money drawdown;
- stagnation, exposure, concentration, and cost-percentage metrics;
- full metric registry.

### Determinism and evidence

Implemented:

- named ChaCha20 RNG streams;
- domain-separated identities;
- atomic artifact publication;
- content-bound manifests;
- compiler/execution identity split;
- genuine returned-package importer;
- explicit rejection of superseded identities.

## Layer-1 evidence state

The authoritative matrix contains 22 nodes:

- 10 `ACCEPTED` under narrow evidence contracts;
- 12 `IMPLEMENTED_UNPROVED`;
- 0 searchable.

Accepted component evidence remains valid where not dependent on the defective historical ten-strategy ATR runtime. Historical ten-strategy native runs are preserved as failure evidence and do not count toward corrected acceptance.

## Ten-strategy suite

Verified locally:

- suite identity frozen;
- corrected Wilder ATR source generated;
- v2 compiler/execution identity split;
- genuine EX5 with zero errors and warnings;
- sealed corrected Rust evidence;
- persistent Windows evidence runner and atomic return contract.

Still missing:

- GDAXI/M1 A1 and A2 corrected native runs;
- AUDCAD/M1 B1 and B2 corrected native runs;
- exact ten-ledger reconciliation in all four packages;
- repeatability proof;
- formal acceptance record.

## Control-plane scaling

The control plane currently executes tasks sequentially. A bounded worker pool is new implementation, not hardening of an existing pool. It is required before large Phase-3 batches but is not a substitute for Phase-2 evidence.

## Repository hygiene

Four historical untracked Phase-0A result directories were present at the reviewed snapshot. They are not accepted evidence. Gasper must explicitly choose to archive/commit them as historical evidence or delete them.
