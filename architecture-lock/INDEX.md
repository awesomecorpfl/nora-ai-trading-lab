# INDEX.md
Nora AI Trading Lab — Architecture Package (Final v1 Lock, Linux-First Research Boundary)

Produced from the Fable 5 architectural review and reconciled with the actual project environment.

This final v1 package incorporates six project-level corrections:

1. **Linux-first research boundary**: strategy generation, backtesting, robustness, Monte Carlo, clustering, portfolio research, and experiment orchestration run on Fedora through Python + Rust. MT5 is not part of the bulk research loop.
2. **MT5 validation target**: MT5 validation uses the existing dedicated Windows 10 LTSC VM on the Fedora laptop, reached through the already-working `ssh nora-win10` path.
3. **Random-search terminology**: the best-of-N comparison is a matched random-search baseline, not a formal statistical null.
4. **Determinism scope**: determinism is defined at canonical research-content level rather than requiring byte-identical Parquet containers.
5. **Breakout taxonomy**: v1 close-confirmed breakout strategies are explicitly distinct from future intrabar stop-entry breakout strategies.
6. **Trading-timezone contract**: production research datasets may be prepared and evaluated directly in the declared target MT5 broker trading clock; UTC remains optional reference/provenance, not the mandatory strategy clock.

These documents supersede the original planning brief where they differ.

## Linux-first operating boundary

The package now makes the research/validation split explicit:

- Fedora is the research platform.
- Python is the control plane.
- Rust is the compute engine.
- QDM is Fedora-side acquisition/staging/export tooling only.
- Canonical market data is lab-owned M1 Parquet with a versioned trading-timezone contract.
- Production research may use target-broker-time data directly. For Darwinex, Fusion and the intended IC Markets account, the current preferred convention is New York +7 (UTC+02/UTC+03 with the relevant New York DST schedule).
- Higher timeframes are derived internally.
- MT5 is used only at narrow validation boundaries:
  - Phase 2: small parity/canary validation before search is trusted.
  - Phase 7: native Darwinex MT5 confirmation of finalists after MQL5 generation.
- Final demo-VPS deployment remains a manual human action outside the lab automation scope for v1.

## Recommended reading order

1. **FINAL_ARCHITECTURE.md** — final system design and the Linux research / MT5 validation boundary.
2. **ARCHITECTURE_DECISIONS.md** — locked decisions, prototype items, and deferrals.
3. **BUILD_ROADMAP.md** — implementation sequence and acceptance gates.
4. **RISKS_AND_FAILURE_MODES.md** — technical, research-validity, parity, and portfolio risks.
5. **OPEN_QUESTIONS.md** — the remaining questions that genuinely require empirical answers.
6. **FINAL_V1_RECONCILIATION_NOTES.md** — history of the project-level corrections and environment reconciliation.

## How to use this package

- Treat Fedora/Python/Rust as the default execution location for all research work.
- Treat MT5 as an execution-fidelity authority, not a strategy-generation or robustness-compute platform.
- Keep Phase 2 parity small and decisive: prove simple strategies reconcile before building search.
- Use the existing dedicated Windows VM for MT5 validation; do not redesign the VM boundary unless the actual known-working backtest workflow cannot be codified reliably.
- Apply the Phase 0C provider/broker-reference decision and the explicit trading-timezone contract when freezing the Phase 1 data contract; do not silently flatten broker-time semantics to UTC.
- Treat BUILD_ROADMAP sequencing rules as binding gates.
