# Phase 2X/2Y gap audit (pre-repair)

| Requirement group | State before repair | Exact boundary |
|---|---|---|
| Expected output vectors, null masks, field schema, vector identity | missing | `lab/phase2x_batch.py::manifest` stores only `row_count` |
| Immutable manifest/preflight | partial | `manifest()` reconstructs validity; `preflight()` has no input contract path |
| Artifact identity/source substitution checks | partial | `preflight()` checks package fields but not source hashes, vectors, or staged inventory |
| Staging determinism/existing destination/cleanup | implemented and tested | `stage`; `Phase2XBatch.test_preflight_and_deterministic_atomic_staging`, `test_existing_and_injected_failure_leave_no_package` |
| Duplicate targets/unexpected files/malformed completion contract | missing | no validator |
| Result identity/compiler/runtime/row-count checks | partial | `lab/phase2y_reconcile.py::reconcile` |
| Columns, null masks, vectors, divergence, tolerance | missing | `reconcile` accepts generic `values` without comparison |
| Non-finite rejection | partial | generic value loop rejects non-finite, without output-field binding |
| Immutable reconciliation evidence/atomic publication | missing | `reconcile` returns an in-memory dictionary |
| Mixed outcomes and complete synthetic matrix | missing | `tests/test_phase2y_reconcile.py` has only two tests |
| Native-parity/grammar/search closure | implemented and tested | target flags in `manifest`; batch and reconcile tests |

The missing vector binding and numeric comparison are concrete implementation
defects in batch identity `97d223ac2e217da907094b07fcc77e8ae97b6c713380c1aa47bf5e475779b23f`.
The next contract revision is therefore allowed to receive a new identity while
preserving all frozen executable-source and Rust identities.
