# Phase 0A implementation plan

## Discovered environment

- Fedora 44 hosts an autostarted libvirt user-session domain named `win10`.
- The VM is Windows 10 IoT Enterprise LTSC (10.0.19044), 8 GiB RAM, 4 vCPU.
- Existing OpenSSH is forwarded only on `127.0.0.1:2222`; the existing key works when SSH is invoked with an explicit config, because a host-wide SSH drop-in has unsafe permissions.
- One MT5 installation exists: Darwinex MetaTrader 5 build 5836 at `C:\Program Files\Darwinex MetaTrader 5\terminal64.exe`.
- Its data root is discovered from `origin.txt`, not assumed. Existing Darwinex-Live history and prior GDAXI tester artefacts are present.

## Proposed path

Fedora stages this contained spike over SSH/SCP, then calls a PowerShell runner. The runner discovers the MT5 data root, compiles and places a probe EA under `MQL5\Experts\NoraPhase0A`, materializes a per-run tester INI, launches `terminal64.exe /config:...`, and copies report, logs, data manifest, semantic trade CSV, and metrics CSV into its isolated work directory. Fedora retrieves, parses, and semantically compares two runs.

## Files and evidence

The spike contains the EA, pinned templates, a Windows runner, a Fedora orchestrator, report parser/comparator, and evidence/verdict documents. It records EA and data hashes, the rendered configuration, terminal exit status, tester report, normalized trades/metrics, and interruption observations.

## Material risk

Historical data is proven by a read-only manifest/hash instead of an overwrite or download. The tester config route and report location must still be demonstrated on this specific MT5 build. MT5 or broker-data updates invalidate the corresponding provenance snapshot.

