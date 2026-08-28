---
title: "Publication & Recovery"
linkTitle: "Publication & Recovery"
date: 2026-08-08
lastmod: 2026-08-24
authors: [Vonng]
description: "The target-scoped state machine for publishing, recovering, retaining, and safely deleting repository objects."
categories: [Design]
tags: [publish, transaction, object-storage]
url: "/blog/design/publication/"
aliases:
  - "/docs/design/publication/"
weight: 40
icon: fa-solid fa-arrows-rotate
draft: false
---

Building and publishing are separate state transitions. A build produces a target-neutral
Generation. Publication applies that Generation to one provider prefix and records enough
evidence to recover without guessing.

## Ownership split

| Repository-scoped | Target-prefix-scoped |
|---|---|
| Package Object | Publication Attempt |
| Desired and Built state | Applied Checkpoint |
| Generation and Changeset | Remote inventory |
| Retained payload/metadata references | Grace and deletion evidence |

The split prevents a successful filesystem publication from being treated as proof about
R2, and prevents one target's partial attempt from contaminating another target.

## Durable target identity and rebind

A target has two nested identities. Storage identity covers provider, endpoint, region, and bucket;
target identity adds the public-tree prefix. Repository identity, both target identities, and the
three authority acknowledgements are immutable after the first bind. This is what lets attempts,
checkpoints, grace, and maintenance survive a configuration-file edit without being reinterpreted
as evidence for another namespace.

Target name, `public_endpoint`, and `max_cache_ttl` are mutable only through explicit
[`publish --rebind`](/docs/command/publish/#rebind-mutable-target-settings). Initial bind, migration
backfill, and every accepted rebind append an immutable binding revision. Rebind holds the same
exclusive locks as publish and rechecks immutable fields inside the transaction; changing storage
or prefix requires a new target.

Pending target maintenance freezes TTL in both directions. A filesystem conditional-delete
workflow also freezes `public_endpoint`. Changing the current TTL never rewrites historical grace:
deletion eligibility is the later of the stored deadline and the applied checkpoint plus the
current grace minimum.

## Publication phases

```text
plan
  -> create-only payload
  -> checksum-addressed metadata
  -> durable commit intent
  -> protocol pointers, one view at a time
  -> provider and canonical public verification
  -> applied checkpoint
  -> grace
  -> evidence-gated deletion
```

Before commit intent, only add-only objects may be written. `publish --abort` may reconcile
and remove private filesystem staging, but it does not delete remote objects. Exact
abandoned-object evidence is retained so a later attempt can safely recognize and reuse
matching bytes.

Commit intent is persisted before the first mutable APT stable alias or protocol pointer.
After that point, the only recovery direction is forward. Object stores do not provide a
multi-key atomic commit, so SOW permits a bounded mixed-generation window while it rolls
individual views forward in a deterministic order.

## Pointer order

Within a view, immutable content is installed first. Signature companions are installed
before their corresponding mutable pointer. Examples:

```text
RPM: checksum-named repodata -> repomd.xml.asc -> repomd.xml
APT: by-hash/direct indexes -> Release.gpg -> InRelease/Release
```

A client that sees a new pointer can therefore reach every object and signature it names.

## Public verification

Routine publication verifies the exact changed closure and every affected final pointer; it does
not publicly download every unchanged package. Provider receipts and public visibility are separate
proofs. Filesystem and R2 HTTP(S) targets share a canonical-GET verifier with independent response
header and body-idle deadlines, a size-plus-one oversize guard, short bounded retries for transient
408/425/429/5xx responses, and cache-TTL retries for stale content or missing objects.

No-cache requests are revalidation hints only. A later ordinary canonical GET must observe the
expected bytes before publication can checkpoint. For filesystem conditional deletion, HTTP 404 or
410 proves public absence; a stale 200 is retried through the TTL. `file://` instead uses exact,
descriptor-bound absence. R2 public absence and remote deletion remain disabled.

Filesystem aliases are checked on prospective canonical paths before durable bind, including case
aliases on case-insensitive volumes. A failed backend/path preflight creates no binding row and no
target prefix.

## Published-pointer fence

Once a configured target has an Applied Checkpoint, local configuration cannot silently
withdraw a public Dist, architecture, or signing pointer that target still owns. The
operator must first retire or unbind the target, or publish a replacement under a new name
and prefix.

This turns a dangerous omission into an explicit lifecycle decision.

## Retention without payload copies

A retained Generation stores metadata, manifests, and reference sets — not another package
tree. Repository-local reachability includes:

- current Desired/Built memberships;
- retained Generation references;
- active operation and recovery journals;
- publication grace and recovery roots.

Local garbage collection may remove a canonical Pool object only when it is outside that
complete closure and the exact file identity still matches the recorded candidate.

## Remote deletion is a capability

Remote physical deletion additionally requires authoritative inventory, target ownership,
grace expiry, cache-absence evidence when applicable, and an atomic conditional delete
primitive. A provider that cannot satisfy the primitive can still publish, but SOW must
report unreachable candidates rather than issue an unsafe unconditional delete.

The `r2` provider is handled this way: publication is implemented, while remote physical
deletion is deliberately disabled and target GC remains report-only.

## Recovery outcomes

| Durable boundary | Legal outcome |
|---|---|
| No commit intent | reconcile, then abort or retry |
| Commit intent present | roll forward only |
| Applied checkpoint present | converge and enter grace |
| Evidence contradicts | fail closed; do not invent state |
