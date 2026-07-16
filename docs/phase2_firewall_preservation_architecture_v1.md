# Phase-2 firewall preservation architecture v1

Status: prospective contract. It does not complete Phase 2 or authorize search.

## Decision

Use Option C: current semantic invariants plus an immutable case-relative
baseline. Historical drift is retained and reported, but is not an execution
gate unless it violates a current invariant.

The transient digest `2cd05921dffd76aa5e671bd54b030746a98a2ac002c777ef16582774937875e3`
remains unexplained and uncredited. Its inventory was never retained. The
legacy digest `4ddb062a0c72fc27b165d25662bafebe8ca22d3fc1a0c7b15a06715a373ba5b4`
is a six-field projection (name, enabled, direction, action, profile, group),
not a security baseline. Reproducing it does not automatically establish a
safe current state.

## Three layers

1. Preflight validates all firewall profiles, rule ownership, Nora namespace,
   exact executable allow predicates, filter cardinality, and deterministic
   canonicalization.
2. A case binds one immutable complete baseline. Every operation binds that
   baseline plus pre/post semantic, unrelated-rule, profile, Nora-rule, and
   legacy digests. Final equality is exact for the canonical scope; the
   expected Nora lifecycle is evaluated separately.
3. Campaign history and the legacy projection are forensic comparisons only.

## Capture-campaign ownership

Complete-inventory stability campaigns use `nora.phase2_firewall_campaign_v1`.
Each campaign has a caller-supplied immutable campaign ID and an atomically reserved
root at `firewall-campaigns/<campaign-id>`.  The root contains an immutable owner
record before the first capture.  It binds the host, user, reserving process and
start time, command identity, repository commit, capture-tool identity, capture
count, and sequencing interval.

Capture slots are ordered, one-based immutable claims.  A slot claim is an atomic
file publication and is rejected if a claim, receipt, or final capture already
exists.  The capture tool writes only to a unique campaign-scoped temporary file;
the campaign owner publishes it to the final slot path through an atomic same-volume
move, then writes an immutable receipt binding the claim, owner, temporary and final
artifact identities, implementation identity, order, timestamps, byte size, and
hash.  A failed capture is explicitly classified as a partial and cannot silently be
reused.  Completion requires every ordered slot, every receipt, one owner and one
implementation identity, and no partial state.  The independent Fedora verifier
rejects missing, duplicate, reordered, substituted, foreign-owner, or mixed-identity
campaign members.

## Policy-store and trust boundaries

The inventory retains `ActiveStore` as effective merged policy and
`PersistentStore` as the local ownership view. Profiles are captured from the
active policy. Nora rules are those whose internal name or group begins
`NoraPhase2Containment-`; only PersistentStore Nora rules with exact expected
names and application paths may be owned by cleanup or recovery.

Windows captures raw policy through NetSecurity cmdlets. Canonicalization and
invariant verification are independently repeated on Fedora. Operation ZIPs
and the ordered case envelope remain the evidence architecture; firewall
artifacts are immutable references, not a replacement for operation packages.

## Canonicalization

Schema `nora.phase2_firewall_inventory_v1` uses UTF-8 canonical JSON (sorted
keys, compact separators, one trailing LF) and SHA-256. Enums are lowercase;
Booleans are JSON Booleans; missing scalars are null; collections are arrays.
Windows paths use backslashes, remove redundant separators, and compare
case-insensitively by a stored lowercase canonical form. Filter arrays are
deduplicated and ordinally sorted. Rules sort by store view, policy source
type, policy source, instance ID, and internal name. Duplicate stable
identities or multiple associated scalar filters fail closed.

The semantic digest includes profiles, effective rules, and persistent rules.
The unrelated digest excludes the Nora namespace. A separate Nora digest
retains its lifecycle. The profile digest covers all canonical profile fields.

Localized display name, localized description, runtime status/status code,
primary status, enforcement status, and capture time are retained under
`diagnostics` but excluded from semantic equality: they do not define packet
policy or ownership and are demonstrably presentation/runtime metadata.

## Invariants

Preflight fails if any Domain, Private, or Public profile is absent or disabled;
profile/default-action data is unavailable; an enabled allow rule explicitly
targets terminal64.exe, metatester64.exe, or a qualified Nora path; any Nora
rule already exists; Nora identities are duplicated, foreign, contradictory,
or outside PersistentStore; a filter association is ambiguous; a stable
identity has differing semantics; or repeated capture changes.

Unrelated allow rules that do not target containment paths are permitted.
Cleanup and recovery must prove exact Nora name/GUID/path ownership and exact
pre/post equality of unrelated and profile digests.

## Migration

Legacy packages and envelopes remain immutable and valid for what they proved,
but do not prove this complete contract. They are never retrofitted. All future
terminal-state matrix cases require v1 firewall-preservation bindings. The
previous abandoned case remains architecture evidence and requires a fresh
complete-contract case for final firewall-preservation credit.

## Future native-testing policy

Phase-2 containment acceptance proceeds with the identified MetaTester inbound
allow rule disabled. FR-T1 and native MT5 work must first be attempted while it
remains disabled. It may never be enabled automatically. If a later authorized
native test proves it indispensable, a separate human-authorized, time-bounded
case must capture complete pre-state, enable only the exact GUID and verified
scope, run only the authorized test, disable it again, prove exact restoration,
and publish its own immutable operation packages and case envelope.
