# Phase 2B typed AST evaluation

`evaluate_ast` uses the existing task envelope with `task_version`, `task_type`, `input_path`, `output_path`, `output`, and the accepted typed `ast`. It reads a typed Parquet artifact, resolves numeric and nullable Boolean references by declared runtime type, and atomically writes exactly `timestamp` and the requested nullable Boolean output. Timestamps and row order are preserved without conversion.

Comparisons are exact and nullable: if either numeric operand is null the result is null. `not` preserves null. `and` and `or` use strong Kleene logic: AND is false if either input is false, true only for true/true, otherwise null; OR is true if either input is true, false only for false/false, otherwise null. Arguments are evaluated left to right without reordering or simplification.

The evaluated identity uses `nora-ast-evaluation-semantic-v1` and commits to canonical AST identity, a logical typed-input content commitment, requested output name/schema, timestamps, and nullable Boolean output. Failed tasks publish no final artifact, success summary, or success identity.

The committed task is `engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json`: it evaluates `sma3 > 1.1008` AND (`close.cross_above.sma3` OR NOT `sma3.cross_below.close`). Its AST identity is `667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664`; evaluated identity is `e098bfc87897802116a54ed21cdc2f530619201a22c55f41ac965e39b1bbd5a9`.

This produces a deterministic signal artifact only. Null is not a trade decision; no entry/exit, position, execution, simulator, MQL5 translation, parity, or searchable grammar exists. Phase 3 remains blocked.
