# Nora AI Trading Lab — Risks and Failure Modes v2

Ordered by likely damage and probability.

## 1. Evidence and parity

### R1 — Compiler evidence mistaken for semantic parity

A generated EA can compile cleanly and still implement the wrong formula.

**Mitigation:** full identity chain and accepted native reconciliation before parity-verified or searchable state. Preserve failed evidence.

### R2 — Corrected ten-strategy campaign remains incomplete

Without four fresh corrected runs, the suite cannot prove corrected parity.

**Mitigation:** FR-T1 is the immediate hard blocker; fail closed on any environmental or ledger mismatch.

### R3 — Tolerance creep

Budgets may be widened after observing differences.

**Mitigation:** fixture-specific versioned budgets frozen before execution; no global tolerance; any mismatch becomes diagnosis.

### R4 — Three execution implementations drift

Simulator, ten-strategy suite, and generated MQL5 overlap.

**Mitigation:** explicit execution-policy identities and a post-acceptance suite-to-simulator equivalence fixture.

### R5 — Exit-price convention ambiguity

Bar-open and decision-bar-close signal/time exits coexist.

**Mitigation:** human D3 decision; every grammar binds one policy identity.

## 2. Search and model risk

### R6 — Grammars cannot be expressed in the AST

Cross and Slope transforms exist but typed AST nodes do not.

**Mitigation:** FR-T4 admission work before grammar materialization; no bypass through hard-coded strategy paths.

### R7 — Registry overengineering

Too many independently governed registries create drift and process burden.

**Mitigation:** one typed store, static schema tables, evidence derived from manifests.

### R8 — Behavioral archive degenerates

Too many descriptor dimensions create one-candidate-per-cell behavior.

**Mitigation:** 3–4 coarse dimensions in v1; population study before locking.

### R9 — Local refinement becomes hidden optimization

Repeated neighborhoods may overfit or consume OOS information.

**Mitigation:** IS-only scope, fixed budget, declared improvement/plateau rules, lineage and trial counts.

### R10 — Opaque ranking

Weighted composites or post-hoc metric changes hide researcher degrees of freedom.

**Mitigation:** lexicographic protocol, family metric pre-registration, deterministic tie handling, DD as gate only.

## 3. Metric and cost risk

### R11 — Money metrics without a cost/sizing producer

Current ledgers are per-unit gross and cannot support full account-currency claims.

**Mitigation:** choose D6 before Phase 3; use per-unit/R-multiple with versioned approximation or gross screening plus mandatory cost stress. Do not claim money drawdown early.

### R12 — Invalid ratios presented as favorable values

Zero denominators can inflate PF or return/DD.

**Mitigation:** explicit null policy; no sentinel; positive-peak requirement; declared zero-drawdown ordering.

### R13 — Broker/source mismatch

Research prices, sessions, spread, and native broker behavior may differ.

**Mitigation:** separate data, broker-profile, and execution-policy identities; contextual evidence and finalist native checks.

## 4. Data and leakage

### R14 — Silent timezone or DST conversion

Time-dependent rules can be wrong while prices look valid.

**Mitigation:** versioned time contracts, conversion history, double-conversion rejection, gap/fold tests.

### R15 — Lockbox erosion

Repeated access or undocumented trial counts destroys validation value.

**Mitigation:** lockbox sealed at first production ingestion, logged human-gated access, SQLite trial ledger.

### R16 — Data leakage across funnel stages

Local refinement, contextual tests, or ranking may consume validation data improperly.

**Mitigation:** per-stage data-access map embedded in the robustness protocol identity.

### R17 — Production-data acquisition becomes automated or uncontrolled

Large downloads can consume time and create unreviewed contracts.

**Mitigation:** advance notice; Gasper manually prepares final broker-time datasets; hashes and provenance recorded.

## 5. Determinism and operations

### R18 — Sequential control plane becomes a bottleneck

No worker pool currently exists.

**Mitigation:** bounded process pool before large search; one SQLite writer; workers publish immutable files.

### R19 — Concurrency corrupts task state

Retries or crashes may duplicate accepted work.

**Mitigation:** guarded transitions, idempotent registration, atomic outputs, concurrent kill/resume acceptance.

### R20 — Global RNG cursor makes resume schedule-dependent

Worker order may alter results.

**Mitigation:** immutable domain-separated per-task/per-shard seeds.

### R21 — Laptop thermal or memory limits invalidate estimates

Phase-0B synthetic speed is not production capacity.

**Mitigation:** bounded Phase-3 workload calibration on approved data and grammars before setting batch budgets.

### R22 — Windows runner ambiguity

SSH disconnect or launcher existence may be mistaken for success.

**Mitigation:** detached observable jobs, persistent evidence root, atomic completion markers, importer validation.

### R23 — Historical untracked directories cause evidence confusion

Old partial outputs may be mistaken for current evidence.

**Mitigation:** explicit Gasper decision to archive/commit/delete; never infer acceptance from directory names.

## 6. Robustness and scientific validity

### R24 — Cheap and expensive stages are ordered poorly

Parameter MC/WFO may run on thousands of weak candidates.

**Mitigation:** mechanical, IS/OOS, cost, neighborhood, Trade MC, context, and clustering first.

### R25 — Contextual evidence becomes a universal rejection gate

A strategy may be incorrectly rejected for family-irrelevant behavior.

**Mitigation:** separate context evidence codes; promotion to gate requires a frozen family protocol.

### R26 — Trade MC confused with re-backtest perturbation

Different uncertainty questions become mixed.

**Mitigation:** separate registry/test families, inputs, seeds, and outputs.

### R27 — SQX internals copied without verified semantics

Unresolved fitness, WFO, WFV, SPP, selector, and precision behavior may enter Nora.

**Mitigation:** Nora-owned protocols and fixtures; SQX findings remain a closed reference corpus.

### R28 — Multiple testing produces impressive noise

Large populations inevitably generate false winners.

**Mitigation:** trial counts, matched random baseline, lockbox, placebo tests, immutable protocols, failures retained.

## 7. Portfolio and deployment

### R29 — Portfolio dominated by one strategy or family

**Mitigation:** concentration caps, marginal stressed drawdown, top-strategy/family/symbol dropout tests.

### R30 — Historical max drawdown used as a sizing guarantee

**Mitigation:** stressed drawdown distributions and explicit reserve.

### R31 — Native finalist validation becomes part of discovery

**Mitigation:** MT5 only after Linux funnel survival; no MT5 feedback loop into search thresholds.

### R32 — Automated deployment outruns governance

**Mitigation:** approved EA deployment remains manual in v1.

## 8. Project waste guards

Do not:

- build search on an unaccepted simulator;
- rebuild the working VM without a failed requirement;
- port every SQX indicator;
- build full evolutionary infrastructure early;
- build broad tick infrastructure before finalists;
- treat recommendations as binding gates without evidence;
- let documentation override machine-readable status.
