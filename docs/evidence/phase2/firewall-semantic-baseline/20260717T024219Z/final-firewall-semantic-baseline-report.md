# Final Phase-2 Firewall Semantic Baseline

Verdict: PASS

## Campaign

- Run ID: `semantic20-20260717T024219Z`
- Launch ID: `synlc-20260717T024219Z`
- Campaign ID: `sync-20260717T024219Z`
- Repository qualification HEAD: `336ec9ba99d1f7fe53cf4bf7f8f84db88010e02a`
- Owner PID: `3744`
- Wrapper PID: `5608`
- Owner acknowledgment: `BOOTSTRAP_ACQUIRED`
- Completion: `complete`

## Twenty-capture result

All 20 ordered slots were independently verified on Fedora. Every claim, receipt, and inventory is bound to the same campaign owner, repository HEAD, capture-tool identity, and ordered slot. All 20 semantic invariant verdicts are `PASS`. There are no duplicates, missing slots, foreign campaign artifacts, or partials.

### Stable semantic digests

- Canonical digest: `179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8`
- Unrelated/canonical digest: `179c09c2fa2db2bf303f60b0c2f45dd8f85bc81f6f36cf63700bec23d60553d8`
- Firewall-profile digest: `209cb421ee9b3ab58588443ab1e25157d95b219d2d09d0c071a27b82f0e8bd72`
- Nora-rule digest: `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`

Each digest occurred exactly once as a distinct value across the 20 captures, meaning each was stable across all 20.

## Frozen implementation identities

- Launcher: `3e3bdb46c5fcf555fc3493e8cada718b7b03b2d64dbf8f17f5249ccbc4f11371`
- Wrapper: `48aa6336bade5ff29a801c222218969453e0108da8f18007be0ebbc79be85e9e`
- Campaign: `4ff07f32c89b4150bd35eb5f96389f3107eb13c1942deeed22666fc01271c9ee`
- Capture tool: `a7d525cb75f1a61188c06b744aee72eb9b4b418b7fc9a7d6a62168d708b0f3d7`
- Evidence runner: `0cda81f5bbf4b1051f06276101975c2b44c02d9e6b14a9892c83865f4c56b5b2`
- Fedora campaign verifier: `53d1bef6cb13e77feb98dbdc7cd6ed2dbab6244055d4159049e5485b5520864c`
- Fedora semantic verifier: `2afa1d9d38212fdb30b06f60ccdf50f5176bca1179ed178278bd7109362266c7`

All deployed PowerShell components parsed under PowerShell 5.1 with zero parser errors.

## Validation

- Focused campaign/capture/verifier tests after repair: `43 passed`
- Full Python suite: `486 passed, 1 skipped`
- Rust engine suite: `49 passed`
- Phase-0b Rust suite: `5 passed`
- Windows-to-Fedora retrieval: `69/69` files byte-identical by size and SHA-256
- Fedora independent semantic verification: `20/20 PASS`

The complete slot table, with every inventory path, size, SHA-256, receipt, claim, and verdict, is in `semantic-firewall-baseline.json` and `evidence-manifest.json`.

## Cleanup and frozen boundaries

- Exact launch directory remaining: `0`
- Exact campaign directory remaining: `0`
- Related processes remaining: `0`
- Pending owner/slot/partial/temporary artifacts: `0`
- Nora firewall rules: `0`
- Domain, Private, Public firewall profiles: enabled
- MetaTrader 5 Strategy Tester Agent rule: present and disabled
- Phase 2: incomplete
- Phase 3: unauthorized
- `search_authorized`: false
- Transactional containment acceptance: not published
- Push: not performed

## Prior accepted evidence bindings

- Prior synthetic lifecycle evidence: `docs/evidence/phase2/synthetic-launcher/20260717T043548Z/`
- Prior explicit Case-C evidence: `docs/evidence/phase2/synthetic-launcher/20260717T051316Z-casec/`
- Neither prior evidence directory was modified.
