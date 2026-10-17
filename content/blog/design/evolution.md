---
title: "SOW Design Evolution: From Route Graphs to the Repository Core"
linkTitle: "Design Evolution"
date: 2026-08-10
lastmod: 2026-10-17
authors: [Vonng]
description: "How SOW moved from the v0.1 distribution platform to a repository engine, and how v0.2 through v0.6 refined that model."
categories: [Design]
tags: [architecture, repository, migration, decision]
weight: 20
url: "/blog/design/evolution/"
icon: fa-solid fa-code-branch
draft: false
---

SOW moved from a Git-based distribution control plane in v0.1 to a repository engine in
v0.2. This article traces that change and the refinements through v0.6.0.

The earlier versions below refer to released Git tags; v0.6 is the current documentation target.
Some archived plans used “v0.2” and
“v0.3” for development designs. In particular, the C2 layout with RPM hardlinks inside each
view was replaced before v0.2.0 shipped.

Four articles cover the earlier work in detail:

- [The Original v0.1 Program](/blog/design/v01-program/) describes the initial scope and
  why it became too broad.
- [The v0.1 Decision Ledger](/blog/design/v01-decisions/) records all 44 surviving ADRs
  and how each decision changed.
- [What v0.1 Actually Proved](/blog/design/v01-evidence/) summarizes the 112 dated test
  and review reports.
- [The v0.2 Reset](/blog/design/v02-reset/) explains the Plain/Managed split and the
  change from C2 to a single-payload layout.

## The short history

| Release | Main changes | Public layout |
|---|---|---|
| v0.1 | Git/CAS state, Routes, Edge authorization, cloud workflows, and Pigsty migration | Retired |
| v0.2 | Plain/Managed modes, one package pool per Repository, metadata-only views, retained Generations, and target publication | Introduced the current `pool/ + dists/` layout |
| v0.3 | Removed V1, cached package facts, simplified Plain builds, and batched payload commits | Unchanged |
| v0.4 | Single-pass verification, independent RPM trust rings, target rebind, and migration/recovery fixes | Unchanged |
| v0.5 | Package-path reservations, removal and recovery fixes, signing checks, and reproducible Plain timestamps | Unchanged |
| v0.6 | Previous Plain RPM indexes, recorded Managed publication times, stronger file checks, consistent state reads, and less repeated I/O | Unchanged |

The source tags preserve the earlier implementations:
[v0.1.0](https://github.com/pgsty/sow/tree/v0.1.0),
[v0.2.0](https://github.com/pgsty/sow/tree/v0.2.0),
[v0.3.0](https://github.com/pgsty/sow/tree/v0.3.0),
[v0.4.0](https://github.com/pgsty/sow/tree/v0.4.0), and
[v0.5.0](https://github.com/pgsty/sow/tree/v0.5.0).

## v0.1: useful questions, too many product concepts

The first plan covered Git-backed state, content-addressed storage, Routes and Views,
snapshots, remote providers, Edge authorization, and legacy migration. Forty-four ADRs,
numbered through 0045, documented the decisions and their failure cases.

The combined scope made ownership difficult to explain. Several objects could describe
the same package bytes and published paths. Local repository generation also depended on
cloud, Edge, and migration concepts.

The v0.2 reset removed Git as the authoritative product database, the separate CAS layer,
the Route/View/Snapshot command model, and Edge access control. It made local repository
construction the core task.

## v0.2: establish a small ownership model

v0.2 split the product into two execution paths:

- **Plain** scans a caller-owned directory and rebuilds RPM or DEB metadata in place.
- **Managed** owns a Workspace containing independent Repositories. Each Repository has
  its own Pool, Dists, SQLite state, locks, and recovery records.

This reset introduced the terms still used today: Package Object, Membership, Desired and
Built state, Generation, and Changeset. Stable lock files coordinate access. Generated
files replace the protocol pointers last. Managed journals record how to recover an
interrupted operation.

The first implementation, called C2, still placed package hardlinks in each RPM view.
That layout changed before release.

## v0.2.0: make Repository root the delivery unit

The single-payload decision was written on 2026-08-05 and shipped in v0.2.0 on August 8.
It removed package aliases from RPM views. One Repository has one canonical `pool/` and
metadata-only `dists/`. The complete root is the unit to copy, host, authorize, and publish.

v0.2.0 also separated local and remote state:

- Package Objects, Desired/Built state, Generations, Changesets, and local retention belong
  to the Repository.
- Publication Attempts, Applied Checkpoints, remote inventories, cache grace, and deletion
  records belong to one Repository and one target prefix.

Repositories do not deduplicate packages across their boundaries. A target prefix has one
owner. Compatibility exports are separate copies outside the canonical Repository.

## v0.3: simplify and optimize the same model

v0.3 kept the v0.2.0 public layout. It removed the V1 runtime and migration harness,
introduced the package-facts cache, and made Plain generation a rebuildable one-pass
operation. It also expanded Membership in batches and grouped payload commits to reduce
filesystem work.

<span id="v04-harden-evidence-rather-than-add-another-model" data-td-print-local></span>

## v0.4: strengthen verification and recovery

v0.4 made Managed deep verification a bounded single pass. RPM verification must succeed
within one trust ring; it cannot combine partial results from unrelated rings. An explicit
rebind operation can update mutable target settings. Migration, publication recovery, and
public-delivery checks also became stricter.

An early coordinated-publication proposal considered using rclone for bulk transfer. The
final design kept native providers so SOW could check object identity, record receipts,
control commit order, and recover publication from the same state machine.

## v0.5: preserve package URLs and committed state

v0.5.0, released on 2026-09-29, kept the same public layout and upgraded managed state to
schema 13. The new pool-path indexes prevent different package bytes from taking over an
existing URL, including a URL recorded by an earlier publication.

The release also fixed recovery after Dist removal and package re-addition, preserved
committed changes after interruption, and checked conflicting signing policies before
changing Desired state. Plain `create --metadata-timestamp` added an explicit timestamp
for reproducible RPM metadata; its default is zero. See the
[v0.5.0 changelog](https://github.com/pgsty/sow/blob/v0.5.0/CHANGELOG.md) for the full changes.

## v0.6: verify once, preserve the result

v0.6 keeps schema 13 and the same public layout. It records one publication time for each
new metadata build and reuses that time during recovery. File checks bind verified bytes
to the opened file, so later steps can safely reuse verification results within an operation.

SQLite reads use a consistent snapshot. Commands preserve committed results when later
maintenance fails. Plain RPM updates keep the current and immediately previous metadata
sets, so clients can finish fetching files from the previous index.

These changes improve the existing model without another full repository scan or recovery
state machine. See the [v0.6.0 release note](/blog/release/sow-v0.6.0/) for behavior and upgrade details.

## What survived every redesign

Several v0.1 rules continue in the smaller model:

- Give each durable fact one owner.
- Keep package bytes separate from rebuildable metadata.
- Prepare immutable payload and metadata before replacing protocol pointers.
- After a durable commit intent, complete the operation through forward recovery.
- Check references and exact identity before deletion. Remote deletion also checks cache
  grace and provider capabilities.
- Record compatibility results with the source version, client, provider, and environment
  that produced them.

<span id="documentation-authority" data-td-print-local></span>

The current rationale is in [Design Principles](/blog/design/principles/),
[System Model](/blog/design/model/), [Single-Payload Repository](/blog/design/single-payload/),
and [Publication & Recovery](/blog/design/publication/). Use [SOW Docs](/docs/) for commands
and operating procedures, and [Release Notes](/blog/release/) for version-specific changes.
