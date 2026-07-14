# Phase-2 ten-strategy identity split v2

The historical v1 `NativeTargetDescriptor` mixed compiler inputs with native
execution and evidence roles. It remains readable so prior compiler and native
evidence is preserved, but it is not eligible for v2 native acceptance.

The v2 compiler-semantic descriptor binds only the generated MQL5 compile unit,
its included runtime, MetaEditor product/path/build, invocation and success
policies, compiler-log/redaction evidence schemas, EX5 output contract, source
and package schemas, and compile allowlist. Execution-role bytes cannot change
the v2 compile-input identity.

The separate native-execution contract binds the genuine EX5, Windows launcher,
tester configuration builder, forensic collector, environmental evaluator,
marker contract, CSV producer, atomic package builder, Fedora transfer/retrieval
orchestrator, genuine importer, and exact reconciliation implementation.
Synthetic tooling is typed as fixture-only and cannot fill a genuine role.

The identity graph is:

```text
MQL5 sources/includes
  -> compiler-semantic descriptor
  -> compile input
  -> genuine v2 compiler evidence
  -> compiled EX5 identity

compiled EX5 identity + native-execution role contract
  + suite/fixture/environmental contracts
  -> execution packet -> final batch -> staged inventory
  -> atomic native run package -> genuine importer
  -> exact reconciliation -> native acceptance
```

Compiler evidence never depends on launcher, collection, transfer, ingestion, or
reconciliation bytes. An execution packet does depend on those bytes and on
fresh genuine v2 compiler evidence. The corrected v1 compiler packet is valid,
source-correct historical proof, but is acceptance-superseded and cannot be
materialized into a v2 execution contract. Genuine recompilation is mandatory.

Searchability remains false. This contract does not start search or Phase 3.
