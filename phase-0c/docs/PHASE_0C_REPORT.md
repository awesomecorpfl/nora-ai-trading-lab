# Phase 0C final report

## Verdict: CONDITIONAL PASS

Dukascopy M1, acquired/exported with Quant Data Manager (QDM), is accepted as the canonical **research M1 provider** for EURUSD and GBPJPY, subject to retaining raw provenance and gap policy. The small Dukascopy tick sample is characterized and usable for research-cost/context checks. It is not broker parity evidence. Darwinex remains the required native-MT5 parity and broker-economics/specification reference, but this phase has no new Darwinex tick/spec export because the tiny MQL5 extractor could not be compiled/run through a supported non-invasive path.

## M1 findings

The two ignored QDM exports directly cover the requested 2024-01-01 through 2025-12-31 window. They were exported in `Etc/UCT`, with start-of-bar configuration and no DST transform.

| Symbol | Rows | First / last | Duplicates / unordered | Bad OHLC / zero volume | Gap events; median / p95 / max |
| --- | ---: | --- | --- | --- | --- |
| EURUSD | 744,789 | 2024-01-01 22:00 / 2025-12-31 21:58 | 0 / 0 | 0 / 0 | 2,574; 120 s / 660 s / 176,460 s |
| GBPJPY | 744,902 | 2024-01-01 22:04 / 2025-12-31 21:58 | 0 / 0 | 0 / 0 | 1,178; 240 s / 173,100 s / 176,760 s |

All parsed bar timestamps are minute-aligned. The raw missing-minute totals (EURUSD 306,410; GBPJPY 306,293) include scheduled weekend/holiday closures and must not be interpreted as an intraday-fill instruction. Weekend rows are expected early Sunday trading: EURUSD 16,157 and GBPJPY 15,703.

The required 2025-06-06 20:00 through 2025-06-09 04:00 UTC check shows Friday close at 20:59 UTC and Sunday reopen at 21:00 (EURUSD) / 21:06 (GBPJPY). Thus the session is not a continuous UTC weekend series. The small GBPJPY delayed reopen and the regular short intraday gaps are retained as provider observations.

The spring window (2025-03-23 through 2025-04-06) remains at the 21:00 UTC Sunday opening convention, including the European DST date; there is no one-hour duplicated/skipped M1 timestamp. The autumn window shows the expected provider-session move: 21:00 UTC Sundays on October 19/26 and 22:00 UTC on November 2, again with no timestamp duplication. This is session behavior expressed in UTC, not an export DST conversion. Production evaluation must therefore support explicit broker-time/DST rules rather than assume a UTC-only strategy clock.

Long-window discontinuities above one hour outside Friday-to-Sunday session transitions were limited to: a roughly 66–67 minute 2024-10-09/10 interruption, Christmas partial-day closures (about 14.1 h), and New Year closures (about 24.0 h). They are flagged for calendar/session treatment, not repaired.

Complete machine-readable results: `results/m1/`.

## Dukascopy ticks

The Dukascopy provider import UI was date-granular. It acquired 2025-06-03 only (not additional history) with add-only-missing-data. QDM then exported the full day in UTC custom CSV with `Date`, millisecond `Time`, `Bid`, and `Ask`. The analysis uses only a derived, hashed 08:00:00.000 through 12:00:00.999 UTC slice.

| Symbol | Full-day acquired | Four-hour quotes | Endpoint range | Duplicate / unordered | Missing bid/ask / crossed | Spread min / median / p95 / max | Positive delta min / median / p95 / max | Gaps >1 s (median / p95 / max) |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| EURUSD | 93,516 | 19,817 | 08:00:00.635–12:00:00.975 | 0 / 0 | 0 / 0 | 0.00001 / 0.00004 / 0.00006 / 0.00012 | 0.052 / 0.256 / 2.888 / 15.101 s | 1.666 / 5.156 / 15.101 s |
| GBPJPY | 118,558 | 21,864 | 08:00:00.177–12:00:00.905 | 0 / 0 | 0 / 0 | 0.004 / 0.018 / 0.026 / 0.034 | 0.051 / 0.205 / 2.678 / 15.807 s | 1.726 / 4.995 / 15.807 s |

The CSV supports millisecond display; observed positive timestamp deltas bottom out at 51–52 ms in this interval. No obvious malformed/crossed-quote anomaly occurred. Quote gaps up to roughly 16 seconds are present and remain visible in the reports. These are Dukascopy-provider observations only; no claim of provider-to-Darwinex parity is made.

## Darwinex reference result

The existing dedicated Windows VM and `C:\Program Files\Darwinex MetaTrader 5\terminal64.exe` were read-only verified. A minimal `SymbolInfo*` plus bounded `CopyTicksRange` script is technically suitable, but the established environment record says MetaEditor command-line compilation is broken and requires GUI compilation. Building/deploying a new remote execution harness or changing the terminal workflow would be a material detour and was not done.

Evidence gap: no Phase 0C Darwinex EURUSD/GBPJPY symbol-spec snapshot or 2025-06-03 08:00–12:00 broker tick extract exists. Before a broker-parity decision, manually compile/run a one-shot, read-only MQL5 script that writes those `SymbolInfo*` fields and bounded `CopyTicksRange` values to `MQL5/Files`; record server/broker timezone semantics and hashes. No broker login, terminal architecture, validation harness, or trading configuration should change.

## Recommendations and limitations

- Use **Dukascopy** for canonical research M1; use **Quant Data Manager** only to acquire/export it.
- Use **Darwinex MT5 native history** for final parity checks and **Darwinex SymbolInfo/broker metadata** for execution economics, contract details, swaps, margin and sessions. They are distinct reference roles from the research provider.
- Research tick spreads are descriptive, not Darwinex trading costs. Commission, swap, slippage, margin and broker session rules require the Darwinex reference capture.
- The date-level tick acquisition limitation is documented in provenance. The four-hour analysis is intentionally a derived slice, not a claim that the provider imported only four hours.
- The staged raw files are ignored; committed JSON reports and provenance make the findings reproducible without placing market data in Git.
