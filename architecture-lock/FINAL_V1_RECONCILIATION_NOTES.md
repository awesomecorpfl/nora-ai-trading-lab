# FINAL_V1_RECONCILIATION_NOTES.md

This package is the reconciled final v1 architecture lock.

It incorporates the Fable 5 architecture review plus the actual project environment and workflow.

## Project-level corrections

### 1. Linux-first research boundary

The strategy builder/tester is fundamentally a Fedora system.

Python + Rust own:

- data ingestion;
- strategy generation;
- backtesting;
- search;
- robustness testing;
- Monte Carlo;
- clustering;
- portfolio research;
- orchestration and recovery.

MT5 is not part of the bulk research loop.

### 2. MT5 validation target and actual environment

The validation target is the existing dedicated Windows 10 LTSC VM on the Fedora laptop.

Known facts:

- access works through `ssh nora-win10`;
- SSH key authentication is already configured;
- the VM is fresh and dedicated to MT5 research/validation;
- it is not used for live trading;
- one fresh Darwinex MT5 terminal is installed;
- Darwinex access uses an investor/read-only login;
- Nora has already run MT5 backtests through the CLI path.

Therefore the project does not need to prove that Windows or SSH exists. It needs to codify the known-working backtest path into a reproducible repository-owned harness.

### 3. MT5's two narrow roles

MT5 enters at two points only:

1. **Phase 2 parity canaries** — small correctness checks before search.
2. **Phase 7 finalist validation** — production MQL5 and native Darwinex confirmation after Linux funnel survival.

The research funnel itself remains Linux-native.

### 4. QDM boundary

QDM is assigned to Fedora as an external acquisition, inspection, staging, and export tool.

It is not:

- canonical storage;
- provider identity;
- operational state;
- required runtime dependency.

The original lock preferred lab-owned UTC M1 Parquet. Phase 0C evidence and the production-data requirement refine that rule: canonical research data is lab-owned M1 Parquet with an explicit, versioned trading-timezone contract. Production datasets may be intentionally prepared and evaluated directly in the target MT5 broker clock. For Darwinex, Fusion and the intended IC Markets account, the present preference is New York +7 (UTC+02/UTC+03 with the relevant New York DST schedule). UTC remains useful as optional instant/reference metadata, not the only mandatory strategy clock.

This is a data-contract refinement, not a macro-architecture change. Fedora/Python/Rust remain the research boundary; QDM remains acquisition/staging/export tooling; MT5 remains narrow validation infrastructure. The contract records timezone identity, DST regime, source and bar timestamp semantics, session clock, strategy evaluation clock, optional UTC reference instant and conversion provenance, and guards against double conversion.

### 5. Random-search terminology

Use **matched random-search baseline**, not “empirical null.”

The baseline measures whether guided search/refinement adds value at a matched trial budget.

Placebo/permutation-style tests remain the null-style integrity checks.

### 6. Determinism requirement

Research determinism means semantically identical:

- trades;
- metrics;
- simulation outcomes;
- canonical content hashes.

Byte-identical Parquet containers are not required unless the writer guarantees stable serialization.

### 7. Breakout taxonomy

v1 uses **close-confirmed breakout**:

- breakout confirmed at bar close;
- entry next bar open.

This is not equivalent to future intrabar stop-entry breakout logic.

### 8. Deployment boundary

After native Darwinex MT5 confirmation, moving an approved EA to the demo VPS is a manual human action.

Automated demo/live deployment is deferred beyond v1.

---

## Interpretation of the earlier Phase-0A experiments

Earlier exploratory attempts around custom-symbol import, portable copies, and startup-script execution remain useful evidence about those specific mechanisms.

They should not be interpreted as evidence that:

- the dedicated VM is unsuitable;
- Darwinex broker access is contamination;
- a new Windows VM is required;
- MT5 must own the research data path.

The revised architecture uses the existing working environment narrowly and keeps the research platform on Linux.
