# Corrected Phase-2 Firewall Semantic Baseline

Verdict: PASS

New final run: `semantic20-20260717T034100Z`

Prior diagnostic run `20260717T024219Z` is superseded as the final baseline, preserved unchanged. Reasons: mixed process identity in the earlier launch receipt, unavailable submitted-command binding, and incorrect completion receipt paths pointing to captures.

## Binding and validation
- Repository commit: `8e2dac34acc4682c3de1b063ecc82fb17aa93e44`
- Launch/campaign: `synlc-20260717T034100Z` / `sync-20260717T034100Z`
- Separate wrapper and campaign process records: PIDs `1984` and `1964`, both complete and distinct.
- Submitted-command SHA-256: `66f8f7e74f632e04413e1532869bf1c14a422dfda692e2fd6901fd684d00422d`; non-circular basis and actual final command are recorded in intent.
- Completion binds `receipts/01.json` … `receipts/20.json` under `receipt_paths`; captures are separate under `capture_paths`.

## Tests
- Focused: **52 passed**
- Python: **495 passed, 1 skipped**
- Rust engine: **49 passed**
- Phase-0b Rust: **5 passed**
- PowerShell 5.1 parser errors: **0** for all changed deployed components.

## Focused synthetic checks
- Positive: `bindlaunch-20260717T033200Z` / `bindcampaign-20260717T033200Z`, `BOOTSTRAP_ACQUIRED`, process binding PASS.
- Negative: wrong hash rejected with `submitted command hash mismatch`, PASS.

## Twenty ordered slots
| Slot | Inventory path | Size | SHA-256 | Verdict |
|---:|---|---:|---|---|
| 1 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\01.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/01.json` | 870649 | `3d9a993dbb3a92f93961fdcd0c0672a282bb66d590aba3b7bd5579dd4afa91bf` | **PASS** |
| 2 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\02.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/02.json` | 870649 | `a1e71c644b3bbc6ac54360d5fa53b52e48fd2b6232b0030770c74b857a60e6fb` | **PASS** |
| 3 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\03.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/03.json` | 870649 | `3d143f2081ab482c28f76821d74b4467d2f74d97dd30c4570b1e8df70902244e` | **PASS** |
| 4 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\04.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/04.json` | 870649 | `72d2ce4c227c52e2ba541a11e728960e10f3275d9305173a8188e92fffcd66e3` | **PASS** |
| 5 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\05.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/05.json` | 870649 | `4928a88f94655ba13ab9d4b1ff06c29ad9cb19a0a9f566b85896b4ef287a42cd` | **PASS** |
| 6 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\06.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/06.json` | 870649 | `cca34d29899244ece7cc3a5711f20c6171b194e9370fd0694507c1240c7d1565` | **PASS** |
| 7 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\07.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/07.json` | 870649 | `d0be37ba3c71e7a29cf7b23ddbd787bc9207b6dba87afb93bb7357f33c48c87a` | **PASS** |
| 8 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\08.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/08.json` | 870649 | `771f139f65a020cfb140f28e0c4588c821f8998555d1b254b288e08f6f394287` | **PASS** |
| 9 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\09.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/09.json` | 870649 | `abce2736cdd16f574543e4cca64b21adff846efbe2143645bfa126359c758199` | **PASS** |
| 10 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\10.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/10.json` | 870649 | `66d7d946e762fad2966cacee837f53dece4b2017ad70f630c9e1b96f17dfb5b8` | **PASS** |
| 11 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\11.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/11.json` | 870649 | `63660f8d00aa8da00b0b22f33d8491070a2e7028d7e1243fb20bb9a481640fb0` | **PASS** |
| 12 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\12.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/12.json` | 870649 | `1e8181715b31ed75b2cd0df07eb60e4b6fe8abcf65be4892ad2cc45c471a8c6d` | **PASS** |
| 13 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\13.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/13.json` | 870649 | `73376158100aa9b8412aa71a5b7a5063d1e515d1cb1a5855ce5ab4ae6a58abcd` | **PASS** |
| 14 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\14.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/14.json` | 870649 | `5ef5d0cdff7775397524568b93fae50bf175a0823d45094e656e5f5aa1f96739` | **PASS** |
| 15 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\15.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/15.json` | 870649 | `e45113d6feaf6cbd6770ed7ea0471be72c27269571dde4719cb698b28191f7a1` | **PASS** |
| 16 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\16.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/16.json` | 870649 | `c578f78c937ff9e76a09ff4d09c73dda47d46c8eeccd9512443cb516c5a50247` | **PASS** |
| 17 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\17.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/17.json` | 870649 | `6742fd6e47b90978d3ddedf7f2680ff1efc57f3abbf9359c743e04f9ef681e43` | **PASS** |
| 18 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\18.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/18.json` | 870649 | `9137ddf77d6641f094b862ed863775ae06da76754299b5541080b515ad509f10` | **PASS** |
| 19 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\19.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/19.json` | 870649 | `a848e42a4de37753abd45d1dced3707b36dbf8b322bf219ac77d060a42f34a90` | **PASS** |
| 20 | `C:\NoraEvidence\Phase2\firewall-campaigns\sync-20260717T034100Z\captures\20.json` → `docs/evidence/phase2/firewall-semantic-baseline/semantic20-20260717T034100Z/windows-package/firewall-campaigns/sync-20260717T034100Z/captures/20.json` | 870649 | `f2cdba0045b7d04bdd81e6a81f2e5fbe4960d730d64e78ac9f5cac71183d8520` | **PASS** |

Digest stability: canonical, unrelated, profile, and Nora digests are each stable across all 20 captures.

## Retrieval and cleanup
- SCP/SSH retrieval: **80/80 files byte-identical** by size and SHA-256.
- Exact runtime launch/campaign directories removed; related processes zero; exact-run pending artifacts zero; Nora rules zero.
- All firewall profiles enabled; tester rule present and disabled; terminal/tester processes zero.
- Phase 2 incomplete; Phase 3 unauthorized; `search_authorized=false`; no acceptance publication; no push.
