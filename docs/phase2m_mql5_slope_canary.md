# Phase 2M — MQL5 Slope Transform Canary

## Overview

This document records the deterministic generation of the MQL5 slope transform canary from the already-accepted Rust slope implementation. The canary consists of:

1. **NoraPhase2SlopeRuntimeV1.mqh** — deterministic MQL5 slope runtime
2. **NoraPhase2SlopeTesterCanaryV1.mq5** — no-trading EA tester with embedded Rust-derived vectors
3. **Manifests** — deterministic JSON manifests with SHA-256 source hashes and semantic identities

No MetaEditor compilation or MT5 Strategy Tester execution occurs in this phase. Generation is pure source production.

---

## Committed Rust Fixture

### Input Fixture
- **Path**: `engine/labengine/tests/fixtures/phase2_indicator_utc.parquet`
- **Semantic Identity**: `5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383`
- **Rows**: 12
- **Columns**: timestamp, open, high, low, close, volume, spread

### Task Specification
```json
{
  "task_version": 1,
  "task_type": "compute_indicators",
  "input_path": "engine/labengine/tests/fixtures/phase2_indicator_utc.parquet",
  "output_path": "/tmp/phase2_slope_output.parquet",
  "indicators": [
    {"name": "SMA", "output": "sma3", "period": 3},
    {"name": "Slope", "input": {"series": "sma3", "type": "numeric"}, "lookback": 1, "output": "sma3.slope"},
    {"name": "Slope", "input": {"series": "sma3.slope", "type": "numeric"}, "lookback": 1, "output": "sma3.slope.delta"}
  ]
}
```

### Task Command
```bash
engine/target/release/labengine engine/labengine/tests/fixtures/phase2_slope_task.json
```

### Output Artifact Identity
- **Slope Runtime Identity**: `45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499`
- **Output Parquet**: `/tmp/phase2_slope_output.parquet`

---

## Exact Input Vector (sma3)

The SMA3 values computed by the Rust engine from the 12-row close series:

```text
Index:  0        1        2         3         4         5         6         7         8         9        10        11
Value: null     null     1.1006    1.1009333333333335  1.1009666666666666  1.1013333333333335  1.1013666666666666
       1.1017333333333335  1.1017666666666666  1.1021333333333334  1.1021666666666665  1.1025333333333334
```

Null positions: `[0, 1]` (first 2 rows — SMA warmup with period 3)

---

## Frozen Slope Formula and Null Policy

### Formula
```
slope[i] = (current[i] - current[i - lookback]) / lookback
```
With `lookback = 1`:
```
slope[i] = current[i] - current[i - 1]
```

### Null Propagation Rules
1. **Warmup**: First `lookback` rows (1 row) → `null`
2. **Null current endpoint**: If `current[i]` is null → `null`
3. **Null previous endpoint**: If `current[i - lookback]` is null → `null`
4. **Finite only**: Non-finite result → `null` (Rust errors; MQL5 returns null)
5. **Row count preserved**: Output length = input length = 12
6. **Timestamp ordering preserved**: No reordering

---

## Exact Expected Slope Vector (from Rust)

```text
Index:  0    1    2    3                    4                 5                    6                 7                    8                 9                    10                11
Value: null null null 0.00033333333333351867 3.333333333310762e-05 0.00036666666666684833 3.333333333310762e-05 0.00036666666666684833 3.333333333310762e-05 0.00036666666666684833 3.333333333310762e-05 0.00036666666666684833
```

- Rows 0–2: null (warmup + SMA null propagation)
- Row 3: (1.1009333333333335 - 1.1006) / 1 = 0.0003333333333335
- Row 4: (1.1009666666666666 - 1.1009333333333335) / 1 = 3.33333333331e-05
- Row 5: (1.1013333333333335 - 1.1009666666666666) / 1 = 0.00036666666666684833
- ... alternating pattern continues

**Full precision preserved** — no rounding applied to expected values.

---

## Generated Source Contracts

### Runtime Source
- **File**: `NoraPhase2SlopeRuntimeV1.mqh`
- **SHA-256**: `a3b2dc447b59e6800dee7c875e9d25ea2353fc32b04c73391871623c08842c80`
- **Depends on**: `NoraPhase2RuntimeV1.mqh` (Phase-2F nullable runtime)
- **Exports**: `NoraSlopeLookback1V1(current, previous) -> NoraNullableDoubleV1`

### Runtime Manifest
```json
{
  "slope_runtime_version": "nora_mql5_slope_runtime_v1",
  "nullable_runtime_identity": "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d",
  "supported_operations": ["slope"],
  "supported_lookbacks": [1],
  "formula": "(current - previous) / lookback",
  "source_filename": "NoraPhase2SlopeRuntimeV1.mqh",
  "source_sha256": "a3b2dc447b59e6800dee7c875e9d25ea2353fc32b04c73391871623c08842c80",
  "slope_runtime_identity": "cb9eee8e4c03d6c6d95c6ba384701187c93730f77fafe3a22a2f8902410c68ae"
}
```

### Tester Source
- **File**: `NoraPhase2SlopeTesterCanaryV1.mq5`
- **SHA-256**: `6d4f2e9f0a7e1dcd33004500dfea8deaad4c5a4e9804e57ef8377369f67a4f53`
- **Includes**: `NoraPhase2RuntimeV1.mqh`, `NoraPhase2SlopeRuntimeV1.mqh`
- **CSV Output**: `nora_phase2_slope_tester_v1.csv`
- **Schema**: `record_type,row_index,actual_slope,expected_slope,row_pass,row_count,passed_rows,failed_rows,overall_pass`

### Tester Manifest
```json
{
  "slope_tester_version": "nora_mql5_slope_tester_canary_v1",
  "nullable_runtime_identity": "1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d",
  "slope_runtime_identity": "cb9eee8e4c03d6c6d95c6ba384701187c93730f77fafe3a22a2f8902410c68ae",
  "rust_input_identity": "5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383",
  "rust_slope_identity": "45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499",
  "lookback": 1,
  "row_count": 12,
  "input_vector": [null, null, 1.1006, 1.1009333333333335, ...],
  "expected_slope_vector": [null, null, null, 0.00033333333333351867, ...],
  "result_filename": "nora_phase2_slope_tester_v1.csv",
  "source_filename": "NoraPhase2SlopeTesterCanaryV1.mq5",
  "source_sha256": "6d4f2e9f0a7e1dcd33004500dfea8deaad4c5a4e9804e57ef8377369f67a4f53",
  "slope_tester_identity": "a25fe8a6b459499debdbc9d48c8d4dd498a9684bf67b196501ebed743b48b54d"
}
```

---

## Semantic Identities

### Slope Runtime Identity
```
nora.mql5.slope_runtime_v1.semantic.v1
```
Bound to:
- Runtime protocol version: `nora_mql5_slope_runtime_v1`
- Nullable runtime identity: `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d`
- Exact formula: `(current - previous) / lookback`
- Null policy: null if either endpoint is null
- Finite policy: null if non-finite
- Supported lookback inventory: [1]
- Generated source bytes
- Source SHA-256

### Slope Tester Identity
```
nora.mql5.slope_tester_canary_v1.semantic.v1
```
Bound to:
- Tester protocol version
- Nullable and slope runtime identities
- Rust input identity
- Rust slope identity
- Lookback: 1
- Exact ordered input vector
- Exact expected slope vector
- CSV schema and result filename
- Generated source bytes
- Source SHA-256

---

## Repeatability Evidence

Generated twice in separate directories:
- `artifacts/phase2m_slope_gen1/`
- `artifacts/phase2m_slope_gen2/`

**Verification**:
- Runtime source: byte-identical
- Runtime manifest: byte-identical
- Tester source: byte-identical
- Tester manifest: byte-identical
- Source SHA-256: identical
- Semantic identities: identical
- No path-dependent content detected

---

## Mutation Evidence

### Input Mutation
Changed `input_vector[5]` from `1.1013333333333335` to `1.1014`.
- Rust slope output changes at index 5 and 6
- Tester source changes (embedded vectors differ)
- Tester source SHA-256 changes
- Tester semantic identity changes

### Lookback Mutation
Attempted lookback `2` (not supported).
- Generator rejects with deterministic error: "supported_lookbacks mismatch"
- No silent acceptance beyond lookback 1

### Null Mutation
Changed `input_vector[3]` from `1.1009333333333335` to `null`.
- Expected slope at index 3 and 4 become null (endpoint propagation)
- Tester source changes
- Tester source SHA-256 changes
- Tester semantic identity changes

---

## Atomic Failure Modes

Each failure produces deterministic non-zero exit, no manifest, no partial source:

| Failure | Trigger | Result |
|---------|---------|--------|
| Missing Rust input fixture | Evidence file missing | Exit 2, "slope evidence is unreadable" |
| Non-finite input value | `input_vector` contains NaN/Inf | Exit 2, "input values must be finite" |
| Expected vector length mismatch | 11 or 13 rows | Exit 2, "vectors must have length 12" |
| Incorrect Rust slope identity | Manifest `rust_slope_identity` mismatch | Exit 2, "Rust slope artifact identity does not match" |
| Unsupported lookback | Evidence `lookback` != 1 | Exit 2, "slope evidence is not the accepted sma3/slope fixture" |
| Pre-existing output target | Re-generate in same directory | Exit 2, "targets must not already exist" |

---

## Regression Test Results

### Rust Suite (engine/labengine)
```bash
cd engine/labengine && cargo test --release
```
- All tests pass
- Slope identity preserved: `45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499`

### Python Suite
```bash
cd /home/gasper/nora-ai-trading-lab && python -m pytest tests/ -v
```
- Phase-1 tests pass
- Phase-2L semantic result preserved: `ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687`
- Phase-2L CSV preserved: `2f7ffa9a8e32b5b3bcadf1fa00013de3969cc3ea34cf52ed754c3979d3843756`

### Focused Phase-2M Tests
- Generator CLI help
- Slope runtime generation
- Slope tester generation
- Repeatability verification
- Mutation rejection
- Atomic failure verification

---

## Preserved Identities

| Artifact | Identity |
|----------|----------|
| Phase-2L semantic result | `ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687` |
| Phase-2L CSV | `2f7ffa9a8e32b5b3bcadf1fa00013de3969cc3ea34cf52ed754c3979d3843756` |
| Rust slope identity | `45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499` |
| Nullable runtime identity | `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d` |
| Slope runtime identity | `cb9eee8e4c03d6c6d95c6ba384701187c93730f77fafe3a22a2f8902410c68ae` |
| Slope tester identity | `a25fe8a6b459499debdbc9d48c8d4dd498a9684bf67b196501ebed743b48b54d` |

---

## Explicit Statement

**No MetaEditor compilation or native MT5 Strategy Tester execution occurred during this phase.** All artifacts are generated source code and deterministic manifests produced by the Python generator in `lab/mql5gen/slope.py` using the committed Rust fixture as the single source of truth.

---

## Git Status (Pre-commit)

```bash
# New files to commit:
lab/mql5gen/slope.py
artifacts/phase2m_slope_evidence.json
artifacts/phase2m_slope_gen1/NoraPhase2SlopeRuntimeV1.mqh
artifacts/phase2m_slope_gen1/NoraPhase2SlopeRuntimeV1.manifest.json
artifacts/phase2m_slope_gen1/NoraPhase2SlopeTesterCanaryV1.mq5
artifacts/phase2m_slope_gen1/NoraPhase2SlopeTesterCanaryV1.manifest.json
docs/phase2m_mql5_slope_canary.md
```
