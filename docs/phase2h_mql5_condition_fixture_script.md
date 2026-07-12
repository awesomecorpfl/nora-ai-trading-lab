# Phase 2H: deterministic MQL5 condition fixture script

Phase 2H adds a Python-generated MQL5 source fixture only. It does not compile or execute MQL5, access MT5 data, generate an EA, place orders, or make a parity claim.

## Command and callable

```bash
PYTHONPATH=. python -m lab.mql5gen fixture-script \
  --condition-manifest tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.manifest.json \
  --evidence tests/fixtures/phase2g_translation_evidence.json \
  --output-dir tests/fixtures/phase2h_mql5_condition_fixture
```

Callable:

```python
lab.mql5gen.generate_fixture_script(condition_manifest_path, evidence_path, output_dir)
```

## Frozen dependencies

The generator rejects missing, malformed, extra-field, or mismatched contracts. Required values are:

```text
runtime_identity = 2ba6078adcd10d991d3ef1ada26baa791a0c6054707a84acaceaa6fe23f2b176
runtime_source_sha256 = 42b7239442090a68fdacdc481925cd6b9819b572ea083efce3f3e3cbbb27d2a4
condition_translation_identity = 22ff3c2cc2d387173eb066c428eac99f663263a6d7dda773f44647ec371509bd
condition_source_sha256 = 1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4
canonical_ast_identity = 667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664
evaluated_signal_identity = e098bfc87897802116a54ed21cdc2f530619201a22c55f41ac965e39b1bbd5a9
```

## Embedded fixture and script behavior

The committed evidence supplies exactly 12 ordered rows. Bindings are taken from the condition manifest, in its order:

```text
boolean close.cross_above.sma3
boolean sma3.cross_below.close
numeric sma3
```

Every binding is validated on every row. Numeric values are finite or null; Boolean values are exactly null, false, or true. Numeric nulls use a separate null mask and `NoraNumericNullV1`; no NaN or sentinel is emitted. Boolean nulls use `NORA_BOOL_NULL_V1`.

The generated script is `NoraPhase2ConditionFixtureV1.mq5`. It includes exactly:

```mql5
#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2ConditionV1.mqh"
```

`OnStart()` opens `nora_phase2_condition_fixture_v1.csv`, writes the fixed header, iterates rows `0..11`, calls the generated nullable condition and trigger functions once per row, compares each result with embedded expectations, writes every row, then writes a summary record. It has deterministic file-open and row-count failure branches and never calls market, order, position, or trade APIs.

## CSV schema

The fixed columns are:

```text
record_type,row_index,actual_nullable,expected_nullable,actual_trigger,expected_trigger,row_pass,row_count,passed_rows,failed_rows,overall_pass
```

Normal rows use `record_type=row` and `row_index=0..11`. The final record uses `record_type=summary` and `row_index=-1`; summary values are in the final five columns. Nullable text is exactly `null`, `false`, or `true`.

## Frozen manifest and vectors

Generated files:

```text
tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.mq5
tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.manifest.json
```

Expected nullable vector:

```text
[null, null, false, true, true, true, true, true, true, true, true, true]
```

Expected trigger vector:

```text
[false, false, false, true, true, true, true, true, true, true, true, true]
```

Frozen script SHA-256:

```text
b3b98996545d1277d4b2fa51db7c14c943ad733c018717110dab45e05f0022a7
```

Fixture identity, using domain `nora.mql5.condition_fixture_script_v1.semantic.v1`:

```text
ab09f18f446897f5cd28adcfc4a1260688cc8c397c58ba400516db6006e89d1e
```

The identity binds fixture protocol, runtime and translation identities, AST identity, ordered bindings, exact row inputs, expected vectors, CSV schema, result filename, source bytes, and source hash. Paths are excluded.

## Repeatability and sensitivity

Two fresh output directories produced byte-identical scripts, equal source hashes, equal manifests, and equal fixture identities.

Changing one expected trigger value (and its row expectation) produced:

```text
source_sha256 = 6e1efa50a2a9001976e2f5e88b2a6e019867c03f5ee8562a5d5563a1aba142ae
fixture_identity = 89a9b5e689fae7e845570dd23455dbb660ce468cdc77da742ff9a666c4f8a3b1
```

Changing row 2's `sma3` input from `1.1006` to `1.1007` produced:

```text
source_sha256 = af13e9bd5fc7d601520efb5254e47a88e1add43a7f883c8c2ea66d6350f8c2ba
fixture_identity = 41c777db25d39b03941bf5186d499fe706aa82c0399dd779182a64062c929226
```

Neither mutation is committed as an accepted fixture.

## Static checks and atomic failures

Focused source checks verify `OnStart`, both frozen includes, exact generated condition/trigger names, the fixed CSV filename, absence of timestamps/paths, and absence of `OrderSend`, `CTrade`, buy, sell, position, and market calls. These are source-contract checks only; MQL5 is not compiled or executed.

Focused CLI failures cover incorrect condition identity, missing evidence binding, invalid Boolean evidence, and pre-existing targets. Each returns non-zero, publishes no manifest or fixture identity, and leaves no newly published script or partial file. Existing incompatible targets are not overwritten.

## Regression commands

```bash
cargo test --manifest-path engine/Cargo.toml
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools \
  uv run --with pytest --with 'pyarrow>=20,<24' pytest -q
```

All previous Phase 2A–2G metrics, RNG, simulator, bracket, time-exit, indicator, transform, AST, condition, intent, time-contract, UTC, runtime, and translation identities remain preserved.
