# Phase 2B typed AST foundation

This checkpoint introduces only a hand-authored, deterministic Rust AST document: `{schema_version: 1, root: ...}`. The exact node inventory is `numeric_series`, `number`, `boolean_series`, `compare` (`gt`, `gte`, `lt`, `lte`), `and`, `or`, and `not`.

`numeric_series` and `number` are Numeric; `boolean_series` is Boolean; `compare` takes two Numeric operands and returns Boolean; `and` and `or` take at least two Boolean arguments and return Boolean; `not` takes one Boolean argument and returns Boolean. The root must be Boolean. Every document, node, and reference object rejects unknown fields. References are declarations only: their kind and declared type must agree, but they are not runtime-resolved here.

Canonical JSON is emitted from the typed representation. It includes `schema_version`, lower-case node/operator spellings, typed numeric constants (`50` and `50.0` are identical), and normalizes negative zero to zero. Object order and formatting do not matter; `and`/`or` argument order is preserved. There is no sorting, deduplication, simplification, or algebraic/logical rewrite. The semantic SHA-256 is over the canonical AST with the `nora-ast-semantic-v1` domain prefix.

The `canonicalize_ast` task uses the existing versioned task envelope with `task_version`, `task_type`, `output_path`, and `ast`. It atomically publishes a final canonical JSON artifact and success summary containing schema version, Boolean root type, semantic identity, and artifact path. Failed tasks publish neither final artifact nor success summary/identity.

The committed structural fixture is `engine/labengine/tests/fixtures/phase2_ast_task.json`; its frozen semantic identity is `7f6898acef2fb8a2cfa2d07f951931dd68834e6729e2d1c57952dd3f5f5f0afd`.

Deliberately deferred: runtime AST evaluation, market-data loading, entry/exit and risk schemas, execution or simulation, MQL5 translation, parity, grammar registration, and sampling. This AST is not searchable. The concrete searchable node inventory is not permanently admitted until Rust, MQL5, and parity evidence exist. Phase 3 remains blocked.
