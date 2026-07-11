# Phase 2A-2 Layer-1 conventions

All unavailable output is `null` (`Option<f64>`); no pre-warmup value is
invented. Windows include the completed current bar. Periods must be positive
and inputs finite. SMA seeds at its first full window; EMA seeds with that
window's SMA; ATR, RSI and ADX use Wilder smoothing. RSI emits 50 for a flat
seed/current state and 100 for gain-only states. ADX uses Wilder-smoothed
DM/TR and then Wilder-smoothed DX.

MACD is fast EMA minus slow EMA, with signal EMA seeded from available MACD
values. ER is change divided by absolute path (zero path is 0); KAMA seeds at
index `period` and uses squared adaptive smoothing. CCI and VWAP use typical
price `(H+L+C)/3`. Stochastic uses inclusive highest/lowest windows, 50 for a
zero range, and SMA %D. Bollinger uses population standard deviation and its
width is `(upper-lower)/middle` (0 for a zero middle). Keltner uses close EMA
and Wilder ATR. Linear regression emits the fitted value at the current x and
its slope. Highest/Lowest are inclusive.

Session OHLC is running OHLC only: it resets at declared trading-day boundary
or session-clock date and cannot look ahead. VWAP uses canonical `volume`,
resets identically, and fails closed on any missing volume; it never substitutes
unit/tick/real volume. Declared-clock DST resolution is reused unchanged.

The legacy anchor compatibility applies only to the original **unversioned**
Phase-1 contract shape. A current explicitly versioned contract without
`higher_timeframe_anchoring` now fails aggregation closed.

`compute_indicators` is a strict v1 JSON task with canonical input, new output
path, and a bounded named spec list. Current task-exposed columns are SMA, EMA,
RSI, ATR, ROC, ER, CCI, Highest and Lowest; the remaining locked kernels are
available to subsequent bounded task revisions, not an expression language.
