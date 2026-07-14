# Ten-strategy embedded-fixture tester history-synchronization diagnosis

## Observation

The four canonical native runs (GDAXI/M1 A1, A2 and AUDCAD/M1 B1, B2) completed
and produced byte-identical CSVs, but the captured MT5 tester journals show that
the terminal synchronized broker market history before the EA's `OnInit` ran,
even though the EA consumes only its embedded `NoraBar` fixture arrays and writes
the result CSV from `OnInit`.

Representative journal evidence (run A1):

```
Core 1   connecting to 127.0.0.1:3000
Core 1   connected
Core 1   common synchronization completed
Core 1   login (build 5836)
Core 1   GDAXI: symbol to be synchronized
Core 1   GDAXI: symbol synchronized, 3720 bytes of symbol info received
Core 1   GDAXI: load 25 bytes of history data to synchronize
Core 1   GDAXI: history synchronized from 2019.01.02 to 2026.07.08
Core 1   GDAXI,M1: history cache allocated for 2646736 bars and contains 393092 bars
Core 1   GDAXI,M1: every tick generating
```

## Root cause

The launcher (`phase-0a-h/windows/execute-ten-strategy-packet.ps1`) drives the
strategy tester against a real broker symbol (`GDAXI` or `AUDCAD`) on `M1` with a
six-year date range (`2020.07.01` to `2026.07.01`). Selecting a real
symbol/timeframe in the MT5 strategy tester inherently forces the terminal to
synchronize symbol info and history for that symbol and to allocate the M1
history cache that drives the test's tick stream. This synchronization is a
property of the tester framework and the selected real symbol; it is not caused
by the EA, which reads no market data. The `Environment`/`Login`/`Server`
configured in the installed `backtest_run.ini` cause the agent to log in to the
trade server, after which the selected symbol is synchronized from the
server/cached history.

In particular:

* symbol/timeframe selection automatically triggers synchronization;
* the embedded-fixture EA cannot suppress tester-side history preparation;
* the tester requires a symbol to drive `OnTick`, so it cannot run with no symbol;
* the `UseRemote=0`/`UseCloud=0` settings disable cloud agents but not local
  symbol/history synchronization against the connected server.

## Prevention

Complete prevention without either a custom/offline symbol or host-level network
isolation is not achievable through tester `.ini` configuration alone, because a
real selected symbol is always synchronized. Introducing a custom symbol is out
of scope here (it would add a new local market-data path, which this canary
forbids). Therefore the repository-owned guarantee is **fail-closed journal
detection**: the launcher scans the captured tester-journal segment for a frozen
vocabulary of history-synchronization/download markers and fails the run if any
is present, recording `history_synchronization_detected` and
`history_synchronization_prevention='fail_closed_journal_scan'` in `execution.json`.

The frozen marker vocabulary lives in `lab/native_target.HISTORY_SYNCHRONIZATION_FORBIDDEN_MARKERS`
and is mirrored verbatim in the launcher. A run that touches synchronized
history can no longer be accepted.

The smallest complementary platform-side prevention to attempt on the Windows
host (not required for the fail-closed guarantee) is bounded network isolation
of the tester process during the run, so the terminal cannot reach the trade
server and cannot synchronize beyond its existing local cache; this requires
host-level verification and is deliberately not encoded as untested script here.

## Test coverage

`tests/test_phase2_ten_strategy_atr_parity.py::test_history_sync_detection_rejects_real_tester_journal_and_accepts_clean`
proves the detection rejects the captured A1 journal and accepts a clean one, and
`test_launcher_script_contains_fail_closed_sync_scan` binds the launcher script
to the fail-closed behavior and the frozen markers.
