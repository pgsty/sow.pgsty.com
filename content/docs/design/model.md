---
title: "System Model"
linkTitle: "System Model"
description: "The objects and state transitions that connect packages, distributions, generations, and publication targets."
url: "/docs/design/model/"
weight: 200
icon: fa-solid fa-diagram-project
---

The model is deliberately layered. Configuration expresses intent, the database records
owned state, and the public tree is a deterministic projection. None of those layers may
quietly become a substitute for another.

## Object hierarchy

```text
Workspace
├── Repository
│   ├── Package Object
│   ├── Dist
│   │   └── Membership -> Package Object
│   ├── Desired state
│   ├── Built Generation
│   └── Retained Generation references
└── Publication Target
    └── Repository + provider + prefix
```

### Workspace

A Workspace supplies discovery, configuration, and coordination. It owns `sow.yml`, the
private `.sow/` directory, and stable lock paths. It is not a package deduplication domain.

### Repository

A Repository is the smallest self-contained public archive and the unit of package
identity. It owns one `pool/`, one set of `dists/`, one state database, and one Generation
sequence. Two Repositories share no package bytes or counters even when their inputs match.

### Package Object

A Package Object is identified by its final SHA-256 after any package signing. Logical
coordinates such as name, version, release, and architecture are metadata; the digest is
the byte identity. Re-adding the same digest is idempotent. Different bytes at the same
canonical pool path are a hard conflict.

### Dist and Membership

A Dist is an APT or RPM publication policy and a collection of memberships. Membership is
many-to-many: one Package Object may belong to several Dists without acquiring another
canonical payload. Neutral packages (`all` or `noarch`) project into every matching
architecture view but remain one logical membership.

### Desired, Built, and Generation

Desired state is what configuration and package operations ask for. Built state is the
last fully rendered and validated public tree. A Generation is an immutable inventory of
that Built state; a Changeset is the exact difference between two inventories.

Keeping Desired and Built separate lets an interrupted operation be described honestly:
the intent may have changed while the last committed public tree remains valid.

### Publication Target

A target binds one Repository to a provider endpoint and prefix. Publication attempts,
applied checkpoints, remote inventory, grace, and delete evidence are target-scoped.
Building a Repository is target-neutral; publishing it is not.

## State flow

```text
package input
    -> inspect/sign/hash
    -> Package Object + Membership
    -> Desired state
    -> render and validate
    -> Built Generation + Changeset
    -> target publication attempt
    -> applied checkpoint
```

Every arrow is journaled or transactional. A later stage consumes an immutable identity
from the previous one rather than reinterpreting mutable paths.

## Public and private state

| Public, copy as one unit | Private, never serve |
|---|---|
| `<repo>/pool/` | `sow.yml` |
| `<repo>/dists/` | `.sow/` databases and journals |
| protocol signatures and indexes | locks, stages, recovery pre-images |
| Generation-described regular files | credentials and provider receipts |

A copy of only the public tree is a valid static repository. It is not an authoritative
writer: without the matching private state it cannot safely resume publication history,
retention, or garbage collection.

## Locking boundary

Workspace lifecycle operations take the Workspace lock. Repository mutations take a
stable Repository lock. When both are required, acquisition order is Workspace then
Repository, released in reverse. Stable lock paths prevent a rename or recovery operation
from accidentally creating a second writer on a new inode.

The model assumes one authoritative Workspace and exclusive write authority for every
configured target prefix. Distributed arbitration between independent Workspaces is a
non-goal.
