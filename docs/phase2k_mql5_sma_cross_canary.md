# Phase 2K MQL5 SMA and cross canary

Phase 2K generates source and local semantic evidence only. No MQL5 compilation or native execution was performed.

The committed source chain is `engine/labengine/tests/fixtures/phase2_indicator_utc.parquet`, consumed by `phase2_cross_task.json`. Its raw `close` series is the accepted 12-row Phase-2 fixture:

`[1.1003, 1.1009, 1.1006, 1.1013, 1.1010, 1.1017, 1.1014, 1.1021, 1.1018, 1.1025, 1.1022, 1.1029]`

The Rust task was executed locally before freezing [series_evidence.json](../tests/fixtures/phase2k_mql5_sma_cross/series_evidence.json). It reported source identity `5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383`, SMA artifact identity `bd53bf9c88cd55fbf8d0fffb791648ff7ee6bf585efd4294042671e79eb995e9`, and cross artifact identity `274e22b09159252cc2a964cf08623de8dd9743c3152fea672a0c9ead749ff814`.

SMA period 3 has two warm-up nulls. It accepts only finite raw values; any null in the three-value window returns null. The sum is the explicit left-to-right window sum divided by `3`. Cross row zero is null. A cross result is null if either current or previous operand is null. `cross_above` uses previous-left `<=` previous-right and current-left `>` current-right. `cross_below` uses previous-left `>=` previous-right and current-left `<` current-right.

The generated runtime is [NoraPhase2SeriesRuntimeV1.mqh](../tests/fixtures/phase2k_mql5_sma_cross/runtime/NoraPhase2SeriesRuntimeV1.mqh) with manifest identity `4102f23095201f5c37e8a6737d32f22eb31713f4f0ec9cae68803e6d3efbce8e` and source SHA-256 `6fbbe35045be59cdf571a623e38a213ca053be32fab153f858d461c1d4ac1b2d`. It includes the repaired nullable runtime and exposes only `NoraSma3V1`, `NoraCrossAboveV1`, and `NoraCrossBelowV1`.

The generated tester source is [NoraPhase2SeriesTesterCanaryV1.mq5](../tests/fixtures/phase2k_mql5_sma_cross/tester/NoraPhase2SeriesTesterCanaryV1.mq5), SHA-256 `bc62801db8965d268e192d3dadb8ba7b11a7c5e3d5a432fbadd3f2241a4d2757`, identity `78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4`. It embeds the raw close values, computes all three series in row order, then passes them to the accepted condition and trigger functions. The later native CSV schema has 17 columns covering intermediate and final values.

Expected intermediate vectors are:

```text
sma3 = [null, null, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334]
close.cross_above.sma3 = [null, null, null, true, false, false, false, false, false, false, false, false]
sma3.cross_below.close = [null, null, null, true, false, false, false, false, false, false, false, false]
nullable = [null, null, false, true, true, true, true, true, true, true, true, true]
trigger = [false, false, false, true, true, true, true, true, true, true, true, true]
```

Generation was repeated into separate fresh directories and produced byte-identical sources, manifests, hashes, and identities. A finite input mutation changed the tester source hash and identity. Period 4 is rejected because the manifest supports only period 3. Static checks reject trading, market-data, indicator-handle, account, and price APIs. Missing evidence, non-finite input, inconsistent vectors, identity mismatch, and pre-existing targets publish no successful manifest or identity.

The accepted runtime, condition, AST, and Phase-2J semantic-result identities remain unchanged. This canary has not been compiled or executed in MT5 yet.
