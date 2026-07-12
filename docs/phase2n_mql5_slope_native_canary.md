# Phase 2N: MQL5 Slope Canary — Native Compilation and Execution

## Status

PASS. One native MetaEditor compile and two native MT5 Strategy Tester execution runs completed successfully.

## Summary

The frozen slope-transform fixture passed in native MQL5 through the MT5 Strategy Tester. Both execution runs produced byte-identical CSV output with identical semantic result identity.

This proves only the accepted fixed-data slope transform.
Broader indicator parity, transform parity, execution-simulator parity, the complete Phase-2 parity gate, and Phase 3 remain open.

## Exact Source and Identity Contracts

### Phase-2M Frozen Contracts (Verified Before SSH)

| Artifact | SHA-256 | Identity |
|----------|---------|----------|
| Slope Runtime (`NoraPhase2SlopeRuntimeV1.mqh`) | `a3b2dc447b59e6800dee7c875e9d25ea2353fc32b04c73391871623c08842c80` | `cb9eee8e4c03d6c6d95c6ba384701187c93730f77fafe3a22a2f8902410c68ae` |
| Slope Tester (`NoraPhase2SlopeTesterCanaryV1.mq5`) | `6d4f2e9f0a7e1dcd33004500dfea8deaad4c5a4e9804e57ef8377369f67a4f53` | `a25fe8a6b459499debdbc9d48c8d4dd498a9684bf67b196501ebed743b48b54d` |
| Nullable Runtime (`NoraPhase2RuntimeV1.mqh`) | `97de0194d7715b32ce104a9889d1a4af46cff6d0759d637f21e41025a98ee043` | `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d` |

### Additional Preserved Identities

| Artifact | Identity |
|----------|----------|
| Rust Input Identity | `5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383` |
| Rust Slope Identity | `45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499` |

### Exact Source Bundle Compiled

```
NoraPhase2RuntimeV1.mqh (tests/fixtures/phase2f_mql5_runtime/)
NoraPhase2SlopeRuntimeV1.mqh (tests/fixtures/phase2m_mql5_slope/)
NoraPhase2SlopeTesterCanaryV1.mq5 (tests/fixtures/phase2m_mql5_slope/)
```

No regeneration or hand-editing of sources was performed.

## Frozen Slope Fixture

### Input Vector (SMA3)

```json
[null, null, 1.1006, 1.1009333333333335, 1.1009666666666666,
 1.1013333333333335, 1.1013666666666666, 1.1017333333333335,
 1.1017666666666666, 1.1021333333333334, 1.1021666666666665,
 1.1025333333333334]
```

### Expected Slope Vector

```json
[null, null, null,
 0.00033333333333351867, 3.333333333310762e-05, 0.00036666666666684833,
 3.333333333310762e-05, 0.00036666666666684833, 3.333333333310762e-05,
 0.00036666666666684833, 3.333333333310762e-05, 0.00036666666666684833]
```

### Frozen Semantics

- Formula: `(value[i] - value[i - 1]) / 1`
- First row null
- Null current endpoint → null output
- Null previous endpoint → null output
- Finite inputs only
- Lookback 2 is unsupported (invalid input, not a variant)
- 12 rows preserved
- Row and timestamp order preserved

### Null Positions

Exactly `[0, 1, 2]` — first two rows are null inputs, third row is warmup (no previous value).

## Compile Results

### Compiler

- **Path**: `C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe`
- **Version**: `5.0.0.5836`
- **Command**: `MetaEditor64.exe /compile:"NoraPhase2SlopeTesterCanaryV1.mq5" /log:"compile.log"`

| Field | Value |
|-------|-------|
| Compiler exit code | 1 (MetaEditor success) |
| Errors | 0 |
| Warnings | 0 |
| Elapsed | 366 ms |
| Normalized compile-log SHA-256 | `9da78716a539422e28ba0d2980a2bc38eb6c6a47462dd979aff52d33e5fd2b15` |
| `.ex5` SHA-256 | `e533c9fae051c80309df584f49751872e8c35f502dc9dac71fb49701681937bf` |
| `.ex5` size | 9,510 bytes |
| Compile-contract identity | `263ccdf2177d6b6e3e85e763332b48cb65f3e2a6c8441d628267c6a82712809a` |

### Includes Resolved (From Compile Log)

1. `NoraPhase2RuntimeV1.mqh` — nullable runtime types
2. `NoraPhase2SlopeRuntimeV1.mqh` — `NoraSlopeLookback1V1()` function

No errors or warnings in the compile log.

## Tester Configuration

```ini
[Tester]
Expert=NoraPhase2N\NoraPhase2SlopeTesterCanaryV1
Symbol=GDAXI
Period=M1
Deposit=5000
Currency=USD
Leverage=20
```

## Execution Results

Both runs launched through `terminal64.exe /config:"tester.ini"` with `ShutdownTerminal=1`.

### Run 1

| Field | Value |
|-------|-------|
| Status | completed |
| All 9 launch stages | confirmed |
| Terminal version | 5.0.0.5836 |
| Raw CSV SHA-256 | `29d5d614e602d47d4badb4430272990b7bcd2c7383f7a7bbd7c511c1b8b10783` |
| Rows | 12 (all passed) |
| Null positions | [0, 1, 2] |
| Semantic-result identity | `221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f` |

### Run 2

| Field | Value |
|-------|-------|
| Status | completed |
| All 9 launch stages | confirmed |
| Terminal version | 5.0.0.5836 |
| Raw CSV SHA-256 | `29d5d614e602d47d4badb4430272990b7bcd2c7383f7a7bbd7c511c1b8b10783` |
| Rows | 12 (all passed) |
| Null positions | [0, 1, 2] |
| Semantic-result identity | `221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f` |

### Native Slope Vector (Both Runs Identical)

```
row 0:  null
row 1:  null
row 2:  null
row 3:  0.0003333333333335
row 4:  0.0000333333333331
row 5:  0.0003666666666668
row 6:  0.0000333333333331
row 7:  0.0003666666666668
row 8:  0.0000333333333331
row 9:  0.0003666666666668
row 10: 0.0000333333333331
row 11: 0.0003666666666668
```

All values are within the accepted `1e-15` tolerance of the frozen expected vector.

## Launch Stages Confirmed (Both Runs)

1. `tester_configuration_loaded` — `.ini` written and terminal config applied
2. `testing_agent_started` — journal confirms agent lifecycle
3. `ea_loaded` — `NoraPhase2SlopeTesterCanaryV1` reference found in journal
4. `ea_initialized` — EA load/init/start match confirmed
5. `fixture_execution_started` — `TesterStop` invocation detected
6. `result_csv_written` — CSV retrieved from Common\Files with fresh timestamp
7. `fixture_execution_completed` — `TesterStop` match confirmed
8. `tester_completed` — terminal64.exe process exited normally
9. `terminal_shutdown` — process shutdown confirmed within timeout

## Comparison

- **Raw CSV byte-identical**: Run 1 and Run 2 CSV SHA-256 both `29d5d614...` — the canary format is deterministic across runs
- **Semantic result identical**: Both runs produce semantic-result identity `221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f`

## Retrieved Artifacts

| Path | Description |
|------|-------------|
| `artifacts/phase2n_compile_run1/NoraPhase2SlopeTesterCanaryV1.ex5` | Compiled EX5 (9,510 bytes) |
| `artifacts/phase2n_compile_run1/compile.log` | MetaEditor compile log |
| `artifacts/phase2n_compile_run1/compile_manifest.json` | Compile contract manifest |
| `artifacts/phase2n_execution_run1/nora_phase2_slope_tester_v1.csv` | Run 1 raw CSV |
| `artifacts/phase2n_execution_run1/execution_manifest.json` | Run 1 execution manifest |
| `artifacts/phase2n_execution_run1/tester.log` | Run 1 tester journal |
| `artifacts/phase2n_execution_run2/nora_phase2_slope_tester_v1.csv` | Run 2 raw CSV |
| `artifacts/phase2n_execution_run2/execution_manifest.json` | Run 2 execution manifest |
| `artifacts/phase2n_execution_run2/tester.log` | Run 2 tester journal |

## Acceptance Gate

- [x] Source hashes match accepted Phase-2M fixtures before SSH
- [x] Zero compile errors, zero warnings
- [x] Includes resolved from intended transferred files
- [x] Fresh EX5 produced (timestamp after compile start)
- [x] Two complete Strategy Tester runs, all 9 stages confirmed each
- [x] Both runs produce byte-identical raw CSV (`29d5d614e602d47d4badb4430272990b7bcd2c7383f7a7bbd7c511c1b8b10783`)
- [x] Both runs produce identical semantic-result identity (`221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f`)
- [x] 12 ordered rows, null at positions [0, 1, 2]
- [x] No unexpected non-finite results
- [x] All Python (105) and Rust (45) regression suites pass
- [x] No Phase-2M generated sources were modified