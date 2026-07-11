# Phase 2C entry conditions and raw intents

The strict version-1 condition is `{schema_version, side: long|short, entry: {signal: {series, type: boolean}, timing: next_open}}`. It is typed, canonicalized, and hashed with `nora-entry-condition-semantic-v1`; labels are excluded.

`build_entry_intents` reads a typed nullable Boolean signal artifact and writes exactly timestamp plus one nullable Boolean output. `intent[0]` is null and `intent[j] = signal[j-1]`; null is preserved, no future row is appended, repeated true values are preserved, and the final source state is reported but not executed. The entry-intent identity binds condition identity, logical input, output name, timestamps, and nullable content.

This is raw eligibility only: true does not place an order. No positions, deduplication, exits, SL/TP, sizing, fills, costs, trades, simulator, MQL5, parity, or searchable grammar exists. Phase 3 remains blocked.
