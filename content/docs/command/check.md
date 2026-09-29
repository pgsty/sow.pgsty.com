---
title: "sow check"
linkTitle: "check"
description: "Run the full read-only integrity and delivery-readiness verification pipeline."
categories: [Command]
tags: [cli, audit, signing]
url: "/docs/command/check/"
weight: 1300
icon: fa-solid fa-list-check
---

`sow check` is the deep read-only gate for a managed Repository. It hashes bytes, validates state,
reconstructs expected views, and verifies declared signatures. It never repairs, builds, recovers an
Operation, or takes the write lock.

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
| `--json` | Emit the `sow.cli/v1` envelope | false |

## Verification layers

In steady state, the checker reports nine ordered layers:

| Layer | Verification | `checked` counts |
|---|---|---|
| `config` | `sow.yml` parses and validates for the Repository | configuration objects |
| `state` | SQLite `quick_check`, foreign keys, journal, and recovery evidence | one state database |
| `public-modes` | File and directory permissions across the served tree | inspected paths |
| `retained` | Explicit retained records and frozen Generation manifests (a damaged retained root fails this layer; see [`retain rm`](/docs/command/retain/#retain-rm)) | retained records |
| `package-bytes` | SHA-256 of pool and private pending payloads | Package Objects |
| `desired-membership` | Membership rows resolve under current policy | memberships |
| `index` | Rendered indexes match the membership they claim | Dists |
| `signature` | Every declared metadata and package signature verifies | signatures |
| `generation-manifest` | Built Generation manifest matches files on disk | one manifest |

During a non-terminal Repository layout transition, `check` instead reports `config`, `state`,
`public-modes`, then a conditional `layout-transition` layer and stops. It returns not-ready until
the diagnosed [`repo migrate`](/docs/command/repo/#sow-repo-migrate) operation completes or is
aborted before commit.

### Physical evidence and I/O contract

`package-bytes` never trusts a cached fingerprint as a substitute for authenticity. Each run hashes
every unique physical payload exactly once, using descriptor-bound evidence keyed by device, inode,
size, mtime, and ctime. Hard links to the same inode share that proof; retained Generations, final
manifest traversal, and `changes` reuse it without another payload scan. The `checked` column counts
logical objects, not the number of full-file streams.

A DEB or unsigned RPM needs one complete payload stream. A signed RPM uses at most one additional
main-header-to-EOF stream to verify every signature packet against all candidate trust rings; the
cost does not grow with Dist, retained Generation, or trust-ring count. A forged or concurrently
replaced file invalidates the descriptor evidence and fails closed.

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

A dirty Repository can have nine individually valid layers: the old Built Generation is intact and
the new Desired state is valid. It still fails the delivery gate because the two do not match:

```console
sow check
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5
...
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

The exit code is `5`. Run [`sow build`](/docs/command/build/) and check again. Do not weaken a release
pipeline to accept this state.

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
- [`sow build`](/docs/command/build/) — converge Desired and Built state
- [Exit Codes](/docs/reference/exit-codes/) — why a dirty Repository maps to `5`
- [Observability & Audit](/docs/feature/audit/) — operating checks and audit together
