# Phase 2 Layer-1 reconciliation and first-batch local readiness

Verdict: the authoritative locked Layer-1 inventory is reconciled and the first native batch is locally sealed. No genuine compiler or MT5 execution occurred, no native result is claimed, the selected nodes remain non-searchable, and Phase 2 remains incomplete.

## Inventory

The machine-readable authority is `tests/fixtures/phase2_layer1_first_batch/authoritative_matrix.json` (`682e4563a5460429860e1b7d0727c0288f99f7180948e0e49a32c8c63b06d104`). It contains 22 canonical families: 18 indicators and four transforms. Seven have narrow accepted evidence (SMA, MACD, ATR, Cross, Slope, Distance/ATR, and Percentile); 15 are implemented but unproved. None is searchable. Existing target-specific harness evidence remains valid and is not downgraded by the newer batch architecture.

| Family | Outputs | State | First batch | Initial-ten need |
|---|---|---|---|---|
| SMA | value | ACCEPTED | no | accepted dependency |
| EMA | value | IMPLEMENTED_UNPROVED | yes | mandatory trend baseline |
| ADX | adx | IMPLEMENTED_UNPROVED | no | optional diversity |
| ER | ratio | IMPLEMENTED_UNPROVED | no | not required |
| KAMA | value | IMPLEMENTED_UNPROVED | no | not required |
| MACD | macd, signal, histogram | ACCEPTED | no | optional diversity |
| Linear Regression | value, slope | IMPLEMENTED_UNPROVED | no | not required |
| RSI | value | IMPLEMENTED_UNPROVED | no | optional diversity |
| CCI | value | IMPLEMENTED_UNPROVED | no | not required |
| ROC | value | IMPLEMENTED_UNPROVED | no | optional diversity |
| Stochastic | k, d | IMPLEMENTED_UNPROVED | no | complex optional node |
| ATR | value | ACCEPTED | no | accepted dependency |
| Bollinger Bands/Width | middle, upper, lower, width | IMPLEMENTED_UNPROVED | no | optional diversity |
| Keltner | middle, upper, lower | IMPLEMENTED_UNPROVED | no | complex optional node |
| Highest | value | IMPLEMENTED_UNPROVED | yes | mandatory breakout level |
| Lowest | value | IMPLEMENTED_UNPROVED | yes | mandatory breakout level |
| Session OHLC | open, high, low, close | IMPLEMENTED_UNPROVED | no | not required before ten |
| VWAP | value | IMPLEMENTED_UNPROVED | no | not required before ten |
| Cross | boolean | ACCEPTED | no | accepted dependency |
| Slope | value | ACCEPTED | no | accepted dependency |
| Distance/ATR | value | ACCEPTED | no | accepted dependency |
| Percentile | rank | ACCEPTED | no | optional diversity |

Every matrix record separately binds canonical identity, Rust and typed-AST state, output arity/names, null/warmup semantics, MQL5 state, local fixture, compiler/result/reconciliation state, grammar/search state, dependencies, and its exact remaining evidence gap.

## Initial v1 dependency map and batch selection

The frozen dependency map (`4190da25741e44d2c59f44582ba2831aa81322675ad8181a82eab2c407e786de`) records five trend-pullback and five close-confirmed breakout designs. The suite depends on the accepted next-open execution contract and the accepted time-rule contract. Trend designs use EMA, Slope, ATR, Distance/ATR, and Cross. Breakout designs use Highest/Lowest completed levels and Cross. No new indicator family, population, or search grammar is introduced.

The batch plan identity is `7012e4ad5d702d42ff32f4f1822eee5a87445b61c138777f61709370fcb49d98`. The selected canonical identities are:

- EMA/value: `8d9c826fbf38563a96fcce863882f11209839cde55849e78410656f3323ccaab`
- Highest/value: `3f3c32a76f0a5fe6fc9e6bc9993397d9c71ba290f52ae616895d5d265843ee2b`
- Lowest/value: `81badad2583b1701408a63ed41d89382d70723eac585cdbe1275fb078835f5c3`

This is dependency-complete for the missing Layer-1 pieces of the representative suite and stays below the six-family limit. Accepted nodes are excluded. ADX, ER, KAMA, Linear Regression, RSI, CCI, ROC, Stochastic, Bollinger, and Keltner are deferred as optional or complex diversity. Session OHLC and VWAP are excluded because the first ten do not require them.

## Numeric protocol and formula contracts

The numeric parity protocol identity is `f1b3f721ff42ae399d7f98a2bb7a1a350a4fba301336363712df0986cbc08c5e`; the failure vocabulary identity is `0c0c97243a7c1fa8a4fca2567d14c94c4d823ac7c2d6ce69eb0f540cd5ac9c93`. Row count, timestamp, order, null state, warmup, decisions, output presence/names, reason codes, and invalid-input class are exact. Finite values record both sides, absolute/relative error, practical ULP distance, maxima, percentiles, first divergence, and warmup/steady-state class.

Budgets are per node/output and identity-bound. No empirical native budget is accepted in this tranche. Native results must first be observed, exact matches classified separately, and the smallest supported budget explicitly accepted. Synthetic within-budget tests use an explicitly supplied test-only budget and cannot establish native tolerance.

All three outputs use an independent generated implementation over identical embedded vectors; no platform indicator handle is used. Reference mode is oldest-to-newest embedded rows, shift zero, and no buffer. EMA uses an arithmetic seed and the `2/(period+1)` recurrence, resetting seed state after a null. Highest and Lowest use complete inclusive rolling windows; any null in the window makes the output unavailable. Period zero produces `invalid_period`. Output name is exactly `value`.

The real Rust task output identity is `0dc7a7e9474df678c4b8384438fd909a2902e1b3878e39fd13fefa4e2e0fa460`; expected vectors are `6aff5416bff4523857eb5deac509e726aa75aa2785762646569dee229b6ff071`; output schema is `79a65e010133d998bcdd0f47fec35b55cfd5fbf143f071a91e4e5ad9033a97bf`. Eleven fixed scenarios cover ordinary, flat, increasing, decreasing, repeated, zero-range, null-reset/window, warmup, minimum period, and invalid period behavior.

## Typed target and readiness

The selected typed AST nodes validate numeric input and positive periods, canonicalize deterministically, evaluate through the Rust kernels, and translate to the independent generated MQL5 runtime. They are explicitly not grammar-admitted or searchable. The MQL5 tester embeds inputs only; expected outputs are not resolver inputs and it has no chart, history, clock, tick, account, order, position, randomness, or platform-indicator dependency.

Frozen identities:

- runtime: `3645d4e252080d266ded55845102f024237843c31fad5f28391aafc10a9b4533`
- tester: `1153507eee52c1001b8ceab02860ed97518a1c847b8b4967977367c8b9fe93be`
- executable package: `65ddd67d3abddff2788011bc9cb22427ebabb3a1eddf18215d89b74e416eabec`
- target descriptor: `157592202895624446e7e6809040cd8acddeadc5d0daa29e199b2ad0dc6b903f`
- compile input: `894290b2fe777eb5086e0b48f88ec0420df9348c874cf69091b4921145ea1a59`
- precompile batch: `77f44173b9859f9cfd76251b5517d476f532bd49934c0fec71216d79147bff93`
- precompile staged inventory: `8f24899fc3d31549f55ea8a459a466c8ac523aaf037d75300b6dfd0711de054f`
- local readiness: `b0df72a0120389f85b8c3b66b02a28ef0ecc7e12ae1781fe9cb36f953e371aba`

The synthetic protocol-only identities are compiler output `338851917781f6a3b4c435eea637a9d2242051d5fa2a5077b2cf05bd77865ee4`, execution packet `6b60f604fbb58c49707c92074c22781f932afc25d8d9a5a8eaa2752b864c6874`, final batch `58144e5a9434db740870d731ec736f7824433f8129f1fa594a4fab1d90d97127`, final staged inventory `1fa149f2873151af64d8c021c5c5c43e5c75769e10b24f26aaa13b3c63c0d5cc`, and reconciliation `dd5cceac2039b4edd2735bd7b3f16164ea9d386accf08d044191f96e0b7778e1`. They test the typed import and returned-package machinery only and are not native evidence.

## Native next step

On an explicitly authorized future native tranche, stage the byte-frozen precompile batch, compile the single tester with the declared MetaEditor build and clean-log policy, import its compiler record/log/fresh EX5 through the typed importer, then run independent A1/A2 GDAXI/M1 and B1/B2 AUDCAD/M1 host contexts. Return each bounded journal, report substitute, marker states, run record, and CSV in an atomic package. Reconcile exact fields first, record numeric observations without a preaccepted budget, propose the smallest per-output budgets if any non-exact finite values occur, and require explicit acceptance.

No additional market data is required: the canary uses only fixed embedded vectors generated from committed inputs.
