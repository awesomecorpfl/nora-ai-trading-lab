# Phase 2 multi-operation evidence architecture

Status: accepted architecture decision for implementation. This decision covers
containment evidence only and does not complete Phase 2 or authorize search.

## Decision

Use immutable authoritative operation packages plus one immutable case envelope.
An operation package proves one executed operation. A case envelope proves the
ordered, causal relationship among all operations required for one acceptance
case. Formal case credit requires both independently verified operation packages
and a verified final envelope.

The alternative—a case-level executor that duplicates capture and publication—
was rejected. It would create a second operation-capture boundary, make partial
failure evidence harder to preserve, and require a larger migration away from
the existing atomic Windows ZIP and Fedora retrieval contracts.

## Trust and artifact boundaries

1. The Windows runner executes and captures one operation into a private capture
   directory. The operation summary binds a distinct `case_id` and
   `operation_id`.
2. The Windows publisher independently validates the capture and atomically
   publishes an immutable operation ZIP. The ZIP manifest binds both identities.
3. The case-envelope builder reads every referenced ZIP, independently verifies
   its bytes, manifest, identities, exit, verdict, repository commit, and
   component hashes, then atomically publishes canonical envelope JSON.
4. The Windows reader is read-only. The Fedora retrieval transaction verifies
   size and SHA-256 before atomically publishing a local copy and immutable
   receipt.
5. The Fedora verifier independently revalidates every retrieved operation ZIP,
   retrieval receipt, and envelope reference. Verification is read-only.

Operation packages and envelopes are immutable. Identical repeat publication is
idempotent; conflicting publication fails without overwrite. A partial case may
retain valid operation packages, but cannot receive case credit until the full
envelope validates.

## Ordering and relationships

The envelope contains a declared sequence and ordered operation entries. Each
entry has one predecessor (null only for the first operation) and a causal
relationship. Cleanup and recovery are operations in their own right. A reuse
operation after cleanup names the cleanup operation as predecessor; its own ZIP
does not claim that cleanup occurred within the reuse command.

The same model represents interruption boundaries and concurrency: an
interruption is an operation with its durable pre/post digests and failure stage;
concurrent owner and loser operations share a concurrency relationship and bind
separate packages and exits. No schema redesign is required.

## Compatibility and migration

Existing `nora.phase2_containment_atomic_evidence_v1` ZIPs without a distinct
`operation_id` remain immutable diagnostic evidence. They cannot be included in
a v1 case envelope. New operation packages retain the ZIP schema and required
members but bind `case_id` to the outer case and `operation_id` to the individual
operation. Prior readiness remains incomplete and non-searchable.

## Acceptance implications

The envelope proves composition; it does not replace operation evidence. Missing,
duplicate, reordered, foreign, substituted, or conflicting packages fail closed.
Cleanup, recovery, retrieval, and later successful commands cannot mask an
earlier operation or infrastructure failure. This architecture alone grants no
formal containment acceptance.
