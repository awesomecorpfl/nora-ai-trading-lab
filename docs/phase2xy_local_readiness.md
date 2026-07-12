# Phase 2X/Y local readiness

Batch V2 `46329192b3fa4dedf6d3f1f007cc45e7e9cb035b56f06d50097c42d51dbfb9d6`
preflight passes locally. Its staged inventory identity is
`b3ec7cb917cdab309465a8dfcb7a5768b4f079116b32513ae88ff8304f4109de`.

Two fresh independent staging directories are byte-identical for the committed
allowlist. Filesystem-backed **synthetic protocol evidence** verifies exact and
within-tolerance two-target packages, as well as every reconciliation class:
`PASS_EXACT`, `PASS_WITHIN_TOLERANCE`, `FAIL_CONTRACT`, `FAIL_IDENTITY`,
`FAIL_COMPILE`, `FAIL_INTERRUPTED`, `FAIL_INCOMPLETE`, `FAIL_RUNTIME`,
`FAIL_ROW_ALIGNMENT`, `FAIL_NULL_ALIGNMENT`, and `FAIL_VALUE_MISMATCH`.

Returned-result V1 carries schema and package identities, batch/target
identities, compiler/runtime states and references, exact hash/size inventory,
and a bound CSV schema. Ingestion rejects escaping paths and symlinks where
supported, inventory drift, hashes/sizes, malformed CSV, null-token errors and
non-finite values. Reconciliation precedence is contract, identity, compile,
interrupted, incomplete, runtime, row, null, value, tolerance, exact.

No authoritative state is mutated. Evidence publication is atomic, refuses an
existing destination, removes failed temporary output, and repeated valid
publication is byte-identical. The frozen MACD vector identity remains
`da3e3f4a7e72da71b9dc0cd683b3c7f47d65cf5db845f7bfc47aac51e75454f3`; the
percentile vector identity remains
`3cf2b7f64356f83734a4b0317a5f15fc80b6ba4bb5d4b82bf91749f701d16485`.

MACD and percentile are Rust implemented and executable MQL5 generated; local
native batch, returned-result contract, filesystem ingestion, and local
reconciliation are ready. Native execution was not attempted, no native result
was returned or accepted, grammar remains closed, and neither item is
searchable.
