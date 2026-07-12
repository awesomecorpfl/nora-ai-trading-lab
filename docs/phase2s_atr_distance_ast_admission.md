# Phase 2S: ATR and Distance/ATR AST admission

Phase 2S adds a backward-compatible feature-expression extension to the schema-1 typed AST. Existing `kind` nodes, canonical JSON, and identities are unchanged. New numeric feature nodes use typed `type` objects: ATR is limited to numeric `high`, `low`, and `close` series with `period: 3` and `method: "wilder"`; Distance/ATR is limited to aligned numeric `value` and `reference` series with an admitted ATR denominator.

Rust evaluates complete aligned nullable numeric series through the accepted `indicators::atr` and `indicators::transform_distance_atr` kernels. Feature dependencies are deduplicated by canonical feature identity and ordered deterministically. Distance/ATR is same-row and null for null or non-positive denominators.

The MQL5 bridge is deliberately two-stage. Its Stage-A feature plan emits deterministic precomputed buffers which call the accepted Phase-2P `NoraAtr3V1` and `NoraDistanceAtrV1` runtime functions. The existing scalar nullable-condition translator is unchanged and can consume row-indexed buffers. No indicator formula is copied into the translator and no accepted runtime source is regenerated.

Admission is narrow: ATR3/Wilder and same-row Distance/ATR only. The accepted Phase-2Q native semantic identity is `8a912bd9152d16c8e94b1a96210d2cc6917c5b2639f615b0ecd4931dac2669f2`. This admission does not authorize search or Phase 3; the overall Phase-2 gate remains blocked.
