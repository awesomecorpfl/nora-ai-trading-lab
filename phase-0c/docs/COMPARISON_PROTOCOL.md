# Phase 0C comparison protocol (pre-QDM)

Provider identity and acquisition tool identity are separate. QDM is an acquisition/export tool, not a provider or canonical store.

## Candidate symbols and windows

1. **EURUSD** — liquid major; baseline for provider timestamp/gap and spread differences.
2. **GBPJPY** — distinct Asian/London overlap and wider/variable liquidity; exposes session and spread behavior.
3. **XAUUSD** (only if QDM and Darwinex both expose it) — non-FX contract, swap, tick-value and session comparison.

For each: long M1 window `2024-01-01..2025-12-31`; spring DST `2025-03-23..2025-04-06`; autumn DST `2025-10-19..2025-11-02`; bounded ticks `2025-06-03 08:00..12:00 UTC`; weekend edge `2025-06-06 20:00..2025-06-09 04:00 UTC`.

## Measurements

M1: counts, endpoints, duplicates, ordering, missing minutes, weekend/session handling, DST, zero-volume, malformed OHLC, gap distribution, and aligned OHLC differences. Ticks: resolution, ordering, duplicates, gaps, bid/ask, spread distribution, session edges, anomalies. Specifications: digits, point, tick size/value, contract, lot limits/step, swaps/mode/triple day, margin and sessions.

The analyzer accepts explicit CSV mappings; it does not assume QDM layout. It produces a compact JSON summary and must be paired with a completed provenance record.
