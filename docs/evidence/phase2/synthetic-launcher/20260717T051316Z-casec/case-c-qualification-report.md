# Phase-2 Case-C Owner-Binding Mismatch Qualification

**Verdict: PASS**

## Scope

One isolated Case-C synthetic launcher tranche only. Cases A, B, and D were not rerun. The prior 20260717T043548Z evidence directory was not modified. No MT5, terminal64.exe, metatester64.exe, market-data, firewall mutation, Phase-3 work, push, or twenty-capture campaign occurred.

## Run identity

- Run ID: `20260717T051316Z-casec`
- Launch ID: `synlc-20260717T051316Z-casec`
- Campaign ID: `sync-20260717T051316Z-casec`
- Qualification HEAD: `008bc62ebbc8bc754128a4c04cf3e7944516b3b1`
- Prior evidence HEAD: `dfac6d2ee445bf01e247fd8a7d67286d9eda12ee`

## Deliberate mismatch and causal result

The synthetic campaign intentionally published an owner record with:

- Claimed `parent_process_id`: `999999`
- Actual live campaign parent PID: `4664`
- Campaign owner PID: `1716` (matched the live process PID)
- Wrapper PID: `4664` (matched the live process parent PID)

The repaired wrapper compared the owner record against the live CIM process observation and produced:

`OWNER_BINDING_MISMATCH`

The comparison record shows:

- `launch_id`: equal
- `owner_pid`: equal
- `parent_process_id`: **not equal** (`999999` vs `4664`)
- `wrapper_pid`: equal
- mismatch detected: `true`
- bootstrap acknowledged: `false`
- success receipt present: `false`
- claims count: `0`

## Retained evidence

All runtime evidence was copied to the Windows sealed location before the exact launch and campaign directories were cleaned. The repository copy contains the byte-identical retained package under `raw/`, including the intent, wrapper start/outcome, owner record, causal mismatch record, live-process observation, verifier comparison, terminal outcome, stdout/stderr files, and injected synthetic campaign script.

The prior Case-C clarification is copied unchanged as `superseded-case-c-clarification-20260717.md`; it remains the historical limitation record and was not edited.

## Validation

- Focused Python launch contract/regression tests: **6 passed**
- Full Python suite: **486 passed, 1 skipped**
- Rust engine workspace: **49 passed, 0 failed**
- Phase-0b Rust suite: **5 passed, 0 failed**
- PowerShell 5.1 parser: wrapper errors `0`; Case-C harness errors `0`
- Deployed wrapper SHA-256: `48aa6336bade5ff29a801c222218969453e0108da8f18007be0ebbc79be85e9e`
- Deployed launcher SHA-256: `3e3bdb46c5fcf555fc3493e8cada718b7b03b2d64dbf8f17f5249ccbc4f11371`
- Deployed campaign SHA-256: `4ff07f32c89b4150bd35eb5f96389f3107eb13c1942deeed22666fc01271c9ee`
- Deployed runner SHA-256: `ce82c75ee7dbed36c5cb2d2a5b76cd35dfb7bcb8a32020e2e53b5728cb3c572e`
- Deployed capture-tool SHA-256: `0153f6cdada06a98f7c7ae3af704a36c232bb3b2ba625640fc928a808d5cfe57`

## Cleanup and boundaries

- Synthetic launch directory remaining: `0`
- Synthetic campaign directory remaining: `0`
- Related process count remaining: `0`
- Nora firewall rules: `0`
- Domain, Private, Public firewall profiles: enabled
- MetaTrader 5 Strategy Tester Agent rule: present and disabled
- Phase 2: incomplete
- Phase 3: unauthorized
- `search_authorized`: false
- Push: not performed

The evidence manifest is stored beside this report. The final evidence-only commit is created after all destination byte-identity checks pass.
