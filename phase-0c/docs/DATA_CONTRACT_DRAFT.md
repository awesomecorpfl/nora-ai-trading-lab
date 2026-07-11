# Phase 0C data-contract skeleton — unresolved pending evidence

- Canonical store: lab-owned UTC M1 Parquet; not created in this phase.
- M1 convention, source timezone, DST transform, session model, gap/duplicate/malformed policies: **UNRESOLVED pending matched exports**.
- Higher timeframes: derived internally from canonical M1.
- Raw → hashed staged source → validation → canonical is the intended boundary; only raw/staged analysis exists here.
- Provider identity, broker-reference identity, symbol mapping, tick role, broker-spec provenance and data/spec change detection are required provenance fields; no provider is selected.
- QDM is Fedora-side acquisition/inspection/export tooling only; it is not provider, canonical store, or runtime dependency.
