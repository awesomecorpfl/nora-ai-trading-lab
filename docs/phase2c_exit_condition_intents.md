# Phase 2C exit conditions and raw exit intents

## Frozen condition

The version-1 typed exit condition is:

```json
{"schema_version":1,"side":"long","exit":{"signal":{"series":"entry_signal","type":"boolean"},"timing":"next_open"}}
```

Only schema version `1`, sides `long` and `short`, Boolean signal references, and timing `next_open` are valid. Unknown fields and malformed values fail closed. Canonical compact JSON is hashed with `nora-exit-condition-semantic-v1`. The frozen fixture condition identity is `efac24c8026e31877c64cb09ddaa167f45d26833d998b6916fd7fd854ee627bd`.

## `build_exit_intents` task and artifact

The strict task envelope is `{task_version: 1, task_type: "build_exit_intents", input_path, output_path, output, condition}`. Its input must contain UTF-8 `timestamp` and the condition's referenced nullable Boolean signal. The requested output name must be non-empty, must not be `timestamp`, and must not conflict with an input column.

The published Parquet artifact is atomically written with exactly `timestamp` and the requested nullable Boolean output column. Timestamps, ordering, and row count are unchanged. The success summary reports task type, rows, side, timing, signal and output columns/types, source and intent true/false/null counts, terminal source signal, condition schema/identity, intent identity, and artifact path. Every count group sums to the row count.

Completed-bar source signal `i` becomes raw eligibility at bar `i + 1` open: `exit_intent[0] = null` and `exit_intent[j] = exit_signal[j - 1]`. Null stays null, repeated true values remain repeated, and the terminal source signal is reported only; it creates no additional row.

The exit-intent identity is SHA-256 in the `nora-exit-intent-semantic-v1` domain. It binds the frozen exit-condition identity, canonical typed input content, requested output name, `timestamp:boolean` output schema, timestamps, and nullable Boolean output content. Paths and Parquet container bytes do not define the identity. Failed task or runtime validation publishes no final artifact and no successful JSON/identity summary.

The committed Cross → AST evaluation → exit-intent fixture produces:

```text
[null, null, null, false, true, true, true, true, true, true, true, true]
```

For 12 rows, source counts are true `9`, false `1`, null `2`; intent counts are true `8`, false `1`, null `3`; the terminal source signal is `true`.
Its frozen exit-intent identity is `ee1eec561a4edace64868240a8201a336ba62b2a632db62dde5400717cef2d2a`.

## Scope boundary

An exit intent is raw close eligibility only: `true` does not close a position, and repeated true intents are unsuppressed. No position, order, fill, trade, SL/TP, cost, or simulator exists. No MQL5 or parity has been claimed; the condition is not searchable. Phase 3 remains blocked; the locked architecture requires narrow parity-gated execution semantics and prohibits search before Phase 2 parity passes.
