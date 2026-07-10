# Phase 0A-P verdict: FAIL

Prior FAIL verdicts remain preserved at `e3c4925` and `6b845b7`.

## Isolation result

The only available signed MT5 build (5836) was copied, never moved, from `C:\\Program Files\\Darwinex MetaTrader 5` to `C:\\Users\\Gasper\\NoraMt5Portable\\app`. Provisioning recorded a manifest of the original terminal data root before copy and a manifest of the copied app. The portable terminal path was `C:\\Users\\Gasper\\NoraMt5Portable\\app\\terminal64.exe`.

## Startup result

A minimal `StartupPing` script was compiled inside the copied portable tree. It was launched only as `terminal64.exe /portable /config:<alternative-config>`, with `Login=0` and no `Server`. It emitted no machine-readable startup marker and left no running terminal process. Thus the required unattended startup execution proof failed before custom-data or tester execution. No broker account, Darwinex profile/history, UI automation, or tester run was used.

## Verdict rationale

The copied program tree demonstrates filesystem isolation, but not a reliable unattended MT5 execution boundary. Without a dependable config-driven bootstrap, this VM cannot meet the custom-data import, completed-report, two-run semantic reproducibility, or interruption/recovery contract.

## Recommendation

Move validation to a dedicated Windows environment provisioned from a known standalone MT5 distribution, with a documented first-run bootstrap that is independently proven under the intended Windows session model. It must have an isolated portable data root, no broker account configuration, a fixed custom-symbol data bundle, config-driven script execution, and durable SSH-accessible job/result state. Those conditions address the demonstrated startup failure and broker synchronization, rather than merely duplicating the current Darwinex terminal.
