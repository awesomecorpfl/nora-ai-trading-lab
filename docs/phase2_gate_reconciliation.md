# Stage 7: Phase-2 gate reconciliation

Verdict: the complete Phase-2 gate remains **false**. MACD, Percentile, and the frozen execution-model canary have narrow native parity acceptance; none of those acceptances admits new grammar or searchability. Search and Phase 3 remain closed.

The machine-readable matrix is `tests/fixtures/phase2_gate_reconciliation.json`. Its identifiers resolve to the detailed implementation inventory in `tests/fixtures/phase2_remaining_parity_inventory.json`; no Rust implementation, MQL5 source, or local canary is promoted to native parity without committed evidence.

## Accepted-node matrix

| Node | Exact accepted restriction | Rust / AST / evaluation | MQL5 / local generation | Native evidence / parity | Grammar | Search | Evidence commit |
|---|---|---|---|---|---|---|---|
| MACD | close; EMA 2/4; signal 3; arithmetic seeds; committed recurrence; compact signal; original-row alignment; histogram subtraction; CSV V3; GDAXI/M1 and AUDCAD/M1 | implemented / not integrated / Rust identity bound in current package | executable V3 runtime and tester / deterministic | committed compile plus four executions / accepted | false | false | `23ddd31` |
| Percentile | nullable aligned finite source; lookback 4; average rank; committed null windows; CSV V3; GDAXI/M1 and AUDCAD/M1 | implemented / not integrated / Rust identity bound in current package | executable V3 runtime and tester / deterministic | committed compile plus four executions / accepted | false | false | `23ddd31` |
| Execution model | frozen twelve scenarios; completed-bar signals; next-open entry; gap price; signal/time exits; gap > signal > time > intrabar; pessimistic dual touch; terminal no-trade | implemented / fixed Rust evidence / plan `597e997b…` | executable fixed-path runtime/tester / deterministic | compile plus four independent exact reconciliations / accepted | false | false | acceptance index `2e8312d5…` |
| ATR3/Wilder | typed high/low/close; period 3; Wilder | implemented / integrated in local AST gate | generated / deterministic | committed native evidence / accepted | true for this restricted node only | false | `fc363988` |
| Distance/ATR | same-row value/reference over admitted ATR3/Wilder denominator | implemented / integrated in local AST gate | generated / deterministic | committed native evidence / accepted | true for this restricted node only | false | `fc363988` |
| Slope, SMA/cross, condition | frozen canary contracts only | implemented / typed local paths | generated / deterministic | committed legacy/native canary evidence / accepted | false | false | `f201077`, `92851bf` |

The remaining Layer-1 indicators are implemented in Rust where recorded by the source inventory, but have no complete MQL5/native parity chain and remain non-searchable. Execution simulator semantics are native-reconciled only for the exact embedded twelve-scenario contract; this does not establish broker-clock, strategy, or broader grammar coverage.

## Execution-canary local readiness

The execution canary has genuine compiler evidence, a sealed final packet, and four independently fresh returned packages. A1/A2 and B1/B2 are repeatable, GDAXI/M1 and AUDCAD/M1 are semantically identical, all decision and price fields reconcile exactly, and parity is accepted narrowly. Grammar and searchability remain false.

## Binding gate matrix

| Requirement | Status | Concrete reason | Smallest evidence tranche |
|---|---|---|---|
| Synthetic execution fixtures: next-open, signal exit, time exit, combined precedence, determinism | ACCEPTED | Frozen Rust and native fixed-path ledgers reconcile exactly in four independent host-context runs | None for this restricted contract |
| Layer-1 indicator/transform coverage | PARTIAL | MACD and Percentile are now accepted narrowly; ATR/Distance-ATR, slope, SMA/cross, and condition evidence do not complete the all-Layer-1 gate | Reconcile remaining Layer-1 contracts and typed AST admission boundaries |
| Declared strategy/session/broker clock; broker fixtures; DST spring/fall; Friday close; rollover; Monday open; ORB; derived timeframe anchoring | BLOCKED | No paired native time/session canary exists | Freeze one broker-time fixture inventory and matched native canary |
| Ten hand-designed strategies, initial-v1 grammar coverage, trade-by-trade reconciliation, parity budget | BLOCKED | Zero completed durable strategy reconciliations | One strategy canary after execution semantics are native-reconciled |
| Repeated Linux experiment replay: trades, metrics, simulator outcomes, canonical hashes | PARTIAL | Component-level deterministic tests exist; no complete experiment replay bundle | One repeated experiment artifact binding all outputs and hashes |
| Placebo/scrambled-data edge destruction | BLOCKED | No known-edge scramble fixture or destruction statistic | Define one deterministic scramble and expected edge-destruction measure |

The statuses are intentionally independent: native parity acceptance does not imply grammar admission; grammar admission does not imply searchability; and any non-accepted binding requirement keeps the complete gate false.

The machine-readable matrix assigns every binding sub-requirement independently. All eight frozen engine/execution checks are now `ACCEPTED`; Layer-1 Rust, executable MQL5, and committed native coverage remain `PARTIAL`, with remaining Layer-1 targets `BLOCKED`; broker-clock/session, strategy, complete Linux replay, and placebo gates remain non-accepted and therefore keep Phase 2 incomplete.

## Identity reconciliation

Historical scaffold identities remain recorded for MACD and Percentile. The corrected current Percentile package supersedes stale package identity `cd14eae8…`; its current runtime, tester, and package identities are `d727c93b…`, `f8e07706…`, and `5ba578e6…`. The current native batch is `593dc35e…`; historical batches are `46329192…` and `ad2b40b5…`; staged inventory identity is `33db36cb…`. Compiler policy is `nora.metaeditor_cli_success_v1` for MetaEditor build `5.0.0.5836`. Raw native evidence and formal acceptance are preserved at the pushed baseline commit `23ddd31d…`.

Superseded identities cannot be selected as current: current package/source bindings are content-verified by the native-evidence tests and the stale Percentile package is explicitly rejected.

## Next critical path

Select paired time/broker-clock native fixtures. The execution model is now fixed and native-reconciled, so broker/session clock behavior is the highest-dependency remaining prerequisite for the ten hand-designed strategy reconciliations. This remains before search and Phase 3.
