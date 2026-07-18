# Broker-native edge-survival validation

## Purpose

The ten-strategy suite has two different native validation jobs. The embedded MT5 smoke canary validates compilation, EX5 loading, tester startup, EA lifecycle, and execution of synthetic embedded OHLC fixtures. It uses exact fixture reconciliation.

This document defines the future finalist-stage broker-native validation job. It is intentionally not required for the current ten-strategy system-test fixtures. Its question is:

> Does the strategy's edge survive the move to native MT5 and broker-native data despite legitimate differences from Python/Rust research?

It is not a request for trade-by-trade identity.

## What MT5 supplies

For this tranche, MT5 supplies the native execution environment and broker-native observations:

- selected symbol and server identity;
- broker-native bars/ticks used by the native EA;
- tester date range and timezone interpretation;
- native spread, slippage, filling, and execution behavior where configured;
- native trade records and summary metrics.

The run is read-only and must not place live trades. The investor account protects that boundary but does not make broker data identical to research data.

## Expected differences

Differences from Python/Rust are expected from:

- source and vendor data;
- broker/server timezone;
- bar construction and missing bars;
- spread and commission assumptions;
- slippage and gap handling;
- indicator implementation details;
- tester execution semantics;
- session and contract rules.

These differences are not automatically defects. They become defects when the strategy behavior or edge no longer survives within the pre-frozen acceptance budgets.

## Required acceptance stages

### Stage A — native execution health

Hard pass/fail checks:

- corrected source compiles with the required MetaEditor build;
- EX5 loads in the native tester;
- tester agent starts;
- EA starts and completes without fatal runtime failure;
- no live trade occurs;
- native output and provenance artifacts are complete;
- broker/history/cache observations are classified, not ignored.

### Stage B — native behavioral similarity

Compare native results with the Python/Rust research reference using `nora.phase2_broker_native_similarity_v1`.

The report must include at least:

- trade count;
- gross PnL;
- net PnL after the declared cost model;
- profit factor;
- maximum drawdown;
- win rate;
- average trade;
- explicit `edge_survives` verdict.

The comparison reports absolute and relative deltas. It does not claim exact trade identity.

### Stage C — edge survival

Native acceptance requires all of the following:

- the budget map was frozen before the native result was inspected;
- all declared metric deltas are within budget;
- the native edge-survival criterion is true;
- the comparison provenance binds symbol, server, timeframe, date range, timezone, spread, commission, slippage, and source identities;
- any divergence is explained or explicitly classified;
- `native_parity_accepted` remains false for this similarity result unless a later human gate explicitly promotes it;
- `searchable` remains false.

## Duplicate runs

Duplicate native runs are repeatability checks, not cross-engine parity checks. Under the same frozen terminal, symbol, server, date range, tester settings, and cost assumptions, repeated runs should be stable. If broker cache or source data changes, preserve that as environmental provenance and assess whether it affects the similarity verdict.

A1/A2 and B1/B2 must not be interpreted as proof that Python, Rust, SQX, and MT5 will produce identical trade ledgers.

## Budget governance

No default tolerance values are encoded here. The native package must carry a complete, explicit budget map before launch. A missing, partial, negative, or post-result budget map fails closed.

The budget decision is a human gate. It must state:

- allowed trade-count difference;
- allowed gross/net PnL absolute and/or relative difference;
- allowed profit-factor difference;
- allowed drawdown difference;
- allowed win-rate difference;
- allowed average-trade difference;
- the exact definition of `edge_survives`;
- whether native costs are included and how.

## Scope boundary

This tranche does not authorize:

- strategy search;
- broad grammar admission;
- production deployment;
- live trading;
- full broker-universe import;
- unbounded broker exploration.

The embedded smoke canary and broker-native edge-survival validation remain separate evidence classes.
