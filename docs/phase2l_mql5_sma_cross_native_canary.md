# Phase 2L: MQL5 SMA and Cross Native Canary

## Status

PASS. Two native compile runs and two native MT5 Strategy Tester execution runs completed successfully.

## Summary

The frozen SMA3, cross-above, cross-below, and nullable-condition fixture passed in native MQL5 through the MT5 Strategy Tester.

This proves only the accepted fixed-data SMA/cross/condition fixture.
Broader indicator parity, transform parity, execution-simulator parity, the complete Phase-2 parity gate, and Phase 3 remain open.

## Exact Source and Identity Contracts

### Phase-2K Frozen Contracts (Verified Before SSH)

| Artifact | SHA-256 | Identity |
|----------|---------|----------|
| Series Runtime (`NoraPhase2SeriesRuntimeV1.mqh`) | `6fbbe35045be59cdf571a623e38a213ca053be32fab153f858d461c1d4ac1b2d` | `4102f23095201f5c37e8a6737d32f22eb31713f4f0ec9cae68803e6d3efbce8e` |
| Series Tester (`NoraPhase2SeriesTesterCanaryV1.mq5`) | `bc62801db8965d268e192d3dadb8ba7b11a7c5e3d5a432fbadd3f2241a4d2757` | `78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4` |

### Additional Preserved Identities

| Artifact | Identity |
|----------|----------|
| Nullable Runtime | `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d` |
| Condition Translation | `1fa3d6613348a2fa532c4393e2a95795546c9cc5e2c86d010ee30fa9fe9632af` |
| Evaluation AST | `667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664` |
| Phase-2J Semantic-Result | `b66f60ad5ae4cc036d29197063e2dbe355cafac96085c359e92783ac74da74e4` |

### Exact Source Bundle Compiled

```
NoraPhase2RuntimeV1.mqh (tests/fixtures/phase2f_mql5_runtime/)
NoraPhase2SeriesRuntimeV1.mqh (tests/fixtures/phase2k_mql5_sma_cross/runtime/)
NoraPhase2ConditionV1.mqh (tests/fixtures/phase2g_mql5_condition/)
NoraPhase2SeriesTesterCanaryV1.mq5 (tests/fixtures/phase2k_mql5_sma_cross/tester/)
```

No regeneration or hand-editing of sources was performed.

## Compile Results

### Compiler
- **Path**: `C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe`
- **Version**: `5.0.0.5836`

### Run 1
| Field | Value |
|-------|-------|
| Compiler exit code | 1 (MetaEditor success) |
| Errors | 0 |
| Warnings | 0 |
| Normalized compile-log SHA-256 | `44362cf0dd73f3fe4ebc2888acb55e3f50d772884f4c411931d914c4e1875bb3` |
| `.ex5` SHA-256 | `6299874748ca333f5eface76d41807fd90658bd47fe56c1da1f22085696d5fb5` |
| `.ex5` size | 13,050 bytes |
| Compile-contract identity | `51042f17b3268fbce9619fe74d2ba52eb50ceff92281be0df51270b95887a1fa` |

### Run 2
| Field | Value |
|-------|-------|
| Compiler exit code | 1 (MetaEditor success) |
| Errors | 0 |
| Warnings | 0 |
| Normalized compile-log SHA-256 | `8b1089784de9a0cd922b9f903b2d13b4b3e7a31cc27e60e7d0a78dfecd0ff104` |
| `.ex5` SHA-256 | `e6e64d991e5578ba9635541d064be15e7fe4623d5b4418d074d293f9eb0ae68d` |
| `.ex5` size | 12,662 bytes |
| Compile-contract identity | `95b83795d593da4f05acc56020c5921e4946cb136ad8586d2474750cb16a0d28` |

## Tester Configuration

```ini
[Tester]
Expert=NoraPhase2L\NoraPhase2SeriesTesterCanaryV1
Symbol=GDAXI
Period=M1
Deposit=5000
Currency=USD
Leverage=20
Model=0
ExecutionMode=0
Optimization=0
OptimizationCriterion=0
FromDate=2020.07.01
ToDate=2026.07.01
ForwardMode=0
Report=<run-specific>
ReplaceReport=1
ShutdownTerminal=1
UseLocal=1
Visual=0
```

No `input` values or `.set` file used. Fixture compiled directly into EA.

## Native Lifecycle Evidence

Both runs confirmed all lifecycle stages via native journals:

| Stage | Run 1 | Run 2 |
|-------|-------|-------|
| tester_configuration_loaded | true | true |
| testing_agent_started | true | true |
| ea_loaded | true | true |
| ea_initialized | true | true |
| fixture_execution_started | true | true |
| result_csv_written | true | true |
| fixture_execution_completed | true | true |
| tester_completed | true | true |
| terminal_shutdown | true | true |

## Common Result File

- **Filename**: `nora_phase2_series_tester_v1.csv`
- **Location**: `C:\Users\Gasper\AppData\Roaming\MetaQuotes\Terminal\Common\Files`
- **Freshness**: Confirmed pre-run absence, post-run creation with timestamp verification

## Native Run 1

### Result CSV SHA-256
`2f7ffa9a8e32b5b3bcadf1fa00013de3969cc3ea34cf52ed754c3979d3843756`

### SMA3 Vector
```
null, null, 1.1006000000000000, 1.1009333333333335, 1.1009666666666667, 1.1013333333333335,
1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334,
1.1021666666666665, 1.1025333333333334
```

### Cross-Above Vector
```
null, null, null, true, false, false, false, false, false, false, false, false
```

### Cross-Below Vector
```
null, null, null, true, false, false, false, false, false, false, false, false
```

### Nullable Condition Vector
```
null, null, false, true, true, true, true, true, true, true, true, true
```

### Trigger Vector
```
false, false, false, true, true, true, true, true, true, true, true, true
```

### Reconciliation
| row_count | passed_rows | failed_rows | overall_pass |
|-----------|-------------|-------------|--------------|
| 12 | 12 | 0 | true |

### Execution Identity
`296a2697406db8c6aacd28a6004e5bb6c79b0d0651e957d4680537d6f6f658c1`

### Semantic-Result Identity
`ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687`

## Native Run 2

### Result CSV SHA-256
`2f7ffa9a8e32b5b3bcadf1fa00013de3969cc3ea34cf52ed754c3979d3843756`

### SMA3 Vector
Identical to Run 1.

### Cross-Above Vector
Identical to Run 1.

### Cross-Below Vector
Identical to Run 1.

### Nullable Condition Vector
Identical to Run 1.

### Trigger Vector
Identical to Run 1.

### Reconciliation
| row_count | passed_rows | failed_rows | overall_pass |
|-----------|-------------|-------------|--------------|
| 12 | 12 | 0 | true |

### Execution Identity
`cba31edc8468e5d73f9fbe1449f88470c1b521706e6c8448d6f3b5f6142389d6`

### Semantic-Result Identity
`ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687`

## Identity Comparison

| Identity | Run 1 | Run 2 | Match |
|----------|-------|-------|-------|
| Execution Identity | `296a2697...` | `cba31edc...` | Expected: No (`.ex5` hashes differ) |
| Semantic-Result Identity | `ff48ba25...` | `ff48ba25...` | **YES** |
| Result CSV SHA-256 | `2f7ffa9a...` | `2f7ffa9a...` | **YES** |

The two semantic-result identities match. Execution identities differ as expected because `.ex5` container hashes differ.

## Failure Evidence

All fail-closed tests pass. Verified behavior:

1. Frozen source/identity mismatch → fails before SSH
2. Missing/fresh CSV → requires pre-run absence, rejects stale
3. Numeric mismatch → `_numeric_match` with 1e-15 tolerance
4. Invalid tokens → `_canonical_nullable`, `_canonical_numeric`, `_canonical_cross` reject
5. Inconsistent summary → summary counts must match row passes
6. Missing stages → Stage evidence check fails

No passed manifest or semantic-result identity published on failure.

## Static No-Trading/No-Market Verification

Phase-2K static checks confirmed. Compiled source bundle contains no:
- OrderSend, CTrade, Buy, Sell
- Position APIs, account mutation
- iMA, indicator handles
- CopyBuffer, CopyRates, CopyClose
- SymbolInfoTick
- bid/ask/spread reads
- Market-data calculations

Tester uses only embedded fixture arrays.

## Regression Testing

### Python Suite
- **Complete**: 77 passed, 1 skipped
- **Focused Phase-2L**: 11 passed (`test_phase2l_series_tester_canary.py`)

### Rust Suite
- Not run in this environment (no C compiler toolchain available in Flatpak)

## Files Changed

### Modified
- `lab/mt5/__init__.py` — Series tester compile/execute orchestration, `reconcile_series_csv` with numeric tolerance, identity constants
- `phase-0a-h/windows/execute-series-tester-canary.ps1` — Fixed journal path detection, stage markers, result_fresh handling

### Added
- `phase-0a-h/windows/compile-series-tester-canary.ps1` — MetaEditor compilation
- `tests/test_phase2l_series_tester_canary.py` — 11 reconciliation/failure tests
- `docs/phase2l_mql5_sma_cross_native_canary.md` — This documentation

### Unchanged (Frozen Phase-2K)
All 7 generated source/manifest files preserved without modification.

## Preserved Identities

| Identity | Value | Verified |
|----------|-------|----------|
| Series Runtime SHA-256 | `6fbbe35045be59cdf571a623e38a213ca053be32fab153f858d461c1d4ac1b2d` | Local |
| Series Runtime Identity | `4102f23095201f5c37e8a6737d32f22eb31713f4f0ec9cae68803e6d3efbce8e` | Local |
| Series Tester Source SHA-256 | `bc62801db8965d268e192d3dadb8ba7b11a7c5e3d5a432fbadd3f2241a4d2757` | Local |
| Series Tester Identity | `78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4` | Local |
| Nullable Runtime Identity | `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d` | Local |
| Condition Identity | `1fa3d6613348a2fa532c4393e2a95795546c9cc5e2c86d010ee30fa9fe9632af` | Local |
| Evaluation AST Identity | `667db0ab50a7f3b9aba9d1296395f45e46f721945dec9d64340a3250421df664` | Local |
| Phase-2J Semantic-Result | `b66f60ad5ae4cc036d29197063e2dbe355cafac96085c359e92783ac74da74e4` | Preserved |