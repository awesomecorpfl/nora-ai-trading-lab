# OPEN_QUESTIONS.md
Nora AI Trading Lab — Genuine Open Questions

Only questions requiring empirical evidence remain here.

---

## Q1. Can Nora's known-working MT5 CLI workflow be codified into a repository-owned validation harness?

**Known starting point**

- dedicated Windows 10 LTSC VM already exists;
- SSH alias is `nora-win10`;
- SSH key access already works;
- VM is not used for live trading;
- one fresh Darwinex MT5 terminal is installed;
- investor/read-only broker login is used;
- Nora has already run MT5 backtests through the CLI path.

**Why it matters**

The project needs a reproducible narrow validation boundary, not a new Windows platform.

The unresolved question is whether the working method can be packaged with:

- pinned config;
- completion detection;
- artifact return;
- parsing;
- semantic two-run comparison;
- interruption classification.

**Answer by**: Phase 0A.

**Decision it unblocks**: repository-owned MT5 validation harness interface.

---

## Q2. What is the numeric parity budget?

Need hard tolerances for:

- indicator values;
- trade-match percentage;
- P&L divergence;
- timing/price tolerances where exact identity is not mechanically possible.

**Answer by**: empirical Phase-2 canary runs.

---

## Q3. What is the exact Phase-2 parity data path?

Candidate routes:

1. extract broker-reference data to Linux and compare Rust against MT5 over the matched broker period;
2. import a pinned canonical fixture into MT5 if required for stricter identical-data tests;
3. use both for different parity questions.

Custom-symbol import is not assumed and is not a Phase-1 prerequisite.

**Answer by**: Phase 2.

**Decision it unblocks**: final parity-harness data contract.

---

## Q5. What are the account parameters for v1 portfolio research?

Needs:

- account currency;
- intended capital;
- maximum acceptable dollar DD;
- leverage/margin rules;
- broker lot constraints.

**Answer by**: before Phase 6.

---

## Q6. What is the exact Hermes wake mechanism and token budget per experiment?

The event log can be built first, but dispatch and budget need numeric decisions before Nora workshop integration.

**Answer by**: before Phase 8.

---

## Q7. Which two symbols/families anchor the first end-to-end experiment?

Phase 2–4 need concrete instruments and families for:

- data;
- costs;
- parity;
- grammar;
- contextual tests.

**Answer by**: start of Phase 2.

---

## Q8. What exact final Darwinex native validation protocol applies to finalists?

Expected direction:

- production MQL5;
- Darwinex native tester;
- approximately six-year confirmation window where protocol/data permit;
- explicit tester mode;
- fixed cost/account settings;
- returned report and trade list;
- comparison against Linux results.

The precise window and pass criteria must be frozen before Phase 7.

**Answer by**: before Phase 7.

---

## Not open questions

Already decided:

- Linux-first research platform;
- Rust/Python split;
- subprocess + file boundary;
- SQLite/Parquet/DuckDB roles;
- QDM on Fedora only as acquisition/staging/export tooling;
- typed AST;
- v1 narrow execution semantics;
- pessimistic ambiguity;
- funnel order;
- v1 search mechanism;
- behavioral archive;
- portfolio method class;
- lockbox policy;
- Nora governance model;
- existing Windows VM as MT5 validation environment;
- manual demo-VPS deployment boundary.
