# Nora AI Trading Lab — Current Project Status

**Snapshot UTC:** 2026-07-18T02:15:00Z  
**Repository:** `/home/gasper/nora-ai-trading-lab`  
**Branch:** `main`  
**Snapshot HEAD:** `ae415c2`

This is the concise operational “you are here” view. It supplements but never overrides tracked code, schemas, tests, sealed evidence, machine-readable gates, or the final architecture lock.

## Authority

- Final backup: `/home/gasper/Documents/Nora's Lab Docs/NORA_ARCHITECTURE_LOCK_FINAL.zip`
- Backup SHA-256: `7e053baf2eac358cd9cbc6bf704c237d16eea0f8c31eefd57ef4ef59741a2e31`
- All ten archive entries were byte-for-byte identical to repository `architecture-lock/` at this snapshot.
- Historical Original/New Plan, Fable, SQX, and additional documents preserve rationale; they do not override the final lock.

## Git and validation baseline

After a fresh direct fetch:

- `origin/main`: `5ec53a70690c081f8e1539d1d9f3a6d4c48c062e`
- Local relationship: **25 ahead / 0 behind**
- Commit topology: linear; zero merges and zero replacement refs
- Outgoing net range: 34 paths, 1,416 insertions, 11 deletions
- Tracked outgoing changes under protected directories: none
- Four protected directories remain untracked and intentionally uninspected
- Architecture-lock changes: none
- Authorization flips: none
- `git diff --check`: PASS

Validated after the third fail-closed repair round and evidence commit:

- Python compile: PASS
- Complete pytest: `544 passed, 4 skipped`
- Rust engine: `49 passed, 0 failed`
- Rust Phase-0B: `5 passed, 0 failed`
- Windows PowerShell 5.1 fail-closed repair harness: PASS (full JSON verdict captured at `20260718T020500Z`)
  - burned identity rejected; competing and legacy prepared jobs rejected
  - 11 unrelated semantic mutations detected; 6 target semantic rejections
  - restoration self-hash mismatch caught; zero firewall mutation; zero MT5 invocation
- Firewall mutation during repair validation: false
- MT5 invocation during repair validation: false

Of the four skipped tests, three require PowerShell 5.1 unavailable on Fedora and one requires unavailable Phase-2I compile evidence. Their relevant fail-closed PowerShell boundaries were executed separately on `nora-win10`; skipped tests are not counted as passes.

## Independent outgoing review

The first independent fail-closed review returned `DO_NOT_PUSH` with seven blocking findings:

1. qualification identity reuse was not mechanically impossible;
2. partial/orphan reconciliation entries were invisible;
3. another prepared job could evade the runtime conflict guard;
4. the prepared operator packet was stale against implementation bytes;
5. the restoration script did not authenticate its own deployed bytes;
6. restoration/postflight did not bind complete firewall semantics;
7. a helper inventory was unsealed and overclaimed as evidence.

The first repair/evidence pair (`f2531030b6e2c64ddca8b8d2f5a6d2e6a90df997`, `5ea5c88e9fd63f068857c25a5bd80740f0a84d5b`) closed B1, B2, B4, and B7, but independent re-review correctly kept `DO_NOT_PUSH` for three remaining defects:

- B3 still missed prepared jobs represented only through legacy `Keys`/`Values`;
- B5 left the old restoration packet actionable despite stale commands and hashes;
- B6 omitted owner, interface-alias, and local/remote-user semantics.

Follow-up implementation commit `a64bc607cc97d1178e5e479bfbfa4d2b8af38dd2` normalizes legacy jobs at the production launch guard and completes target/unrelated firewall semantics. Follow-up evidence commit `92b2dde13950a05cef9a276d3fe770e21c6b8502` seals exact non-credit boundaries, the PowerShell 5.1 result, and restoration-packet supersession at:

- `docs/evidence/phase2/pi0-outgoing-review-repair/20260718T004745Z/`
- `docs/evidence/phase2/pi0-outgoing-review-repair/20260718T011100Z/`

Third repair commit `ae415c2` adds the explicit supersession record for the stale `20260717T185409Z` operator packet (`may_execute=false`, `NON_CREDIT_SUPERSEDED`) and fixes the Windows harness mock `Profile` field to match the PowerShell adapter representation (`'Domain, Private'` string, not CIM integer). The harness ran on Windows PS 5.1 with a full clean JSON verdict.

Important classifications:

- the old `20260717T185409Z` FR-T1R2 packet is `NON_CREDIT_SUPERSEDED_PREPARATION` and must not be executed;
- the old `20260717T192223Z` FR-T1R2 packet is `NON_CREDIT_SUPERSEDED_PREPARATION` and must not be executed;
- the old `20260717T204540Z` restoration packet is now also `NON_CREDIT_SUPERSEDED_PREPARATION`, has `may_execute=false`, and has no replacement executable packet;
- the old helper inventory is `NON_CREDIT_UNSEALED_DIAGNOSTIC` and grants no acceptance;
- all repair evidence packages are `REPAIR_VALIDATED_NON_ACCEPTANCE`;
- independent re-review of the 25-commit outgoing range at `ae415c2` returned **PASSED** with zero blockers.

## Program position

- Phase 0A: conditional pass under the final lock
- Phase 0B: pass
- Phase 0C: conditional pass
- Phase 1: conditional pass
- Phase 2: **incomplete**
- Phase 3: **unauthorized**
- Search authorization: **not authorized**; machine governance does not permit search
- Searchable components: **zero**

The architecture-era `tests/fixtures/phase2_gate_reconciliation.json` remains the adopted Phase-2 gate baseline. Its prose next-critical-path text predates later transactional-containment and FR-T1 work, so live code, evidence, and current machine-readable records govern the operational position.

## Verified or narrowly accepted foundations

- Deterministic M1 ingestion and typed time contracts
- M5/H1 aggregation
- Rust indicator and transform kernels accepted under narrow component-specific gate records; grammar admission remains false
- Typed AST foundation and canonical identities
- Named deterministic RNG streams
- Frozen market simulator semantics and closed-trade metrics
- SQLite/Parquet/JSON control-plane foundations
- Narrow frozen-contract native canary, time-rule, MACD, and percentile parity
- Narrow historical firewall launcher/campaign evidence chain; it does not accept current FR-T1 repair bytes or grant FR-T1 readiness
- Read-only firewall qualification and terminal-state matrix evidence
- Transactional containment:
  - status: `TRANSACTIONAL_CONTAINMENT_ACCEPTED`
  - acceptance ID: `tca1-20260717T160046Z`
  - candidate SHA-256: `d4aa8d482658e3ce4b85e738d2e5072b74cd35b5282bee6e8ac147463b2dd4c1`
  - acceptance artifact SHA-256: `32c9635239c31bc686db4d5566065e45d783af4883e0ce7ea86fdbaa95e01c72`

These foundations do not imply Phase-2 completion, grammar admission, searchability, or Phase-3 authorization.

## Current coherent objective — FR-T1 readiness

The ten-strategy v2 local contract remains fail closed:

- genuine v2 recompilation required
- compile evidence pending
- final packet not ready
- native execution not attempted
- native parity not accepted
- Phase-2 gate incomplete
- production data not required
- searchable false

The repaired operator controls now:

- reject every reused/burned qualification identity before creating evidence;
- reject every partial or orphan reconciliation entry;
- treat every non-current prepared job as a conflict;
- authenticate restoration-script bytes;
- bind exact tester-rule policy source/source type;
- hash comprehensive unrelated-firewall semantics;
- reopen and bind before/after receipts during postflight.

## Latest unsealed live observation

A read-only operator query at `2026-07-18T00:51Z` observed:

- no `terminal64` or `metatester64` process;
- one exact `MetaTrader 5 Strategy Tester Agent` rule in PersistentStore and one in ActiveStore;
- the rule enabled in both views.

This observation was not published as a tracked, manifest-bound live-state artifact and therefore must not be treated as continuously current or sufficient mutation authorization. Before selecting any PI-1 mutation path, repeat the read-only query and preserve an exact timestamped observation packet.

The branch is fail closed:

- present-enabled exact rule → prepare an exact disable transaction;
- absent exact rule → prepare a fresh restoration packet;
- any other cardinality or semantics → stop and investigate.

No firewall state was changed during PI-0 reconciliation or repair validation.

## Next dependency-ordered actions

1. Commit this status snapshot and present the normal-push decision to Gasper; do not push without authorization.
2. At PI-1 entry, publish a fresh read-only, timestamped, manifest-bound tester-rule observation and select the fail-closed present/absent/other branch.
3. Prepare the applicable exact transaction with before/after identity, comprehensive unrelated-firewall preservation, and rollback.
4. Obtain Gasper's explicit authorization before any firewall mutation or project-progressing Windows deployment.
5. Execute and independently verify the exact disabled-rule prerequisite.
6. Issue a fresh operator packet bound to the deployed implementation; never reuse the superseded packet or qualification ID.
7. Re-run FR-T1 containment-only qualification.
8. Complete genuine v2 recompilation and packet materialization before presenting a separate authorization boundary for the corrected four-run native FR-T1 campaign.

## Frozen boundaries

- Never inspect or modify the four protected untracked directories.
- `/home/gasper/trading-lab` is retired; its useful historical assets are isolated under `research/` and are not part of the active build.
- No search before Phase-2 completion and signed D8.
- No hidden tolerance widening or post-result threshold changes.
- No production-data acquisition without Gasper.
- No MT5 bulk research.
- No automated live deployment in v1.
- Preserve failed, burned, diagnostic, and superseded evidence.
- No amend, reset, rebase, squash, force-push, history rewriting, or replacement refs.

## Continuity

Live reset-safe progress:

`/home/gasper/.hermes/project-state/nora-ai-trading-lab/PROGRESS.md`

Complete acceptance-bounded program:

`/home/gasper/.hermes/project-state/nora-ai-trading-lab/PROGRAM.md`
