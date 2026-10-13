---
title: "sow check"
linkTitle: "check"
description: "Verify repository files, indexes, state, and signatures before delivery."
categories: [Command]
tags: [cli, audit, signing]
url: "/docs/command/check/"
weight: 1300
icon: fa-solid fa-list-check
---

`sow check` verifies a managed Repository before delivery. It checks package hashes, stored state, indexes, signatures, and the Generation manifest. The command is read-only; run `sow build` first if Desired state differs from the Built Generation.

## Synopsis

```text
sow check [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-j, --jobs N` | Parallel verification workers; at least `1` | logical CPU count |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Verify named Dists; repeatable | all Dists |
| `--json` | Output JSON | false |

## Verification layers

For a Repository with no unfinished layout migration, `check` reports nine layers:

| Layer | Verification | `checked` counts |
|---|---|---|
| `config` | `sow.yml` parses and validates for the Repository | configuration objects |
| `state` | SQLite `quick_check`, foreign keys, journal, and recovery evidence | one state database |
| `public-modes` | File and directory permissions across the served tree | inspected paths |
| `retained` | Retained records and their saved Generation manifests; see [`retain rm`](/docs/command/retain/#retain-rm) to handle a damaged record | retained records |
| `package-bytes` | SHA-256 of pool and private pending payloads | Package Objects |
| `desired-membership` | Membership rows resolve under current policy | memberships |
| `index` | Rendered indexes match the membership they claim | Dists |
| `signature` | Every declared metadata and package signature verifies | signatures |
| `generation-manifest` | Built Generation manifest matches files on disk | one manifest |

During an unfinished layout migration, `check` reports `config`, `state`, `public-modes`, and `layout-transition`, then stops. Follow the reported [`repo migrate`](/docs/command/repo/#sow-repo-migrate) instruction to complete or abort that migration.

### Package verification {#physical-evidence-and-io-contract}

Each run hashes the package files again. Hard links to the same physical file share one hash check. Signed RPMs also undergo signature verification. The `checked` count refers to package objects, not file reads.

```console
sow check
repository=pigsty status=clean ready_to_copy=true revision=5 generation=5
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=67
retained	ok=true	checked=0
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=8
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=1
```

## Dirty is not deliverable

A dirty Repository needs a build before it can pass `check`. The old Built Generation and new Desired state can each pass their own checks while differing from each other:

```console
sow check
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5
...
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

The exit code is `5`. Run [`sow build`](/docs/command/build/), then run `sow check` again.

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Every layer passes and the Repository is ready to copy |
| `1` | I/O failure during verification |
| `2` | Usage error, Workspace not found, or implicit Repository selection is ambiguous |
| `5` | A verification layer failed, or Repository is not deliverable |
| `6` | Explicit Repository or Dist is not configured |

## See also

- [`sow status`](/docs/command/status/) — cheap state query
- [`sow build`](/docs/command/build/) — build indexes from Desired state
- [Exit Codes](/docs/reference/exit-codes/) — why a dirty Repository maps to `5`
- [Observability & Audit](/docs/feature/audit/) — operating checks and audit together
