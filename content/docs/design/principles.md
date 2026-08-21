---
title: "Design Principles"
linkTitle: "Principles"
description: "The invariants SOW uses to keep ownership, generated state, publication, and evidence understandable."
categories: [Design]
tags: [plain, managed, repository]
url: "/docs/design/principles/"
weight: 100
icon: fa-solid fa-ruler-combined
---

SOW is not primarily a metadata generator. It is an ownership and state-transition system
whose output happens to be APT and RPM repositories. The following principles keep that
system small enough to reason about.

## One owner for every durable fact

Every durable fact has one scope and one authority:

| Fact | Owner |
|---|---|
| Package bytes and package identity | Repository |
| Desired memberships and Built state | Repository |
| Generation and Changeset | Repository |
| Publication attempt and applied checkpoint | Repository + target prefix |
| Remote inventory, grace, and delete evidence | Repository + target prefix |

State is not silently shared across Repositories or publish prefixes. The same package may
therefore exist once in each Repository or target. That is intentional: local deduplication
must not create distributed ownership.

## Canonical data, rebuildable projections

Managed package bytes in `pool/` are canonical data. In Plain mode, the top-level package
files are canonical instead. Protocol indexes, architecture views, reports, and compatibility
exports are projections; they never become a second owner of package bytes.

The durability rule follows the authority. Managed removes a projection through its recorded
operation and removes canonical data only after reachability across every live and retained
owner. Plain simply regenerates its owned index paths from the current package directory.

## The public tree is the delivery unit

A Repository root contains `pool/ + dists/`. That complete tree is the unit for static
hosting, copying, authorization, and publication. A single RPM architecture leaf is a
client view, but it is not an independently owned Repository.

Private state such as `sow.yml`, `.sow/`, locks, journals, credentials, and recovery files
must never be served as part of that tree.

## Pointers commit; payloads prepare

Publication follows this order:

```text
payload -> immutable/checksum-named metadata -> mutable pointer -> grace -> delete
```

Payload and immutable metadata may arrive before they are visible. A protocol pointer such
as `repomd.xml`, `Release`, or `InRelease` is the commit boundary. Nothing is deleted until
the new pointer is durable and the old reader/cache window is closed.

## Recovery cost follows state cost

Plain has no desired-state history to preserve. Its cheapest correct recovery is a fresh
one-pass scan and overwrite rebuild, so it stores no transaction journal and does not spend
package-size I/O proving an old attempt.

Managed state is different. Before commit intent, an operation may be abandoned if exact
reconciliation proves that no public pointer changed. After commit intent, recovery is
forward-only. Managed does not guess whether a half-finished publication "probably worked";
it compares journals, manifests, checkpoints, provider identities, and the public tree.

Contradictory evidence stops the operation. A visible refusal is safer than an invisible
fork in repository history.

## Compatibility is a matrix

Standards compliance, ordinary client behavior, mirror-tool behavior, object-storage
layout, proxy normalization, and filesystem semantics are different questions. SOW records
them separately and uses a real client or provider for the claim being made.

The canonical Repository and an exported RPM mirror leaf are therefore separate artifacts;
evidence for one does not establish compatibility for the other.

## Evidence never upgrades itself

A specification is not implementation. A unit test is not a live-client result. A local
Hugo build is not a published site. A dated result remains attached to its source revision,
environment, and version; it cannot be reused as a PASS for a later layout without rerunning
the relevant gate.

## Non-goals keep the model honest

The current contract does not promise cross-Repository deduplication, overlapping writers,
bucket-global coordination, arbitrary third-party mirror compatibility, or safe remote
deletion on providers without an atomic conditional delete primitive. Excluding these is
part of the safety contract, not an unfinished implementation detail.
