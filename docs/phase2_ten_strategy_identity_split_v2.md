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
orchestrator, and genuine importer. Exact reconciliation remains a role only for
the embedded synthetic smoke canary. Broker-native validation uses the separate
`nora.phase2_broker_native_similarity_v1` report and its pre-frozen budget map.

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
  -> embedded smoke exact reconciliation
  -> broker-native similarity report + edge-survival gate
```

Compiler evidence never depends on launcher, collection, transfer, ingestion, or
reconciliation bytes. An execution packet does depend on those bytes and on
fresh genuine v2 compiler evidence. The corrected v1 compiler packet is valid,
source-correct historical proof, but is acceptance-superseded and cannot be
materialized into a v2 execution contract. Genuine recompilation is mandatory.

Searchability remains false. This contract does not start search or Phase 3.
