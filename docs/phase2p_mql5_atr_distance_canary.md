# Phase 2P: deterministic ATR and Distance/ATR MQL5 canary generation

Phase 2P is local-only generated-source evidence. It does not compile MQL5, execute MT5, claim native parity, authorize search, or alter the UTC fixture clock.

## Frozen Rust evidence

The exact command used to reproduce the committed vectors is:

```text
engine/target/debug/labengine engine/labengine/tests/fixtures/phase2_distance_atr_task.json
```

The exact task JSON is retained in [the Rust-derived evidence](../tests/fixtures/phase2p_mql5_atr_distance/phase2p_atr_distance_rust_evidence.json). Its input fixture is `engine/labengine/tests/fixtures/phase2_indicator_utc.parquet`, source identity `5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383`, and semantic output identity `c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad`. The twelve timestamp labels are ordered UTC fixture labels and are copied without conversion or broker-time transformation.

The evidence separates the Rust ATR identity `26363cfb22ba13fdd5f922173373d56f6aff5b57c3e66604dbec28908b68708d` from the Rust Distance/ATR identity `f4964fe1ecba67ab79654e59069ca5110e8330956b02b381517cf37bccf17f1f`; the fixture-package identity is not a substitute for either.

## Exact semantics

ATR has period 3. Row 0 true range is `high-low`. Every later row is `max(high-low, abs(high-previous_close), abs(low-previous_close))`. The first ATR is the arithmetic mean of true ranges 0 through 2 at row 2; every later value is `(previous_atr*2 + current_true_range)/3`. Rows 0 and 1 are null. Rust rejects non-finite OHLC input; the generated runtime returns null for non-finite input or result. Rows retain source order and count.

Distance/ATR is same-row signed `(close-sma3)/atr3`. It is null when close, SMA3, or ATR is null; it is also null unless the ATR denominator is finite and strictly positive, and when the numerator or quotient is non-finite. It neither shifts nor drops rows. The frozen output has twelve rows and null positions `[0, 1]` for both ATR and Distance/ATR.

## Generated artifacts

The committed package contains [ATR runtime](../tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2AtrRuntimeV1.mqh), [Distance/ATR runtime](../tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2DistanceAtrRuntimeV1.mqh), and [fixed-data tester](../tests/fixtures/phase2p_mql5_atr_distance/NoraPhase2AtrDistanceTesterCanaryV1.mq5), with their machine-readable manifests. Their source identities are independent:

- ATR runtime: SHA-256 `aa88f1627a016c20859b8eb4ecf7717b3d922ab879adeb63f3f460fa8d2c478c`, identity `80445d259d9ac9bcf3a15bf6ec12a160594237ee469b2ee53c46d22f99370194`.
- Distance/ATR runtime: SHA-256 `80dada0eb19f53672e90009bce8d39fc74e18eaaed530e0725715be0fa417a19`, identity `008c2f3a1824a8a22b03c6b447e3ae1a06cdd6c852381d96c8ca7eefba730c12`.
- Tester: SHA-256 `490a0c37f1d611c48f57e50dfb533265790950fa76b0e0a08edd915c91f05f0a`, identity `38c4e578079fd42ec31c390c84e78162d120b67a7bad48fb7859eb350dbad51e`.

The tester uses only the committed twelve-row arrays. Its future CSV contract emits row/timestamp, OHLC, prior close, actual and expected ATR, numerator, actual and expected Distance/ATR, nullable states, and pass/fail fields.

Focused tests generate the complete package twice in independent temporary directories and require byte identity for evidence, both runtimes and manifests, and tester and manifest. They also prove high, low, prior-close-gap, numerator, and nullable mutations change the specified vector positions and the relevant semantic identity. Failure tests verify no partial generated package survives malformed/missing inputs, incorrect identities or vector lengths, non-finite input, unsupported period, zero ATR denominator, pre-existing targets, or a staged publish failure.
