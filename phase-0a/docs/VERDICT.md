# Phase 0A verdict: FAIL

The existing Fedora → SSH → Windows 10 LTSC → MT5 config route can start MT5 unattended, discover and compile/place an EA, and begin automatic testing. It cannot presently be accepted as the MT5 orchestration boundary.

## Evidence collected

- Fedora reached the VM at the pre-existing localhost SSH forward and ran PowerShell non-interactively.
- The VM is an autostarted `win10` libvirt domain running Windows 10 IoT Enterprise LTSC 10.0.19044; Darwinex MT5 build 5836 is installed.
- The runner discovered the data root from `origin.txt`, compiled `Phase0Probe.mq5` there with zero compiler errors, and verified the generated EX5 hash.
- MT5 accepted the generated `/config:` file. After the runner read the single existing tester login/server at runtime (never committed), its terminal journal recorded `Tester automatical testing started`.
- Two attempts (real-tick model and open-prices model) immediately entered `AutoTesting GBPAUD: history synchronization started` before the probe executed. This is unrelated to the pinned GDAXI probe range. Both were interrupted by stopping only the owned `terminal64` and `metatester64` processes.

## Unmet acceptance requirements

No completed test report, semantic trade list, metrics, return transfer, or two-run semantic comparison was produced. The history manifest was captured before launch, but MT5 then began uncontrolled network synchronization, so it cannot establish deterministic data provenance.

## Interruption observations

- Fedora-orchestrator interruption: the remote runner writes `status.json` before launch; a later rerun replaces only its own `NoraPhase0A\\runs\\<run-id>` folder. It has no resume/checkpoint protocol.
- Result-transfer interruption: retrieval occurs only after a completed remote runner; no atomic transfer/resume mechanism is implemented.
- MT5/tester interruption: forcibly stopping the two owned processes was successful. The run remained marked `running`, confirming recovery-state hardening is required.
- VM reboot behavior: not exercised because the active tester could not reach a controlled completion. Read-only VM inspection shows libvirt autostart enabled and `on_reboot=restart`, but the runner has no reboot-resume mechanism.

## Required decision / recommendation

Do not proceed with this VM as the orchestration boundary yet. First harden the VM path: identify why automatic tester startup synchronizes unrelated symbols, establish a frozen/offline MT5 history set or an approved snapshot/copy method, and add durable remote job/result state with atomic retrieval. If that cannot be done without altering broker data or VM/network setup, choose a dedicated Windows validation machine.

