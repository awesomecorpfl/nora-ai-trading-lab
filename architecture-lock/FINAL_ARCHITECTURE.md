# Nora AI Trading Lab — Final Architecture v2

This is the target architecture for the complete lab. Current implementation status is recorded separately in `IMPLEMENTATION_STATUS.md`.

## 1. Design principles

1. Research remains Linux-first.
2. Correctness, determinism, and evidence identity take priority over feature count.
3. MT5 is used only where native execution fidelity is required.
4. Search cannot outrun parity.
5. Production data time semantics are explicit and never silently normalized.
6. Cheap, high-rejection robustness stages run before expensive stages.
7. Every stochastic and resumable unit has an immutable identity.
8. Human decisions control search authorization, lockbox access, risk limits, and deployment.

## 2. System boundary

```text
manual/provider acquisition and broker reference exports
                         |
                         v
              Fedora staging and validation
                         |
                         v
 canonical Parquet + explicit time/broker/data contracts
                         |
              +----------+----------+
              |                     |
              v                     v
       Python control plane      Rust labengine
       state, scheduling,        indicators, AST,
       manifests, reports,       simulation, metrics,
       MQL5, MT5 control         robustness, portfolio
              |                     |
              +----------+----------+
                         |
                  accepted survivors
                         |
                         v
                  MQL5 generation
                         |
                         v
         Windows MT5 native parity / finalist checks
                         |
                         v
              manual approved deployment
```

## 3. Language and process ownership

### Rust

Rust owns deterministic compute:

- canonical Parquet reading and validation;
- time-aware aggregation;
- indicator and transform kernels;
- typed AST parsing, validation, canonicalization, hashing, and evaluation;
- intent generation;
- execution simulation;
- metric kernels;
- deterministic sampling and refinement kernels;
- Monte Carlo and robustness kernels;
- joint portfolio replay and stress kernels;
- synthetic integrity fixtures.

### Python

Python owns control and governance:

- SQLite operational state;
- task registration and lifecycle;
- batch scheduling and worker-pool control;
- checkpoint/resume and atomic artifact registration;
- protocol and gate enforcement;
- data ingestion orchestration;
- MQL5 generation;
- Windows runner orchestration;
- returned-package verification and reconciliation;
- clustering and archive reports;
- human decision packets;
- CLI and event dispatch.

### Process boundary

```text
labengine <task.json>
  reads: immutable Parquet/JSON inputs
  writes: immutable Parquet/JSON outputs and exit status
```

No PyO3, RPC, or socket protocol is required for v1. Tasks should normally be shardable into bounded units with atomic outputs.

## 4. Storage

### SQLite

One control-plane writer owns mutable state:

- experiments;
- stages and tasks;
- task attempts and transitions;
- checkpoints;
- protocol decisions;
- trial counts;
- lockbox access log;
- artifact registry;
- events and human approvals.

Workers never write SQLite directly.

### Parquet

Immutable artifacts:

- canonical market data;
- derived timeframes;
- indicator series;
- intents and ledgers;
- metrics;
- robustness shards;
- behavioral descriptors;
- portfolio simulations.

### DuckDB

Optional stateless analysis over Parquet. It is not an authoritative database.

## 5. Data and time contracts

Every dataset identity includes:

- provider and source-symbol identity;
- file/content hash;
- date range and timeframe;
- source and bar timestamp semantics;
- dataset timezone and DST regime;
- session clock and trading-day boundary;
- strategy evaluation clock;
- higher-timeframe anchoring rules;
- conversion history and double-conversion guard;
- spread preparation and cost-reference metadata;
- schema/protocol version.

Current UTC fixtures remain unchanged.

Production research datasets are manually prepared by Gasper when needed. The preferred MT5 production clock is New York time plus seven hours, seasonally UTC+02/UTC+03 following New York DST. The lab validates and records the declared contract; it does not silently convert it.

Large or tick-data acquisition requires advance notice and explicit approval.

## 6. Broker profiles

Broker profiles are schema-validated, identity-hashed data documents, not separately governed software registries.

A profile may include:

- broker and account class;
- timezone/DST and trading-day boundary;
- symbol mapping and session schedule;
- point, tick size, digits, contract size;
- volume min/max/step;
- spread evidence and policy;
- commission, swap, slippage policy;
- stop/freeze levels;
- margin and trading mode;
- evidence provenance.

Observed broker facts and research policy assumptions must be separate fields.

Initial scope: Darwinex Zero Forex. Fusion Markets, Darwinex Classic, Darwinex Zero Futures, and IC Markets are deferred until a consumer exists.

## 7. Strategy representation

The strategy model separates:

- AST schema identity;
- canonical AST identity;
- family grammar identity;
- parameter-vector identity;
- execution-policy identity;
- strategy-instance identity;
- dataset identity;
- metric-protocol identity;
- robustness-protocol identity;
- experiment identity.

Canonical encoding excludes display labels, local paths, timestamps, file-container metadata, unordered map order, and report formatting.

Identity layers should be added only when a consumer and validator exist. The hierarchy is prototyped against current manifests before it is locked as a complete registry contract.

## 8. Component registry and admission

Use one versioned registry store with typed `registry_kind` variants rather than many independently governed registries.

True component records include:

- indicators and named outputs;
- transforms;
- entry and exit actions;
- execution policies;
- time rules;
- metrics;
- robustness tests;
- family grammars;
- MQL5 translators.

Boolean operators and comparisons are static AST-schema tables. Compiler, parity, and native states are derived from sealed manifests by identity reference. Broker profiles are data documents.

### Evidence states

```text
unimplemented
→ implemented
→ translated
→ compiler_verified
→ parity_pending
→ parity_verified
→ searchable
```

Also: `deprecated`, `rejected`.

Rules:

- dependency identity changes expire downstream evidence;
- compiler evidence is never semantic parity;
- `parity_verified` is still non-searchable;
- only Gasper may explicitly promote a component to searchable;
- promotion requires Phase-3 authorization and active grammar dependency closure.

## 9. Execution policies

Narrow v1 semantics remain:

- completed-bar evaluation;
- next-open market entry;
- one position;
- fixed initial stop and target;
- signal exit;
- time exit;
- pessimistic intrabar ambiguity;
- gaps at observed open;
- no pending entries, partial exits, or complex trailing.

Two existing exit-price conventions must remain distinct identities:

- `market_v1_open_exit`: signal/time exits at current bar open; recommended for initial Phase 3 because it has accepted native evidence.
- `ten_suite_close_exit`: signal/time/Friday exits at decision-bar close; frozen for suite regression evidence.

A family grammar references exactly one execution-policy identity.

## 10. Initial family grammars

No grammar is active until Phase 3 is authorized and all dependencies are searchable.

### Trend-pullback v1.0

Deliberately narrow two-condition form:

```text
trend filter AND pullback trigger
```

Proposed dependencies:

- trend: EMA ordering and/or EMA slope;
- pullback: distance from EMA normalized by Wilder ATR;
- optional long/short mirrored templates;
- completed-bar signal, next-open entry;
- selected signal/time/bracket exits;
- strict parameter constraints such as fast period < slow period;
- no optional third filter in v1.0;
- bounded AST complexity.

### Close-confirmed breakout v1.0

Proposed form:

- completed-bar close crosses Highest/Lowest reference;
- optional narrow trend filter only if predeclared;
- next-open entry;
- strict lookback and symmetry constraints;
- selected signal/time/bracket exits;
- no intrabar stop-entry semantics.

Cross and Slope typed AST admission is pre-grammar work.

## 11. Candidate generation

Deterministic pipeline:

```text
family quota
→ structural template
→ typed component selection
→ constrained parameter sampling
→ canonicalization
→ semantic validation
→ canonical identity
→ duplicate check
→ simulation
→ metrics
→ descriptors
→ archive decision
```

Requirements:

- immutable domain-separated seeds;
- no global mutable RNG cursor;
- invalid relationships prevented during generation;
- bounded retry counts;
- deterministic failure codes;
- batch-level checkpointing;
- lineage from template and parent identities;
- matched best-of-N random-search baseline.

## 12. Local refinement

Local refinement is deterministic and IS-only.

- only declared parameters are eligible;
- neighborhoods preserve relational constraints;
- domains are discrete and versioned;
- evaluation budget is fixed before execution;
- candidate ranking uses the family protocol;
- ties resolve by canonical identity;
- acceptance requires a predeclared improvement threshold;
- plateau rules are versioned;
- lineage and task identity are recorded.

It is not mutation, Parameter MC, grid optimization, or WFO.

## 13. Behavioral archive

Use only 3–4 coarse cell dimensions in v1:

- trades/month bucket;
- holding-period bucket;
- long/short balance bucket;
- session-concentration bucket.

Other descriptors remain diagnostic until population studies prove they add nonredundant diversity.

Each archive protocol defines:

- descriptor formulas and version;
- cell identity;
- capacity;
- replacement comparator;
- sparse-cell behavior;
- deterministic ties;
- migration policy when descriptor versions change.

Global ranking and archive-cell replacement may use different comparators.

## 14. Metrics and ranking

Nora owns metric semantics. SQX formulas are evidence, not authority.

Principles:

- exact unrounded internal values;
- display rounding only;
- deposits/withdrawals excluded;
- invalid denominators become null;
- no profit-factor sentinel;
- positive running peak required for percentage drawdown;
- stagnation measured in completed bars;
- minimum samples before unstable ratios;
- Monte Carlo percentiles are descriptive.

Phase-3 screening units must be decided before ranking is frozen. Recommended basis: per-unit or R-multiple returns with an explicit versioned cost approximation. Full account-currency money metrics wait for a cost and sizing contract.

Initial lexicographic framework:

1. mechanical validity;
2. minimum trade floor;
3. drawdown ceiling as a hard gate;
4. predeclared family metric: net result or average trade;
5. return/drawdown with explicit zero-drawdown handling;
6. AST simplicity;
7. canonical identity.

Drawdown is not also used as an opaque weighted score. Archive replacement uses a separately declared comparator.

Sharpe, Sortino, and stability remain diagnostic until Nora-owned formulas are frozen.

## 15. Robustness funnel

Each stage declares allowed data access, gate/context role, protocol identity, seed/shard identity, checkpoint, and failure code.

```text
Stage 0  Mechanical and data-contract validity
Stage 1  Frozen IS/OOS and temporal validation
Stage 2  Cost stress
Stage 3  Local parameter neighborhood
Stage 4  Trade-list Monte Carlo
Stage 5  Contextual market/timeframe/session/regime evidence
Stage 6  Behavioral clustering and representative selection
Stage 7  Family-specific Parameter MC, WFV, or WFO
Stage 8  Portfolio gate
Stage 9  Tick and native MT5 finalist validation
```

Rules:

- cheap filters first;
- Trade MC and re-backtest perturbation are distinct;
- contextual failures do not become rejection gates without a frozen family protocol;
- expensive tests run only on a small representative set;
- completed shards are independently reusable;
- incomplete outputs never count as success;
- WFV/WFO semantics are Nora-owned and fixture-tested, never copied from unresolved SQX behavior.

## 16. Multiple-testing and lockbox governance

- Permanent lockbox defined at first production-data ingestion.
- Access is human-gated and logged.
- Trial counts are ledgered per experiment.
- Protocol thresholds cannot change mid-experiment.
- A matched best-of-N random baseline is mandatory for Phase-3 acceptance.
- Placebo/permutation integrity tests are permanent.
- DSR is diagnostic only unless a separate protocol is approved.

## 17. Worker pool and resumability

Before large search batches, Python gains a bounded process worker pool:

- default starting point: four workers, subject to Phase-3 calibration;
- one SQLite writer in the control plane;
- workers write immutable files only;
- idempotent task registration;
- guarded task transitions;
- atomic output publication;
- retry policy by task type;
- kill/resume proof with zero duplicate accepted tasks;
- runtime ledger for wall-time estimation.

## 18. MQL5 and MT5

MT5 has two narrow roles:

1. Phase-2 component and strategy parity before search.
2. Phase-7 finalist confirmation after Linux robustness and portfolio selection.

Admission equation:

```text
Rust semantics
+ deterministic MQL5 translation
+ parity fixture
+ compiler evidence
+ accepted native evidence
= parity_verified
```

`parity_verified` does not equal searchable.

The ten-strategy suite is:

- a Phase-2 architecture canary;
- a compiler/native evidence packet;
- a regression suite;
- not the permanent Phase-3 execution path.

After suite acceptance, add an equivalence fixture binding suite outputs to the AST → intents → simulator path.

## 19. Portfolio architecture

Deferred until funnel-validated strategies exist.

- joint daily P&L replay;
- downside/tail correlation;
- drawdown overlap;
- loss-streak and recovery analysis;
- concentration caps;
- greedy forward selection;
- marginal stressed drawdown contribution;
- drawdown-based risk budgets;
- broker-compatible sizing;
- portfolio Monte Carlo;
- cost shocks and dropout stress.

No covariance/mean-variance optimization.

## 20. Nora/Hermes governance

- event-driven and gate-based;
- CLI-only in v1;
- routine progress without AI wakeups;
- closed decision packets;
- immutable experiment protocols;
- explicit human approvals;
- no threshold adjustment based on observed results;
- manual deployment outside the automated lab.

## 21. Deferred work

- evolutionary search until two-family sampling/refinement plateaus under matched budgets;
- pending orders, partial exits, and advanced trailing;
- advanced indicator families without evidence of diversity value;
- remote/distributed compute;
- GUI and MCP;
- ML survival models, HMM/Markov regimes, and surrogate allocation;
- automated demo/live deployment.
