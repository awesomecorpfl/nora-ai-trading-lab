# RISKS_AND_FAILURE_MODES.md
Nora AI Trading Lab — Top Risks and Mitigations

Ordered roughly by expected damage × likelihood.

---

## 1. Research/MT5 boundary risks

### R1. Treating MT5 as the research platform
Running generation, broad robustness, or Monte Carlo through MT5 would make the lab slow, brittle, and hard to resume.

**Mitigation**: Linux-first boundary is locked. MT5 is used only for Phase-2 canary parity and Phase-7 finalist validation.

### R2. Engine/MT5 divergence discovered after large-scale search
A fast Rust engine is dangerous if mechanically wrong.

**Mitigation**: small Phase-2 go/no-go parity gate before search; MQL5-translatability grammar rule; canary reconciliation after engine changes.

### R3. Validation harness fragility
The existing VM path works in practice, but undocumented launch/config/report assumptions could fail later.

**Mitigation**: codify the known-working `ssh nora-win10` workflow into a repository-owned harness; explicit completion state; atomic result return; semantic two-run comparison; interruption classification.

### R4. Subtle semantic mismatch
Warmup, incomplete-bar indexing, session resets, DST, spread, swap timing, and fill semantics can look “close enough” while invalidating research.

**Mitigation**: focused parity fixtures, DST/weekend canaries, trade-by-trade reconciliation, frozen parity budget.

### R5. Broker/source mismatch
Canonical research data and Darwinex broker history may differ.

**Mitigation**: Phase 0C comparison; preserve provider identity and broker-reference identity separately; use matched reference extracts for parity analysis; record all transformation provenance.

---

## 2. Data risks

### R6. Confusing QDM with the data provider
QDM is a tool, not the provider or canonical database.

**Mitigation**: provider identity stored separately; QDM version and export settings recorded; staged input hash before ingestion.

### R7. Opaque timezone/DST conversion
A timezone-converted CSV can silently become an untraceable research source.

**Mitigation**: versioned trading-timezone contract; record timezone identity, DST regime, source/bar timestamp semantics, session and strategy clocks, optional UTC reference instant, and every conversion. Preserve intentionally prepared broker-time production data directly where declared.

### R7a. Research/MT5 clock mismatch
Silent conversion, an incorrect DST regime, double conversion, session-rule drift, or an incorrect Friday-close time can make a strategy trade on a different clock from its target MT5 broker.

**Mitigation**: deterministic conversion rules with a conversion ledger and double-conversion guard; named/versioned broker-time contract; DST/weekend/session canaries; parity fixtures for Friday close, ORB, rollover, daily reset and Monday open; compare declared research clock to the target MT5 broker clock before parity/finalist runs.

### R8. Data leakage between discovery and validation
Repeated reuse of recent data or broker validation windows creates hidden selection.

**Mitigation**: versioned data splits, lockbox policy, logged access, no threshold changes mid-experiment.

---

## 3. Quant/research-validity risks

### R9. Optimistic simulation bias
Ambiguous fills inflate whole candidate populations.

**Mitigation**: pessimistic ambiguity rule, synthetic fixtures, narrow v1 semantics, early cost stress.

### R10. Look-ahead and session leakage
Incomplete bars, future session statistics, or hindsight regime labels create fake edge.

**Mitigation**: completed-bar signals, forward-valid features, canary and placebo tests.

### R11. Cost-model self-deception
Thin modeled costs create fragile M1 strategies.

**Mitigation**: broker-reference symbol specs, variable-cost analysis where available, Tier-1 cost stress, Darwinex native finalist confirmation.

---

## 4. Overfitting and selection-bias risks

### R12. Industrial-scale multiple testing
Large search populations inevitably produce impressive noise.

**Mitigation**: matched random-search baseline, permanent lockbox, tracked trial counts, placebo/permutation-style integrity tests, DSR diagnostic only.

### R13. Threshold drift
Changing gates after seeing results recreates researcher degrees of freedom.

**Mitigation**: protocol immutability enforced in control plane.

### R14. Lockbox erosion
Repeated “just one look” destroys the lockbox.

**Mitigation**: human gate and permanent access log.

### R15. Survivorship-biased research memory
If only winners are remembered, Nora learns false priors.

**Mitigation**: failures and rejection reasons are first-class records.

---

## 5. Portfolio risks

### R16. Correlation underestimation
Calm-period correlation understates crisis dependence.

**Mitigation**: downside/tail correlation, DD overlap, correlated cost shocks, loss-clustering bootstrap, concentration caps.

### R17. Hero-strategy dependence
A portfolio can look diversified while one EA dominates.

**Mitigation**: mandatory dropout stress.

### R18. Sizing from realized historical DD
Historical max DD is a poor risk budget.

**Mitigation**: stressed 95th/99th percentile portfolio DD plus reserve.

### R19. Optimizer instability
Mean-variance optimization is unstable and targets the wrong risk measure.

**Mitigation**: locked exclusion; greedy selection + drawdown budgets + caps.

---

## 6. Technical/operational risks

### R20. Crash recovery that almost works
Lost or duplicated tasks silently corrupt results.

**Mitigation**: immutable task outputs, task ledger, kill/reboot acceptance tests, idempotent commands.

### R21. Laptop thermal and memory limits
Sustained 12-thread work may throttle; careless buffering can consume 40 GB RAM.

**Mitigation**: Phase 0B worker benchmark, per-task memory estimates, streaming writes.

### R22. SQLite contention
Multiple writers undermine reliability.

**Mitigation**: WAL mode, one control-plane writer, engine workers only write files.

### R23. Nondeterminism creep
Parallel reduction order or unseeded randomness breaks reproducibility.

**Mitigation**: fixed reduction rules, named seeded RNG streams, semantic determinism CI.

### R24. Premature infrastructure detours
Building new VMs, terminals, import systems, or Windows automation unrelated to the narrow validation contract wastes time.

**Mitigation**: preserve the known-working existing VM path; infrastructure work must be justified by a failed acceptance criterion, not by theoretical cleanliness.

---

## 7. Ways this project wastes months

| Failure pattern | Guard |
|---|---|
| Running the research funnel through MT5 | Linux-first boundary |
| Building search on an unvalidated simulator | Phase-2 parity gate |
| Rebuilding a working VM path unnecessarily | Existing validation boundary lock |
| Gold-plating AST nodes MT5 cannot translate | Grammar admission rule |
| Adding evolutionary machinery before sampling plateaus | Search sequencing rule |
| Running Parameter MC/WFO on thousands of doomed candidates | Funnel ordering |
| Porting every indicator before the pipeline works | Layer-1 limit |
| Wiring Nora early as a workaround for missing automation | Phase-8 sequencing |
| Trusting recovered state that duplicated work | Phase-1 task-ledger acceptance |
| Believing survivors that do not beat matched random search | Required baseline |
| Automating deployment before research is trustworthy | Manual deployment boundary |

---

## 8. False-confidence checklist

1. Would the result survive pessimistic-fill assumptions?
2. Did survivors beat the matched random-search baseline?
3. Was any threshold changed after the experiment started?
4. Has the lockbox been touched?
5. Do current canaries still reconcile between Rust and MT5?
6. Is the candidate relying on a data-source/broker mismatch?
7. Does the portfolio survive removal of its best contributor?
8. Has MT5 accidentally crept into work Linux should own?
