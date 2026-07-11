# Phase 0C data contract — completed draft

## Roles and provenance

| Role | Decision |
| --- | --- |
| Research M1 provider | **Dukascopy** |
| Acquisition/export tool | **Quant Data Manager** (QDM), build 125.2692 |
| Native MT5 parity reference | Darwinex MT5, investor/read-only terminal, when captured |
| Broker economics/specification reference | Darwinex MT5 `SymbolInfo*` fields and current broker contract/session metadata |

Provider and tool are separate fields. QDM is neither a data provider nor a runtime dependency.

Every raw artifact must record provider, tool/version, local and source symbols, acquisition interval and granularity, source/output time semantics, DST transformation, export format/settings, SHA-256, rows and endpoints. Derived slices add a parent SHA-256 and exact inclusive bounds.

## Time model

Canonical research storage must retain unambiguous timestamp semantics and source timestamp semantics. It may store and evaluate directly in the declared broker/trading timezone; a UTC instant is optional reference/interoperability metadata, not the mandatory strategy clock. This Phase 0C sample is UTC, with no export-time DST conversion. It does **not** establish UTC as the only production strategy clock.

Phase 1 planning must support explicit timezone identity, DST regime/rule version, source timestamp semantics, bar timestamp semantics, session clock, strategy/evaluation clock, optional UTC reference instant, and provenance for every conversion. A conversion, when used, must be deterministic, reproducible and guarded against accidental double conversion; no fixed-hour shift is acceptable. Strategy rules use the declared strategy clock for session filters, daily boundaries, swap/rollover and MT5 parity checks. The current production preference for Darwinex, Fusion and the intended IC Markets account is the common New York +7 broker-time convention (UTC+02/UTC+03 with the relevant New York DST schedule), while future named timezone contracts remain supported.

## M1 contract

- Bar convention: start-of-bar, as configured in QDM; one-minute timestamps are UTC-aligned.
- Canonical higher timeframes are derived internally from canonical M1, never separately mixed provider bars.
- Reject unparseable time, non-numeric OHLC, `low > min(open, high, close)`, or `high < max(open, low, close)`.
- Preserve all raw gaps. Classify scheduled provider session/holiday closures separately from unexpected intraday gaps; do not fill either silently.
- Preserve zero volume as observed; it is not a missing-value marker in this sample.

## Tick contract

- Keep provider bid and ask independently, with the maximum exported timestamp precision; do not synthesize a mid price as the raw quote.
- Retain date-level raw acquisition/export where QDM requires it, then create a hashed, bounded derived slice for analysis.
- Reject/flag unordered timestamps, duplicate timestamps, missing bid/ask, crossed quotes and long quote gaps; thresholds are reporting policy, not data mutation.

## Boundary

The intended pipeline remains: immutable staged raw → hash/provenance → validation report → future lab-owned canonical store. Phase 0C creates no canonical Parquet store and does not start Phase 1.
