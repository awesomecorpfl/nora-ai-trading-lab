# Phase 0A verdict: CONDITIONAL PASS

The existing Darwinex VM path is a working narrow MT5 validation boundary.

## Demonstrated evidence

- Fedora launches the native Darwinex tester over the established SSH path using a run-local config derived on Windows from the existing working configuration. Credentials remain only on Windows.
- MT5 completed two pinned `GDAXI / Strategy 3.85.120 / H1 / 2020.07.01–2026.07.01` tests unattended. Native journals recorded `successfully finished`; each run produced a fresh run-local 2,111,532-byte report.
- The HTML parser extracted 597 ordered MT5 **Deals** per report. It compares native execution-level fields as emitted by MT5; it does not call them reconstructed round-trip trades.
- Both sequences and parsed report metrics were semantically equal. No report bytes, output paths, run IDs, or report-generation metadata are compared.
- A foreground Fedora launch was interrupted during the first run; the Windows-side runner persisted `status.json`, completed independently, and the report was safely retrieved afterwards. The failed initial retrieval created only a `.partial` local directory and was never accepted as a result.

## Bounded remaining hardening

The harness needs explicit aggregate metric extraction beyond the currently parsed report label/value subset, and a dedicated safe tester-kill/VM-restart recovery exercise. These do not block Phase 1's Linux-first engine/control-plane work; they block relying on this harness for unattended finalist batches until done.

