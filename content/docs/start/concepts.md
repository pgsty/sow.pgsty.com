---
title: "Core Concepts"
linkTitle: "Core Concepts"
description: "The v0.2.0 model: Plain and Managed execution, pools and views, Desired Membership, and Built Generations."
url: "/docs/start/concepts/"
weight: 400
icon: fa-solid fa-diagram-project
---

## Plain or Managed

The two execution paths are separate.

| | Plain | Managed |
|---|---|---|
| Entry point | `sow create DIR` | `init`, `repo`, `dist`, `add`, `rm`, `build` |
| State | package directory | `sow.yml` plus private SQLite/journals |
| Public layout | flat RPM/DEB indexes | Repository `pool/ + dists/` |
| Formats | RPM and DEB may share one directory | one format per Dist |
| Architecture views | no | yes |
| Policy and audit | no | yes |
| Metadata signing and publication targets | no | yes |

Choose Plain when directory contents already equal the desired repository. Choose Managed
when SOW must own membership, policy, generations, signing, audit, or publication.

## Managed hierarchy

```text
Workspace                    /srv/sow
├── sow.yml                  configuration
├── .sow/                    private state; never served
└── Repository               /srv/sow/local
    ├── pool/                canonical package payloads
    └── dists/
        └── Dist             one named RPM or DEB membership set
            └── views        metadata rendered per architecture
```

- **Workspace** is the configuration and discovery boundary.
- **Repository** is the isolation, Generation, publication, and public-tree boundary.
  Repositories do not deduplicate payloads with one another.
- **Dist** is a named membership set in exactly one package format.
- **Architecture view** is derived output, not a second membership set. `noarch` RPMs and
  `all` DEBs are selected into every applicable view without duplicating their pool bytes.

## One canonical payload

A package object is identified by its exact-byte SHA-256. Its logical coordinate comes
from the RPM header or DEB control data, not the filename.

Each accepted payload has one canonical path under the Repository `pool/`. RPM architecture
views contain `repodata/` only; their package locations use parent-relative paths back to
the pool. APT `Packages` entries name the same pool directly.

Ordinary package clients and mirror tools are different contracts. Default `dnf reposync`
rejects the canonical RPM view's parent traversal. When a self-contained RPM mirror leaf
is required, create a separate artifact with `sow export rpm-leaf`.

## Desired and Built

Managed mode tracks intent and public bytes separately:

```text
add / rm -> Desired Membership (revision)
                    |
                  build
                    v
             Built Generation -> pool/ + dists/
```

`add` and `rm` build affected Dists by default. `--skip` records membership changes but
leaves the Repository `dirty`; `sow build` later converges Desired into a new Built
Generation.

- `sow status` reads state cheaply and reports `ready_to_copy`.
- `sow check` performs the full, read-only delivery proof. Dirty or recovering state is
  not deliverable.
- `sow changes [BASE_GENERATION]` describes the physical difference between a recorded
  Generation and the current Built Generation. It is evidence and planning output, not a
  substitute for publication recovery or remote verification.
- `sow publish TARGET` publishes a verified Generation through the configured provider and
  records target-scoped recovery/checkpoint state.

## Transactions and failure states

Writes are serialized by Workspace or Repository locks and journal their intent before
public mutation. Payloads and immutable metadata are prepared before mutable protocol
pointers. A later writer recovers an interrupted operation before starting new work.

The operational states are:

| State | Meaning |
|---|---|
| `clean` | Desired and Built agree |
| `dirty` | Desired changed; Built is still the previous committed Generation |
| `recovering` | a nonterminal operation must be resolved |
| `error` | durable evidence conflicts; SOW refuses to guess |

Use `status` to diagnose and `check` as the release gate. Do not publish a Repository with
`ready_to_copy=false`.

## Continue

- [Managed Workspaces](/docs/feature/managed/)
- [Pool & Architecture Views](/docs/feature/views/)
- [Transactions & Recovery](/docs/feature/transactions/)
- [Publication & Recovery](/docs/design/publication/)
