# Phase 2A-1A: canonical Parquet reader

The reader reuses the Phase-1 `lab.core.ingest_csv` wire format exactly: UTF-8
`timestamp`, Float64 `open`, `high`, `low`, `close`, nullable Float64 `volume`
and `spread`, plus the `nora.contract`, `nora.source_sha256`, and
`nora.timeframe` schema metadata keys.  No Parquet is rewritten and no timestamp
is converted.  The string timestamp remains the declared-clock label; a
`NaiveDateTime` is parsed only to enforce strict label ordering.

Phase 1 did not serialize a `contract_version` or `schema_version`; its
unversioned `nora.contract` object is therefore the supported legacy version 1.
If either field is supplied, it must be an unsigned integer equal to 1 (and the
two fields must agree).  The reader validates every Phase-1 required contract
field, conversion history, and optional later declarations for trading-day
boundary, higher-timeframe anchoring, and double-conversion protection.  Those
three optional declarations are exposed as `Option` values because the actual
Phase-1 writer did not require or synthesize them; the reader never invents
their meaning.

`content_identity` is SHA-256 over a length-delimited domain tag, canonical
JSON contract (JSON object keys are normalized by `serde_json`), each original
timestamp label in row order, and the IEEE-754 bits plus null markers for OHLC,
volume, and spread.  It intentionally excludes Parquet page layout,
compression, file metadata ordering, and `nora.source_sha256`: those can vary
without changing canonical market semantics.  This makes the identity stable
across repeated reads without requiring byte-identical rewritten Parquet.
