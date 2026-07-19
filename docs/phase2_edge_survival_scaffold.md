# Edge-survival scaffold

## Purpose

This document describes the **scaffolding** for the broker-native edge-survival gate, not a live validation run. The gate itself is defined in [`docs/phase2_broker_native_edge_survival.md`](phase2_broker_native_edge_survival.md). Its question is:

> Does a selected finalist strategy's edge survive the move to native MT5 and broker-native data, despite legitimate differences from Python/Rust research?

The ten hand-designed system-test fixtures are **not finalists**. They validate the pipeline (compile → load → tester → EA lifecycle → CSV → reconciliation → ingestion), not edge. No edge claim is intended for any of them, and none of them has a broker-native implementation — the canary EA exits inside `OnInit` with synthetic OHLC.

Promoting a fixture to finalist status to run the survival gate would manufacture a fake edge claim and destroy the credibility of the result. The scaffolding exists so that when a genuine finalist arrives — from authorized research, after the Phase-3 search freeze lifts — the gate is already built, tested, and impossible to retrofit around.

## What the scaffold provides

Three process primitives in [`lab/phase2_edge_survival_scaffold.py`](../lab/phase2_edge_survival_scaffold.py):

### 1. `freeze_reference_metrics`

Freezes the Python/Rust reference metrics for a finalist into a tamper-evident artifact with an identity hash. The artifact binds:

- `finalist_identity`
- all seven similarity metrics (`trade_count`, `gross_pnl`, `net_pnl`, `profit_factor`, `max_drawdown`, `win_rate`, `average_trade`)
- the reference's own `edge_survives` claim
- the `reference_runner_identity` (so the Python/Rust runner can't be silently swapped)
- a `frozen_at` ISO timestamp

**Must be created before the native result is inspected.** The report assembler rejects any reference frozen after the native observation timestamp.

### 2. `freeze_similarity_budget`

Records the **human-gate** budget decision as a signed artifact. Records:

- the `reference_identity` this budget applies to (must match)
- the full budget map for all seven metrics (validated by `lab.phase2_native_similarity.validate_budget_map`: complete coverage, non-negative tolerances)
- `gate_authority` — who decided
- `edge_survives_definition` — a human-language statement of what "edge survives" means for this finalist
- `native_cost_included` — whether native costs are folded into the comparison
- a `frozen_at` timestamp

**Must be frozen before the native result is inspected.** The report assembler rejects any budget frozen after native observation, and rejects any budget whose `reference_identity` doesn't match the frozen reference.

### 3. `bind_native_provenance`

Binds the broker-native provenance into a single identity hash. The required fields are:

- `symbol`, `server_identity`, `timeframe`
- `date_range_start`, `date_range_end`
- `timezone_identity`
- `spread_model`, `commission_model`, `slippage_model`
- `source_identity`

Any missing or empty field fails closed. The resulting `provenance_identity` must be carried by the similarity report; substitution is detected.

## The ceremony — `assemble_edge_survival_report`

The full report assembler wires the three primitives together and delegates the metric comparison to `lab.phase2_native_similarity.build_similarity_report`. It refuses to run when:

- the reference was frozen after the native observation;
- the budget was frozen after the native observation;
- the budget's `reference_identity` doesn't match the frozen reference;
- any input has the wrong schema;
- any native metric is missing or `edge_survives` is non-boolean.

The assembled report carries:

- `edge_survival_accepted` (from the similarity verdict)
- `native_parity_accepted = False` (always — parity requires a separate human gate)
- `searchable = False` (always — Phase 3 remains closed)
- a `report_identity` binding finalist, reference, budget, provenance, and similarity identities

## Broker-data EA skeleton

[`lab/mql5gen/edge_survival_skeleton.py`](../lab/mql5gen/edge_survival_skeleton.py) generates a compilable MQL5 EA that is **intentionally non-strategic**. It:

- declares the cost-model inputs (`CostModelSpread`, `CostModelCommission`, `CostModelSlippage`);
- opens a result CSV with the 18-column schema the similarity report consumes;
- refuses to run outside the tester (`MQLInfoInteger(MQL_TESTER)` guard);
- provides stubbed `EvaluateEntry` / `EvaluateExit` extension points;
- never places a real order — `OrderSend` is documented as the boundary a finalist must respect.

The manifest carries `skeleton_not_strategic: True` and a `skeleton_identity` hash that binds the source, CSV schema, and extension-point contract. When a real finalist replaces the skeleton, the identity changes and the scaffold detects the substitution.

A finalist implementation plugs its real entry/exit logic into the marked extension points, respects the declared cost model, and emits trades in the skeleton's CSV schema.

## How a future finalist plugs in

1. **Authorized research produces a finalist.** Not the ten fixtures — a genuine strategy with an edge claim, selected through whatever research process is authorized at that time.

2. **The Python/Rust reference is frozen.** `freeze_reference_metrics` captures the finalist's metrics + `edge_survives` claim + the runner identity. This artifact is durable and timestamped.

3. **The human budget gate runs.** A human (recorded as `gate_authority`) decides the tolerance for every metric, writes the `edge_survives_definition`, and freezes the budget. This must happen before the native result is inspected.

4. **The finalist EA replaces the skeleton.** The finalist's real MQL5 implementation takes the skeleton's extension-point contract, fills in `EvaluateEntry` / `EvaluateExit`, and is compiled and run against broker-native data through the existing MT5 tester pipeline.

5. **Native provenance is bound.** `bind_native_provenance` captures the symbol, server, timeframe, range, timezone, cost models, and source identity of the native run.

6. **The report is assembled.** `assemble_edge_survival_report` wires reference + budget + provenance + native metrics into the survival verdict. Freeze-order invariants guarantee nothing was retrofit.

## Why this isn't the survival run

- The ten fixtures have no edge to survive. Running the similarity against them produces a predetermined `edge_survives = false` — theater, not validation.
- Phase 3 (strategy search) remains closed. A real finalist requires authorized research, which is not this tranche.
- The canary EA exits in `OnInit` and has no `OnTick` strategy. It cannot run against broker data at all.
- The budget decision is a human gate that must state what "edge survives" means for a *specific* finalist. No finalist, no meaningful budget.

The scaffold is the maximal honest progress available without unfreezing Phase 3 or faking a finalist.

## Tests

[`tests/test_phase2_edge_survival_scaffold.py`](../tests/test_phase2_edge_survival_scaffold.py) locks every fail-closed path:

- reference freeze: missing metric, non-boolean `edge_survives`, empty finalist, tamper-evidence
- budget freeze: partial budget map, negative tolerance, empty edge definition, tamper-evidence
- provenance binding: missing field, empty field, tamper-evidence
- report assembly: happy path, reference/budget frozen after native, budget not bound to reference, wrong schemas, missing native metric, non-boolean native `edge_survives`, provenance substitution resistance
- EA skeleton: stable artifacts, CSV schema coverage, extension points declared, tester-only guard, non-strategic by default

26 tests. All must pass before this scaffold can be trusted to hold a real finalist's result.
