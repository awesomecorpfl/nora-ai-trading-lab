# BUILD_ROADMAP.md
Nora AI Trading Lab — Implementation Roadmap

Phases are in dependency order. Acceptance gates are binding.

The roadmap is explicitly Linux-first: research compute remains on Fedora. MT5 appears only in a narrow early parity gate and late finalist validation.

---

## Phase 0 — Risk and calibration spikes

### 0A — Codify the existing MT5 validation harness

The existing Windows 10 LTSC VM is already a dedicated MT5 research/validation machine.

Known environment:

- Fedora host;
- SSH alias `nora-win10`;
- SSH key already configured;
- one fresh Darwinex MT5 terminal;
- investor/read-only broker login;
- no live-trading use of the VM;
- Nora has already run MT5 backtests through CLI orchestration.

Task:

Audit the actual known-working workflow and turn it into a small repository-owned validation harness.

Prove:

- Fedora can launch a pinned MT5 backtest through the existing SSH path;
- EA/config placement is repeatable;
- the run completes;
- result/report artifacts return to Fedora;
- output can be parsed into machine-readable metrics and a semantic trade list;
- the exact pinned test can be run twice with semantically identical results;
- interrupted or incomplete runs are not accepted as success;
- restart/interruption behavior is documented.

Broker history synchronization is treated as normal tester state preparation, not as proof that the environment is invalid.

Phase 0A does **not** require:

- a new VM;
- a new Windows install;
- a second MT5 terminal;
- QDM installation;
- custom-symbol import;
- a permanent parity dataset strategy.

**Acceptance**: one repository-owned Fedora command or script launches the same pinned broker-native MT5 test twice through `ssh nora-win10`, retrieves the outputs, and produces a semantic comparison verdict.

### 0B — Engine throughput prototype

Build a crude Rust prototype:

- load 10 years of M1 for one symbol;
- compute 3 indicators;
- evaluate roughly 1,000 dummy AST strategies;
- use next-open entry and intrabar SL/TP logic.

Benchmark sustained throughput with 4/6/8/10/12 workers.

**Acceptance**: measured throughput and wall-time extrapolation for a 25k-candidate Tier-1 pass, with a target of hours rather than days.

### 0C — Data provider and broker-reference check

Install/evaluate QDM on Fedora as acquisition/staging tooling.

Use QDM and existing broker extraction utilities to compare candidate source and broker reference data for 2–3 symbols:

- gaps;
- timestamp conventions;
- DST;
- session boundaries;
- M1 alignment;
- sample tick behavior;
- broker symbol specifications.

Record provider identity separately from QDM version/tool identity.

Hash staged exports and record timezone/DST/export settings.

**Acceptance**: written data-contract draft validated against real files and broker extracts.

0B and 0C may proceed in parallel after the 0A harness direction is clear.

---

## Phase 1 — Lab foundation

Build:

- canonical data contract;
- QDM-independent staged-file ingestion;
- canonical M1 Parquet store with explicit, versioned trading-timezone contract;
- symbol/timezone/DST/session model, source and bar timestamp semantics, strategy evaluation clock, optional UTC reference instant, and conversion provenance/double-conversion guard;
- preserve directly prepared broker-time datasets rather than silently normalizing every input to UTC; support broker-time Friday close, ORB, rollover, daily-reset and other session rules;
- SQLite state schema;
- Parquet artifact conventions;
- hash registry;
- task/checkpoint framework;
- systemd supervisor;
- idempotent CLI skeleton;
- event log;
- protocol versioning;
- dummy resumable workflow.

**Acceptance**
1. Dummy multi-stage experiment runs through `lab experiment launch`.
2. Kill/reboot tests resume with zero lost completed tasks and zero duplicated tasks.
3. Repeating a CLI command is idempotent.
4. Every artifact is reproducible from provenance.

---

## Phase 2 — Engine proof + narrow MT5 parity gate

Build:

- Layer-1 indicators;
- minimal typed transforms;
- AST schema/canonicalization/hashing;
- v1 execution simulator;
- synthetic execution fixtures;
- deterministic RNG streams;
- baseline metrics;
- minimal MQL5 generator for the v1 canary node set;
- small MT5 parity harness using the existing Phase-0A VM path.

MT5 work in this phase is deliberately small.

Do not run search populations in MT5.

**Acceptance**
1. All synthetic execution fixtures pass.
2. Layer-1 indicator implementations match MT5/reference behavior within documented tolerance on parity datasets.
3. At least 10 simple hand-designed strategies spanning the initial v1 grammar generate to MQL5 and reconcile trade-by-trade within the provisional parity budget.
4. Same Linux experiment run twice gives semantically identical trades, metrics, simulation outcomes, and canonical content hashes.
5. Placebo/scrambled-data test destroys a known canary edge.

**Go/no-go gate**: if simple parity cannot be achieved, no search engine is built.

---

## Phase 3 — Search

Build:

- first two family grammars;
- stratified sampler;
- canonical-hash dedup;
- behavioral descriptors;
- descriptor archive;
- local refinement;
- lineage tracking;
- compute budgets.

Initial families:

- trend-pullback;
- close-confirmed breakout.

**Acceptance**
1. 10k+ candidates sampled with zero canonical duplicates in repeated test.
2. Descriptor archive shows meaningful coverage.
3. Matched best-of-N random-search baseline produced.
4. Sampling run is resumable at batch granularity.

No mutation/crossover yet.

---

## Phase 4 — Cheap robustness, Tiers 0–3.5

Build:

- mechanical integrity;
- IS/OOS;
- temporal segments;
- cost stress;
- dollar-DD gates;
- cheap parameter neighborhood;
- Trade MC;
- related market/TF contextual tests;
- session/regime decomposition;
- behavioral clustering;
- representative selection;
- machine-readable failure reasons.

**Acceptance**
1. 10k candidates reduce to roughly 10–100 representatives in bounded laptop wall time.
2. Every rejection stores a reason code.
3. Survivors materially outperform the matched random-search baseline on validation data.
4. Every tier supports interruption/resume.

---

## Phase 5 — Expensive robustness, Tier 4

Build:

- Parameter Manipulation MC, sharded and resumable;
- parameter-surface summaries;
- WFV default;
- WFO only for families whose protocol requires reoptimization;
- runtime learning.

**Acceptance**
1. Expensive tests run only on clustered representatives.
2. Scheduler predicts wall time within ±30%.
3. Interrupted two-hour Parameter MC loses at most one shard.
4. Explicit decision-gate approval required.

---

## Phase 6 — Portfolio lab, Tiers 5 and 7

Build:

- joint daily P&L replay;
- downside/tail correlation;
- DD overlap;
- loss-streak and recovery analysis;
- concentration caps;
- greedy portfolio selection;
- drawdown-based risk budgeting;
- broker-compatible lot sizing;
- portfolio MC;
- correlated cost shocks;
- dropout stress;
- portfolio provenance.

**Acceptance**
1. Portfolio construction meets a stated dollar-DD constraint.
2. Constructed hero-dependent portfolio is rejected by dropout stress.
3. Portfolio artifacts are fully reproducible.

---

## Phase 7 — High-fidelity finalist validation

Only Linux-pipeline finalists reach this stage.

Build/harden:

- finalist tick retest where required;
- production-grade MQL5 generation;
- magic-number handling;
- contract/spec handling;
- robust logging and error handling;
- batch native MT5 validation through the existing Windows VM;
- automatic result retrieval;
- reconciliation reports;
- parity-budget mismatch alerts.

Native validation target: Darwinex MT5 in the existing dedicated VM.

The expected final confirmation window is approximately six years where the selected protocol and data availability permit.

**Acceptance**
1. Finalists flow Linux strategy → MQL5 → native Darwinex MT5 validation without manual file handling.
2. Results return and reconcile automatically.
3. Any divergence outside the parity budget flags the candidate.
4. A final validation report clearly distinguishes Linux research results from native broker-terminal confirmation.

Manual deployment of approved EAs to the demo VPS is outside the automated lab workflow.

---

## Phase 8 — Nora workshop

Build:

- decision packets;
- enumerated choices;
- Hermes wake dispatch;
- Telegram status;
- manifest-driven auto-advance;
- challenge-mode queries;
- research-memory CLI.

**Acceptance**
1. Full experiment runs end-to-end with Nora waking only at declared gates/exceptions.
2. Token use measured and within budget.
3. Nora cannot alter thresholds mid-experiment.
4. Recovered state is accurately reflected after crash/restart.

---

## Phase 9 — Deferred intelligence

Deferred until sufficient trustworthy experiment history exists:

- ML survival predictors;
- surrogate compute allocation;
- anomaly models;
- regime models;
- Markov/HMM risk scaling;
- GA search.

---

## Binding sequencing rules

1. **Do not build search until Phase 2 simple parity passes.**
2. **Do not put MT5 in the bulk research loop.**
3. **Do not add a searchable AST node before Rust implementation + MQL5 translation + parity fixture exist.**
4. **Do not add mutation/crossover until sampling + local refinement plateaus on at least two families.**
5. **Do not build expensive Parameter MC/WFO infrastructure until cheap-tier attrition reduces populations to roughly ≤100 representatives.**
6. **Do not build portfolio tooling before a real pool of funnel-validated strategies exists.**
7. **Do not build broad tick infrastructure before M1 finalists exist.**
8. **Do not connect Nora to the full funnel until a full experiment runs hands-free.**
9. **Do not touch the permanent lockbox before a finalist portfolio exists and human approval is given.**
10. **No ML/regime/Markov work before trustworthy lab history exists.**
11. **Do not automate demo/live deployment in v1.**
12. **Do not redesign the Windows validation environment while the existing dedicated VM and known-working SSH/backtest path can satisfy the narrow validation contract.**

## Deliberately postponed

GUI, MCP, cloud/distributed compute, pending-order execution semantics, partial exits, advanced trailing, Layer-3/4 indicators, volume/TPO profile families, speculative micro-optimization, HMM/Markov/ML layers, and automated deployment.
