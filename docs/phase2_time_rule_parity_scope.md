# Phase 2 time-rule parity scope

This tranche preserves existing UTC fixtures exactly. They remain UTC labels and are never
rewritten into broker time. Future production datasets are manually prepared in their declared
broker clock; the engine validates that declaration and does not perform an automatic production
conversion.

| Item | Current implementation | Evidence | Gap for this tranche |
|---|---|---|---|
| Declared dataset/strategy/session clocks | `TimeContract`, `ClockModel` | Rust unit tests | Versioned canary contracts and native evidence |
| NY plus seven | `america_new_york_plus_7_v1`, NY DST-derived +02/+03 | Rust transition tests | Fixed epoch vector and MQL5 parity |
| Source and bar timestamp semantics | UTC/broker-local; start-of-bar only | canonical reader tests | Explicit fixed canary rows |
| Session and overnight windows | `TimeWindow` supports midnight crossing | Rust unit tests | Parameterized fixture/native rows |
| Spring/fall DST | gap/fold local labels fail closed; UTC projection is ordered | Rust transition tests | Epoch-based native rows and anchors |
| Friday close | generic strategy-clock predicate | Rust unit test at 17:00 | Fixed 16:25 NY contract rows |
| Rollover/Monday/ORB/reset | parameterized primitives | Rust unit tests | Frozen parameters and native rows |
| M5/H1 anchoring | contract-aware aggregation | Rust aggregation tests | Fixed DST/session-anchor evidence |
| Conversion state | history and repeated target rejection | reader tests | Explicit canary rejection rows |

No universal rollover, Monday, ORB, or session default is introduced. Each is an explicit
fixture/task parameter. MT5 is used only as a fixed-vector validation appliance.
