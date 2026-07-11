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

Canonical research storage should retain an unambiguous UTC instant and source timestamp semantics. This Phase 0C sample is UTC, with no export-time DST conversion. It does **not** establish UTC as the only production strategy clock.

Phase 1 planning must support an explicit strategy/evaluation clock: UTC or a named target-broker timezone/DST convention. A broker-time projection must be deterministic from the UTC instant, carry its IANA timezone/rule version (or broker session rule) in provenance, and be used for session filters, daily boundaries, swap/rollover and MT5 parity checks. No fixed-hour shift is acceptable.

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
