# Nora AI Trading Lab — Architecture Decision Register v2

No decision in this file self-executes. Human approval and repository evidence remain required.


## Package adoption

| ID | Decision | Status |
|---|---|---|
| A1 | Replace the earlier seven-document architecture package with this final package while preserving the earlier version in Git history | LOCKED |
| A2 | Treat D1–D8 as future gate decisions, not prerequisites to adopting the architecture package | LOCKED |
| A3 | Keep the SQX findings, New Plan, and Fable Review folders as supporting evidence outside the architecture-lock directory | LOCKED |

## Retained locks

| ID | Decision | Status |
|---|---|---|
| L1 | Fedora/Linux owns strategy generation, research backtesting, robustness, Monte Carlo, clustering, portfolio research, and orchestration | LOCKED |
| L2 | Rust compute engine and Python control plane | LOCKED |
| L3 | Subprocess JSON/Parquet file boundary; no PyO3/RPC/socket protocol in v1 | LOCKED |
| L4 | SQLite mutable state, Parquet immutable artifacts, DuckDB stateless analytics | LOCKED |
| L5 | Explicit versioned dataset timezone, DST, session, strategy-clock, anchoring, and conversion-history contract | LOCKED |
| L6 | Gasper manually prepares final production datasets; the lab validates rather than silently converts them | LOCKED |
| L7 | Typed canonical AST with stable semantic identities | LOCKED |
| L8 | Completed-bar decisions, next-open entries, narrow v1 execution, pessimistic ambiguity | LOCKED |
| L9 | MT5 is a narrow parity/finalist authority, not a research loop | LOCKED |
| L10 | Existing `nora-win10` VM remains the validation environment | LOCKED |
| L11 | Cheap robustness filters before expensive Parameter MC/WFV/WFO | LOCKED |
| L12 | Hard rejection gates and contextual evidence remain distinct | LOCKED |
| L13 | Permanent lockbox, logged access, trial counts, matched random baseline, placebo integrity tests | LOCKED |
| L14 | Portfolio selection uses stressed drawdown, greedy addition, caps, and dropout stress | LOCKED |
| L15 | Event-driven Nora governance with immutable protocols and human gates | LOCKED |
| L16 | Large market-data acquisition requires advance notice to Gasper | LOCKED |
| L17 | Manual deployment remains outside automated v1 | LOCKED |

## Approved revisions to the earlier plan

| ID | Decision | Status | Resolution |
|---|---|---|---|
| R1 | Native evidence required before searchability | LOCKED | Extend grammar admission: Rust + translation + fixture + compiler + accepted native evidence |
| R2 | Registry shape | APPROVED_WITH_REVISION | One typed store; static operator tables; evidence derived from sealed manifests; broker profiles as data documents |
| R3 | Initial families | APPROVED_WITH_REVISION | Trend-pullback v1.0 and close-confirmed breakout v1.0; no optional third trend filter; exact execution-policy identity required |
| R4 | Candidate generation | APPROVED | Stratified family/template quotas, constrained sampling, canonical dedup before simulation, immutable seeds |
| R5 | Local refinement | APPROVED_WITH_REVISION | Deterministic, bounded, IS-only, constraint-preserving, predeclared improvement/plateau rules |
| R6 | Behavioral archive | PROTOTYPE_FIRST | 3–4 coarse descriptors only; tune on an authorized population before freezing |
| R7 | Ranking | APPROVED_WITH_REVISION | Lexicographic; DD gate-only; metric/unit choice predeclared; zero-DD behavior explicit |
| R8 | Metric ownership | APPROVED_WITH_REVISION | Nora-owned semantics; cost/money metrics only after cost and sizing contracts |
| R9 | Robustness stages | APPROVED_WITH_REVISION | Add per-stage data-access map and immutable shard protocol |
| R10 | Immutable per-shard RNG | APPROVED | No shared mutable cursor |
| R11 | Family-specific WFV/WFO | DEFERRED | Nora-owned protocol and fixtures only; never copy unresolved SQX mechanics |
| R12 | Evolution | DEFERRED | Activate only after two-family plateau, resume, dedup, archive, and matched-budget proof |

## Prototype before locking

| ID | Item | Required proof |
|---|---|---|
| P1 | Complete identity hierarchy | Demonstrate each proposed identity has a consumer and validator using the 22-node matrix and ten-strategy suite |
| P2 | Registry implementation | Reconcile a single-store prototype 100% against authoritative sealed manifests |
| P3 | Broker-profile schema | Validate against one real Darwinex Zero export when Gasper authorizes it |
| P4 | Archive grid and replacement comparator | Population coverage and sensitivity study |
| P5 | Metric unit/cost approximation | Small deterministic fixtures and explicit protocol |
| P6 | Worker-pool sizing | Approved-dataset workload calibration after Phase-3 authorization |
| P7 | WFV/WFO family protocol | Deterministic small fixture and demonstrated family need |
| P8 | Portfolio rules | Real survivor pool and Gasper-approved capital/risk inputs |

## Decisions required before Phase 3

| ID | Decision | Recommendation |
|---|---|---|
| D1 | Layer-1 gate scope | Narrow to initial grammar-dependency closure |
| D2 | Parity budgets | Field/fixture-specific and versioned; no global tolerance |
| D3 | Execution-policy convention | Use bar-open signal/time exits for initial grammars |
| D4 | Family ranking metric | Pre-register net result or average trade per family |
| D5 | Trade floors and drawdown ceilings | Pre-register per family and timeframe |
| D6 | Metric unit and cost basis | Per-unit/R-multiple with versioned cost approximation, or gross plus mandatory cost stress |
| D7 | Initial data, splits, lockbox, and trial ledger | Gasper-prepared contracts and sealed lockbox before first search |
| D8 | Phase-3 authorization | Separate signed approval after the gate closes |

## Additional explicit decisions

| ID | Decision | Status |
|---|---|---|
| M1 | Keep lockbox and trial-count governance as a first-class manifest requirement | LOCKED |
| M2 | Treat bar-open and decision-bar-close exits as different execution-policy identities | LOCKED; Phase-3 selection pending D3 |
| M3 | Do not claim account-currency money metrics until cost and sizing contracts exist | LOCKED |
| M4 | Right-size native parity to active grammar dependency closure | RECOMMENDED; pending D1 |
| M5 | Historical untracked Phase-0A directories require explicit archive/commit/delete decision | OPEN |

## Deferred

- pending orders, partial exits, advanced trailing;
- Layer-2–4 indicators and volume/profile families;
- broad broker expansion;
- remote/distributed workers;
- GUI/MCP;
- ML, HMM, Markov, and surrogate allocation;
- automated demo/live deployment.

## Rejected approaches

- MT5 bulk research;
- PyO3/RPC rewrite without measured need;
- XML-only strategy identity;
- universal unrestricted grammar;
- mutable global RNG;
- hidden candidate repair;
- unrestricted tree growth;
- opaque weighted fitness;
- copying unresolved SQX ranking, WFO, WFV, SPP, or profit-factor sentinel behavior;
- evolutionary search in initial Phase 3;
- immediate multi-broker scope.

## Authorization state

- Phase 2 complete: no.
- Phase 3 authorized: no.
- Searchable components: none.
