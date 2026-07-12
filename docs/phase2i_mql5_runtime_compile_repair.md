# Phase 2I repair: MQL5 runtime compile canary

## Verdict

PASS after a narrow generator-level MQL5 syntax repair. The script was not executed and no MT5 parity claim is made.

## Root defect and cascade

The original MetaEditor 5.0.0.5836 log in the preserved Phase 2I blocked evidence reported its first errors in `NoraPhase2RuntimeV1.mqh` at lines 32, 37, 50, 58, 63, and 71. The generated runtime used C++-style value `const` qualifiers and named scalar parameters `input`; MetaEditor treats `input` as a reserved token. The later field, comparison, and return diagnostics were parser cascades.

After removing value `const` qualifiers, renaming the reserved parameters, and using MQL5 object reference syntax for nullable structs, the next compiler run reduced to the genuine MQL5 rule: `NoraNullableDoubleV1` objects are reference-only. The final generator correction uses `const NoraNullableDoubleV1 &` for nullable struct inputs and retains `double &output` only for the explicit numeric extraction output. Scalar Boolean parameters are passed by value with non-reserved names.

No Rust AST semantics changed.

## Generator and resealed identities

The repair was made in `lab/mql5gen/__init__.py`, then the Phase 2F runtime, Phase 2G condition, and Phase 2H fixture were regenerated through their existing commands. Semantic vectors and ordered bindings remain unchanged.

| artifact | old source / identity | repaired source / identity |
|---|---|---|
| runtime | `42b7239442090a68fdacdc481925cd6b9819b572ea083efce3f3e3cbbb27d2a4` / `2ba6078adcd10d991d3ef1ada26baa791a0c6054707a84acaceaa6fe23f2b176` | `97de0194d7715b32ce104a9889d1a4af46cff6d0759d637f21e41025a98ee043` / `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d` |
| condition | `1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4` / `22ff3c2cc2d387173eb066c428eac99f663263a6d7dda773f44647ec371509bd` | `1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4` / `1fa3d6613348a2fa532c4393e2a95795546c9cc5e2c86d010ee30fa9fe9632af` |
| fixture | `b3b98996545d1277d4b2fa51db7c14c943ad733c018717110dab45e05f0022a7` / `ab09f18f446897f5cd28adcfc4a1260688cc8c397c58ba400516db6006e89d1e` | `b3b98996545d1277d4b2fa51db7c14c943ad733c018717110dab45e05f0022a7` / `d283a5a37e64f426f39f813d1f2f68fa64e4c92cbd61b2cdbd59b9f1eac1f858` |

The old values remain historical inputs in the preserved Phase 2I blocked commit/evidence; they were not silently rewritten.

## Local semantic gate

Before Windows contact, the complete Rust/Python semantic checks passed. The nullable truth tables, all four comparisons, Rust cross-check, accepted nullable vector, trigger vector, deterministic generation, and path independence remained unchanged.

## Native compile runs

Command:

```bash
PYTHONPATH=. python -m lab.mt5 compile-condition-canary \
  --runtime tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.mqh \
  --condition tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.mqh \
  --script tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.mq5 \
  --output-dir artifacts/phase2i_compile
```

Observed compiler:

```text
C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe
5.0.0.5836
```

Both fresh remote/Fedora runs passed acceptance with `0` errors, `0` warnings, and non-empty `.ex5` output. MetaEditor returned process exit code `1` for both successful runs; the harness records it but accepts only the parsed zero-error/zero-warning log plus non-empty `.ex5`, as required by the compile contract.

Both normalized logs have SHA-256 `d36387714d0bcaba022368561a2ddea4482471efd07714f7574e1790561a7792`. Both compile-contract identities match:

```text
a089a280eeebe82be78660410391323887cade8d36c0c26c2173e8ab4076558d
```

The `.ex5` hashes differed, so MetaEditor container bytes are empirically nondeterministic here:

```text
run 1: a9985b2140f40b2ae35d2facb5123b58c807dd455de98eeab740efdbbac75b5a (10834 bytes)
run 2: 55581f9c1497737108723cd8396e6bcf2921e9c306fcde5d28cecdb5e109b5b9 (10980 bytes)
```

Normalized two-run evidence is committed in `tests/fixtures/phase2i_repaired_compile_evidence.json`.

## Failure evidence

The preserved local source-hash mismatch test still fails before SSH and publishes no accepted artifact. After the success path worked, a temporary syntax-invalid script was compiled through the existing helper. MetaEditor returned one error and zero warnings; the retrieved log SHA-256 was `3add703a422fa5abd7dc27cc1dbf473b94d634fd0e3e909344956dde58fdae50`. The repository published no success manifest or accepted `.ex5`; the invalid source was not committed.

## Regression commands

```bash
cargo test --manifest-path engine/Cargo.toml
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools \
  uv run --with pytest --with 'pyarrow>=20,<24' pytest -q
```

No script execution, CSV retrieval, Strategy Tester run, EA generation, or parity claim occurred.
