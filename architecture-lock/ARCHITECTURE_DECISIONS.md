# ARCHITECTURE_DECISIONS.md
Nora AI Trading Lab — Decision Register

---

## LOCK NOW

### L1. Linux-first research platform
All strategy generation, research backtesting, robustness, Monte Carlo, clustering, portfolio construction, and experiment orchestration run on Fedora.

MT5 is excluded from the bulk research loop.

### L2. Rust engine + Python control plane **[disputed]**
Keep the split.

Rust owns compute-heavy deterministic simulation and batch work. Python owns orchestration, state, reporting, clustering, MQL5 generation, and MT5 validation control.

Spike 0B calibrates throughput and worker economics; the split itself is locked.

### L3. Process boundary: subprocess + files **[disputed]**
Use JSON task specifications in and Parquet/JSON outputs out.

Do not use PyO3, RPC, or sockets in v1.

Reason: crash isolation, replayability, checkpointing, and independent lifecycles matter more than microsecond call overhead at task-scale granularity.

### L4. SQLite + Parquet + DuckDB **[disputed]**
- SQLite: mutable operational state.
- Parquet: immutable artifacts and canonical market data.
- DuckDB: stateless analytics over Parquet.

No persistent DuckDB source of truth and no Postgres requirement for v1.

### L5. Single typed AST with canonicalization, stable hashing, and versioned schema
Core enabler for deduplication, lineage, provenance, deterministic search, and MQL5 generation.

### L6. MQL5-translatability is a grammar admission rule
No searchable AST node or indicator exists without:

- Rust implementation;
- MQL5 translation;
- parity fixture.

Permanent rule.

### L7. Narrow v1 execution semantics
- completed-bar signals;
- next-open market entries;
- M1 intrabar SL/TP path;
- pessimistic ambiguity;
- simple exits/trailing only.

Pending entries, partial exits, and complex trailing are deferred.

### L8. Pessimistic ambiguity resolution
Always resolve ambiguous bars pessimistically.

### L9. MT5 parity is a small Phase-2 gate, not a research loop
Before search, simple canary strategies and indicators must reconcile between Rust and MT5.

This does not mean research populations are run through MT5.

### L10. Existing Windows VM is the MT5 validation boundary
The existing dedicated Windows 10 LTSC VM remains the validation target.

Known working access path: `ssh nora-win10`.

Do not create a new VM or second terminal unless later evidence shows the existing dedicated VM cannot support the narrow validation contract.

### L11. Robustness funnel ordering
Cheap, high-rejection tests run first.

Order principle:

cost stress
→ IS/OOS and temporal segments
→ cheap parameter neighborhood
→ Trade MC
→ contextual generalization
→ clustering
→ Parameter MC
→ WFV/WFO
→ portfolio stress
→ finalist tick/MT5 validation.

### L12. Universal gates vs contextual evidence
Family-specific protocols distinguish universal hard gates from contextual generalization evidence.

### L13. Multiple-testing control
Use:

- permanent lockbox;
- matched best-of-N random-search baseline;
- tracked trial counts;
- placebo/permutation-style integrity tests;
- DSR diagnostic only.

The matched baseline is not a formal statistical null.

### L14. Portfolio construction
Use:

- greedy forward selection;
- marginal stressed dollar-DD contribution;
- drawdown-based risk budgets;
- concentration caps;
- dropout stress.

No covariance/mean-variance optimization.

### L15. Dollar drawdown is first-class
Portfolio DD target flows into strategy risk budgets and lot sizing.

### L16. Nora governance
- event-driven wakeups;
- CLI-only;
- closed decision packets;
- protocol immutability enforced by control plane;
- human gate for lockbox and deployment.

### L17. Determinism is a tested semantic invariant
Same canonical inputs must reproduce trades, metrics, simulation outcomes, and canonical content hashes.

### L18. Layer-1 indicator set + minimal typed transforms
Start with the locked primitive set and only expand by evidence.

### L19. Lab integrity suite
Synthetic fixtures, canaries, and placebo tests are permanent CI requirements.

### L20. Data contract direction
- canonical M1 Parquet with an explicit, versioned trading-timezone contract, not UTC-only storage;
- production research may evaluate directly in the declared target MT5 broker clock; the current intended-broker preference is New York +7 (UTC+02/UTC+03 with the relevant New York DST schedule);
- provenance includes timezone identity, DST regime/rule version, source/bar timestamp semantics, session clock, strategy clock, optional UTC reference instant, and every conversion;
- conversion is deterministic and guarded against accidental double conversion; future timezone contracts remain supported;
- one primary M1 provider selected in Phase 0C;
- internally derived higher TFs;
- tick data only where justified.

### L21. QDM runs on Fedora as acquisition/staging/export tooling
QDM is not the provider identity, canonical store, or runtime source of truth.

Files crossing into the lab are hashed and provenance-recorded before ingestion.

### L22. Finalist deployment remains manual in v1
After Linux research and Darwinex MT5 confirmation, moving an EA to the demo VPS is a manual human action.

Automated live deployment is not part of v1.

---

## PROTOTYPE BEFORE LOCKING

### P1. Repository-owned MT5 validation harness over the existing known-working path
Nora already has working SSH access and has run MT5 backtests through the CLI.

The prototype task is to audit and codify that actual workflow into a reproducible repository-owned harness for:

- pinned test configuration;
- launch;
- completion detection;
- artifact return;
- parseable results;
- two-run semantic comparison;
- interruption classification.

This is a narrow validation harness, not a platform-selection spike.

### P2. Engine throughput and worker count
Benchmark 4/6/8/10/12 workers and determine sustained thermal throughput.

### P3. Exact AST node inventory
Approach is locked; concrete v1 node inventory is frozen through Phase-2 co-design with MQL5 generation.

### P4. Numeric parity budget
Freeze empirically after early Phase-2 reconciliation.

### P5. Behavioral descriptor definitions and grid resolution
Tune on a real population, then freeze per protocol version.

### P6. Clustering features and thresholds
Start with trade-time overlap, daily P&L correlation, and canonical-structure distance.

### P7. Cost models per symbol
Validate spread/slippage/swap model shapes against broker reference data and MT5 reports.

### P8. WFV vs WFO policy per family
WFV default. WFO only where protocol requires reoptimization.

### P9. Scheduler runtime-learning model
Start simple with historical medians by task type and candidate count.

### P10. Phase-2 parity data path
Determine the cleanest parity reference route:

- broker reference data extracted to Linux for matched canary comparison; or
- pinned canonical fixture imported to MT5 if necessary.

Do not make custom-symbol import a prerequisite for Phase 1.

---

## DEFER

### D1. Evolutionary machinery
Only after stratified sampling + refinement plateaus.

### D2. Pending orders, partial exits, advanced trailing
Execution v2 after stable parity.

### D3. Condition-mask caching and micro-optimization
Benchmark first.

### D4. Layer-2–4 indicators and advanced volume/profile families
Evidence-driven expansion.

### D5. ML survival predictors and surrogate allocation
Requires accumulated lab history.

### D6. Regime/HMM/Markov risk layers
Future work only.

### D7. Remote/distributed workers
File task boundary leaves room later.

### D8. GUI and MCP
Out of v1 scope.

### D9. Automated live/demo deployment
Manual human deployment remains the v1 boundary.
