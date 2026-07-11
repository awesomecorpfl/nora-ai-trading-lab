# Phase 0B verdict: PASS

This is a throughput spike, not production engine code or a market-validity test.

## Measured workload

Each repetition generated 5,256,000 deterministic synthetic M1 OHLC bars (ten 365-day years), precomputed EMA/RSI/ATR, and evaluated 1,000 distinct parameterized candidates: 5.256 billion strategy-bar evaluations. Candidates produced 13,842,360 aggregate closed positions and nonzero aggregate P&L, so work was not optimized away. Tests cover deterministic rerun, parameter variation, next-open entry, target hit, and pessimistic stop/target ambiguity.

| workers | mean seconds | mean candidates/s | peak RSS |
|---:|---:|---:|---:|
| 1 | 12.781 | 78.24 | 290 MiB |
| 4 | 5.981 | 168.53 | 290 MiB |
| 6 | 5.934 | 168.54 | 290 MiB |
| 8 | 6.156 | 162.50 | 290 MiB |
| 10 | 6.172 | 162.14 | 290 MiB |
| 12 | 6.157 | 162.43 | 290 MiB |

Recommend **4 workers** for sustained scheduling: it has the best observed mean and leaves capacity for the desktop/VM. Six is statistically tied in this short sample, but offers no clear benefit.

## Extrapolation

At 168.53 candidate-backtests/s, 25,000 candidates on the same one-symbol/ten-year synthetic workload is **148.3 seconds (2.47 minutes)** plus approximately 0.2 seconds shared data/indicator preparation per task. Real Phase-4 work will be slower because it adds real parsing/Parquet, richer ASTs, costs, metrics, multiple symbols, and artifact I/O; this result only establishes substantial hours-not-days headroom for Tier-1-style screening.

## Process boundary and observations

The binary's data generation plus shared indicator preparation was 0.17–0.20s versus ~6s at recommended concurrency, so a JSON task read/result write and process startup on 1–10 minute tasks is economically immaterial at this scale. RSS stayed near 290 MiB because bars/indicator arrays are shared across worker threads. `sensors` exposed no readable temperature; no throttling claim is made. Future scheduler policy should retain a thermal observation hook and default to four workers until an extended thermal run is measured.

## Limitation

No suitable local 10-year M1 dataset was available. The runtime fixture is deterministic and intentionally not a substitute for Phase 0C provider selection or canonical UTC M1 Parquet validation.
