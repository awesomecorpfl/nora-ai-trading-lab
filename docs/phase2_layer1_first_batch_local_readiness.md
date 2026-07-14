# Phase 2 Layer-1 reconciliation and first-batch local readiness

Verdict: the authoritative locked Layer-1 inventory is reconciled and EMA/value, Highest/value, and Lowest/value have narrow native parity acceptance for the frozen batch-one contract. The four authoritative returned packages reconcile `PASS_EXACT`. The selected nodes remain non-searchable, grammar admission is unchanged, and Phase 2 remains incomplete.

## Inventory

The machine-readable authority is `tests/fixtures/phase2_layer1_first_batch/authoritative_matrix.json` (`8c842057b6d9efebbfd17ffaf583f4058d7464816f29d078d80db3403768b3bf`). It contains 22 canonical families: 18 indicators and four transforms. Ten have narrow accepted evidence (SMA, EMA, MACD, ATR, Highest, Lowest, Cross, Slope, Distance/ATR, and Percentile); 12 are implemented but unproved. None is searchable. Existing target-specific harness evidence remains valid and is not downgraded by the newer batch architecture.

| Family | Outputs | State | First batch | Initial-ten need |
|---|---|---|---|---|
| SMA | value | ACCEPTED | no | accepted dependency |
| EMA | value | ACCEPTED | yes | accepted trend baseline |
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
| Highest | value | ACCEPTED | yes | accepted breakout level |
| Lowest | value | ACCEPTED | yes | accepted breakout level |
| Session OHLC | open, high, low, close | IMPLEMENTED_UNPROVED | no | not required before ten |
| VWAP | value | IMPLEMENTED_UNPROVED | no | not required before ten |
| Cross | boolean | ACCEPTED | no | accepted dependency |
| Slope | value | ACCEPTED | no | accepted dependency |
| Distance/ATR | value | ACCEPTED | no | accepted dependency |
| Percentile | rank | ACCEPTED | no | optional diversity |

Every matrix record separately binds canonical identity, Rust and typed-AST state, output arity/names, null/warmup semantics, MQL5 state, local fixture, compiler/result/reconciliation state, grammar/search state, dependencies, and its exact remaining evidence gap.

## Initial v1 dependency map and batch selection

The frozen dependency map (`d62ed415efc6cc4ecff7157f26912b7048c0f29e978f28fe27a16f8e4dc71681`) records five trend-pullback and five close-confirmed breakout designs. The indicator dependencies for that frozen suite are parity-ready; this does not claim the ten strategies themselves are reconciled. The suite depends on the accepted next-open execution contract and the accepted time-rule contract. Trend designs use EMA, Slope, ATR, Distance/ATR, and Cross. Breakout designs use Highest/Lowest completed levels and Cross. No new indicator family, population, or search grammar is introduced.

The batch plan identity is `7012e4ad5d702d42ff32f4f1822eee5a87445b61c138777f61709370fcb49d98`. The selected canonical identities are:

- EMA/value: `8d9c826fbf38563a96fcce863882f11209839cde55849e78410656f3323ccaab`
- Highest/value: `3f3c32a76f0a5fe6fc9e6bc9993397d9c71ba290f52ae616895d5d265843ee2b`
- Lowest/value: `81badad2583b1701408a63ed41d89382d70723eac585cdbe1275fb078835f5c3`

This is dependency-complete for the missing Layer-1 pieces of the representative suite and stays below the six-family limit. Accepted nodes are excluded. ADX, ER, KAMA, Linear Regression, RSI, CCI, ROC, Stochastic, Bollinger, and Keltner are deferred as optional or complex diversity. Session OHLC and VWAP are excluded because the first ten do not require them.

## Numeric protocol and formula contracts

The numeric parity protocol identity is `f1b3f721ff42ae399d7f98a2bb7a1a350a4fba301336363712df0986cbc08c5e`; the failure vocabulary identity is `0c0c97243a7c1fa8a4fca2567d14c94c4d823ac7c2d6ce69eb0f540cd5ac9c93`. Row count, timestamp, order, null state, warmup, decisions, output presence/names, reason codes, and invalid-input class are exact. Finite values record both sides, absolute/relative error, practical ULP distance, maxima, percentiles, first divergence, and warmup/steady-state class.

Budgets are per node/output and identity-bound. The four native runs observed exact equality, so the accepted budget is exact zero only for this immutable batch, node/output set, eleven scenarios, runtime/tester/package, and parity protocol. It cannot be generalized to another indicator or fixture. Synthetic within-budget tests use an explicitly supplied test-only budget and cannot establish native tolerance.

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
- precompile batch (post-acceptance local readiness): `47e4015c8595652a4d6a5b1fc1313e62cad382e55e5eda37ba1867c7ada6fca7`
- precompile staged inventory: `8f24899fc3d31549f55ea8a459a466c8ac523aaf037d75300b6dfd0711de054f`
- local readiness: `53559ef3df814265d242a70cebeb6ca56d75cb49891fc2d822f651c15ae5c558`

The synthetic protocol-only identities are compiler output `338851917781f6a3b4c435eea637a9d2242051d5fa2a5077b2cf05bd77865ee4`, execution packet `6b60f604fbb58c49707c92074c22781f932afc25d8d9a5a8eaa2752b864c6874`, final batch `f68add39ff29c1e572f7c78f1883acef90f3b61e3bf723c311e4b99f657896e9`, final staged inventory `1fa149f2873151af64d8c021c5c5c43e5c75769e10b24f26aaa13b3c63c0d5cc`, and reconciliation `847f5597e4dc73af6e053d506fc664a7e3d2d3b3df53a4f1be89738e2cf8dc86`. They test the typed import and returned-package machinery only and are not native evidence.

## Native acceptance

The genuine chain is compiler output `b3e3ccd6b7b5c622459896f872f9f4f395e8ff259af74c07bfafa96e4a109e1d`, EX5 `b8b2fb37964ee5c667c8bf8275e318e4e44fee7c1b825f69ade774b8c70386de` (17,514 bytes), execution packet `72c2397f1984436fed98589712a72bf750f00fff5ca3134e61db537522ed660b`, and final batch `c2fcc551377a5569df4fa5cd632d5236df1d60ce08ebf7a76cc5d7e8b501cbbb`. A1, A2, B1RR, and B2 each pass exact structural and numeric reconciliation. Original B1 is preserved only as non-authoritative historical mechanical evidence; B1RR is its authoritative fresh replacement.

The canary reads only fixed embedded vectors. The preserved tester journals record automatic terminal host-history checks (and AUDCAD download messages); those terminal-side events were not canary inputs and host neutrality proves they were semantically inert. No project data acquisition or UTC conversion occurred.
