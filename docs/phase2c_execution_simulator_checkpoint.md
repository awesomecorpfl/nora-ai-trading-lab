# Phase 2C execution simulator checkpoint

This is the authoritative checkpoint for accepted Phase 2C execution behavior. It freezes the deterministic one-position simulator, initial brackets, maximum-bars exits, their coexistence, artifacts, identities, and fail-closed boundary. It does not add a trading-performance layer.

## Accepted commit chain

```text
c000bb22019645f10bd1a590ad55255f89070b05  phase2c: add minimal stateful market simulator
f3f8cb7d30b2da14ceb8bd3f0e9f703a0d101393  phase2c: seal minimal market simulator
7e75c044321a3268453ea427c4335b2cd40416f0  phase2c: add initial bracket artifacts
567319f6e5899dc54be044c0858a756ba733ee9d  phase2c: execute unambiguous initial brackets
8ee5ea5a00303b72f1204a6267a5861a21eaeccc  phase2c: seal unambiguous bracket execution
2cf7f6de155efe14eaf3698430884d1830cd10fd  phase2c: add pessimistic bracket ambiguity
6748761c6d22bd0bb5a9beb9e07646cc0661b957  phase2c: seal pessimistic bracket ambiguity
910d7c46368481be997554848ac96fe56bb1aea1  phase2c: add gap-open bracket fills
d3859319a732d3f45f45b1ce0e2967bef2089606  phase2c: seal gap-open bracket fills
697fa84b352556f050d0d87b7598cc1615b4ac0f  phase2c: finalize gap-open execution seal
0a95b587eb95b5c2d5fb51ed98d90172f3df203a  phase2c: add typed maximum-bars config
3e606d07d075571655f052dfd4f58097a1d6faa8  phase2c: execute standalone maximum-bars exits
61d9f2fb0d8ccdd8d625297c78cbdfa3882a11dd  phase2c: seal standalone time-exit identity
e6a87cce4212e2a7d8a0ecebab17593585523821  phase2c: integrate time and bracket exits
e8cda8f02f5fc0e770aa15fa8c955b5ba14cfb04  phase2c: seal combined exit identities
```

## Frozen state machine

When flat:

```text
entry true
→ open at current row open
→ ignore same-row exit
→ no same-entry-row bracket or time exit
```

When carrying a position:

```text
validate OHLC
→ gap-open bracket
→ signal exit
→ maximum-bars time exit
→ intrabar bracket
```

After any close:

```text
same-row entry is ignored and counted
→ no same-row close and reopen
```

Signal and time exits fill at the current open. Exactly-one-level unambiguous bracket hits fill at their bracket level; pessimistic ambiguous hits fill at the stop; supported gap events fill at the actual row open. Terminal policy is `leave_open`: no artificial final-row close or synthetic closing event is created.

## Supported execution configuration

| Configuration | Accepted behavior |
| --- | --- |
| No `initial_bracket_execution` | Construction only; no bracket execution. |
| `ohlc_unambiguous_v1` | Executes exactly-one-level hits; rejects dual-touch ambiguity and gaps. |
| `ohlc_pessimistic_v1` | Resolves dual-touch at the stop; rejects gaps. |
| `ohlc_pessimistic_gap_v1` | Adds inclusive gap-open stop/target fills at the actual open. |
| `time_exit.model = max_bars_held_v1` | Due when `current_index - entry_index >= max_bars_held`. |

Bracket execution and max-bars time exit may coexist and follow the frozen ordering above.

## Immutable artifacts

```text
Closed-trade ledger
trade_id: UInt64
side: Utf8
entry_timestamp: Utf8
exit_timestamp: Utf8
entry_index: UInt64
exit_index: UInt64
entry_price: Float64
exit_price: Float64
bars_held: UInt64
gross_pnl_per_unit: Float64

Initial-bracket artifact
entry_id: UInt64
side: Utf8
entry_timestamp: Utf8
entry_index: UInt64
entry_price: Float64
initial_stop_price: Float64
initial_target_price: Float64

Bracket-exit event artifact
trade_id: UInt64
entry_id: UInt64
side: Utf8
exit_timestamp: Utf8
exit_index: UInt64
exit_reason: Utf8
exit_price: Float64
bar_open: Float64
bar_high: Float64
bar_low: Float64

Time-exit event artifact
trade_id: UInt64
side: Utf8
entry_timestamp: Utf8
entry_index: UInt64
exit_timestamp: Utf8
exit_index: UInt64
exit_reason: Utf8
exit_price: Float64
bars_held: UInt64
max_bars_held: UInt64
```

Event exclusivity is absolute: a bracket close produces one bracket event and no time event; a time close produces one time event and no bracket event; a signal close produces neither. A trade has at most one closing event, and a terminal-open position has none.

## Counters and failure boundary

The successful summary reports entries opened, closed trades, ignored entries while open, ignored exits while flat, signal closes, time-exit closes, initial-stop closes, initial-target closes, pessimistic ambiguity resolutions, gap-open resolutions, bracket-event rows, and time-exit event rows. Each close increments exactly one exit-category counter: signal, time, initial stop, or initial target. Gap and pessimistic-resolution counters may additionally describe that same close.

The boundary is fail-closed for timestamp/row misalignment, invalid bracket offsets, malformed OHLC, unambiguous dual-touch ambiguity, unsupported gaps, invalid time-exit configuration, and invalid execution configuration/model. Such failures have a non-zero exit, deterministic error, no success summary, no final ledger, no applicable final event artifact, and no successful identity publication.

## Frozen identity registry

```text
Minimal committed-chain simulator:
7b39a70d2fe5312a5dc1970254c50a350012309a50c7a3610992c225efa5a5b1
Minimal repeat-run fixture simulator:
2dedf9984a2e09ec91602b6819fee8474f9ea6b69e1fa20cd428c8e9927cb8ad
Construction-only initial bracket:
ece1581fec67637f24283f0c0c76a343688d214d7522dce41333e20c0a82c52d
Pessimistic simulator:
8d4c56e148daadc93cb0cde685bf226a794648382b49928788fb7425134f9114
Pessimistic bracket execution:
ec29fa95b3f88765aba68dca233aa17b74330db8648f622b346692a02c020eb1
Gap-enabled simulator:
a08f68c954d6b164ecd95aac8022f42b6febe3ba343ad7ad58c66848a4b67bae
Gap-enabled bracket execution:
fc9643977935e601cb22cb1d9a78321b41a2500b1407f3cb53a2730d07f56fc0
Standalone long time-exit simulator:
c1fdb17f6b5ca3694418d815c3bbf0c73b99e16927fe93dfe6cf9d034e9472dd
Standalone max-bars time exit:
1d0035f0d20c2a2a96ec8beb8f7beac0b4918ae04a99728e186987ff6d50b1cd
Combined baseline simulator:
febe2e780e027d0df4ab1a4237205ce3f3be53c87a29b17fa30e29b990a8c45c
Combined baseline bracket execution:
23be1c1145d7b9e6ed4dbef6736d9308f62830e0fbc4bd7a19fc31cb88547313
Combined baseline time exit:
635c5bf8b8a50d7ea4cdaed3bab45b72fa020acddde402f910064bc4f9e6bf59
Combined terminal-open simulator:
3868cb0d5399ce2409f1308c6803cebafae2b555d36db84e792617dfce6b1ab7
Combined terminal-open bracket execution:
08f24a6bb1f1f5719581402f220ed0528198187131f08efc2243bc8a9ec7cb70
Combined terminal-open time exit:
e5a390171aca42218d788bdaa8bf254f392d95b1b39f84d3c1912012eaf032fb
```

Previously frozen indicator, transform, AST, evaluated-signal, condition, and intent identities remain authoritative in their existing checkpoint documents: [Phase 2B AST checkpoint](phase2b_ast_checkpoint.md), [Phase 2A indicator checkpoint](phase2a_indicator_transform_checkpoint.md), and the Phase 2C intent/condition documents.

## Regression checkpoint and deferred scope

Verification commands:

```bash
cargo test --manifest-path engine/Cargo.toml
.venv/bin/python -m unittest discover -s tests
```

Current regression floor: Rust 44 passed; Python 36 passed.

Deferred: spread, commission, slippage, swap, position sizing, trailing stops, pending orders, partial exits, deterministic RNG streams, baseline performance metrics, MQL5 translation, MT5 parity, searchable grammar, and Phase 3 search. Search remains blocked until the complete Phase-2 Rust↔MT5 parity gate passes.
