---
title: "sow show"
linkTitle: "show"
description: "Inspect one package and its storage and membership."
categories: [Command]
tags: [cli, managed, signing]
url: "/docs/command/show/"
weight: 900
icon: fa-solid fa-file-lines
---

`sow show` displays one package in the selected Repository. The text output summarizes its identity, storage, and membership. Add `--json` for the complete stored package record.

## Synopsis

```text
sow show PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Narrow candidates to these Dists; repeatable | Repository scope |
| `--json` | Output JSON | false |

## Package reference

`PACKAGE` accepts a `sha256:<hex>` content identity, canonical `rpm:<NEVRA>` or
`deb:<name>=<version>:<arch>` coordinate, full package filename, or bare binary name. See
[Package References](/docs/reference/package-ref/) for the exact grammar.

A bare name must resolve to exactly one Package Object in the selected scope. Unlike `sow rm foo`,
which removes every matching version from Desired Membership, `sow show foo` refuses ambiguity and
prints the candidates:

```console
sow show libpq5 -r pgsql -d trixie
operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1:amd64 sha256:fa84dc64..., deb:libpq5=18.3-1:amd64 sha256:491992c5..., deb:libpq5=18.3-1:arm64 sha256:3a2f7ef7...
```

Copy an exact coordinate or SHA-256 from the error or from [`sow ls`](/docs/command/ls/) and retry.

## Output

Without `--json`, `show` prints the identity, storage path, and Desired/Built locations in a compact
human-readable form:

```console
sow show centos-release-6-0.el6.centos.5.x86_64.rpm -r demo -d el9
package repository=demo coordinate="centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16 format=rpm architecture=x86_64 size=19776 storage=pool
pool=pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
dists=el9 built_dists=el9
```

Adding `--json` returns the complete Package Object under `result.package` in the standard envelope,
including the normalized fields below.

| Field | Meaning |
|---|---|
| `canonical_arch` | `x86_64`, `aarch64`, or `neutral` for RPM `noarch` / DEB `all` |
| `kind` | Policy class: `main`, `debuginfo`, `debugsource`, `llvmjit`, `dbgsym`, or `dbg` |
| `source` | Normalized source-package name |
| `payload_sha256` | RPM signature-neutral digest used for re-signing idempotence |
| `signature_key` | Embedded package-signature key ID, when present |
| `storage` | `pending` before build; `pool` once placed in the local package pool |
| `dists` / `built_dists` | Desired and current Built Membership |

Without `-d`, lookup includes stored objects with no current membership. With `-d`, candidates must be Desired members of a selected Dist. The returned `dists` and `built_dists` lists cover the entire Repository.

## Exit codes

| Code | Trigger |
|---|---|
| `0` | One Package Object printed |
| `1` | Runtime I/O failure |
| `2` | Usage error, Workspace not found, or implicit Repository selection is ambiguous |
| `5` | Repository state database unreadable or inconsistent |
| `6` | Explicit scope is not configured, or the reference matched nothing/several objects |

## See also

- [`sow ls`](/docs/command/ls/) — obtain exact identities from Dist Membership
- [`sow where`](/docs/command/where/) — search across Repositories
- [`sow rm`](/docs/command/rm/) — remove matching Desired Membership
- [JSON Output](/docs/reference/json/) — complete result schema
