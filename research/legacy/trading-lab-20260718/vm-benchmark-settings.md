# VM Performance Benchmark Settings

**Purpose:** Find optimal VM resource allocation for MT5 backtesting by measuring run time.

## Test Configuration

| Setting | Value |
|---|---|
| Strategy | GDAXI\Strategy 1.38.195 |
| Symbol | GDAXI |
| Timeframe | H1 |
| Modeling | Every Tick (0) |
| Leverage | 1:20 |
| Deposit | $5,000 USD |
| Date Range | 2020.07.01 - 2026.07.01 |
| mmLots | 0.01 |

## Results Comparison

| VM Config | Test | Duration | vs Baseline |
|---|---|---|---|
| **6 vCPUs / 16GB** | Run 1 (first download) | ~59 minutes | — |
| **6 vCPUs / 16GB** | Run 2 (data cached) | **~73 seconds** (0:01:10.855) | **baseline** |
| **4 vCPUs / 8GB** | Run 1 (after reboot) | **~73 seconds** (0:01:12.240) | +1% |
| **4 vCPUs / 8GB** | Run 2 (data cached) | **~90 seconds** | +23% (variance) |
| **2 vCPUs / 4GB** | Run 1 | **~110 seconds** (1:50) | +51% slower |
| **2 vCPUs / 4GB** | Run 2 | **~100 seconds** (1:40) | +37% slower |
| **2 vCPUs / 6GB** | Run 1 | **~110 seconds** (1:50) | +51% slower |
| **2 vCPUs / 6GB** | Run 2 | **~100 seconds** (1:40) | +37% slower |

## Key Findings

1. **4 vCPUs / 8GB = 6 vCPUs / 16GB** — Identical performance, frees up resources
2. **2 vCPUs is the bottleneck** — 4GB vs 6GB RAM made **zero difference**
3. **CPU bottleneck at 2 cores** — Constant context switching between Windows and MT5
4. **RAM headroom beyond 4GB doesn't matter** — 2GB overhead + 2GB working set = 4GB total

## Memory Pressure Analysis

| VM Config | Total RAM | Windows | MT5 | Available | Bottleneck |
|---|---|---|---|---|---|
| 6 vCPUs / 16GB | 16GB | ~2GB | ~3GB | 11GB | none |
| 4 vCPUs / 8GB | 8GB | ~2GB | ~3GB | 3GB | none |
| 2 vCPUs / 4GB | 4GB | ~2GB | ~2GB | 0GB | **CPU + RAM** |
| 2 vCPUs / 6GB | 6GB | ~2GB | ~2GB | 2GB | **CPU only** |

**At 2 vCPUs / 4GB:**
- No RAM headroom + CPU context switching = 37% slower

**At 2 vCPUs / 6GB:**
- Sufficient RAM but CPU bottleneck remains = **identical performance to 4GB**

## Recommendation

**4 vCPUs / 8GB is the sweetspot.**
- Identical performance to 6 vCPUs / 16GB
- Frees up 2 vCPUs and 8GB RAM on host
- 3GB RAM headroom is sufficient
- 2 vCPUs (any RAM) is too slow — CPU bottleneck confirmed

**Why 2 vCPUs fails:**
- MT5 backtester is single-threaded but requires background threads for I/O, GUI, etc.
- With only 2 cores: one for MT5 simulation, one for everything else
- Constant context switching = 37% performance penalty
- Adding RAM (4GB→6GB) doesn't help because bottleneck is CPU

## Notes

- Historical data for one symbol over 6 years: ~50-100MB once cached
- Bottleneck is CPU core count, not RAM (once you have ≥4GB)
- Every Tick modeling: single-threaded CPU-intensive, but needs background threads
- 4 vCPUs provides enough parallelism for overhead + simulation