# Phase 2A-1 plan

`labengine` will be split into data/contract, time/session, aggregation and task-output modules. It will read Phase 1 Parquet metadata (`nora.contract`, `nora.timeframe`, `nora.source_sha256`) and validate `timestamp/open/high/low/close/volume`, the declared contract, ordering and duplicates without conversion. A named contract represents UTC or later broker-time rules; the New-York-plus-seven convention is a supported configuration, not a loader action.

Aggregation uses local declared timestamp minutes and contract trading-day/session anchors. Tasks are JSON `validate_dataset` and `aggregate`; output is deterministic JSON plus derived Parquet. Tests will create Phase-1-format Parquet through the existing Python writer, then invoke the Rust binary and publish output through the existing Phase-1 artifact boundary.
