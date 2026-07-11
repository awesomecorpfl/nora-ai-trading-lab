# QDM CLI discovery (2026-07-10)

## Installed application

| Item | Observed value |
| --- | --- |
| Application directory | `/home/gasper/Applications/QDataManager` |
| CLI invocation | `./qdmcli` from that directory |
| CLI binary | executable x86-64 ELF launcher |
| Application build | `125.2692` (reports itself as QuantDataManagerPro Build 125) |
| CLI help | `internal/web/QDM/help.txt` within the installed application |
| Shared application state | `user/data/data.db`, `user/settings/`, and `user/log/QuantDataManager/` below the application directory |
| Java launcher configuration | `qdmcli.config`; runtime/VM options only, not provider or symbol settings |

The CLI and GUI use the same application-local `user/` state directory.  QDM starts a local command server on port 5050 for each CLI invocation; the installed GUI log and command-line process both identify the same application data root.  This is evidence of shared symbol/data/settings state, rather than an inference from product naming.

## Verified commands and capabilities

The bundled help documents `-symbol`, `-instrument`, `-data`, `-run`, `-gui`, `-deletefile`, and `-waitfor`.  The following were executed successfully against this installation:

```text
./qdmcli -license action=info
./qdmcli -symbol action=list
./qdmcli -instrument action=list
./qdmcli -data action=timezones
```

The documented commands support symbol list/add/edit/delete/clear, provider selection (`dukascopy` included), M1 or tick symbol type, instrument listing, data update/import/export, date-bounded export, CSV format selection/custom columns, output directory selection, and named time zones including `Etc/UCT`.

The instrument listing contains `EURUSD_dukascopy`, `GBPJPY_dukascopy`, and `XAUUSD_dukascopy`.  The Phase 0C configuration deliberately uses only EURUSD and GBPJPY.

## Minimal QDM configuration created

Created entirely through the CLI:

```text
./qdmcli -symbol action=add symbols=EURUSD,GBPJPY datasource=dukascopy datatype=M1 bartype=startofbar
./qdmcli -symbol action=add symbols=EURUSD,GBPJPY datasource=dukascopy datatype=TICK
```

QDM's subsequent list identifies these local configurations as:

```text
EURUSD      EURUSD  M1    Dukascopy
EURUSD(2)   EURUSD  TICK  Dukascopy
GBPJPY      GBPJPY  M1    Dukascopy
GBPJPY(2)   GBPJPY  TICK  Dukascopy
```

No GUI setup was required.  These configurations are QDM-local acquisition setup; they are not MT5 settings and they do not change the Darwinex VM.

## Bounded-acquisition finding and blocker

The CLI help presents `datefrom` and `dateto` as general `-data` arguments, but its only documented update examples have no date range.  A bounded update was tested:

```text
./qdmcli -data action=update symbols=EURUSD,GBPJPY timeframe=M1 \
  datefrom=2024.01.01 dateto=2025.12.31
```

QDM accepted the command but immediately began downloading and writing its full available historical range (starting around 2003–2005), rather than the requested 2024–2025 interval.  The process was terminated at approximately nine percent of its write pass.  A later symbol listing reported zero retained records/date range, so no usable Phase 0C export resulted.  The QDM data directory grew only to 36 MiB and no raw data was copied into the repository.

Therefore the installed CLI proves a **full CLI configuration/export path**, but not a bounded-download path.  Date-bounded **exports** are documented; data acquisition itself appears whole-symbol in this build.  We must not continue the update without an explicit decision to permit QDM's full-history local cache, because that would violate the Phase 0C instruction not to download large unnecessary datasets.

## Export contract once acquisition is authorized

Destination (ignored by git): `phase-0c/staged/qdm/`.

| Symbol | Kind | UTC interval |
| --- | --- | --- |
| EURUSD, GBPJPY | M1 long | 2024-01-01 through 2025-12-31 |
| EURUSD, GBPJPY | M1 spring DST | 2025-03-23 through 2025-04-06 |
| EURUSD, GBPJPY | M1 autumn DST | 2025-10-19 through 2025-11-02 |
| EURUSD, GBPJPY | M1 weekend/session | 2025-06-06 20:00 through 2025-06-09 04:00 |
| EURUSD, GBPJPY | Tick | 2025-06-03 08:00 through 12:00 UTC |

Provider identity will be recorded as **Dukascopy** and acquisition-tool identity as **Quant Data Manager**.  The target is comma-delimited CSV with a header, UTC output (`Etc/UCT` if the CLI export behavior confirms it), no fixed-hour shift, preserved bid/ask, and the highest timestamp precision exposed by the selected QDM CSV format.  The exact bar timestamp convention and any undocumented timezone transformation remain explicitly unknown until a real export is inspected.

## Final bounded-tick outcome (2026-07-11)

The provider-specific Dukascopy GUI path was used after the M1 synchronization. It exposes a date selector, not hour-level bounds. With **Add only missing data**, it therefore acquired exactly the single UTC date `2025-06-03` for the existing tick symbols, rather than full tick history:

| Local QDM symbol | Provider/source symbol | Records acquired |
| --- | --- | ---: |
| `EURUSD(2)` | Dukascopy `EURUSD` | 93,516 |
| `GBPJPY(2)` | Dukascopy `GBPJPY` | 118,558 |

The CLI exported only that existing date, in `Etc/UCT`, using custom CSV `Date,Time,Bid,Ask` and `[Time:HH:mm:ss.SSS]`. The Phase 0C analysis then used only a derived 08:00:00.000–12:00:00.999 UTC slice. This is date-level acquisition and four-hour analysis; it is not a full-history tick synchronization.
