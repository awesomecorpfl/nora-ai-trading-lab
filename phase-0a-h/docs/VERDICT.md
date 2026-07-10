# Phase 0A-H verdict: FAIL

The original Phase 0A FAIL at `e3c4925` remains unchanged. This bounded remediation did not establish a deterministic unattended custom-symbol path.

## What was proven

- `bases\\Custom` is a separate local MT5 namespace from `bases\\Darwinex-Live`.
- The former failure was broker-driven: after Darwinex authorization, MT5 logged `AutoTesting GBPAUD: history synchronization started`.
- Fedora generated and SCP-transferred a fixed 12-row M1 fixture (SHA-256 recorded locally). The isolated MQL5 importer compiled successfully after source correction.

## Blocking evidence

The generated config-driven `[StartUp]` invocation did not execute the importer: no `import.json` marker appeared in MT5 Common Files and no custom-symbol validation could be collected. MT5 remained running until the owned process was stopped. No UI fallback was used.

Therefore the spike cannot prove custom symbol creation/import, custom-symbol testing, report/trade/metric return, two-run reproducibility, or interruption recovery. Creating a separate terminal/data directory is the next plausible isolation method, but it would materially alter the existing VM installation footprint and is intentionally not attempted without Gasper's decision.

## Recommendation

Use a dedicated Windows validation environment (or explicitly authorize a separate portable/lab-only MT5 instance in this VM). It must contain no broker account/profile, carry a fixed custom-symbol history bundle, and expose a durable job/result directory over SSH. That solves the demonstrated failure by removing the Darwinex account authorization and its automatic history synchronization, rather than merely moving the same terminal state.

