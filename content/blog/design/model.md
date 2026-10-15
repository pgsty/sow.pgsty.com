---
title: "System Model"
linkTitle: "System Model"
date: 2026-08-08
lastmod: 2026-10-13
authors: [Vonng]
description: "The objects and state transitions that connect packages, distributions, generations, and publication targets."
categories: [Design]
tags: [repository, dist, pool, generation]
url: "/blog/design/model/"
aliases:
  - "/docs/design/model/"
weight: 50
icon: fa-solid fa-diagram-project
draft: false
---

SOW uses configuration for repository settings, SQLite for managed state, and a public
directory for client access. The model separates the packages you select from the files
that have been built and published.

<span id="object-hierarchy" data-td-print-local></span>

## Objects

```text
Workspace
├── Repository
│   ├── Pool: package objects
│   ├── Dists: package memberships and policies
│   ├── Desired state
│   ├── Built Generation
│   └── Retained Generations
└── Publication targets
    └── Repository + storage backend + prefix
```

### Workspace

A Workspace contains `sow.yml`, the private `.sow/` directory, and stable lock files.
It groups configuration and lets commands discover the selected Repository.

### Repository

A Repository owns one `pool/`, one `dists/` tree, one state database, and one Generation
sequence. Package deduplication is local to this Repository. Two Repositories with the
same input packages each keep their own copy.

### Package object

SOW identifies a package object by its SHA-256 after package signing. Name, version,
release, and architecture describe the package; the digest identifies its bytes.
Re-adding the same object reuses it. Different bytes at the same Pool path are a conflict.

### Dist and membership

A Dist selects packages and settings for one format, RPM or DEB. A package can belong to
several Dists while keeping one Pool file. Architecture-neutral packages (`noarch` or
`all`) appear in each matching architecture view without another package copy.

### Desired, Built, and Generation

Desired state records the selected packages and configuration. Built state records the
last completed build. A Generation is an immutable inventory of that build, and a
changeset compares two inventories.

An `add --skip` operation can change Desired state without rebuilding indexes. An interrupted
build can also leave unfinished work. Use `sow status` to inspect the difference and
`sow build` to apply pending changes or finish recovery.

### Publication target

A target connects one Repository to a storage backend and prefix. Each target has its own
publication attempts, checkpoints, inventory, and cleanup records.

See [Publication and recovery](/blog/design/publication/#target-identity) for target identity and configuration changes.

## State flow

```text
package input
    -> inspect, sign if configured, and hash
    -> package object and membership
    -> Desired state
    -> render and validate
    -> Built Generation and changeset
    -> target publication attempt
    -> applied checkpoint
```

Managed operations record their progress in transactions and journals. Recovery uses these
records to finish or roll back the interrupted step.

<span id="public-and-private-state" data-td-print-local></span>

## Public and private files

| Serve as a complete Repository | Keep in the private workspace |
|---|---|
| `<repo>/pool/` | `sow.yml` |
| `<repo>/dists/` | `.sow/` databases and journals |
| Generated indexes and signatures | Locks, staging, and recovery files |

A copy of the public tree can serve packages. To continue managing that Repository, keep
the matching private workspace too. A public copy alone has no membership, retention,
or publication history.

<span id="locking-boundary" data-td-print-local></span>

## Locks and writers

The Workspace and each Repository have separate locks. Most reads use shared locks; writes use exclusive locks to prevent concurrent changes to the same state.
`sow status` queries the lock state directly so you can inspect an active writer.

One workspace must own writes to each target prefix. These locks coordinate local processes,
not independent workspaces on different hosts.
