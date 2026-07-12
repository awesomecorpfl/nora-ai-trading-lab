# Phase 2J: MQL5 condition tester canary

## Verdict: BLOCKED

The startup-script route remains historical blocked evidence: both `EURUSD` and the accepted `GDAXI` chart opens failed before script execution. This tester pivot adds a no-trading EA wrapper over the same frozen nullable-condition fixture; it does not replace the historical evidence.

The generated tester fixture is deterministic and binds the frozen runtime, condition, AST, Phase-2H evidence fixture, ordered input rows, expected vectors, CSV schema, source bytes and source hash. Its source is `NoraPhase2ConditionTesterCanaryV1.mq5`, source SHA-256 `26f3edff9d85e95d4de8d63aeb85a049c2aae695a22ecca6f65e6be2d978bdf9`, and identity `11523b0a2c0a5d8e557aa3623ffcb518e2d4d67eec0ee6d6556afc18319e8d2c`.

The EA has no trading, account, market-data, tick-value, indicator, or order API. It waits for its first tester tick, evaluates the twelve embedded fixture rows once, writes the common ANSI CSV with `FileFlush`, logs completion, and calls `TesterStop`.

Two independent MetaEditor compilations succeeded with zero errors/warnings:

```text
5b8b6d28bd7a2553770974052e90069d95500a7d598d107fc8a63dc5332b00b4 (11912 bytes)
41973191d2a1cee0684f1f5a5224f7f6e7f0c50a02df5724cb883f1862d5d608 (11590 bytes)
```

The first Phase-0A-boundary tester launch did not publish the fresh common CSV and remained active until bounded completion handling. No passed execution manifest, CSV, execution identity, or semantic-result identity was published; the second run was not started.

No native nullable-condition semantic canary has passed yet.
The complete Phase-2 Rust↔MT5 parity gate remains open.
Phase 3 remains blocked.
