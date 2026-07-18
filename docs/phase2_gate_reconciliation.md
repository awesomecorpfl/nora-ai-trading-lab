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

## Embedded smoke and broker-native validation

The embedded ten-strategy smoke canary is a narrow exact-reconciliation contract: it validates compile/load/tester/EA lifecycle and execution of synthetic fixtures. It must not be used as a broker-native performance verdict.

The ten-strategy smoke canary is a system-validation fixture, not a claim that the hand-designed strategies have a meaningful edge. It validates compile/load/tester/EA lifecycle, embedded fixture execution, durable publication, and evidence integrity. Broker-native similarity and edge-survival tooling is retained for a later finalist-stage campaign, where strategy quality—not merely system health—will be the question.

## Binding gate matrix

| Requirement | Status | Concrete reason | Smallest evidence tranche |
|---|---|---|---|
| Synthetic execution fixtures: next-open, signal exit, time exit, combined precedence, determinism | ACCEPTED | Frozen Rust and native fixed-path ledgers reconcile exactly in four independent host-context runs | None for this restricted contract |
| Layer-1 indicator/transform coverage | PARTIAL | MACD and Percentile are now accepted narrowly; ATR/Distance-ATR, slope, SMA/cross, and condition evidence do not complete the all-Layer-1 gate | Reconcile remaining Layer-1 contracts and typed AST admission boundaries |
| Declared strategy/session/broker clock; broker fixtures; DST spring/fall; Friday close; parameterized rollover/Monday/ORB; derived timeframe anchoring | ACCEPTED | Exact 18-scenario time-rule canary, four independent host-neutral packages | Holiday calendars and universal production window defaults remain unsupported |
| Ten hand-designed strategies: embedded smoke execution health | PENDING | Corrected compiler evidence exists; fresh native smoke must confirm compile/load/tester/EA lifecycle and embedded fixture execution | One bounded smoke package |
| Ten hand-designed strategies: broker-native edge survival | DEFERRED | These are system-test fixtures, not finalist strategies; no edge claim is intended here | Revisit only for a selected finalist with frozen native data/cost/budget decisions |
| Repeated Linux experiment replay: trades, metrics, simulator outcomes, canonical hashes | PARTIAL | Component-level deterministic tests exist; no complete experiment replay bundle | One repeated experiment artifact binding all outputs and hashes |
| Placebo/scrambled-data edge destruction | BLOCKED | No known-edge scramble fixture or destruction statistic | Define one deterministic scramble and expected edge-destruction measure |

The statuses are intentionally independent: native parity acceptance does not imply grammar admission; grammar admission does not imply searchability; and any non-accepted binding requirement keeps the complete gate false.

The machine-readable matrix assigns every binding sub-requirement independently. All eight frozen engine/execution checks are now `ACCEPTED`; Layer-1 Rust, executable MQL5, and committed native coverage remain `PARTIAL`, with remaining Layer-1 targets `BLOCKED`; broker-clock/session, strategy, complete Linux replay, and placebo gates remain non-accepted and therefore keep Phase 2 incomplete.

## Identity reconciliation

Historical scaffold identities remain recorded for MACD and Percentile. The corrected current Percentile package supersedes stale package identity `cd14eae8…`; its current runtime, tester, and package identities are `d727c93b…`, `f8e07706…`, and `5ba578e6…`. The current native batch is `593dc35e…`; historical batches are `46329192…` and `ad2b40b5…`; staged inventory identity is `33db36cb…`. Compiler policy is `nora.metaeditor_cli_success_v1` for MetaEditor build `5.0.0.5836`. Raw native evidence and formal acceptance are preserved at the pushed baseline commit `23ddd31d…`.

Superseded identities cannot be selected as current: current package/source bindings are content-verified by the native-evidence tests and the stale Percentile package is explicitly rejected.

## Next critical path

Run one bounded embedded smoke package first. Its acceptance question is system health, not strategy quality. Broker-native edge-survival work belongs to a later finalist-stage tranche with its own human decisions. This remains before search and Phase 3.
