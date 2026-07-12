# Phase 2S: ATR and Distance/ATR AST admission

Phase 2S adds a backward-compatible feature-expression extension to the schema-1 typed AST. Existing `kind` nodes, canonical JSON, and identities are unchanged. New numeric feature nodes use typed `type` objects: ATR is limited to numeric `high`, `low`, and `close` series with `period: 3` and `method: "wilder"`; Distance/ATR is limited to aligned numeric `value` and `reference` series with an admitted ATR denominator.

Rust evaluates complete aligned nullable numeric series through the accepted `indicators::atr` and `indicators::transform_distance_atr` kernels. Feature dependencies are deduplicated by canonical feature identity and ordered deterministically. Distance/ATR is same-row and null for null or non-positive denominators.

The MQL5 bridge is deliberately two-stage. Its Stage-A feature plan emits deterministic precomputed buffers which call the accepted Phase-2P `NoraAtr3V1` and `NoraDistanceAtrV1` runtime functions. The existing scalar nullable-condition translator is unchanged and can consume row-indexed buffers. No indicator formula is copied into the translator and no accepted runtime source is regenerated.

Admission is narrow: ATR3/Wilder and same-row Distance/ATR only. The accepted Phase-2Q native semantic identity is `8a912bd9152d16c8e94b1a96210d2cc6917c5b2639f615b0ecd4931dac2669f2`. This admission does not authorize search or Phase 3; the overall Phase-2 gate remains blocked.

## Identity mapping

The repair fixture records separate canonical node, Rust-evaluation, and MQL5-translation identities. ATR uses canonical `dc2a4299ef2a09dc4a78e8597411a925efa17fce4b6f3cf90ed1f591353f8e55`, Rust evaluation `9ae012127d7c79ca433d69292a835e2b50721ec05a38cd08ce3603a15f2b0211`, and translation `e8b07eea8fd6d4052a95dcde0ade1e6b31769d7bc320ce6f1c0ddc1a3d0da253`. Distance/ATR uses canonical `1e6cb47b6a61339caa759bdd5b4d5d75bced27545763cfd4009a7a2dd9d05d28`, Rust evaluation `f40773899d21fc6523c3857dfacbe8c5375e1ca41b247155d66a72b8d4a10b3c`, and translation `01fb662e6d31d4f20efdfaef1f9ad0c6c701ae171015983f870e74f8afa6a583`. The combined canonical AST is `aab0586cdf3bb2d5eea6210f3dcec9b86a52cf116a60a46930d7075cab0c3211`; the combined deterministic plan translation is unchanged at `c78dc2437e47b14868a225916eb9acad4fd4bb0bdd0893e73f5db12032c02311`.
