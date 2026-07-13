# Typed native-evidence boundary for the time-rule canary

The accepted execution-native implementation contains four categories.

| Category | Components |
|---|---|
| Reusable unchanged | canonical SHA-256, MetaEditor policy `nora.metaeditor_cli_success_v1`, freshness assertions, directed dependency graph, path safety, occupied-destination rejection, atomic directory publication, inventory and manifest hashing |
| Reusable through a descriptor | target/schema names, runtime/tester/package/EX5 filenames, compile/execution/collection scripts, marker names, result filename, host matrix, package-member roles, reconciliation implementation identifier |
| Time-rule specific | clock and scenario identities, expected time rows, CSV schema, civil-time/offset/DST/session/anchor/conversion validation, reason vocabulary, exact reconciliation classifications |
| Execution-only | ledger rows, prices and tolerance, direction, entry/exit indices and reasons, execution fixture and accepted execution package paths |

The execution modules hard-code `execution`, `NoraPhase2Execution*`, execution CSV and
markers, ledger schema and price reconciliation, `phase2x_native_batch_v4.json`, and
execution-specific packet and returned-package schemas. Those values are prohibited
from satisfying the time-rule descriptor.

The dependency graph remains strictly forward-only:

`source/package -> compile input -> compiler output -> execution packet -> final batch`

A descriptor owns immutable names and roles. It contains neither expected rows nor
native results. Target-specific code owns semantic rows and reconciliation. Existing
execution artifacts and identities are not rewritten by this architecture.
