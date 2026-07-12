# Phase 2Q native ATR/Distance-ATR evidence

The original native evidence committed at `021ac6d45e0624dd379be79a099022d22c12abd9` is valid and unchanged. Native MetaEditor and terminal commands, timestamps, CSV freshness relationships, hashes, and semantic results were captured contemporaneously by the native manifests.

The Fedora wrapper commands were reconciled afterward from the committed compile and execution manifests. This reconciliation is explicitly classified as `post_run_reconciled_from_committed_command_record`; it is provenance bookkeeping, not contemporaneous native evidence and does not imply a native rerun.

The raw Windows-generated CSV, logs, lifecycle records, and tester configurations are byte-preserved. Their narrow path-specific `.gitattributes` policy marks them non-diffable/non-text so Git does not interpret generated CRLF/trailing-space bytes as source whitespace. Normal source, documentation, manifests, and tests remain subject to ordinary whitespace checks.
