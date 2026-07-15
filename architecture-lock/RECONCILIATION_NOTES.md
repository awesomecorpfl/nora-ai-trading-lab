# Nora AI Trading Lab — Final Architecture Reconciliation and Supersession Notes

This document explains how Architecture Lock v2 differs from the prior seven-document package.

## 1. Supersession

The previous package remains useful historical evidence but its roadmap and status text became stale as the repository advanced. This final architecture package supersedes it as the current project plan.

The prior package should be archived in Git history or a dated archive directory rather than destroyed without a recoverable copy.

## 2. Retained architecture

The following earlier decisions remain correct:

- Linux-first research;
- Rust compute and Python orchestration;
- subprocess JSON/Parquet boundary;
- SQLite/Parquet/DuckDB roles;
- explicit broker-time and DST contract;
- typed canonical AST;
- narrow completed-bar/next-open execution;
- pessimistic ambiguity;
- small Phase-2 MT5 parity before search;
- cheap robustness before expensive robustness;
- portfolio-first risk selection;
- event-driven Nora governance;
- manual deployment boundary.

The implementation has vindicated the formerly disputed Rust/Python, process-boundary, and storage decisions.

## 3. Corrected project status

The prior roadmap described most phases as future work. The repository now proves:

- Phase-0B PASS at 168.53 candidate-backtests/sec with four workers;
- strict ingestion and time contracts;
- NY+7 DST support;
- M5/H1 aggregation;
- Layer-1 kernels and typed transforms;
- typed AST, intents, simulator, metrics, and deterministic RNG;
- MQL5 translation and accepted narrow canaries;
- corrected v2 ten-strategy compiler evidence;
- persistent Windows evidence handling.

Phase 2 remains incomplete because corrected suite execution/reconciliation, replay, placebo, and gate decisions remain open.

## 4. New facts found by independent review

1. Cross and Slope are not typed AST nodes, so the proposed grammars are not yet expressible.
2. Two signal/time exit-price conventions coexist and require explicit execution-policy identities.
3. No account-currency cost/sizing model exists; early ranking cannot claim full money metrics.
4. The Python control plane has no worker pool; bulk scheduling is new implementation.
5. A 16-registry governance model is excessive; one typed store is sufficient.
6. A high-dimensional behavioral archive would collapse into sparse one-candidate cells.
7. Lockbox and trial-count governance must remain explicit.

## 5. SQX reconciliation

Useful SQX concepts retained:

- family-constrained grammars;
- structural and parameter separation;
- selection, lineage, and diversity concepts;
- separate trade-list and re-backtest robustness;
- deterministic shardable simulation design.

Rejected or owned by Nora:

- universal unrestricted block library;
- raw XML identity;
- permissive invalid-candidate repair;
- mutable RNG cursor;
- opaque fitness and comparator behavior;
- SQX profit-factor sentinel;
- unresolved WFO/WFV/SPP mechanics;
- initial evolutionary search.

No additional SQX forensics are required for the current roadmap.

## 6. New admission rule

The old rule required Rust implementation, MQL5 translation, and a parity fixture. The final rule is stronger:

```text
Rust implementation
+ deterministic MQL5 translation
+ parity fixture
+ compiler evidence
+ accepted native evidence
+ explicit human promotion after Phase-3 authorization
= searchable
```

## 7. New Phase-2 gate

The gate is now explicit:

- corrected four-run ten-strategy campaign;
- exact reconciliation;
- bundled whole-experiment replay;
- deterministic placebo destruction;
- machine-readable matrix closure;
- signed D1–D7 decisions;
- separate D8 Phase-3 authorization.

## 8. Roadmap change

The next work is not another architecture study. It is:

1. FR-T1 native corrected suite campaign;
2. FR-T2 replay/placebo fixtures;
3. FR-T3 gate decisions;
4. FR-T4 Cross/Slope AST and registry prototype;
5. FR-T5 worker pool;
6. only then consideration of Phase 3.

## 9. Data boundary

Current UTC fixtures are frozen. Future production datasets remain a manual Gasper preparation step under the intended NY+7 broker-time convention and declared average-spread treatment. No large data acquisition is authorized by this package.

## 10. Current final statement

Architecture direction: adopted as the final current project plan.  
Phase-2 acceptance: incomplete.  
Phase-3 authorization: false.  
Searchability: false.  
Immediate next action: corrected ten-strategy native evidence and exact reconciliation.
