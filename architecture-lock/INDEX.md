# Nora AI Trading Lab — Final Architecture and Project Plan

**Status:** Adopted replacement architecture package; Phase 2 incomplete; Phase 3 unauthorized  
**Evidence snapshot:** repository `main` at `ab989628390f027ebc32ef749b8ffb8b6bfcb319`  
**Prepared:** 2026-07-14

This package replaces the earlier seven-document architecture-lock package as Nora's current full project plan. It incorporates:

- the original Linux-first architecture lock;
- the actual implemented repository state;
- the completed SQX forensic findings;
- the corrected New Plan synthesis and architecture proposals;
- the independent Fable implementation audit and recommended corrections.

Adopting this package does **not** resolve the remaining Phase-2 and Phase-3 gate decisions. Those decisions are intentionally preserved in `PHASE2_COMPLETION_GATE.md`, `ARCHITECTURE_DECISIONS.md`, and `OPEN_QUESTIONS.md` so the architecture can be final while operational gates remain evidence-dependent.

This package is the authoritative prose plan. Current code, tests, sealed evidence, and machine-readable gate matrices remain authoritative for implementation and acceptance status.

## Current binding state

- `phase2_complete: false`
- `search_authorized: false`
- `searchable: false` for every component
- Phase 3 is not authorized.
- No production market-data acquisition is authorized.
- The immediate blocker is the corrected ten-strategy native evidence campaign and exact reconciliation.
- The whole-experiment replay, placebo fixture, machine-readable gate closure, and D1–D8 decisions remain required as specified by the gate document.

## Core architecture

- Fedora/Linux owns research compute.
- Rust owns deterministic compute-heavy kernels and simulation.
- Python owns orchestration, state, evidence handling, MQL5 generation, and reporting.
- The process boundary is subprocess JSON input with Parquet/JSON output.
- SQLite stores mutable operational state.
- Parquet stores immutable artifacts and canonical market data.
- DuckDB is optional stateless analytics, not an authoritative database.
- MT5 is a narrow execution-fidelity authority, not a bulk research platform.
- Production data is manually prepared by Gasper under an explicit broker-time contract.
- The first search release, once separately authorized, is family-constrained stratified sampling plus deterministic local refinement; no evolutionary search.

## Package contents

1. `FINAL_ARCHITECTURE.md` — complete target architecture and subsystem contracts.
2. `ARCHITECTURE_DECISIONS.md` — retained locks, approved revisions, prototypes, deferrals, rejections, and pending gate decisions.
3. `IMPLEMENTATION_STATUS.md` — evidence-backed state of what is actually built.
4. `PHASE2_COMPLETION_GATE.md` — exact evidence and human decisions required before Phase 3 can be considered.
5. `BUILD_ROADMAP.md` — completed work, immediate tranches, later phases, and sequencing rules.
6. `RISKS_AND_FAILURE_MODES.md` — current technical, scientific, evidence, and governance risks.
7. `OPEN_QUESTIONS.md` — unresolved decisions grouped by deadline.
8. `RECONCILIATION_NOTES.md` — how this package reconciles and supersedes the previous architecture lock.
9. `MANIFEST.json` — package file hashes and evidence snapshot.

## Authority order

When documents or evidence conflict, use this order:

1. Current repository code and schemas.
2. Current tests and fixtures.
3. Sealed manifests and machine-readable gate matrices.
4. Git history and commit-linked evidence.
5. This architecture package.
6. SQX forensic reports.
7. Historical architecture documents and planning notes.

No prose document may override a false machine-readable gate.

## Reading order

1. `IMPLEMENTATION_STATUS.md`
2. `PHASE2_COMPLETION_GATE.md`
3. `FINAL_ARCHITECTURE.md`
4. `ARCHITECTURE_DECISIONS.md`
5. `BUILD_ROADMAP.md`
6. `RISKS_AND_FAILURE_MODES.md`
7. `OPEN_QUESTIONS.md`
8. `RECONCILIATION_NOTES.md`

## Adoption and maintenance

- The old seven documents may be removed from the working directory after this package is staged; Git history preserves them.
- Do not delete the separate SQX findings, New Plan, or Fable Review evidence folders.
- Update status facts only from committed repository evidence.
- Preserve historical failures; do not rewrite them as success.
- Record new architecture decisions before implementation depends on them.
- Update the Phase-2 gate only when evidence identities or signed human decisions change.
- Do not mark a component searchable because it compiles or passes a local test.
- Large, multi-symbol, multi-year, or tick-data acquisition requires advance notice to Gasper.
- Current UTC fixtures remain unchanged; future production datasets are validated in their declared broker-time contract.
