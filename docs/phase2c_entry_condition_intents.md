# Phase 2C entry conditions and raw intents

The strict version-1 condition is `{schema_version, side: long|short, entry: {signal: {series, type: boolean}, timing: next_open}}`. It is typed, canonicalized, and hashed with `nora-entry-condition-semantic-v1`; labels are excluded.

`build_entry_intents` reads a typed nullable Boolean signal artifact and writes exactly timestamp plus one nullable Boolean output. `intent[0]` is null and `intent[j] = signal[j-1]`; null is preserved, no future row is appended, repeated true values are preserved, and the final source state is reported but not executed. The entry-intent identity binds condition identity, logical input, output name, timestamps, and nullable content.

Implementation is `91c1d90`; final acceptance closure is this commit. Real CLI evidence proves canonical equivalent conditions preserve condition and intent identities; side, signal selection, output-name, and nonterminal input-content changes are identity-sensitive. Strict condition schema, task-envelope, typed-runtime, and malformed-input failures publish neither artifact nor success summary/identity. Entry-condition canonicalization and entry-intent conversion are fully accepted.

Entry-condition canonicalization and signal-to-intent conversion are fully accepted. This is raw next-open eligibility only: true does not place an order, repeated true intents remain unsuppressed, and no position, order, fill, exit, or trade semantics exist. No MQL5 translation or parity has been claimed; the condition is not searchable. Completed-bar signals and next-open entries are locked narrow execution semantics, while Phase 3 remains blocked until the complete Phase 2 parity gate passes.
