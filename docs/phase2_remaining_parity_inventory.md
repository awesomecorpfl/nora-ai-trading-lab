# Phase 2O: Remaining Parity Inventory

The machine-readable source of truth is `tests/fixtures/phase2_remaining_parity_inventory.json`. It records 50 Phase-2 items and deliberately separates Rust implementation, MQL5 generation, compilation evidence, native execution evidence, and semantic parity. No item is searchable and Phase 3 is not authorized.

## Evidence position

The only durable committed native parity evidence is the fixed 12-row slope canary: semantic identity `221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f`. Its scope is slope lookback 1 over the frozen SMA3 vector, not general indicator, transform, strategy, or execution parity.

Condition and SMA/cross canaries have generated sources and documentation reporting native runs, but their raw compile logs, run manifests, journals, and CSVs are not committed. They are therefore `partially_proven`, not accepted native parity evidence.

## Binding acceptance audit

| Requirement | State | Blocking evidence gap | Smallest advance |
|---|---|---|---|
| Synthetic execution fixtures | partial | No native reconciliation of next-open/bracket/time behavior | Freeze one local execution-parity contract |
| Layer-1 indicator parity | partial | Only slope has durable native evidence; all other primitives lack complete MQL5/native proof | Phase 2P ATR + Distance/ATR local generator contract |
| Strategy/session/time/DST parity | blocked | No paired native session, Friday-close, ORB, rollover, daily-reset, Monday-open, or DST canary | Freeze time/session fixture inventory |
| Ten hand-designed strategies | blocked | No durable trade-by-trade strategy reconciliations | Add one execution-model case after generator support |
| Repeated Linux semantic determinism | partial | Components replay deterministically, but no whole-experiment replay bundle | Add one complete replay fixture |
| Placebo/scrambled edge destruction | blocked | No known-edge scramble fixture | Specify deterministic scramble and required edge-destruction measure |

## Historical label discrepancies

- Phase 2J and 2L documentation calls their narrow native canaries passed, but durable raw native outputs are absent from Git. Their claims are retained as historical documentation, not promoted to accepted evidence.
- Commit `29be0d00608cf2c390c85639c26a021e5ec676b6` documented ignored Phase 2N artifacts. Commit `f2010773ec3cd47e8d1f5c74512e45b12b970786` is the durable evidence repair.
- The Phase 2A–2C labels contain broad local implementation and local tests, not the roadmap's complete Rust↔MT5 parity admission gate.

## Dependency order

1. Phase 2P: local ATR + Distance/ATR MQL5 source/fixture contract.
2. Phase 2Q: native ATR/Distance-ATR canary with durable evidence.
3. Phase 2R: durable repair or clean reruns for the existing condition and SMA/cross canaries.
4. Phase 2S: local execution-strategy generator and next-open/one-exit reconciliation contract.
5. Phase 2T: native hand-designed strategies, time/session/DST, replay, and placebo fixtures.
6. Phase 2U: complete Phase-2 gate audit; only then consider Phase-3 authorization.

## Selected next task: Phase 2P

Phase 2P is local-only: generate a deterministic MQL5 ATR plus Distance/ATR runtime and fixed-data tester from real Rust task output. Its frozen prerequisites are the Rust ATR and Distance/ATR implementations in `engine/labengine/src/indicators.rs` and nullable runtime identity `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d`.

Required outputs are frozen Rust vectors, generated MQL5 runtime/tester sources, source hashes and identities, manifests, repeatability and mutation tests, and a Phase-2Q native-run plan. It must not claim native parity or make any grammar item searchable. Recommended model: GPT-5 Codex.
