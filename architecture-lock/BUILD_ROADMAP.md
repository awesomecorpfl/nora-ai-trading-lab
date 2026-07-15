# Nora AI Trading Lab — Evidence-Based Build Roadmap v2

Phases and tranches are dependency ordered. Completed work is not restated as future implementation.

## Completed and conditional foundation

### Phase 0A — MT5 harness

**Status:** conditional pass.

Completed:

- repository-owned access through `ssh nora-win10`;
- repeatable pinned runs and result return;
- semantic two-run comparison;
- interruption classification.

Later hardening:

- tester-kill/VM-restart recovery;
- finalist-scale reliability;
- richer aggregate extraction.

### Phase 0B — Throughput proof

**Status:** pass.

- 5,256,000 synthetic M1 bars;
- 1,000 candidates;
- 168.53 candidate-backtests/sec at four workers;
- about 290 MiB peak RSS.

Production workload calibration is a future Phase-3 planning task, not missing Phase-0 evidence.

### Phase 0C — Data characterization

**Status:** conditional pass.

- QDM remains acquisition/staging tooling;
- Dukascopy M1 is the initial research-source recommendation;
- explicit time-contract direction validated;
- production and Darwinex broker-reference data remain future manual inputs.

### Phase 1 — Lab foundation

**Status:** conditional pass.

Implemented:

- SQLite WAL state;
- deterministic task and artifact identities;
- guarded lifecycle transitions;
- checkpoints and resume;
- idempotent registration;
- dummy multi-stage workflow;
- provenance and event foundation.

Not a Phase-2 blocker:

- service enable/reboot proof;
- backup and repair procedure.

Required before bulk search:

- bounded worker pool and concurrent kill/resume proof.

## Phase 2 — Engine proof and native parity

### Completed local/narrow work

- strict canonical ingestion;
- time and DST contracts;
- NY+7 support;
- M5/H1 aggregation;
- Layer-1 kernels and typed transforms;
- typed AST and identities;
- entry/exit intents;
- narrow simulator and precedence;
- deterministic RNG;
- narrow metrics;
- MQL5 generation;
- accepted component/time/execution canaries;
- corrected ten-strategy v2 compiler evidence;
- persistent Windows evidence runner.

### FR-T1 — Corrected ten-strategy native campaign

**Model:** Terra.  
**Status:** immediate hard blocker.

- execute GDAXI/M1 A1+A2 and AUDCAD/M1 B1+B2;
- enforce frozen environmental policy;
- return atomic packages;
- import and reconcile all ten ledgers;
- prove repeatability;
- create formal acceptance record;
- never widen budgets or change semantics.

No market data required.

### FR-T2 — Replay and placebo fixtures

**Model:** Luna.  
**May run in parallel with FR-T1.**

- whole-experiment deterministic replay bundle;
- deterministic planted-edge/scramble destruction fixture;
- permanent CI evidence;
- no production data.

### FR-T3 — Gate-closure decision packet

**Model:** Sol for consequential drafting; Luna for mechanical matrix updates; Gasper decides.

- close D1–D7;
- add lockbox/trial-count and execution-policy decisions;
- update machine-readable gate matrix;
- set `phase2_complete` true only if every binding row closes;
- keep Phase-3 authorization separate.

### FR-T4 — Cross/Slope AST admission and registry prototype

**Model:** Luna, with architecture review of canonical encoding.

- typed AST nodes for Cross and Slope;
- strict typing and canonical identities;
- deterministic MQL5 translation;
- local parity fixtures;
- single-store registry prototype derived from manifests;
- remain non-searchable until native admission and authorization.

### FR-T5 — Worker pool

**Model:** Terra.

- bounded process workers;
- one SQLite writer;
- immutable worker outputs;
- retries and guarded transitions;
- concurrent kill/resume proof;
- runtime ledger.

This is required before a large Phase-3 batch but is not evidence that Phase 2 passed.

## Phase-3 authorization gate

Phase 3 may be considered only after `PHASE2_COMPLETION_GATE.md` is satisfied. It begins only after a separate signed D8 authorization.

Before the first search run:

- active grammar dependencies are explicitly searchable;
- execution policy is chosen;
- metric unit/cost basis is frozen;
- family ranking, floors, and ceilings are pre-registered;
- approved data contracts and splits exist;
- lockbox and trial-count ledger are sealed;
- worker pool is accepted;
- Phase-3 workload calibration is complete.

## Phase 3 — Initial search

Build only:

- trend-pullback v1.0;
- close-confirmed breakout v1.0;
- deterministic stratified sampler;
- canonical deduplication;
- bounded local refinement;
- 3–4-dimensional behavioral archive;
- lineage and batch checkpoints;
- matched best-of-N random-search baseline.

Acceptance:

- repeated sampling has zero canonical duplicates;
- batches resume without duplication;
- archive coverage is useful rather than one-candidate-per-cell;
- sampling/refinement beats the matched random baseline at equal budget;
- no lockbox access.

No evolution.

## Phase 4 — Cheap robustness

Order:

1. mechanical/data-contract checks;
2. frozen IS/OOS and temporal validation;
3. cost stress;
4. local parameter neighborhood;
5. Trade MC;
6. contextual market/timeframe/session/regime evidence;
7. behavioral clustering and representatives.

Requirements:

- machine-readable failure/evidence codes;
- per-stage data-access map;
- immutable seeds and shard identities;
- interruption/resume;
- aggressive attrition before expensive testing.

## Phase 5 — Expensive robustness

Only clustered representatives enter:

- Parameter MC;
- parameter-surface summaries;
- WFV by default where justified;
- WFO only for families requiring reoptimization;
- runtime estimation and shard reuse.

Explicit human approval required.

## Phase 6 — Portfolio lab

After a real survivor pool exists:

- synchronized daily P&L;
- tail/downside correlation;
- drawdown overlap;
- concentration caps;
- greedy portfolio construction;
- stressed drawdown allocation;
- broker-compatible sizing;
- portfolio MC and dropout/cost shocks.

Requires Gasper-approved capital, drawdown, leverage, and concentration limits.

## Phase 7 — Finalist validation

Only Linux-pipeline finalists:

- tick retest where justified;
- production-grade MQL5;
- broker-profile binding;
- native Darwinex MT5 run;
- returned reports and ledgers;
- reconciliation under frozen finalist budgets;
- explicit distinction between Linux research and native confirmation.

Large/tick data requires advance notice.

## Phase 8 — Nora workshop

- manifest-driven progression;
- decision packets;
- event-driven Hermes wakeups;
- Telegram milestone reporting;
- research-memory queries;
- immutable protocol enforcement.

## Phase 9 — Deferred intelligence

Only after trustworthy experiment history:

- typed evolutionary search;
- ML survival/allocation models;
- regime/HMM/Markov layers;
- remote/distributed compute.

## Binding sequencing rules

1. No search before Phase-2 gate closure and signed Phase-3 authorization.
2. No searchable component without full evidence and explicit promotion.
3. No MT5 bulk research.
4. No evolution before two-family plateau under matched budgets.
5. No expensive robustness on large populations.
6. No portfolio tooling before validated survivors.
7. No broad tick infrastructure before finalists.
8. No lockbox access before the approved gate.
9. No threshold changes after an experiment begins.
10. No large data acquisition without advance notice.
11. No silent conversion of production broker-time data.
12. No automated deployment in v1.
