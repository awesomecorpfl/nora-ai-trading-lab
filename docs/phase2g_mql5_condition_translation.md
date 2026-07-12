# Phase 2G: deterministic MQL5 condition translation

Phase 2G extends the Python `lab.mql5gen` control-plane generator. It translates only the accepted Phase 2B AST into a nullable MQL5 condition function. It does not generate an EA, indicators, transforms, orders, simulator logic, Strategy Tester code, or parity claim.

## Command and callable

```bash
PYTHONPATH=. python -m lab.mql5gen condition \
  --ast engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json \
  --runtime-manifest tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.manifest.json \
  --output-dir tests/fixtures/phase2g_mql5_condition
```

The callable is `lab.mql5gen.translate_condition(ast_path, runtime_manifest_path, output_dir)`.

## Supported inventory

Nodes, in frozen order:

```text
numeric_series, number, boolean_series, compare, and, or, not
```

Operators, in frozen order:

```text
gt, gte, lt, lte, and, or, not
```

Unsupported nodes/operators fail before publication.

## Runtime dependency

The supplied runtime manifest must exactly match:

```text
runtime_version = nora_mql5_nullable_runtime_v1
runtime_identity = 2ba6078adcd10d991d3ef1ada26baa791a0c6054707a84acaceaa6fe23f2b176
source_sha256 = 42b7239442090a68fdacdc481925cd6b9819b572ea083efce3f3e3cbbb27d2a4
source_filename = NoraPhase2RuntimeV1.mqh
```

The generated header contains exactly one runtime include and does not duplicate the runtime:

```mql5
#include "NoraPhase2RuntimeV1.mqh"
```

## Series binding contract

Referenced series are collected uniquely and sorted lexically by `(series_type, original_series_name)`, with `boolean` before `numeric`. Numeric parameters use `const NoraNullableDoubleV1 &`; Boolean parameters use `NoraTriBoolV1`. Names are MQL5-safe sanitized names with a type/name-derived SHA-256 suffix, preventing collisions after sanitization. The original name, type, and generated parameter name are recorded in the manifest.

The frozen accepted AST bindings are:

```text
boolean close.cross_above.sma3 -> nora_bool_close_cross_above_sma3_47260c9c5e68
boolean sma3.cross_below.close -> nora_bool_sma3_cross_below_close_f82f2c17f999
numeric  sma3                  -> nora_num_sma3_662a95a8677d
```

## Translation rules

Translation is recursive, preserves AST operand order, and performs no simplification, reordering, epsilon comparison, or nullable coercion. Numeric constants are finite deterministic MQL5 literals. Nullable Boolean operations use only Phase 2F helpers; native `&&`, `||`, and `!` are not emitted. Comparisons use `NoraCompare{Gt,Gte,Lt,Lte}V1`.

## Frozen accepted fixture

The generated files are:

```text
tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.mqh
tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.manifest.json
```

Canonical AST identity:

```text
667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664
```

Function names:

```text
NoraCondition_667db0ab50a7f3b9_V1
NoraTrigger_667db0ab50a7f3b9_V1
```

Exact generated nullable evaluator expression:

```text
NoraBoolAndV1(NoraCompareGtV1(nora_num_sma3_662a95a8677d, NoraNumericValueV1(1.1008)), NoraBoolOrV1(nora_bool_close_cross_above_sma3_47260c9c5e68, NoraBoolNotV1(nora_bool_sma3_cross_below_close_f82f2c17f999)))
```

Frozen source SHA-256:

```text
1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4
```

Translation identity (domain `nora.mql5.condition_translator_v1.semantic.v1`):

```text
22ff3c2cc2d387173eb066c428eac99f663263a6d7dda773f44647ec371509bd
```

The identity binds translator version, frozen runtime identity, canonical AST identity/content, inventory, bindings, function names, generated source bytes, and source hash. Paths are excluded.

## Rust semantic evidence

`tests/fixtures/phase2g_translation_evidence.json` was produced by running the real Rust cross/evaluate CLI pipeline against the frozen Phase 2B input fixture. The Rust nullable result vector is:

```text
[null, null, false, true, true, true, true, true, true, true, true, true]
```

The expected MQL5 nullable vector is identical. Applying `NoraConditionTriggersV1` gives:

```text
[false, false, false, true, true, true, true, true, true, true, true, true]
```

The evidence is semantic pre-MT5 evidence only; it is not an MT5 parity claim.

## Repeatability and sensitivity

Two fresh output directories with different AST/output paths produced byte-identical headers, equal source hashes, equal manifests, and equal translation identities.

Changing only the numeric constant to `1.1009` changed:

```text
Rust canonical AST identity: 9ab2e6c138ae0e2b71f10dd902f2d94642a6094948da9be1feca880968fb3d5d
source_sha256:               04b34642ea00d35464ed329265667e3cad33f4721caa57445eb17c4b131643ba
translation_identity:        5fc3c27bb7346a3617f8baaa6a158f95219ba97be57b228dcd73ab7bfd9216a2
```

Changing only `sma3` to `sma4` changed the binding/parameter to `nora_num_sma4_da83dbf7026d` and changed:

```text
Rust canonical AST identity: d6d58b31a872ab988fb64847673350f1836eb097eea75578a6201cdf215895d1
source_sha256:               f27efd069f51ab7682ad7b1b99abad97afbc83c5ffb8008a8c0a585f6fa2a37b
translation_identity:        025ba801e7c348fce8e922a2b8f527c8114422a9130e8bd38360629d5e995aca
```

Neither mutation is committed as a production fixture.

## Atomic failures

Focused CLI failures cover an unsupported node, conflicting series types, a mismatched runtime identity/source contract, and pre-existing generated targets. Each exits non-zero, emits no successful manifest or translation identity, and leaves no newly published condition header or partial file. Existing incompatible targets remain unchanged.

## Regression commands

```bash
cargo test --manifest-path engine/Cargo.toml
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools \
  uv run --with pytest --with 'pyarrow>=20,<24' pytest -q
```

All Phase 2A–2F identities and fixtures remain preserved, including the Phase 2F runtime, canonical/evaluation ASTs, evaluated signal artifact, metrics, named RNG, simulator, bracket/time-exit, condition/intent, indicator/transform, and UTC anchors.
