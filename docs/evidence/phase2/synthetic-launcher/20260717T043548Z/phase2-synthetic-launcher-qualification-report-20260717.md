# Nora AI Trading Lab — Phase-2 Synthetic Launcher Qualification Report

**Run date:** 2026-07-17 04:35 UTC  
**Repository:** `/home/gasper/nora-ai-trading-lab`  
**Scope:** bounded synthetic launcher lifecycle tranche only

## Executive verdict

**PASS — synthetic launcher lifecycle qualification.**

All four synthetic cases passed after repairing the launcher, wrapper, and capture-tool defects:

- **Case A:** successful detached bootstrap — PASS
- **Case B:** campaign exits before owner creation — PASS
- **Case C:** owner-binding mismatch — PASS
- **Case D:** duplicate launch/campaign race — PASS

This does **not** complete Phase 2 overall. Phase 2 remains incomplete, Phase 3 remains unauthorized, and no MT5/tester execution or firewall mutation was performed.

## What was repaired

### Capture tool
`capture-phase2-firewall-inventory.ps1`

- Replaced per-rule filter enumeration with batched filter retrieval.
- Previous behavior: 425 rules × multiple filter cmdlets, hanging beyond 180 seconds.
- Verified behavior after repair: 425 rules processed in approximately 2.6 seconds; capture produced an 851,889-byte JSON inventory.
- Final deployed SHA-256:
  `0153f6cdada06a98f7c7ae3af704a36c232bb3b2ba625640fc928a808d5cfe57`

### Wrapper
`phase2-firewall-launch-wrapper.ps1`

Repaired the PowerShell 5.1/CIM launch path:

- `$args` automatic-variable collision.
- Strict-mode function parameter binding collisions.
- CIM datetime conversion before passing `Start-Process` arguments.
- Idempotent stdout/stderr file creation for reruns.
- Non-empty sentinels for optional metadata so PowerShell does not reject null/empty child-process arguments.

Final deployed SHA-256:
`839d2e9a3932561f4b28e787d8c85b8f20e05111a48f0b66d6a1d3755192d599`

### Launcher
`launch-phase2-firewall-campaign.ps1`

Repaired:

- Matching campaign ownership against the campaign PID rather than the wrapper PID.
- Broken CIM command-line quote escaping.
- Circular submitted-command metadata mutation during base64 payload encoding.

Final deployed SHA-256:
`3e3bdb46c5fcf555fc3493e8cada718b7b03b2d64dbf8f17f5249ccbc4f11371`

## Qualification evidence

Synthetic run timestamp: `20260717T043548Z`

### Case A — successful detached bootstrap

- Launcher exit: `0`
- Wrapper outcome: `BOOTSTRAP_ACQUIRED`
- Intent SHA-256: `07f389fb4867a21b17d262715ab2c1bffb7c9add1e6d261359aa110900a1ea60`
- Wrapper-start SHA-256: `350f1e32e5671354d5eecbd1d49bd185a103c74bc8bf35e129b778d22cc1b0c4`
- Wrapper-outcome SHA-256: `1fa1b4426d8ea90482af3533ba4b5a0bbc6ca033b5b21b4884db8880327acf8a`
- Receipt SHA-256: `d87e3890742fcacf39336db7b7a7dbfaf33728e0e4baae580a44f535627bb826`
- Owner SHA-256: `45e15f2820c7a2e128355c28829b47cf898b47720766ef132de2787719f4ce90`

### Case B — campaign exit before owner creation

- Wrapper exit: `1`
- Outcome: `CAMPAIGN_EXITED_BEFORE_OWNER`
- Receipt: correctly absent
- Result: PASS

### Case C — owner-binding mismatch

- Wrapper exit: `1`
- Outcome: `CAMPAIGN_EXITED_BEFORE_OWNER`
- Receipt: correctly absent
- Claims count: `0`
- Result: PASS

### Case D — duplicate launch/campaign race

- Intent: found; SHA-256 `421b66dc7dd0359988b5683fd25cc971bf2116b3c79e6f11c0093fb006b5e14a`
- One concurrent launch received the receipt; the duplicate was prevented.
- Failure artifact: absent for the winning path
- Result: PASS

## Durable preservation

Windows preservation receipt:

`C:\NoraEvidence\Phase2\synthetic-lifecycle-preservation-20260717T043548Z.json`

The receipt records the final tool hashes, all four PASS outcomes, firewall state, tester-rule state, cleanup counts, and the repository commit used for preservation.

Repository commit recorded by the receipt:
`90c5f8c525378c2b37587249449079977f702573`

## Cleanup and boundary verification

Verified after the run:

- Synthetic launch directories remaining: `0`
- Synthetic campaign directories remaining: `0`
- Phase-2 launcher/campaign/capture processes remaining: `0`
- Nora firewall rules remaining: `0`
- Domain firewall profile: enabled
- Private firewall profile: enabled
- Public firewall profile: enabled
- MetaTrader 5 Strategy Tester Agent rule: disabled
- No firewall rule changes were made.
- No MT5, terminal64, metatester64, or FR-T1 process was launched.
- No Phase-3 operation was authorized.
- No push was performed.

## Repository state

- HEAD: `90c5f8c525378c2b37587249449079977f702573`
- `origin/main`: `e4f4ec62ac89e1f148885eff6663224cc5bafa51`
- Ahead/behind: `87 ahead / 0 behind`
- Tracked files: clean
- Only the four previously protected untracked result directories remain untracked; they were not inspected, hashed, modified, or deleted.

## Final boundary statement

This report certifies the **synthetic launcher lifecycle tranche only**. It does not claim Phase-2 evidence gates E1–E5 or D1–D8 are complete, does not publish `TRANSACTIONAL_CONTAINMENT_ACCEPTED`, and does not authorize live or terminal execution.
