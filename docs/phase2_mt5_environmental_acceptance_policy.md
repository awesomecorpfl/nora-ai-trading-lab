# Phase-2 MT5 environmental acceptance policy

The Phase-2 prohibition is on market-price acquisition, price-history expansion, and externally sourced price-data mutation. It is not a byte-identity requirement for routine MT5 metadata-only cache maintenance.

An embedded-fixture native run passes this gate only when its EA calculations use committed embedded fixtures only; its raw journal and before/after cache inventories are retained; no history or tick file is added or deleted; bar count and earliest/latest history timestamps are unchanged; no bars or ticks are reported downloaded; and no price-data payload is detected.

Every changed cache file must have a recorded size delta within the run's stated bound and an explicit classification. Permitted classifications are symbol-contract metadata refresh, cache-header maintenance, cache-index maintenance, and in-memory cache allocation. Symbol-contract metadata (including the observed 3,720-byte GDAXI contract exchange) is recorded separately from price data. A 25-byte protocol handshake is not price data.

Forbidden events are successful market-price download, bar or tick acquisition, price-history expansion, externally sourced price-data mutation, a new history/tick file, a deleted cache file, a changed bar count or history range, an unbounded mutation, or an unclassified mutation. Ambiguous journal or filesystem evidence, including missing before/after evidence, fails acceptance. A generic journal phrase is not automatically fatal only when the retained complete forensic record explicitly resolves it; otherwise it remains ambiguous and fails closed.

The accepted forensic record is `eff7329a1320d7c9c51cff15b84d7d4d57ecadbf3d8ee86ef4e09d67b65611af`: GDAXI remained at 393,092 bars from 2019.01.02 through 2020.06.30; no files were added or deleted; 36 of 406 cache files received metadata-scale changes, with GDAXI `.hcc` increasing by 120 bytes; and unrelated symbols showed similar maintenance. The committed OHLC fixtures remained the only strategy-calculation input.
