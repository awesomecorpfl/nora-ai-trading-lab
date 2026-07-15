# Phase-2 containment atomic evidence contract

Containment-case evidence is published with schema
`nora.phase2_containment_atomic_evidence_v1`.  The repository-owned
`lab.phase2_containment_evidence` module is read-only with respect to firewall
state: it packages artifacts that have already been captured by the Windows
transaction and verifies their bytes on Fedora.

Each package is a deterministic ZIP published once by same-directory
temporary-file plus `os.replace`.  It contains canonical `summary.json` and
`manifest.json`, separate `stdout.txt` and `stderr.txt`, pre/post durable and
firewall inventories, process evidence, recovery and cleanup records.  The
manifest records every member's path, size, and SHA-256.  The source tree must
contain all required members before a package is created.

The summary binds the case and expected verdict, unique run ID, repository and
Windows script identities, host/evidence-root and transaction identities,
executable arrays and hashes, fault point, command/wrapper and timestamps,
final-caller exit code, recovery/cleanup results, unrelated-firewall result,
and final invariants.  Executable, rule, and application-filter fields are
always arrays, including zero- and one-item cases.

Publication is immutable.  Repeating a publication with identical bytes is an
idempotent success; a conflicting destination fails nonzero.  Verification
opens the archive, rejects unsafe or duplicate member paths, validates schema
and identity, checks the required member set, and independently recomputes
every member hash.  It never creates, enables, disables, deletes, or changes a
firewall rule.

This contract closes an evidence gap in the earlier containment work: the
existing native campaign package builders and Windows forensic copier did not
provide a containment-case schema, immutable duplicate policy, separate
stdout/stderr binding, or a Fedora-side member verifier.
