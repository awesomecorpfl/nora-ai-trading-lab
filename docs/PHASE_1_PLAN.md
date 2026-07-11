# Phase 1 implementation plan

## Scope

Build the Linux-side control-plane foundation only. No indicators, AST, strategy/search/robustness/portfolio logic, MQL5 generation, or MT5 parity strategy work is in scope.

## Structure

```text
lab/                 Python control-plane package
  migrations/        ordered SQLite migrations
  worker.py          deterministic subprocess dummy worker
schemas/             JSON-schema-like contract examples and documentation
protocols/           immutable dummy protocol source
services/            systemd user unit and installation notes
tests/               isolated Python acceptance tests
engine/              reserved Rust workspace with a minimal labengine task-spec validator
artifacts/ data/     ignored runtime roots
docs/                Phase 1 plan and acceptance report
```

## Foundation design

- Python package: stdlib `argparse`, `sqlite3`, `subprocess`, JSON and hashing; PyArrow only for canonical Parquet writing/reading.
- Rust: a separate `engine/` workspace reserves the locked `labengine <task.json>` file/subprocess boundary without adding research logic.
- SQLite: WAL mode and one controller process, with ordered `schema_migrations`; tables for experiments, stages, tasks, task attempts, checkpoints, artifacts, provenance, protocols, events, decisions and budgets.
- Task states: `pending → running → succeeded|failed|interrupted|cancelled`, with explicit allowed transitions. Startup reconciles stale running tasks to `interrupted`; succeeded tasks are never rerun.
- Identity: experiment IDs derive from protocol/config; task IDs derive from experiment/stage/input spec. Insertions and publication are idempotent.
- Artifacts: `artifacts/{experiment}/{stage}/{task}/`; worker writes a `.partial` directory then atomically renames it before the controller verifies/registers it.
- Protocol: source JSON is canonicalized/hashed and snapshotted into SQLite on first use. Later file edits create a distinct protocol identity.
- Provenance: content/config hashes, input-parent artifact IDs, task/experiment/protocol linkage and code revision where available.

## Data contract and time model

The contract model records provider/tool identities, symbols, timestamp/bar semantics, explicit timezone and DST regime, session/strategy clocks, optional UTC reference semantics, conversion history, hashes and endpoints. It accepts a broker-time convention such as `america_new_york_plus_7_v1`, supports future contracts, and rejects conversion histories that already contain the requested conversion or ambiguous fixed-offset-only data.

The staged CSV adapter is mapping-configured (including Phase 0C date/time OHLCV layout), validates timestamps, ordering, duplicates and OHLC, captures provenance, and writes canonical M1 Parquet with timezone-contract metadata. Future higher-timeframe aggregation is specified to anchor to the declared session/trading clock, never implicit UTC day boundaries.

## CLI and dummy workflow

`lab` exposes experiment create/show/launch/resume/status, task list, event list, artifact list, provenance show, protocol show, ingest validate/ingest, and supervisor.

The dummy workflow has three deterministic stages: shard creation, per-shard transform through a subprocess task spec, and aggregation. Checkpoints are recorded after each published task.

## Recovery tests and service

Tests use temporary roots/databases and cover migrations, transitions, idempotency, immutable protocol snapshots, provenance/artifact registration, partial rejection, timezone/double-conversion validation, Parquet contract, and clean/interrupted-resumed workflow equality. A dedicated recovery test interrupts an in-flight subprocess then confirms resume neither loses nor duplicates completed tasks.

`services/nora-lab-supervisor.service` is a non-enabled systemd user unit. It starts `lab supervisor`, restarts on failure, uses no secrets and logs to the journal. Documentation supplies manual install/test commands; it will not touch existing Hermes services.

## Acceptance

Run automated tests, a clean CLI workflow and an interrupted/resumed workflow; compare final content hashes and task attempts. Record the exact evidence and any bounded dependency/service limitation in `docs/PHASE_1_VERDICT.md` before committing.
