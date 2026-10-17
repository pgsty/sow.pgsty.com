---
title: "The v0.2 Reset: Plain and Managed Instead of a Universal Control Plane"
linkTitle: "v0.2 Plain/Managed Reset"
date: 2026-07-31
lastmod: 2026-10-17
authors: [Vonng]
description: "How SOW replaced the v0.1 Git/CAS/Edge platform with two small execution modes, explicit ownership, SQLite state, and a repository-focused release."
categories: [Design]
tags: [history, v0.2, plain, managed, architecture, decision]
url: "/blog/design/v02-reset/"
weight: 80
icon: fa-solid fa-arrows-rotate
draft: false
---

On 2026-07-31, after sealing the v0.1 source baseline, SOW began a product reset. The goal
was a small repository engine that could replace Pigsty's daily package-build workflow.
It kept the earlier lessons about integrity and recovery while removing much of the
control plane.

The result was the split still used today: **Plain** rebuilds caller-owned directories;
**Managed** maintains repositories and their history.

The development design initially used C2 hardlinks inside RPM views. These were replaced
before the v0.2.0 release on August 8. Some archived plans called the C2 build “v0.2.0,” but
the released tag already had one canonical Pool and metadata-only views.

## Why reset instead of incrementally simplifying V1

The v0.1 model had coupled five different jobs:

1. build valid APT/YUM/asset repositories;
2. maintain package history and snapshots;
3. migrate a large legacy Pigsty topology;
4. publish to multiple cloud/CDN targets;
5. enforce commercial Edge access.

Removing one feature at a time would leave the same Git/CAS/Route ownership model in
place. The reset instead asked which facts the core repository engine truly needed to own.

The first phase excluded:

- the V1 Git database, Route/Manifest/Quarantine model, or global content-addressed
  product layer;
- upstream sync, pull/push/copy/move/promote surface, Edge entitlement, CDN bootstrap,
  or commercial topology;
- remote publication/state, object storage, GC, snapshot/freeze, Managed export, or
  serving in the first phase;
- modulemd, source-package building, Web UI, cross-Repository deduplication, or
  multi-writer operation.

Upstream synchronization and channel promotion were deliberately removed even though V1
had real streaming, fuzz, and deterministic-proof evidence for them. Package acquisition
became an external task. Operators can
prepare package sets with dedicated mirror or download tooling, then let SOW own admission,
membership, build, and publication. Some phase-one exclusions—publication, retention, GC,
and external export—returned before the final v0.2.0 tag under the smaller Repository
ownership model.

## Two isolated execution modes

### Plain: rebuild what the caller owns

Plain mode operates on a caller-owned directory of RPM or DEB files:

```bash
sow create /srv/repo
```

It scans packages, renders protocol metadata, validates the result, and installs pointers
last. Plain owns its generated metadata but not a Workspace, Repository database,
Generation history, or long-lived membership state.

Because the desired state is simply “the packages currently in this directory,” the
correct recovery strategy is to rerun the build. Later releases made that principle even
more explicit by removing Plain journals and repeated package reads.

### Managed: own lifecycle and history

Managed mode introduces a Workspace with independent Repositories:

```text
Workspace
├── sow.yml
├── .sow/                    private state, locks, SQLite, journals
└── <repository>/
    ├── pool/                canonical package bytes
    └── dists/               client protocol views
```

Each Repository owns its Pool, Package Objects, Membership, Desired State, Built
Generation, Changeset, lock, database, and recovery state. Different Repositories do not
silently deduplicate or share counters.

A Dist is a named RPM or DEB membership set. Architecture Views are projections of that
membership, not new owners. Neutral packages (`noarch` / `all`) project into every
applicable architecture without duplicating logical membership.

## Decisions that replaced V1 concepts

| V1 concept | v0.2 replacement |
|---|---|
| Git commit/ref as canonical state | Per-Repository SQLite plus explicit filesystem/journal evidence |
| Global CAS and Route materialization | Repository-owned Pool and protocol views |
| View/Snapshot/Stable ref graph | Dist membership, Desired revision, Built Generation, retained state |
| One universal command interface | Separate Plain and Managed commands |
| Implicit legacy topology | Strict `sow.yml` plus explicit names and selectors |
| Cross-product publication saga | Repository build kept separate from target publication |
| Reuse V1 packages directly | Narrow parser/renderer/version/signing ports only |

The critical simplification was that private control state and public repository bytes
could be understood without Git or an Edge router.

## Desired versus Built

Managed mode made interrupted state explicit:

- **Desired State** is the current package and membership intent in SQLite.
- **Built Generation** is the last complete public tree that rendered and validated
  successfully.
- **Changeset** is the exact delta between two built states.

Desired can advance before a new Built Generation completes. The operation journal
records unfinished work, and status shows the difference between Desired and Built.
Recovery uses the recorded operation phase to decide what remains to be completed.

## P0 through P3

The work was intentionally sequenced:

| Phase | Contract |
|---|---|
| P0 | Plain `create`, real RPM/DEB metadata, signing, Pigsty-compatible filtering, pointer-last replacement |
| P1 | Workspace/Repository/Dist lifecycle, strict config, package identity, membership, and query |
| P2 | Add/remove/policy/build operations, journals, crash recovery, and safe mutation |
| P3 | Check, Changeset, handoff, scale, compatibility, and clean-delivery evidence |

Each phase had an API contract, implementation specification, adversarial review, and
acceptance record.

## The C2 hardlink detour

The first Managed RPM layout kept canonical files in a root Pool and added hardlinks below
each architecture View. Metadata used a safe local `pool/...` href. This C2 layout made a
pinned AlmaLinux 9 `reposync` flow work and avoided duplicate local bytes because aliases
shared an inode.

The design had a hidden deployment cost:

- object storage expands each path into a separate full object;
- archive and cross-filesystem copies can lose hardlink identity;
- every Dist/architecture alias looks like another canonical payload;
- retention and GC risk depending on inode/link-count behavior;
- the whole Repository no longer maps one-to-one to static object keys.

The 2026-08-05 snapshot records this C2 implementation and its local test results.

The single-payload contract was written on 2026-08-05, committed as the “next” design on
August 7, and implemented before the August 8 release tag. The final release therefore
shipped:

```text
<repository>/
  pool/       one canonical payload per Package Object
  dists/      metadata-only APT/RPM views
```

Default EL `reposync` became an accepted compatibility limitation; a standalone RPM leaf
moved to an explicit external export. The complete reasoning is preserved in
[Single-Payload Repository](/blog/design/single-payload/).

## What the reset reused

The team did not start from blank code. It retained only narrow components that had no V1
ownership assumptions:

- RPM/DEB parsing and native version comparison;
- metadata rendering, compression, signing, and validation;
- safe filesystem primitives;
- selected client fixtures and fault patterns;
- exact package identity and provenance checks.

The new core had no dependency on Git state, Route receipts, Edge components, legacy migration, or cloud control code.
Those components were kept for reference or removed.

## From acceptance tests to release {#release-evidence-boundary}

The development line recorded P0/P1 acceptance on August 1, P1–P3 acceptance on August 2,
and a local release-gate run on August 5. The final v0.2.0 source was tagged on August 8
after the single-payload implementation, packaging, and CI corrections landed.

The final release also shipped filesystem and R2 publication, retained generations,
external RPM leaf export, and local GC. R2 remote deletion was disabled from the start;
GC for R2 only reported candidates.

## What still defines SOW

- Plain and Managed are isolated modes with different recovery costs.
- Workspace is configuration/discovery scope; Repository is package/history scope.
- Package Object identity is immutable; Membership is logical and many-to-many.
- Desired and Built states are distinct.
- Writers use stable lock files and install protocol pointers last. Managed journals
  record interrupted operations; Plain recovers by rebuilding.
- CLI syntax, JSON envelopes, and exit classes provide a defined automation interface.
- Protocol, client, mirror-tool, and provider compatibility are reported separately.

The current forms are documented in [Get Started](/docs/start/),
[System Model](/blog/design/model/), and [Design Principles](/blog/design/principles/).

## Primary source snapshots

- [v0.2 development design snapshot](https://github.com/pgsty/sow/tree/1e7eb5493cc349372fa40c2f8e6e44d8ddb7801b/design/v0.2)
  — PRD, API, C2 architecture, reviews, and local acceptance.
- [single-payload “next” design](https://github.com/pgsty/sow/tree/8625f5090f5668c69c20f2f17b6466d1228d2fbe/design/next)
  — the design adopted before the release tag.
- [v0.2.0 release note](/blog/release/sow-docs-launch/) and
  [v0.2.0 source tag](https://github.com/pgsty/sow/tree/v0.2.0)
  — the released implementation.

Continue with [Design Evolution](/blog/design/evolution/) for the v0.3 through v0.6
changes that followed.
