# Phase 2I: MQL5 condition compile canary

## Verdict: BLOCKED

The repository-owned compile-only orchestration reached the existing Windows 10 MetaEditor environment, but the frozen Phase-2F runtime header does not compile in that environment. Per the Phase 2I boundary, no Phase-2F, Phase-2G, or Phase-2H source was modified.

No successful `.ex5` or compile manifest is published.

## Existing harness and command

The implementation is Python-owned under `lab/mt5`. It reuses the Phase-0A SSH/SCP configuration and Windows terminal path conventions:

- SSH host alias: `nora-win10` (`127.0.0.1:2222`, existing `~/.ssh/nora_win10` key)
- existing Windows terminal: `C:\Program Files\Darwinex MetaTrader 5`
- existing compiler: `C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe`
- existing staging convention: user-profile-owned `NoraPhase2I` directories

The repository command is:

```bash
PYTHONPATH=. python -m lab.mt5 compile-condition-canary \
  --runtime tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.mqh \
  --condition tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.mqh \
  --script tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.mq5 \
  --output-dir artifacts/phase2i_compile
```

The Windows helper is `phase-0a-h/windows/compile-condition-canary.ps1`. It stages only the three supplied files, invokes MetaEditor with `/compile` and `/log`, captures the process exit code, parses deterministic error/warning counts, retrieves the log/result, and removes the run-local remote staging directory.

## Frozen preflight

All local source and manifest checks passed before SSH contact:

```text
Runtime source SHA-256:   42b7239442090a68fdacdc481925cd6b9819b572ea083efce3f3e3cbbb27d2a4
Condition source SHA-256: 1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4
Fixture source SHA-256:   b3b98996545d1277d4b2fa51db7c14c943ad733c018717110dab45e05f0022a7

Runtime identity:    2ba6078adcd10d991d3ef1ada26baa791a0c6054707a84acaceaa6fe23f2b176
Condition identity:  22ff3c2cc2d387173eb066c428eac99f663263a6d7dda773f44647ec371509bd
Fixture identity:    ab09f18f446897f5cd28adcfc4a1260688cc8c397c58ba400516db6006e89d1e
```

## Compiler evidence

Observed compiler:

```text
path:    C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe
version: 5.0.0.5836
```

The compiler process completed with exit code `0`, but acceptance failed because the compiler log contained `31 errors` and `1 warning`. No non-empty `.ex5` was accepted.

The retrieved UTF-16 compiler log has SHA-256:

```text
4dbcd8d472c086209f9b0e8cc80d3d2ce17caabe4d723b08dcc0d79eca64d5d9
```

The normalized blocked result is committed as `tests/fixtures/phase2i_blocked_compile_evidence.json`.

Normalized first compiler errors:

```text
NoraPhase2RuntimeV1.mqh(32,43): error 149 unexpected token
NoraPhase2RuntimeV1.mqh(37,54): error 149 unexpected token
NoraPhase2RuntimeV1.mqh(50,54): error 149 unexpected token
NoraPhase2RuntimeV1.mqh(58,54): error 155 'input' - comma expected
NoraPhase2RuntimeV1.mqh(63,59): error 155 'input' - comma expected
NoraPhase2RuntimeV1.mqh(71,49): error 149 unexpected token
```

The errors are in the frozen runtime function signatures/expressions, before condition-fixture logic can be accepted. This is a genuine generated-source defect, not a staging or compiler-process failure.

Because compilation is blocked, there are no successful compile-contract identities, `.ex5` hashes, or two-run success results. The `.ex5` container was not treated as an artifact.

## Failure evidence

The local preflight test mutates one source byte and proves a deterministic hash-mismatch failure before `_ssh` is reached, with no manifest or accepted `.ex5`. The compiler failure above retrieved the complete log and published no successful manifest or `.ex5`. Frozen source files remain untouched.

## Regression commands

```bash
cargo test --manifest-path engine/Cargo.toml
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools \
  uv run --with pytest --with 'pyarrow>=20,<24' pytest -q
```

The compile canary was not reported as successful, no script execution was attempted, and no MT5 parity claim was made.
