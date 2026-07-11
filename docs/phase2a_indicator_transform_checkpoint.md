# Phase 2A indicator and transform checkpoint

Verified implementation chain: `36ce036` reader, `5b0ddf6` clocks, `1bc568e` aggregation, `25b4982` identity, `1ea25a2` multi-output indicators, `46563c7` registry, `b9a9f0f` nullable Boolean artifacts, `84fddc3` typed writer, `4d10252` frozen indicator fixture, `922a281`/`10f7433` Slope, `b4bac63`/`5419bdc` DistanceAtr, `f566812`/`9eca0bd` Percentile, and `6ca7e0f` Cross.

Frozen identities: indicator `b47982fda09756ee44a0d281e8e1e16a9ef7dcdc9e46985121c4eec050ba411f`; Slope `45859444114338fbddcc0be2c6962ba5972adf1b9bb09c3fb7418388dce92499`; MACD-Slope `c1d1d4a1003a3c0bc8f6b8b3d3ec736349db90082647a349cebf89b6dd07cb1e`; DistanceAtr `c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad`; Percentile `943765d83d115309867fa8da768fc2a69500e7292f6048ed87541f4e26e63775`; Cross `274e22b09159252cc2a964cf08623de8dd9743c3152fea672a0c9ead749ff814`.

Slope is endpoint difference/lookback; DistanceAtr is signed `(input-reference)/atr` with non-positive denominator null; Percentile is inclusive midrank; Cross is one-bar above/below using prior equality and current strictness. Numeric results are nullable Float64; Cross is nullable Boolean. Ordered registration permits earlier indicators/transforms and rejects unknown, forward, Boolean-to-numeric, and duplicate names. Typed artifacts validate schema, metadata, timestamps, rows, and identity; failed CLI tasks publish neither a final artifact nor a success summary.

Committed fixture data remains UTC and unchanged. Production data is never automatically converted: each dataset declares timezone, DST, session, strategy-clock, and conversion-history contract; no broker clock is global.

These are deterministic engine capabilities only. No MQL5 translation or Rust↔MT5 parity exists; no transform may enter searchable grammar until implementation, translation, and parity evidence exist. This is a Phase 2A checkpoint only; Phase 3 remains blocked by the complete Phase 2 parity gate.
