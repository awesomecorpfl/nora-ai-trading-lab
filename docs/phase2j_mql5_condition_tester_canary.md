# Phase 2J: MQL5 condition tester canary

## Verdict: PASSED (narrow canary)

The startup-script route remains historical blocked evidence: both `EURUSD` and the accepted `GDAXI` chart opens failed before script execution. This tester pivot adds a no-trading EA wrapper over the same frozen nullable-condition fixture; it does not replace the historical evidence.

The prior blocked tester run reached only tester startup and then synchronized unrelated symbols; it did not prove the EA loaded or `OnInit` ran. The generated config used a literal double separator in `Expert=NoraPhase2J\\NoraPhase2ConditionTesterCanaryV1`. The repair emits `Expert=NoraPhase2J\NoraPhase2ConditionTesterCanaryV1`; the tester-agent journal proves that exact Expert was added and tested.

The regenerated deterministic tester fixture has source SHA-256 `2d9dd772d35be45d3fce07da275f7fb22479e54d0d4cdc2cf20ff1440d6f5c1e` and identity `583fe60539d2da2cb46f054d9800d7702efd577b6984d23757794ca91ab259e6`. This supersedes only the historical tester source `26f3edff9d85e95d4de8d63aeb85a049c2aae695a22ecca6f65e6be2d978bdf9` and identity `11523b0a2c0a5d8e557aa3623ffcb518e2d4d67eec0ee6d6556afc18319e8d2c`; runtime, condition, and AST identities are unchanged.

The EA has no trading, account, market-data, tick-value, indicator, or order API. It waits for its first tester tick, evaluates the twelve embedded fixture rows once, writes the common ANSI CSV with `FileFlush`, logs completion, and calls `TesterStop`.

Two independent repaired MetaEditor compilations succeeded with zero errors/warnings:

```text
b5e742389fe0daad3c16fb5d3ab92f670fff81eae2047c1ed59b3c9b0023664f (12596 bytes), compile identity f127389b2bf81c9fadf6c07c8b1557379015ed9782daad74d990fc2230c23266
1ea9245a8c25552e7a8710f08a22a8a37abe800b4f65cf0e04b2448cb0cbd9e3 (11678 bytes), compile identity 1850784121a80315b8ca48de8a7685ac7d7f8aad1745c9e8acea94a0e0f007df
```

`FILE_COMMON` published to the data-root-derived `C:\Users\Gasper\AppData\Roaming\MetaQuotes\Terminal\Common\Files`, not the prior ProgramData assumption. Each repaired run removed the old result, staged the Expert at `MQL5\Experts\NoraPhase2J\NoraPhase2ConditionTesterCanaryV1.ex5`, used the exact single-separator Expert line above, and observed `NORA_PHASE2J_EA_INIT_ENTER`, `NORA_PHASE2J_FILE_OPEN_OK`, `NORA_PHASE2J_FIXTURE_BEGIN`, `NORA_PHASE2J_CSV_FLUSHED`, `NORA_PHASE2J_FIXTURE_PASS`, and `NORA_PHASE2J_TESTER_STOP_REQUESTED` in the tester-agent journal.

Both CSVs have SHA-256 `9c6d6087a669a460b1b90054540741d495e993c9a8fe798aba420948f42755ba`, vectors `[null,null,false,true,true,true,true,true,true,true,true,true]` and `[false,false,false,true,true,true,true,true,true,true,true,true]`, and reconciliation `row_count=12`, `passed_rows=12`, `failed_rows=0`, `overall_pass=true`. Execution identities are `eedc9d10e595284db70b1fd17d8811c375ab7950bb6c8a9dfd2cba9aba3d9cac` and `d5bf1903a741b496d0a4b955de50c7ea5bbe353e852adf97809a3ef51c358985`; both semantic-result identities are `b66f60ad5ae4cc036d29197063e2dbe355cafac96085c359e92783ac74da74e4`.

The frozen nullable-condition fixture passed in native MQL5 through the MT5 Strategy Tester.

This proves only the accepted nullable-condition AST fixture.
Indicator parity, transform parity, execution-simulator parity, the complete Phase-2 parity gate, and Phase 3 remain open.
