# Phase 2J: MQL5 condition execution canary

## Verdict: BLOCKED

The execution command and strict reconciliation surface are implemented, but the existing `nora-win10` Darwinex terminal cannot currently execute a Startup-configured script reproducibly. The native canary was not reported as passed. No execution manifest, accepted CSV, semantic-result identity, Strategy Tester run, order, or parity claim was published.

## Command and ownership

Python owns orchestration and CSV reconciliation:

```bash
PYTHONPATH=. python -m lab.mt5 execute-condition-canary \
  --compile-manifest artifacts/phase2i_compile/compile_manifest.json \
  --ex5 artifacts/phase2i_compile/NoraPhase2ConditionFixtureV1.ex5 \
  --fixture-manifest tests/fixtures/phase2h_mql5_condition_fixture/NoraPhase2ConditionFixtureV1.manifest.json \
  --output-dir artifacts/phase2j_execution
```

The implementation reuses the Phase 2I SSH/SCP boundary and the installed:

```text
C:\\Program Files\\Darwinex MetaTrader 5\\terminal64.exe
version 5.0.0.5836
```

The Windows helper stages the verified `.ex5` under the existing terminal data root, deletes the old local result, launches one run with the existing `[StartUp] Script=...` configuration convention, waits for a fresh result, retrieves logs/CSV, and removes only its run-local staging. It does not use Strategy Tester or an EA.

## Contracts and parser

Local preflight verifies the repaired runtime, condition, fixture, compile-contract identity, compiler version, zero compile errors/warnings, and the `.ex5` hash before SSH. The parser requires the exact 11-column CSV schema, 12 ordered rows, one summary, canonical nullable/Boolean text, expected vectors, row passes, and internally consistent summary counts. Successful publication is atomic and would contain the CSV, execution log, and `execution_manifest.json`.

Execution identities use `nora.mt5.condition_execution_v1.semantic.v1`; semantic-result identities use `nora.mt5.condition_semantic_result_v1.semantic.v1` and exclude the `.ex5` container hash. The two identities are implemented but no successful value exists because native execution is blocked.

## Blocked native evidence

The bounded command used the repaired Phase 2I compile artifact (`a9985b2140f40b2ae35d2facb5123b58c807dd455de98eeab740efdbbac75b5a`). The helper deleted the prior result and confirmed no fresh `nora_phase2_condition_fixture_v1.csv` appeared before its 60-second timeout. It returned:

```text
native execution failed: fresh result CSV was not created before timeout
```

The terminal log shows the requested Startup script configuration was loaded, followed by failure to open the existing `EURUSD` chart profile (`Charts open chart 'EURUSD' failed ...`). The script therefore never produced a CSV. The local failure log SHA-256 is:

```text
ecc5754496a7470d3037e897f9f8e7934325c102f04df900f5f6dda76b4639b6
```

This is consistent with the preserved Phase 0A-H finding that the existing config-driven Startup invocation did not execute the importer and that the terminal remained running until the owned process was stopped. Creating a separate portable terminal/data directory or using UI automation would expand beyond the accepted Phase 2J boundary, so no such workaround was attempted.

Evidence is committed in `tests/fixtures/phase2j_blocked_execution_evidence.json`.

## Local failure checks

Focused tests prove:

- a compile/fixture contract mismatch fails before `_ssh` and publishes no execution manifest;
- malformed or mismatching CSV rows are rejected deterministically;
- no successful identity can be produced from a row mismatch.

The native mismatch path was not intentionally induced in the committed script. Any native mismatch follows the same strict parser failure path, retaining retrieved CSV/log evidence and publishing no successful manifest or semantic identity.

## Scope

This task did not execute the script successfully, retrieve a passing CSV, run Strategy Tester, generate an EA, calculate indicators, place orders, or claim complete Phase-2 parity. Phase 3 remains out of scope.

## Regression commands

```bash
cargo test --manifest-path engine/Cargo.toml
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools \
  uv run --with pytest --with 'pyarrow>=20,<24' pytest -q
```
