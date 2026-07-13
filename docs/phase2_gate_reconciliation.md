# Stage 7: Phase-2 gate reconciliation

Verdict: the complete Phase-2 gate remains **false**. MACD and Percentile native parity are accepted only for their exact fixed contracts; neither is grammar-admitted or searchable. Search and Phase 3 remain closed.

The machine-readable matrix is `tests/fixtures/phase2_gate_reconciliation.json`. Its 50 identifiers resolve to the detailed implementation inventory in `tests/fixtures/phase2_remaining_parity_inventory.json`; no Rust implementation, MQL5 source, or local canary is promoted to native parity without committed evidence.

## Accepted-node matrix

| Node | Exact accepted restriction | Rust / AST / evaluation | MQL5 / local generation | Native evidence / parity | Grammar | Search | Evidence commit |
|---|---|---|---|---|---|---|---|
| MACD | close; EMA 2/4; signal 3; arithmetic seeds; committed recurrence; compact signal; original-row alignment; histogram subtraction; CSV V3; GDAXI/M1 and AUDCAD/M1 | implemented / not integrated / Rust identity bound in current package | executable V3 runtime and tester / deterministic | committed compile plus four executions / accepted | false | false | `23ddd31` |
| Percentile | nullable aligned finite source; lookback 4; average rank; committed null windows; CSV V3; GDAXI/M1 and AUDCAD/M1 | implemented / not integrated / Rust identity bound in current package | executable V3 runtime and tester / deterministic | committed compile plus four executions / accepted | false | false | `23ddd31` |
| ATR3/Wilder | typed high/low/close; period 3; Wilder | implemented / integrated in local AST gate | generated / deterministic | committed native evidence / accepted | true for this restricted node only | false | `fc363988` |
| Distance/ATR | same-row value/reference over admitted ATR3/Wilder denominator | implemented / integrated in local AST gate | generated / deterministic | committed native evidence / accepted | true for this restricted node only | false | `fc363988` |
| Slope, SMA/cross, condition | frozen canary contracts only | implemented / typed local paths | generated / deterministic | committed legacy/native canary evidence / accepted | false | false | `f201077`, `92851bf` |

The remaining Layer-1 indicators are implemented in Rust where recorded by the source inventory, but have no complete MQL5/native parity chain and remain non-searchable. Execution simulator semantics (next-open entry, signal exit, time exit, initial brackets, combined precedence, pessimistic intrabar ambiguity, and gap-open behavior) have deterministic Rust fixtures only; they are not native reconciled.

## Execution-canary local readiness

The execution canary now has committed Rust scenario evidence, deterministic executable MQL5 source generation, and a local immutable batch. Native execution and native parity remain false; grammar and searchability are unchanged. The next native matrix is exactly compile evidence plus two GDAXI/M1 and two AUDCAD/M1 returned packages, four reconciliations, within-context repeatability, and cross-context neutrality.

## Binding gate matrix

| Requirement | Status | Concrete reason | Smallest evidence tranche |
|---|---|---|---|
| Synthetic execution fixtures: next-open, signal exit, time exit, combined precedence, determinism | PARTIAL | Rust fixtures pass, but no native execution-model reconciliation | One order-free native fixture covering next-open plus one exit and precedence |
| Layer-1 indicator/transform coverage | PARTIAL | MACD and Percentile are now accepted narrowly; ATR/Distance-ATR, slope, SMA/cross, and condition evidence do not complete the all-Layer-1 gate | Reconcile remaining Layer-1 contracts and typed AST admission boundaries |
| Declared strategy/session/broker clock; broker fixtures; DST spring/fall; Friday close; rollover; Monday open; ORB; derived timeframe anchoring | BLOCKED | No paired native time/session canary exists | Freeze one broker-time fixture inventory and matched native canary |
| Ten hand-designed strategies, initial-v1 grammar coverage, trade-by-trade reconciliation, parity budget | BLOCKED | Zero completed durable strategy reconciliations | One strategy canary after execution semantics are native-reconciled |
| Repeated Linux experiment replay: trades, metrics, simulator outcomes, canonical hashes | PARTIAL | Component-level deterministic tests exist; no complete experiment replay bundle | One repeated experiment artifact binding all outputs and hashes |
| Placebo/scrambled-data edge destruction | BLOCKED | No known-edge scramble fixture or destruction statistic | Define one deterministic scramble and expected edge-destruction measure |

The statuses are intentionally independent: native parity acceptance does not imply grammar admission; grammar admission does not imply searchability; and any non-accepted binding requirement keeps the complete gate false.

The machine-readable matrix assigns every binding sub-requirement individually. In summary: all eight engine/execution checks are `PARTIAL`; Layer-1 Rust, executable MQL5, and committed native coverage are `PARTIAL`, with remaining Layer-1 targets `BLOCKED`; the declared strategy/session clock is `IMPLEMENTED_UNPROVED` and every broker-time, DST, Friday-close, rollover, Monday-open, ORB, and derived-timeframe fixture is `ABSENT`; completed strategies are `ABSENT`, the required suite and initial-v1 coverage are `BLOCKED`, and trade-by-trade/parity-budget evidence is `ABSENT`; Linux replay is `PARTIAL`, while trades, metrics, simulator outcomes, and canonical hashes are `IMPLEMENTED_UNPROVED`; placebo/scrambled edge destruction is `ABSENT`.

## Identity reconciliation

Historical scaffold identities remain recorded for MACD and Percentile. The corrected current Percentile package supersedes stale package identity `cd14eae8…`; its current runtime, tester, and package identities are `d727c93b…`, `f8e07706…`, and `5ba578e6…`. The current native batch is `593dc35e…`; historical batches are `46329192…` and `ad2b40b5…`; staged inventory identity is `33db36cb…`. Compiler policy is `nora.metaeditor_cli_success_v1` for MetaEditor build `5.0.0.5836`. Raw native evidence and formal acceptance are preserved at the pushed baseline commit `23ddd31d…`.

Superseded identities cannot be selected as current: current package/source bindings are content-verified by the native-evidence tests and the stale Percentile package is explicitly rejected.

## Next critical path

Select execution-model native reconciliation. It has the highest dependency value with the least new scope: strategy reconciliation depends on it, time/session fixtures need a stable fill/exit model, and it closes more of the binding gate than another isolated indicator. This remains before search and Phase 3.
