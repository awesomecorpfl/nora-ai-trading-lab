# PHASE2-CROQ-1 — Credited read-only firewall qualification case

Verdict: PASS

Credit: **GRANTED**. Exactly one read-only qualification operation was executed and independently verified on Windows and Fedora.

## Scope

- Case: `phase2-croq-1-case-20260717T044631Z`
- Operation: `phase2-croq-1-op-20260717T044631Z`
- Qualification launch identity: `phase2-croq-1-case-20260717T044631Z` (direct repository-owned `phase2-evidence-runner.ps1` operation invocation)
- Accepted campaign reference: `sync-20260717T034100Z`
- Repository commit used by the operation: `8e2dac34acc4682c3de1b063ecc82fb17aa93e44`
- Mutation requested: **false**
- Mutation invoked: **false**
- Operation count: **1**

## Baseline binding

Accepted baseline: `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/`, commit `9ae03da91b5d8875e8a0766b580d382628b57beb`, manifest SHA-256 `7b9d79e4ec2dfea01b1c32921847cdc44b579c7837999783ca2bcebe920c80e7`. It remains unchanged.

Pre and post inventories both passed and matched the accepted baseline:

- Canonical: `179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8`
- Unrelated: `179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8`
- Profile: `209cb421ee9b3ab58588443ab1e25157d95b219d2d09d0c071a27b82f0e8bd72`
- Nora: `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`
- Invariants: **PASS**
- Pre/post equality: **PASS**
- Accepted-baseline equality: **PASS**

## Operation package

- Windows package: `C:\NoraEvidence\Phase2\croq-1\operation\phase2-croq-1-op-20260717T044631Z.zip`
- Fedora package: `docs/evidence/phase2/firewall-qualification/phase2-croq-1-case-20260717T044631Z/operation-package/phase2-croq-1-op-20260717T044631Z.zip`
- Size: `1756460` bytes
- SHA-256: `8fd04aa858e2e8c3c4b7f37e09be155a383cc39bb4f9cb0b39f0794b888b981e`
- ZIP members: **11**, all manifest-bound and independently recomputed
- Windows package recomputation: **PASS**
- Windows recomputation envelope: `baaf2fad58107270488162255f4a56453c769fc80e307f4959b00f2c4ae1ebfb`
- Fedora package verification: **PASS**

## Read-only proof

- Runner-owned firewall operation mode: `firewall-readonly`
- Child mutation flag: `False`
- Static mutation-cmdlet check: **PASS**
- Operation exit: `0`
- stderr empty: **PASS**
- Terminal/tester processes in child operation: `0`
- No MT5, tester, history, cache, probe, FR-T1, or market-data action occurred.

## Retrieval

- First package retrieval: `published`, reader/SSH/wrapper exit `0`
- Repeat retrieval: `identical_existing`, reader/SSH/wrapper exit `0`
- First package bytes: `1756460` bytes / `8fd04aa858e2e8c3c4b7f37e09be155a383cc39bb4f9cb0b39f0794b888b981e`
- Repeat package bytes: `1756460` bytes / `8fd04aa858e2e8c3c4b7f37e09be155a383cc39bb4f9cb0b39f0794b888b981e`
- Final envelope retrieval: `published`, Windows/Fedora byte equality verified
- Retrieval receipts and binary-safe stderr artifacts are preserved under `retrieval/`.

## Case envelope

- Fedora envelope: `docs/evidence/phase2/firewall-qualification/phase2-croq-1-case-20260717T044631Z/case-envelope.json`
- Size: `7207` bytes
- SHA-256: `b649cddd46335e7e148d7debdddee39e5e2cafb6f42a9152af4bd4a26e4ff6a3`
- Ordered operation count: **1**
- Operation role: `verification`
- Fedora envelope verification: **PASS**
- Windows envelope schema verification: **PASS**
- No missing, duplicate, reordered, foreign, substituted, or conflicting operation.

## Components and tests

Exact repository/deployed hashes and parser results are in `component-identities.json`; all eight deployed PowerShell components matched exactly and had zero parser errors.

- Focused qualification tests: **99 passed**
- Full Python: **495 passed, 1 skipped**
- Rust engine: **49 passed**
- Phase-0b Rust: **5 passed**

## Accepted synthetic lifecycle evidence

Tracked manifests and preservation records were read and hash-checked only. Cases A–D were **not rerun**. Their recorded outcomes remain A PASS, B PASS, C retained OWNER_BINDING_MISMATCH evidence in the Case-C manifest, and D PASS.

## Cleanup

The final cleanup report is preserved at `cleanup-report.json`: related processes `0`, launch/campaign directories `0`, partial artifacts `0`, pending artifacts `0`, Nora rules `0`, terminal/tester processes `0`; all three firewall profiles enabled; exact tester rule present and disabled; immutable operation package and case envelope retained.

## Boundaries

This grants credit only to PHASE2-CROQ-1. Phase 2 remains incomplete. Phase 3 remains unauthorized. `search_authorized=false`. No terminal-state matrix, FR-T1, MT5/tester execution, broker-profile work, component search, market-data/history activity, or `TRANSACTIONAL_CONTAINMENT_ACCEPTED` publication occurred. No push was performed.
