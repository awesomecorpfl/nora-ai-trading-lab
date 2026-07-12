# Phase 2O: Remaining Parity Inventory

The machine-readable source of truth is `tests/fixtures/phase2_remaining_parity_inventory.json`. It records 50 Phase-2 items and deliberately separates Rust implementation, MQL5 generation, compilation evidence, native execution evidence, and semantic parity. No item is searchable and Phase 3 is not authorized.

## Evidence position

Three narrow native canaries are accepted project evidence. Phase 2J accepts only the nullable-condition tester fixture (tester identity `583fe60539d2da2cb46f054d9800d7702efd577b6984d23757794ca91ab259e6`, semantic identity `b66f60ad5ae4cc036d29197063e2dbe355cafac96085c359e92783ac74da74e4`). Phase 2L accepts only SMA period 3, cross-above, cross-below, and that accepted nullable-condition fixture (series runtime `4102f23095201f5c37e8a6737d32f22eb31713f4f0ec9cae68803e6d3efbce8e`, series tester `78a52f288df45a93e3b026846c7283ddb6d93bcc8192874198827ec93d5041e4`, CSV SHA-256 `2f7ffa9a8e32b5b3bcadf1fa00013de3969cc3ea34cf52ed754c3979d3843756`, semantic identity `ff48ba25e9bcf6bd82d1f30977c5196f18f8f66c9a68c0b1b23b37787a8bf687`).

Phase 2N accepts the fixed 12-row slope canary with semantic identity `221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f`. It alone has the current self-contained raw-native package: committed compile log, EX5, manifests, CSVs, bounded journals, configurations, and contemporaneous freshness metadata. Phase 2J and 2L remain accepted legacy native canaries with committed fixture/manifests/tests and committed native-result summaries, but without that later package-completeness standard. No defect invalidating either legacy canary was found.

## Binding acceptance audit

| Requirement | State | Blocking evidence gap | Smallest advance |
|---|---|---|---|
| Synthetic execution fixtures | partial | No native reconciliation of next-open/bracket/time behavior | Freeze one local execution-parity contract |
| Layer-1 indicator parity | partial | J/L/N accept the frozen condition, SMA3/cross, and slope canaries; all other primitives lack complete MQL5/native proof | Phase 2P ATR + Distance/ATR local generator contract |
| Strategy/session/time/DST parity | blocked | No paired native session, Friday-close, ORB, rollover, daily-reset, Monday-open, or DST canary | Freeze time/session fixture inventory |
| Ten hand-designed strategies | blocked | No durable trade-by-trade strategy reconciliations | Add one execution-model case after generator support |
| Repeated Linux semantic determinism | partial | Components replay deterministically, but no whole-experiment replay bundle | Add one complete replay fixture |
| Placebo/scrambled edge destruction | blocked | No known-edge scramble fixture | Specify deterministic scramble and required edge-destruction measure |

## Historical label discrepancies

- Phase 2J and 2L are accepted legacy native canaries. Their committed evidence summaries are less self-contained than Phase 2N's later raw-native package; this is a completeness distinction, not a validity downgrade.
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

Phase 2P remains local-only: generate deterministic MQL5 ATR plus Distance/ATR runtime and fixed-data tester from `engine/labengine/tests/fixtures/phase2_distance_atr_task.json`. That real Rust fixture has semantic identity `c1acf9dac99daf0006e138426f51b77721fbf4512fba07d10a6c019a0fafd5ad`; it exercises ATR3 and Distance/ATR before a slope consumer. Prerequisites are the Rust ATR and Distance/ATR implementations in `engine/labengine/src/indicators.rs`, their focused Rust tests, `tests/test_phase1.py::test_committed_distance_atr_fixture`, and nullable runtime identity `1155c0caa95789bb452bb7ec322021cad91dbd4b0e9b5a64c80117e337449d4d`. Neither ATR nor Distance/ATR has accepted MQL5/native parity evidence. They remain separate generated identities and failure cases despite sharing one bounded prerequisite fixture.

Required outputs are frozen Rust vectors, generated MQL5 runtime/tester sources, source hashes and identities, manifests, repeatability and mutation tests, and a Phase-2Q native-run plan. It must not claim native parity or make any grammar item searchable. Recommended model: GPT-5 Codex.
