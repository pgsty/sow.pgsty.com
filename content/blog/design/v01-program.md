---
title: "The Original SOW v0.1 Program: A Git for Package Repositories"
linkTitle: "v0.1 Original Program"
date: 2026-07-11
lastmod: 2026-10-13
authors: [Vonng]
description: "Why SOW began as a Git/CAS/Route/Edge control plane, what that model achieved, and why the product later reset around a smaller Repository core."
categories: [Design]
tags: [history, v0.1, git, cas, publication, migration]
url: "/blog/design/v01-program/"
weight: 110
icon: fa-solid fa-code-branch
draft: false
---

The v0.1 program began on 2026-07-11 and was sealed as v0.1.0 on July 31. It aimed to
replace Pigsty's Makefile-and-rclone workflow with one Go control plane for APT, YUM, and
static assets. That control plane covered local state, package history, upstream sync,
channels, views, snapshots, two clouds, CDN behavior, commercial access control, and
migration.

The guiding phrase was **“Git for artifact repositories.”** Package distribution has
immutable content, mutable names, history, promotion, publication, and rollback. The
analogy helped describe those needs, but it also expanded the scope of the product.
The Git/CAS/Route/Edge model was later retired; the current model is described in
[System Model](/blog/design/model/).

## The problem the first design tried to solve

The legacy system already published dozens of stable URLs used by APT, DNF, scripts, and
installation endpoints. A replacement had to preserve those URLs while adding properties
the Makefile workflow could not express safely:

- one identity for every accepted package body;
- desired state separated from what each cloud had actually published;
- snapshots and retained history without guessing which files were still live;
- incremental upload and purge proportional to the change set;
- recovery after a crash between metadata preparation and pointer publication;
- provenance for upstream indexes, package signatures, and migration exceptions;
- private commercial objects that could not leak through a public index or cache key;
- compatibility evidence from real APT/DNF clients rather than metadata syntax alone.

The original program deliberately treated these as one connected ownership problem.

## The selected v0.1 model

### Git was canonical state

`.sow/state` was a normal Git worktree operated through an embedded Go library. Manifests,
refs, provenance, configuration hashes, target checkpoints, and security labels were Git
content. SQLite was only a rebuildable query projection.

This gave every state transition a durable history and made one ref update the local
commit boundary. It also meant that package-management state, publication state, migration
state, and operator intent all had to fit one Git-shaped authority.

### CAS owned the bytes

Package bodies lived in an immutable SHA-256 pool. Published trees used hardlinks into that
pool, so package references determined whether a file could be removed.
This made local deduplication and history inexpensive, but required one filesystem and
made materialized paths, receipts, and inode identity part of the product contract.

### Refs expressed product meaning

Repository, View, Snapshot, Stable, History, and per-target remote refs described the
meaning and retention of content. A mutable view could move without erasing stable or
historical reachability. Removing a view changed references; garbage collection remained a
separate operation that checked all remaining references.

### Each target had its own publication history {#publication-was-a-saga}

Cloudflare R2 and Tencent COS were independent targets. Each target prepared immutable
objects, persisted commit intent, moved protocol pointers, purged the CDN, verified public
visibility, and advanced its own checkpoint. One target succeeding could not be rolled
back merely because the other failed.

The publication order was:

```text
immutable payload
  -> immutable metadata
  -> durable commit intent
  -> mutable protocol pointer
  -> public verification
  -> checkpoint
  -> grace
  -> deletion after reference and identity checks
```

Current publication retains this ordering. Cache grace and provider deletion checks apply
to remote garbage collection.

### Routes and Edge were part of repository correctness

The public tree preserved legacy paths, while generation-aware routes selected immutable
metadata. Private objects lived behind an Edge contract shared by Cloudflare Worker and
EdgeOne. Authentication had to run before origin access; tokens could not enter origin
URLs, cache keys, or logs.

This design made CDN routing, token verification, provider deployment, log sinks, and
cache topology prerequisites of the repository model.

## Why the design was attractive

The model gave each part of the system explicit rules:

- every durable fact had an explicit owner;
- immutable bytes and mutable names were separated;
- local and remote publication states were observable independently;
- pointer-last publication made partial work recoverable;
- GC checked all package references before deletion;
- plans and receipts were revalidated instead of blindly trusted;
- client compatibility, provider compatibility, and implementation evidence were distinct;
- the exact legacy migration surface was treated as data, not tribal knowledge.

These rules continued in later releases with fewer supporting mechanisms.

## Why the product reset

By the end of July, SOW v0.1 had accumulated:

- Git commits and refs as an internal database protocol;
- a global content-addressed store and hardlink materialization layer;
- Route, View, Snapshot, Generation, Projection, Receipt, and Lease concepts;
- APT/YUM/asset synchronization and legacy migration inside the core binary;
- cloud SDK, edge bootstrap, provider attestation, purge, token, and private-origin logic;
- forty-four surviving ADR files and 112 dated evidence reports.

Each individual addition answered a real failure mode. Together they created several
problems.

First, too many objects could appear to own the same package and public path. A package was
simultaneously a CAS object, a manifest entry, a View member, a materialized Route, a
Snapshot reference, and a remote target object.

Second, local repository generation was coupled to cloud and Edge lifecycle decisions.
An operator who only wanted to build a YUM or APT repository inherited the conceptual cost
of commercial access control and distributed publication.

Third, the migration program had become a permanent product subsystem. Exact legacy
topology, Make targets, CDN behavior, and old provider exceptions were valuable during
cutover but did not belong in the long-term repository abstraction.

Finally, recovering every derived path under hostile-writer and crash conditions required
more identity, journal, quarantine, and retirement machinery than the core job justified.

Upstream synchronization and channel promotion were another deliberate scope cut. V1 had
tests for streaming downloads, malformed input, URLs, and verification order, but acquisition
introduced its own policy, retry, provenance, and remote-ownership model. The reset made
package acquisition an external input concern so SOW could own repository admission and
publication without also becoming a universal mirror orchestrator.

## What survived the reset

| v0.1 lesson | Maintained form |
|---|---|
| Every durable fact has one owner | Repository and target-prefix ownership in [System Model](/blog/design/model/) |
| Canonical data differs from projections | One `pool/` plus metadata-only `dists/` |
| Pointers commit after payload preparation | [Publication & Recovery](/blog/design/publication/) |
| Post-commit recovery is forward-only | Managed operation and publication journals |
| Plans and paths are untrusted input | Exact identity, containment, and rebind checks |
| Deletion requires complete evidence | References and exact object identity; cache grace and provider capability for remote deletion |
| Generated server config is derived state | The complete Repository root is the hosting unit; serving remains explicit operator configuration |
| Compatibility is a matrix | [Platforms & Integrations](/docs/reference/compatibility/) |
| Historical evidence never upgrades itself | Dated Design and Release records |

## What was retired

- Git as product state and SQLite as a disposable cache;
- a cross-product CAS and hardlink-based materialization layer;
- the Route/View/Snapshot public command model;
- generated Nginx includes, Route receipts, and V1 serving-control state;
- built-in upstream synchronization, promotion, and legacy Make-target migration;
- Edge token entitlement and private-origin topology as repository prerequisites;
- the multi-cloud publication control plane and provider bootstrap/attestation system;
- V1-specific projection receipts, leases, quarantine commands, and recovery surfaces.

Some implementation ideas later returned under a narrower boundary: SOW manages
repositories and their publication. Package acquisition and serving remain external tasks.

## Timeline

| Date | Milestone |
|---|---|
| 2026-07-11 | Goal, brainstorm, technical research, client and scale baselines |
| 2026-07-12 | Core Git/CAS/publication contract and first protocol/provider evidence |
| 2026-07-13–16 | Package trust, transaction, legacy topology, and migration closure |
| 2026-07-17–20 | Provider bootstrap, Edge confidentiality, deletion capability, and input bounds |
| 2026-07-22–29 | Path-identity, hostile-writer, quarantine, and residue-recovery hardening |
| 2026-07-30–31 | Clean-room MVP evidence and v0.1.0 source seal |
| 2026-08-01 onward | Plain/Managed reset and eventual retirement of the V1 runtime |

## Primary sources and next records

The immutable [v0.1.0 `docs/` tree](https://github.com/pgsty/sow/tree/v0.1.0/docs)
preserves the original [architecture contract](https://github.com/pgsty/sow/blob/v0.1.0/docs/architecture.md),
[requirements traceability](https://github.com/pgsty/sow/blob/v0.1.0/docs/requirements-traceability.md),
[migration material](https://github.com/pgsty/sow/tree/v0.1.0/docs/migration), ADRs, and
evidence for the historical implementation.

Continue with the [v0.1 Decision Ledger](/blog/design/v01-decisions/),
[v0.1 Evidence Ledger](/blog/design/v01-evidence/), and
[v0.2 Reset](/blog/design/v02-reset/).
