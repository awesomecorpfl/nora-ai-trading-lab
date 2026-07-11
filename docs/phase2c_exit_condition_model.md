# Phase 2C exit-condition document model

This commit defines the exit-condition document only. It does not produce an exit-intent artifact and it does not close a position.

## Frozen version-1 schema

```json
{
  "schema_version": 1,
  "side": "long",
  "exit": {
    "signal": {
      "series": "entry_signal",
      "type": "boolean"
    },
    "timing": "next_open"
  }
}
```

`schema_version` is the integer `1`. `side` is exactly `long` or `short` and identifies the position side eligible to close. `exit.signal.series` is a non-empty string; `exit.signal.type` is exactly `boolean`; and `exit.timing` is exactly `next_open`. Unknown fields are rejected at the document, `exit`, and signal-reference levels, as are missing fields and wrong JSON types.

Canonical JSON is generated from the typed document with the repository's compact JSON convention. It includes the schema version, serializes enum values in lowercase, is independent of source key order and whitespace, and is stable under parse/serialize round trips. It does not rewrite or simplify the condition.

The semantic identity is SHA-256 over the domain `nora-exit-condition-semantic-v1` followed by the canonical JSON bytes. It binds the schema version, side, Boolean signal reference, and timing.

## Deferred

No exit-intent artifact is produced; no position is closed. No simulator, trade, SL/TP, costs, MQL5, parity, or searchable grammar exists. Phase 3 remains blocked. The locked architecture requires narrow, parity-gated execution semantics and prohibits search before Phase 2 parity passes.
