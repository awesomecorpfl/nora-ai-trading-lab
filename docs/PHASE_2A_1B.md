# Phase 2A-1B: declared clocks and session-time primitives

`labengine::data` retains the Phase-1 canonical reader boundary unchanged.
`labengine::time` derives an executable `ClockModel` from its validated
`TimeContract`; it does not introduce another contract or rewrite source bars.
The UTC fixture's timestamp label remains `2025.06.03 08:00` and is interpreted
as that same UTC local label.

Supported dataset clock declarations are:

- `UTC` with `dst_regime: "no_dst"`;
- an IANA name such as `America/New_York` with `dst_regime: "iana"`;
- `america_new_york_plus_7_v1` with `dst_regime: "new_york_dst_v1"`.

The last is an explicit configurable broker-clock convention, not a default.
It applies New York's IANA DST transition schedule to a local clock seven hours
ahead of New York: UTC+02 while New York is on standard time and UTC+03 while
New York is on daylight time. `broker` resolves to this clock only for that
declared dataset identity. Session and strategy clocks may instead explicitly
name `UTC`, the dataset clock, or an IANA clock.

Local-label resolution is fail-closed: a spring-forward label that does not
exist returns an error, and an autumn fold with two possible instants returns an
error. No side is selected implicitly. Conversion from a known UTC instant to a
declared local clock is deterministic; the reverse resolution is only accepted
when it is unique.

The module supplies weekday/time-of-day, declared trading-day identity,
cross-midnight windows, Friday-close, opening-range, rollover, daily-reset, and
Monday-open primitives. A trading-day operation rejects a legacy Phase-1
contract that omitted `trading_day_boundary`; it does not pick a default.
Likewise, higher-timeframe anchoring is parsed only when explicitly declared,
for the future aggregation slice to consume. No aggregation is implemented in
this phase.
