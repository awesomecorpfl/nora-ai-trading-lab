# Phase 2N Native Evidence Repair

This repair commits one fresh MetaEditor compile and two independent MT5 Strategy Tester runs for the frozen slope-transform canary. It proves only this fixed-data native transform; it does not prove broad indicator, simulator, strategy, or Phase-2 parity.

The canonical evidence index is `tests/fixtures/phase2n_mql5_slope_native/native_evidence_manifest.json`. The compile and execution manifests contain the contemporaneous Fedora orchestration boundaries, native command arguments, UTC timestamps, native process statuses, pre-run absence checks, filesystem timestamps, hashes, journal byte boundaries, and lifecycle events.

The compile produced EX5 SHA-256 `45c9abea8bf98825ddef761517cdfe7eeb81a329983273f69e4e51c953b24ff1`. MetaEditor reported 0 errors and 0 warnings and exited with status 1. The EX5 was absent immediately before compilation, was written after compile start, and was within the documented two-second filesystem-resolution allowance after compile completion.

Both tester runs exited with status 0. Each target CSV was absent immediately before execution and had a LastWriteTimeUtc at or after its run start. Both produced 12 ordered rows, null positions `[0, 1, 2]`, and 12/12 passing rows. The exact maximum finite absolute slope difference in each run was `4.83554168928535e-17`.

Both raw CSV SHA-256 values are `29d5d614e602d47d4badb4430272990b7bcd2c7383f7a7bbd7c511c1b8b10783`; both canonical semantic-result identities are `221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f`.

The retained tester configurations redact Login and Server values. No credentials or unrelated journal files are committed.
