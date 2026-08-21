---
title: "sow show"
linkTitle: "show"
description: "Inspect one Package Object, including identity, normalized facts, storage, signature, and membership."
categories: [Command]
tags: [cli, managed, signing]
url: "/docs/command/show/"
weight: 900
icon: fa-solid fa-file-lines
---

`sow show` resolves one package reference in the selected Repository and prints the complete Package
Object. It is read-only and takes no write lock.

## Synopsis

```text
sow show PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Narrow candidates to these Dists; repeatable | Repository scope |
| `--json` | Wrap the result in the `sow.cli/v1` envelope | false |

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

The command-specific result is JSON even without `--json`, because the object has no useful compact
table form:

```console
sow show 'rpm:epel-release-0:7-5.noarch' -r pigsty -d el9
{"repository":"pigsty","package":{"sha256":"d6f332ed...","format":"rpm","coordinate":"epel-release-0:7-5.noarch","architecture":"noarch","canonical_arch":"neutral","pool_path":"pool/e/epel-release/epel-release-7-5.noarch.rpm","name":"epel-release","source":"epel-release","version":"7","epoch":"0","release":"5","kind":"main","signature_key":"24C6A8A7F4A80EB5","storage":"pool","created_revision":3,"dists":["el9"],"built_dists":["el9"]}}
```

Adding `--json` places that result under `result` in the standard envelope.

| Field | Meaning |
|---|---|
| `canonical_arch` | `x86_64`, `aarch64`, or `neutral` for RPM `noarch` / DEB `all` |
| `kind` | Policy class: `main`, `debuginfo`, `debugsource`, `llvmjit`, `dbgsym`, or `dbg` |
| `source` | Normalized source-package name |
| `payload_sha256` | RPM signature-neutral digest used for re-signing idempotence |
| `signature_key` | Embedded package-signature key ID, when present |
| `storage` | `pending` before build; `pool` once published into the repository tree |
| `dists` / `built_dists` | Desired and current Built Membership |

`-d` narrows candidate resolution; it does not alter package identity.

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
