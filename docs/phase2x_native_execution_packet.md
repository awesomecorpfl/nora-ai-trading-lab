# Phase 2X native execution packet

This is an execution handoff only. MACD and percentile remain uncompiled,
unexecuted, non-native-parity, non-grammar-admitted, and non-searchable.

1. On Fedora, run `python -c 'from lab.phase2x_batch import preflight; print(preflight("/tmp/phase2x-preflight.json"))'` and require `PASS`.
2. Stage with `python -c 'from lab.phase2x_batch import stage; stage("/tmp/phase2x-stage")'`.
3. Transfer the staged `targets/macd` and `targets/percentile` directories only.
4. On Windows, use `compile-macd-tester-canary.ps1` then
   `execute-macd-tester-canary.ps1`, and the corresponding percentile scripts.
   The expected experts are `NoraPhase2U\\NoraPhase2MacdTesterCanaryV2` and
   `NoraPhase2W\\NoraPhase2PercentileTesterCanaryV2`.
5. Return `compile.json`, `execution.json`, the target CSV,
   `tester-journal.log`, and `lifecycle.jsonl`; completion markers are
   `NORA_PHASE2U_MACD_COMPLETE_V2` and `NORA_PHASE2W_PERCENTILE_COMPLETE_V2`.
6. Return one `returned_result_manifest.json` plus exactly the inventory it
   declares. On Fedora run `python -c 'from lab.phase2y_reconcile import reconcile; print(reconcile("RETURN_DIRECTORY"))'`.

The local returned-result protocol is ready: V1 validates all identities,
compiler/runtime records, inventory hashes and CSV schema before fixed-vector
reconciliation. This is a filesystem contract and synthetic local-readiness
facility only; it is not MetaEditor compilation, MT5 execution, or parity
acceptance.

Only a returned package with exact batch/target identities, successful compile
and runtime records, expected CSV row/null alignment, and a passing
reconciliation review may be considered for native-parity acceptance.
