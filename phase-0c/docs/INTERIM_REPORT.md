# Phase 0C interim report

## Assets

No repository market dataset exists. Older Fusion M1/tick CSVs were found only in a discarded legacy research tree and are reference examples, not inputs. Darwinex MT5 has the built-in `SymbolInfo*` examples but no installed extractor or exports.

## Exact QDM exports needed

Provider: select/export **Dukascopy** through QDM if available (provider must remain recorded as Dukascopy; tool as QDM). Export CSV to `phase-0c/staged/qdm/` (not committed), UTC timestamps, no DST transformation, comma-delimited header. M1: EURUSD and GBPJPY for the long and DST/weekend windows above; XAUUSD only if symbol mapping is available. Ticks: EURUSD and GBPJPY for the bounded window above, preserving bid/ask and maximum available timestamp resolution.

Gasper should record QDM version, provider/source symbol, export dialog settings, and whether bar time denotes start or end. Do not transform data manually before staging.

## Darwinex reference required later

Export a small UTC/broker-time-documented tick sample for the same tick window and a symbol-spec JSON/CSV containing the fields in `COMPARISON_PROTOCOL.md`. The terminal's built-in SymbolInfo examples show the API direction, but no project extractor is installed.
