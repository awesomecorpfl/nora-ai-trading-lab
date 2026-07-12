# Phase 2J: MQL5 condition execution canary

## Verdict: BLOCKED

The historical native canary remains blocked and no successful execution evidence is published. The narrow launch repair is implemented, but the established SSH endpoint was unavailable during this continuation (`127.0.0.1:2222: connection refused`), so the repaired helper could not inspect the terminal or execute either native run. No execution manifest, accepted CSV, semantic-result identity, Strategy Tester run, order, or parity claim was published.

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

The Windows helper stages the verified `.ex5` under the existing terminal data root, deletes the old local result, launches one run with an explicit Startup chart contract, waits for a fresh result, retrieves logs/CSV/journal/stage evidence, and removes only its run-local staging. It does not use Strategy Tester or an EA.

## Launch diagnosis and repair boundary

The preserved failed run hard-coded `Symbol=EURUSD` in its generated `[StartUp]` configuration. Its terminal evidence says the Startup script configuration loaded, then the existing/restored chart profile failed to open an `EURUSD` chart; no `OnStart()` CSV appeared. Thus the requested Startup symbol and restored profile both referenced `EURUSD`. The historical evidence does not prove the Darwinex server connection, nor whether a second terminal process owned the installation; the old helper did not record those facts. It also does not prove that the script loaded, only that its Startup configuration was read.

The exact broker-native symbol selected is `GDAXI`, from the accepted Phase-0A harness verdict: two unattended native MT5 runs completed `GDAXI / Strategy 3.85.120 / H1 / 2020.07.01–2026.07.01`. The Phase-0A-H custom-symbol spike was not used as symbol evidence.

```text
requested_symbol=GDAXI
resolved_broker_symbol=GDAXI
evidence_source=phase-0a-harness/docs/VERDICT.md
```

The helper uses `NoraPhase2ConditionCanaryV1`. If absent, it copies existing valid profile material containing the pinned `GDAXI` chart into that dedicated profile and removes the temporary profile in `finally`; it does not invent chart/profile binary formats. It refuses an unrelated existing `terminal64.exe` process, launches one owned process with a bounded wait, records its PID, requires `ShutdownTerminal=1` to close it, and retains normalized journal/config/stage evidence on failure.

The final intended Startup contract is:

```ini
[StartUp]
Script=NoraPhase2J\NoraPhase2ConditionFixtureV1
Symbol=GDAXI
Period=M1
ShutdownTerminal=1
```

The helper also passes `/profile:"NoraPhase2ConditionCanaryV1"` explicitly. A successful result requires `terminal_started`, `startup_configuration_loaded`, `chart_opened`, `script_loaded`, `script_started`, `result_csv_created`, `script_completed`, and `terminal_shutdown`.

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

Evidence is committed in `tests/fixtures/phase2j_blocked_execution_evidence.json` and remains unchanged as historical evidence. The exact Phase-2I compile artifacts were not present locally; the requested first execution command therefore failed preflight with `compile manifest is unreadable or malformed`, and the compile boundary reached the unavailable SSH endpoint. No native CSV hash, continuation `.ex5` hash, execution identity, or semantic-result identity exists.

## Local failure checks

Focused tests prove:

- a compile/fixture contract mismatch fails before `_ssh` and publishes no execution manifest;
- malformed or mismatching CSV rows are rejected deterministically;
- no successful identity can be produced from a row mismatch.

The native mismatch path was not intentionally induced in the committed script. Any native mismatch follows the same strict parser failure path, retaining retrieved CSV/log evidence and publishing no successful manifest or semantic identity.

Focused launch-stage checks reject unavailable symbols, stale/conflicting processes, chart-open timeout, and script-never-loaded evidence. Each is deterministic and cannot produce a successful manifest or semantic-result identity.

## Scope

This passes one native nullable-condition semantic canary only.
The complete Phase-2 Rust↔MT5 parity gate remains open.
Phase 3 remains blocked.

This continuation did not execute the script successfully, retrieve a passing CSV, run Strategy Tester, generate an EA, calculate indicators, place orders, or claim complete Phase-2 parity.

## Regression commands

```bash
cargo test --manifest-path engine/Cargo.toml
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools \
  uv run --with pytest --with 'pyarrow>=20,<24' pytest -q
```
