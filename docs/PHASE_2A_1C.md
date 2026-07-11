# Phase 2A-1C: contract-aware aggregation and task boundary

`aggregate_m1` supports `M5` and `H1` from canonical M1 only.  It resolves each
unchanged source label through the declared dataset clock, then groups in the
declared `higher_timeframe_anchoring` clock (`session_clock` or
`strategy_clock`).  Legacy Phase-1 contracts without that optional declaration
use `session_clock`; this is explicit in output provenance.  If a
`trading_day_boundary` is declared, every higher-timeframe grid restarts at
that boundary in the strategy clock and the resulting instant is projected to
the anchoring clock.  Thus a window cannot cross a declared trading day, and
UTC/Unix flooring is never substituted for the contract.

The source labels are never rewritten.  The output timestamp is the grouping
anchor instant rendered in the declared dataset clock.  This is label selection
for the derived bar, not a conversion-history event; `conversion_history` is
copied untouched and derived metadata records
`aggregation_is_timezone_conversion: false`.

OHLC is first open, maximum high, minimum low, and final close.  `volume` is
the sum only if every constituent is non-null; otherwise it is null.  `spread`
is the arithmetic mean only if every constituent is non-null; otherwise it is
null.  Missing values are never treated as zero.

The only supported completeness policy is `omit_edge_partials_v1`: the first
and last incomplete windows may be omitted and are counted.  An incomplete
interior window, non-one-minute constituent instant spacing, duplicate labels,
or out-of-order labels fails closed.  DST gaps/folds retain the 1B fail-closed
resolution rule.

The `labengine <task.json>` task schema is strict and versioned
(`task_version: 1`): `validate_dataset` accepts `input_path` and optional
`expected_contract_version: 1`; `aggregate_m1` accepts `input_path`,
`target_timeframe`, `output_path`, and `completeness_policy`.  Unknown fields,
unknown versions/types, malformed input/output paths, and unsupported
timeframes fail with exit code 2 and JSON error output.

Aggregation writes a task-owned same-directory `.<name>.<pid>.partial` file,
checks that it is a nonempty Parquet result, then renames it to the requested
new output path.  Existing output paths are rejected.  The derived Parquet
retains the canonical columns and source contract metadata, and adds
`nora.derived_contract` (time clocks, source/derived timeframe, source semantic
identity, policy/version, conversion state) plus `nora.semantic_sha256`.
