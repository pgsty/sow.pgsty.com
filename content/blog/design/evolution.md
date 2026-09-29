---
title: "SOW Design Evolution: From Route Graphs to the Repository Core"
linkTitle: "Design Evolution"
date: 2026-08-10
lastmod: 2026-08-28
authors: [Vonng]
description: "How v0.1 was retired, v0.2 shipped the single-payload Repository core, and v0.3-v0.4 hardened it."
categories: [Design]
tags: [architecture, repository, migration, decision]
weight: 20
url: "/blog/design/evolution/"
icon: fa-solid fa-code-branch
draft: false
---

This record dates to the 2026-08-10 consolidation of SOW around its Repository core. It
distills the useful decisions from the earlier planning, ADR, review, migration, and
verification trees without turning every intermediate artifact into maintained product
documentation.

Some sealed folders use “v0.2” and “v0.3” for consecutive pre-release design lines. The
version labels below refer only to released Git tags: the C2 hardlink line was replaced
before v0.2.0 was tagged.

The detailed history is preserved in four companion records:

- [The Original v0.1 Program](/blog/design/v01-program/) explains the initial product
  ambition and why its control plane became too broad.
- [The v0.1 Decision Ledger](/blog/design/v01-decisions/) maps every surviving ADR to its
  later fate.
- [What v0.1 Actually Proved](/blog/design/v01-evidence/) summarizes the dated evidence
  without turning test transcripts into maintained documentation.
- [The v0.2 Reset](/blog/design/v02-reset/) records the Plain/Managed product boundary and
  the C2-to-single-payload correction before the release tag.

## The short history

| Line | Design center | Historical status |
|---|---|---|
| v0.1 | Git/CAS ownership, route-aware materialization, edge authorization, provider workflows, and Pigsty migration | Released as v0.1.0; superseded |
| v0.2 | Local Plain/Managed engine, Repository-scoped single-payload tree, metadata-only views, retained Generations, and target-scoped publication | Released as v0.2.0; public layout remains current |
| v0.3 | V1 removal, package-facts caching, one-pass Plain builds, and bounded payload commits | Released as v0.3.0; same public layout |
| v0.4 | Single-pass verification, independent RPM trust rings, explicit target rebind, and migration/recovery hardening | Current released baseline when this record was updated |

The exact code and claims for each released line remain available in the
[v0.1.0](https://github.com/pgsty/sow/tree/v0.1.0),
[v0.2.0](https://github.com/pgsty/sow/tree/v0.2.0),
[v0.3.0](https://github.com/pgsty/sow/tree/v0.3.0), and
[v0.4.0](https://github.com/pgsty/sow/tree/v0.4.0) source tags.

## v0.1: useful questions, too many product concepts

The first program explored a broad package-distribution control plane: Git-backed
canonical state, content-addressed storage, Routes and Views, materialized snapshots,
remote providers, edge authorization, legacy migration, and evidence-bound deletion.
Forty-four surviving ADRs, numbered through 0045, and a large verification tree made
individual failure modes explicit.

That work produced reusable safety ideas, but the combined product surface was too large
for the core job. Too many concepts could own or reinterpret the same package bytes and
published paths. Edge, provider, migration, and repository concerns were coupled before a
small local repository model had been stabilized.

The v0.2 reset therefore retired Git as canonical product state, the separate CAS product
layer, route/view/snapshot abstractions, edge entitlement as a repository prerequisite,
and the expectation that one design should simultaneously own local generation, remote
distribution, legacy migration, and CDN policy.

## v0.2: establish a small ownership model

v0.2 deliberately split the product into two execution paths:

- **Plain** scans a caller-owned directory and rebuilds RPM or DEB metadata in place.
- **Managed** owns a Workspace containing independent Repositories, each with its own Pool,
  Dists, SQLite state, locks, operations, and recovery evidence.

This reset established the durable object vocabulary still used today: Package Object,
Membership, Desired and Built state, Generation, Changeset, and explicit operation
journals. It also established stable lock files, pointer-last file replacement,
fail-closed recovery, and the rule that tests or specifications do not upgrade themselves
into live-client evidence.

During development, the C2 layout still placed package hardlinks in each RPM view. The
sealed archive accurately records that pre-release design line; it must not be relabeled
as behavior shipped by the v0.2.0 tag.

## v0.2.0: make Repository root the delivery unit

The 2026-08-05 single-payload decision removed canonical package aliases from RPM views.
It shipped three days later in v0.2.0. One Repository has one canonical `pool/` and
metadata-only `dists/`; the complete root is the copy, hosting, authorization, and
publication unit.

v0.2.0 also made the state split explicit:

- Package Object, Desired/Built, Generation, Changeset, and local retention belong to the
  Repository.
- Publication Attempt, Applied Checkpoint, remote inventory, grace, and deletion evidence
  belong to one Repository plus one target prefix.

The design rejected cross-Repository deduplication and distributed prefix arbitration.
Those are not missing optimizations: they would change the ownership and failure model.
Compatibility exports remain outside canonical state.

## v0.3: simplify and optimize the same model

v0.3 kept the v0.2.0 public layout. It removed the retired V1 CLI/runtime and migration
harness, introduced the package-facts cache, made Plain generation a rebuildable one-pass
projection, bulk-expanded Membership, and replaced per-object promotion with bounded group
commits. These changes reduced work and code surface without moving ownership away from
Repository `pool/ + dists/`.

## v0.4: harden evidence rather than add another model

v0.4 kept the public layout introduced in v0.2.0 and optimized in v0.3, then concentrated
on integrity and recovery. Managed deep
verification became a bounded single-pass contract; RPM trust requires one independently
verified trust ring instead of evidence assembled across unrelated keys; mutable target
settings can be corrected only through an explicit, audited rebind; and migration,
publication recovery, and public-delivery checks were tightened.

An early coordinated-publication proposal considered handing bulk transfer to rclone.
The final decision kept native providers because publication correctness depends on
provider receipts, exact object identity, commit ordering, checkpoint state, public
visibility, and recovery — not only byte transport.

## What survived every redesign

The useful v0.1 lessons were not discarded with its product model:

- every durable fact needs one explicit owner;
- package bytes and rebuildable projections must not share authority;
- immutable payload and metadata prepare before mutable pointers commit;
- post-commit recovery moves forward; contradictory evidence fails closed;
- deletion requires reachability, grace, ownership, and provider capability;
- path, client, mirror, provider, release, and deployment evidence are separate gates;
- historical PASS results stay attached to their version, source, and environment.

These principles now live in a much smaller object model. See
[Design Principles](/blog/design/principles/), [System Model](/blog/design/model/),
[Single-Payload Repository](/blog/design/single-payload/), and
[Publication & Recovery](/blog/design/publication/).

## Documentation authority

The maintained boundary is now simple:

- [SOW Docs](/docs/) define current user-facing commands, configuration, formats, and
  operating behavior.
- This Design column defines maintained rationale and dated decision history.
- [Release Notes](/blog/release/) define version-level delivery and upgrade claims.
- Source tags preserve exact historical implementation, tests, and superseded prose.

Raw planning prompts, intermediate reviews, generated evidence summaries, and abandoned
specifications remain historical material. They may explain how a conclusion was reached,
but they are not parallel documentation authorities.
