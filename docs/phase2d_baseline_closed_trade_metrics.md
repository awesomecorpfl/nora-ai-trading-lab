# Phase 2D baseline closed-trade metrics

`compute_closed_trade_metrics_v1` is a strict `labengine <task.json>` task:

```json
{"task_version":1,"task_type":"compute_closed_trade_metrics_v1","input_path":"closed_trades.parquet","output_path":"metrics.json"}
```

It accepts no unknown task fields, requires version 1 and distinct non-empty readable input/fresh output paths, and atomically publishes one canonical JSON artifact.

## Input and output contracts

Input is exactly the Phase-2C closed-trade ledger: `trade_id: UInt64`, `side: Utf8`, `entry_timestamp: Utf8`, `exit_timestamp: Utf8`, `entry_index: UInt64`, `exit_index: UInt64`, `entry_price: Float64`, `exit_price: Float64`, `bars_held: UInt64`, `gross_pnl_per_unit: Float64`. All fields are non-null; IDs are sequential from one; sides are `long|short`; prices/P&L are finite; exits follow entries; and held bars equal `exit_index - entry_index`.

The ordered artifact fields are `metrics_version`, `trade_count`, `win_count`, `loss_count`, `breakeven_count`, `gross_profit`, `gross_loss_abs`, `net_gross_pnl`, `average_trade`, `win_rate`, `average_win`, `average_loss_abs`, and `profit_factor`. Version is `closed_trade_metrics_v1`.

Wins/losses/breakevens have P&L `>0`, `<0`, and `==0`. Gross profit is the ordered sum of positive P&Ls; absolute gross loss is the negated ordered sum of negative P&Ls; net is the ordered sum of all P&Ls. Averages divide their matching count; win rate divides total count; profit factor divides gross profit by absolute gross loss. Undefined divisions serialize as JSON `null`: all five division-derived metrics for zero trades, average win without wins, and average loss/profit factor without losses. All losers therefore have profit factor `0.0`; breakevens participate only in total count.

Identity domain `nora.metrics.closed_trades_v1.semantic.v1` binds the metrics protocol/schema, canonical ordered ledger rows, all metric values including null states, and zero/nonzero state. It excludes paths, task location, temporary directories, and unrelated Parquet metadata.

## Evidence

Committed fixtures cover mixed `[2,-1,0,3,-2]`, empty, all-winner `[1,2]`, and all-loser `[-1,-2]` ledgers. Mixed results are count `5`, wins/losses/breakevens `2/2/1`, profit/loss/net `5/3/2`, average trade/win/loss `0.4/2.5/1.5`, win rate `0.4`, and profit factor `1.6666666666666667`. Empty division metrics are all null; winners give average win `1.5` with null loss/profit factor; losers give null average win, loss `1.5`, profit factor `0.0`.

Two fresh mixed runs yield identical artifact content and identity `9f04f167b472cd59d43675c5fc01d76bca4f01bc6f3da9684aaccc975e158dba`, independent of output path. Mutating `-2 → -3` yields loss `4`, net `1`, average loss `2`, profit factor `1.25`, identity `887ba393c9b61f56bfd6f95b9583ae9662865ba0bb3e4ab3af4c800761fc4018`. Reordering P&Ls leaves aggregate values unchanged but changes ordered-ledger identity to `8eb089180cfe2a1cc429290baa5038452a22de3fccea3529f3cc3c448c0ffd0f`.

The frozen committed-chain four-loss ledger has count `4`, wins/losses/breakevens `0/4/0`, gross profit `0`, absolute loss/net approximately `0.0012/-0.0012`, average trade/loss approximately `-0.0003/0.0003`, win rate `0`, null average win, and profit factor `0`.

Malformed schema, non-finite price/P&L, and inconsistent held bars each exit non-zero with deterministic stderr, no stdout success summary, no final metrics file, and no successful metrics identity.

```bash
cargo build --manifest-path engine/Cargo.toml
.venv/bin/python -m unittest tests.test_phase1.Phase1.test_closed_trade_metrics_cli_evidence
cargo test --manifest-path engine/Cargo.toml
.venv/bin/python -m unittest discover -s tests
```

Deferred: equity curves, drawdown, consecutive statistics, exposure/holding metrics, risk-adjusted ratios, annualization, costs, sizing, mark-to-market, RNG, MQL5, MT5 parity, grammar, and search.
