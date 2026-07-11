# FINAL_ARCHITECTURE.md
Nora AI Trading Lab — Recommended Final Architecture (v1)

This document supersedes the brief where they differ. Material changes from the brief are marked **[CHANGE]**.

---

## 1. Verdict on the architecture

The overall shape is sound: Rust engine, Python control plane, Nora as event-driven director, SQLite/Parquet/DuckDB, a tiered robustness funnel, and portfolio-first selection.

Five material corrections define v1:

1. **The project is Linux-first.** Strategy generation, research backtesting, robustness testing, Monte Carlo, clustering, portfolio construction, and orchestration run on Fedora using Python + Rust. MT5 is not part of the bulk research loop. **[CHANGE]**
2. **MQL5 generation and MT5 parity cannot be deferred until the end.** A small Phase-2 parity gate must verify that the Rust engine and generated MQL5 agree on simple canaries before search begins. **[CHANGE]**
3. **The v1 execution model is deliberately narrow.** Bar-close signals, next-open entries, and pessimistic intrabar ambiguity resolution reduce the parity surface. **[CHANGE]**
4. **The search design starts with stratified grammar sampling + local refinement + behavioral archive**, not full evolutionary machinery. **[CHANGE]**
5. **The existing dedicated Windows 10 LTSC VM is a validation appliance, not a research platform.** It is reached through the already-working SSH path and is used for small parity runs and late-stage native Darwinex MT5 confirmation. **[CHANGE]**

The practical boundary is:

```text
providers / broker reference extracts
                |
                v
       QDM and staging on Fedora
                |
                v
 canonical M1 Parquet + versioned
      trading-timezone contract
                |
        +-------+-------+
        |               |
        v               v
 Python control     Rust compute engine
 plane              research backtests,
 orchestration      robustness, MC,
                    clustering, portfolio
        |               |
        +-------+-------+
                |
           survivors only
                |
                v
         MQL5 generation
                |
                v
   Windows VM / Darwinex MT5
   Phase 2 parity canaries
   Phase 7 finalist confirmation
                |
                v
      manual demo-VPS deployment
```

---

## 2. Language and process boundaries

### Rust
One binary, `labengine`, owns compute-heavy deterministic research:

- canonical data loading and higher-timeframe aggregation;
- indicators and typed derived transforms;
- AST validation/evaluation;
- execution simulation;
- batch backtesting;
- Trade Monte Carlo;
- cost stress;
- parameter-neighborhood tests;
- Parameter Manipulation Monte Carlo;
- WFV/WFO compute kernels;
- portfolio replay and portfolio Monte Carlo;
- synthetic fixtures and canary execution tests.

### Python
The `lab` control plane owns:

- experiment and state management;
- task scheduling and sharding;
- checkpoint/resume;
- protocol enforcement;
- funnel orchestration;
- clustering and representative selection;
- reporting and briefing packets;
- QDM-independent ingestion;
- MQL5 code generation;
- MT5 validation orchestration;
- result parsing and reconciliation;
- Nora CLI and event dispatch.

### MQL5
MQL5 is generated output plus small fixed parity/validation harness code.

It is not used for bulk search, robustness, Monte Carlo, or portfolio construction.

### Process boundary — subprocess + files **[LOCK]**

```text
Python control plane
   └── labengine <task.json>
         reads: Parquet + JSON task specification
         writes: Parquet artifacts + JSON summary + exit code
```

No PyO3, RPC, or socket protocol in v1. The file boundary gives crash isolation, replayable tasks, and natural checkpointing.

Task granularity should target roughly 1–10 minutes where practical. Larger jobs are sharded.

---

## 3. Major modules

### Rust engine (`labengine`)

| Module | Responsibility |
|---|---|
| `data` | Canonical Parquet loading, validation, M1→higher-TF aggregation |
| `indicators` | Layer-1 kernels + typed transforms |
| `ast` | Typed AST parse, validate, canonicalize, hash, serialize |
| `sim` | v1 execution simulator, trade ledger, equity curve |
| `backtest` | Batch candidate evaluation and metrics |
| `search` | Deterministic grammar sampling and later optional evolutionary extensions |
| `robust` | Cost stress, Trade MC, parameter tests, WFV/WFO kernels |
| `portfolio` | Joint replay, portfolio MC, DD overlap, dropout analysis |
| `fixtures` | Synthetic-path and canary integrity tests |

### Python control plane (`lab`)

| Module | Responsibility |
|---|---|
| `state` | SQLite mutable operational state |
| `scheduler` | Worker pool, sharding, runtime learning, resume |
| `protocol` | Versioned rules and immutable gate thresholds |
| `funnel` | Tier orchestration and rejection reasons |
| `cluster` | Behavioral descriptors and representative selection |
| `ingest` | QDM-independent staged-file ingestion into canonical Parquet |
| `mql5gen` | AST → MQL5 EA generation |
| `mt5` | Existing-VM validation harness, result parsing, reconciliation |
| `provenance` | Hashes and lineage for data, AST, engine, protocol, seeds, environment |
| `report` | Human/JSON reports and decision packets |
| `cli` | `lab ...` interface |
| `events` | Event log and Hermes wake dispatch |

The `mt5` module is deliberately narrow. It does not schedule research populations.

---

## 4. Storage architecture **[LOCK]**

### SQLite
Mutable operational state only:

- experiments;
- stages;
- tasks;
- checkpoints;
- events;
- decisions;
- budgets;
- trial counts;
- artifact registry.

WAL mode, one control-plane writer.

### Parquet
Immutable research artifacts:

- canonical market data;
- trade ledgers;
- metrics;
- Monte Carlo shards;
- portfolio simulations;
- derived research datasets.

Example convention:

```text
artifacts/{experiment}/{stage}/{task_id}/...
```

### DuckDB
Stateless analytics over Parquet. No persistent DuckDB database is authoritative.

### Canonical market data
- One primary M1 provider is selected through Phase 0C.
- Canonical storage is M1 Parquet governed by an explicit, versioned trading-timezone contract; it is not permanently UTC-only.
- A production dataset may be prepared and evaluated directly in its declared target MT5 broker clock. The current intended-broker preference is the common New York +7 convention (UTC+02/UTC+03, with the relevant New York DST schedule) used by Darwinex and Fusion and expected for IC Markets.
- The contract records timezone identity, DST regime/rule version, source timestamp semantics, bar timestamp convention, session clock and strategy evaluation clock. UTC instants may be retained as optional reference/interoperability metadata.
- Strategy time rules—Friday close, ORB/session windows, daily resets, rollover avoidance and Monday-open handling—evaluate against the declared strategy clock. Conversion, when used, is deterministic, provenance-recorded, and protected against double conversion.
- Higher timeframes are derived internally.
- Tick data is retained only where justified, primarily finalists and parity/cost-reference samples.

---

## 5. Data acquisition and QDM boundary **[LOCK]**

Quant Data Manager runs on Fedora.

QDM is an external:

- acquisition tool;
- inspection tool;
- staging tool;
- export tool.

QDM is not:

- the canonical market-data store;
- the provider identity;
- the operational database;
- a required runtime dependency of the research engine.

Every staged acquisition crossing into the lab records:

- provider identity;
- symbol;
- date range;
- source timestamp semantics;
- timezone/DST interpretation;
- QDM/tool version where used;
- export settings;
- file hash.

The lab then ingests validated staged files into canonical M1 Parquet through its own reproducible code path. Phase 1 preserves the declared trading-timezone/DST semantics and optional UTC reference instant; it must not silently normalize every dataset to UTC and discard broker-time session meaning. Gasper manually prepares final production research data before import, including the intentional timezone/DST treatment and any prepared average-spread treatment. QDM remains acquisition/staging/export tooling and does not replace that production-data decision.

Existing MT5 utilities that extract broker tick data and symbol specifications are reference-data acquisition tools. Their outputs are immutable provenance inputs.

The Windows VM must not become a bulk market-data workspace.

---

## 6. Strategy representation **[LOCK approach; prototype exact node inventory]**

One typed canonical AST is defined in Rust and serialized as JSON.

Core properties:

- strong types such as `Price`, `Indicator<f64>`, `Bool`, `Duration`, `PriceOffset`, `RiskMultiple`;
- canonicalization;
- stable hashing;
- schema versioning;
- lineage;
- family metadata.

**Grammar admission rule**: no AST node or indicator enters the searchable grammar until:

1. the Rust implementation exists;
2. the MQL5 translation exists;
3. a parity fixture exists.

This rule is permanent.

---

## 7. v1 execution semantics **[LOCK]**

- signals evaluated on completed bars only;
- entries at next bar open;
- initial SL/TP;
- time exit;
- signal exit;
- simple ATR/structure trailing at bar boundaries;
- M1 intrabar path for higher-timeframe strategies;
- pessimistic same-bar ambiguity resolution;
- gaps fill at gapped price;
- realistic spread, commission, slippage, and swap models.

Not in v1:

- pending stop/limit entries;
- partial exits;
- same-bar entry+exit;
- complex trailing.

The v1 breakout family is **close-confirmed breakout**: breakout confirmed at bar close, entry next open.

Tick fidelity is reserved for finalists and narrow parity/cost studies.

---

## 8. Determinism **[LOCK]**

All stochastic components use named logged RNG streams seeded from experiment/stage/task identity.

Same canonical inputs must yield semantically identical:

- trades;
- metrics;
- simulation outcomes;
- canonical content hashes;
- decision-relevant outputs.

Byte-identical Parquet container files are required only if the writer guarantees stable serialization.

---

## 9. Search design **[LOCK v1]**

### v1
1. stratified grammar sampling;
2. Tier 0/1 screening;
3. bounded deterministic local parameter refinement;
4. behavioral descriptor archive.

The archive prevents structural monoculture by keeping the best K candidates per descriptor cell rather than ranking everything globally.

Candidate descriptor examples:

- holding-period bucket;
- trades/month bucket;
- long/short balance;
- session exposure;
- trend-vs-mean-reversion sign;
- volatility-regime preference.

### v1.5
Evolutionary machinery is deferred until sampling + refinement demonstrably plateaus.

No NSGA-II, islands, lexicase, or novelty machinery in the v1 critical path.

---

## 10. Robustness funnel **[LOCK ordering]**

```text
TIER 0   Mechanical integrity
TIER 1   IS/OOS + temporal segments + dollar-DD + cost stress
TIER 1.5 Structural dedup + cheap parameter neighborhood
TIER 2   Trade MC + stability metrics
TIER 3   Contextual generalization + session/regime decomposition
TIER 3.5 Behavioral clustering → representatives
TIER 4   Parameter Manipulation MC + WFV/WFO by family protocol
TIER 5   Preliminary portfolio construction and stress
TIER 6   Tick retest → MQL5 generation → native Darwinex MT5 finalist validation
TIER 7   Final portfolio rebuild + portfolio MC + dollar-DD sizing
```

MT5 is intentionally absent from Tiers 0–5.

### Multiple-testing control
- one permanent final lockbox;
- matched best-of-N random-search baseline;
- tracked trial counts;
- placebo/permutation-style integrity tests;
- DSR diagnostic only in v1.

---

## 11. MT5 role and validation contract **[LOCK boundary]**

The existing Windows 10 LTSC VM is already a dedicated MT5 research/validation machine.

Known environment facts:

- Fedora can reach it through `ssh nora-win10`;
- SSH keys are already configured;
- the VM is not used for live trading;
- it contains one fresh Darwinex MT5 terminal;
- Darwinex access is through an investor/read-only login for broker data and tester use without trade execution permission;
- Nora has already run MT5 backtests through the CLI path.

Therefore the architectural question is not whether to build a new VM.

The MT5 contract has two uses:

### Phase 2 — parity canaries
A small set of hand-designed strategies and indicator fixtures are compared between Rust and MT5 before search begins.

This is a correctness gate, not a research-compute stage.

### Phase 7 — finalist validation
Only survivors from the Linux pipeline are:

1. tick-retested where required;
2. generated to production-grade MQL5;
3. run in native Darwinex MT5;
4. confirmed over the selected multi-year validation window, expected to be approximately six years where data availability and protocol permit;
5. reconciled against Linux results within the frozen parity budget.

Deployment to a demo account on the VPS is a manual human step and is out of the automated v1 lab scope.

---

## 12. Portfolio architecture **[LOCK]**

Unit of analysis: joint daily P&L matrix in account-currency dollars.

Selection:

- greedy forward selection;
- marginal effect on stressed dollar drawdown;
- expectancy awareness;
- concentration caps by symbol, currency, asset class, family, and session.

Sizing:

target portfolio dollar DD
→ stressed joint DD distribution
→ marginal DD contribution
→ strategy risk budgets
→ broker-compatible lot sizing.

No mean-variance or covariance-matrix optimization.

Mandatory stress:

- top-strategy dropout;
- family dropout;
- symbol-family dropout;
- correlated spread/slippage shocks;
- regime concentration report.

---

## 13. Nora / Hermes operating model **[LOCK]**

- event-driven;
- gate-based;
- CLI-only;
- no polling;
- protocol thresholds immutable mid-experiment;
- closed decision packets;
- routine progress without AI wakeups;
- human gate for lockbox and real deployment;
- research memory through lab query commands, not raw database access.

One systemd user supervisor runs the control plane. Tasks resume from SQLite state. CLI commands are idempotent.

---

## 14. Layer-1 indicators and transforms

Layer-1 primitives:

- SMA
- EMA
- ADX
- ER
- KAMA
- MACD
- linear regression
- RSI
- CCI
- ROC
- Stochastic
- ATR
- Bollinger Bands / Width
- Keltner
- Highest / Lowest
- Session OHLC
- VWAP

Minimal typed transforms:

- cross;
- slope;
- distance/ATR;
- percentile.

Expansion is evidence-driven and parity-gated.

---

## 15. Decisions now locked

1. Fedora/Linux owns essentially all research compute.
2. MT5 is a narrow execution-fidelity authority, not a bulk research platform.
3. The existing Windows VM remains the MT5 validation environment.
4. Rust engine + Python control plane.
5. Subprocess + JSON/Parquet file boundary.
6. SQLite + Parquet + DuckDB storage roles.
7. QDM on Fedora as acquisition/staging/export tooling only.
8. Canonical M1 Parquet with a versioned trading-timezone contract; higher TFs derived internally.
9. Typed canonical AST with MQL5-translatability admission rule.
10. v1 narrow execution semantics and pessimistic ambiguity resolution.
11. Small Phase-2 MT5 parity gate before search.
12. Stratified sampling + local refinement + behavioral archive for v1 search.
13. Cheap robustness filters before expensive Parameter MC and WFV/WFO.
14. Portfolio-first selection with dollar drawdown as primary risk constraint.
15. Event-driven Nora governance with immutable protocols.
16. Manual human-controlled demo deployment remains outside automated v1 scope.
