# Phase 2R: Remaining Parity Inventory and Acceptance

The broad Phase-2 gate inventory remains `tests/fixtures/phase2_remaining_parity_inventory.json`. The reconciled Layer-1 authority is now `tests/fixtures/phase2_layer1_first_batch/authoritative_matrix.json`; it deliberately separates Rust implementation, typed AST, outputs, null/warmup semantics, MQL5 generation, compilation evidence, native execution, reconciliation, grammar admission, and searchability for all 22 locked families. No Layer-1 item is searchable and Phase 3 is not authorized.

## Executable-source correction

The historical Phase-2U MACD and Phase-2W percentile artifacts are preserved as deterministic scaffolds, not executable MQL5 translations. Their runtime, tester, and package identities remain recorded as historical scaffold identities. They establish neither executable translation nor native handoff/parity, grammar admission, or searchability.

## Evidence position

Five native canaries are accepted project evidence. The time-rule canary adds exact, host-neutral native reconciliation of the fixed 18-scenario dataset/strategy/session-clock contract, New York-plus-seven DST projection, Friday 16:25 cutoff, parameterized rollover/Monday/ORB boundaries, conversion rejection, and M5/H1 anchors. Its raw-native evidence is under `tests/fixtures/phase2_time_rule_native_accepted/`; holiday calendars and universal production defaults remain unsupported. Phase 2Q adds the self-contained ATR/Distance-ATR package with native semantic identity `8a912bd9152d16c8e94b1a96210d2cc6917c5b2639f615b0ecd4931dac2669f2`, ATR runtime identity `80445d259d9ac9bcf3a15bf6ec12a160594237ee469b2ee53c46d22f99370194`, Distance/ATR runtime identity `008c2f3a1824a8a22b03c6b447e3ae1a06cdd6c852381d96c8ca7eefba730c12`, tester identity `38c4e578079fd42ec31c390c84e78162d120b67a7bad48fb7859eb350dbad51e`, and CSV SHA-256 `3fd319613374e0b22ac80cf1fea1cb34c2a37069ee3778cf9f154ac86a1eaccf`. Its raw-native evidence is under `tests/fixtures/phase2q_mql5_atr_distance_native/`.

Phase 2N accepts the fixed 12-row slope canary with semantic identity `221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f`. It alone has the current self-contained raw-native package: committed compile log, EX5, manifests, CSVs, bounded journals, configurations, and contemporaneous freshness metadata. Phase 2J and 2L remain accepted legacy native canaries with committed fixture/manifests/tests and committed native-result summaries, but without that later package-completeness standard. No defect invalidating either legacy canary was found.

## Binding acceptance audit

| Requirement | State | Blocking evidence gap | Smallest advance |
|---|---|---|---|
| Synthetic execution fixtures | partial | No native reconciliation of next-open/bracket/time behavior | Freeze one local execution-parity contract |
| Layer-1 indicator parity | partial | J/L/N accept the frozen condition, SMA3/cross, and slope canaries; all other primitives lack complete MQL5/native proof | Phase 2P ATR + Distance/ATR local generator contract |
| Strategy/session/time/DST parity | accepted (narrow) | Fixed 18-scenario native clock/DST/session/anchoring canary; holiday calendars and universal production defaults remain unsupported | Preserve the accepted contract while advancing remaining Layer-1 and strategy gates |
| Ten hand-designed strategies: embedded smoke | pending | Fresh native confirmation of compile/load/tester/EA lifecycle and embedded fixture execution | Run one bounded smoke package |
| Ten hand-designed strategies: broker-native edge survival | blocked | No frozen broker-native data/timezone/cost/budget decision or similarity report | Freeze D1–D7 assumptions and run one native symbol tranche |
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
5. Phase 2T: native hand-designed strategies, replay, and placebo fixtures.
6. Phase 2U: complete Phase-2 gate audit; only then consider Phase-3 authorization.

## Phase-2Q indicator admission

ATR and Distance/ATR each have accepted native parity, but neither is grammar-admitted or searchable. Native parity does not imply AST admission. The inventory requires typed AST schema/node registration, Rust evaluation, canonicalization, hashing, MQL5 translation, and a native parity fixture; the missing integration paths are `engine/labengine/src/ast.rs` for typed registration/evaluation and canonicalization/hashing, and `lab/mql5gen/__init__.py` for translation coverage. Grammar-admitted node count remains zero; search and Phase 3 remain unauthorized.

Accepted Phase-2Q commits are `a73ed6912c8dc354c36a7475dfe595d622e66d01` (Phase 2P generation), `021ac6d45e0624dd379be79a099022d22c12abd9` (native evidence), and `fc363988af9ee7b80f9ad4f071868a922628ccd6` (evidence repair).

## Remaining critical gates

Time-rule parity is accepted narrowly. Phase 2 remains incomplete: remaining Layer-1 native parity, the embedded ten-strategy smoke, broker-native edge-survival validation, a complete deterministic Linux experiment replay, placebo/scrambled-data edge-destruction evidence, and D1–D7 similarity-budget decisions are still binding gaps. Search and Phase 3 remain explicitly closed.
