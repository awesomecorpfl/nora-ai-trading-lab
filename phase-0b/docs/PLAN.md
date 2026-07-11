# Phase 0B plan

Synthetic deterministic M1 bars represent ten 365-day years (5,256,000 bars). No local canonical ten-year M1/Parquet source exists; an older two-year EURSGD M1 CSV was inspected only for format. EMA(20), RSI(14), and ATR(14) are shared precomputations. One thousand parameter-varied spike candidates use completed-bar signals, next-open entry, SL/TP, and pessimistic ambiguity handling. Matrix: 1/4/6/8/10/12 workers, two repetitions, `/usr/bin/time` RSS. Thermal sensors were unavailable.
