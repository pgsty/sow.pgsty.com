---
title: "sow ls"
linkTitle: "ls"
description: "List Desired and Built package membership for the selected Dists."
url: "/docs/command/ls/"
weight: 800
icon: fa-solid fa-list
---

`sow ls` is a read-only query over Package Objects and Dist Membership. It shows what each selected
Dist should contain and whether that membership is present in the current Built Generation.

## Synopsis

```text
sow ls [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Select a Dist; repeatable | [selection rules](/docs/command/#dist-selection) |
| `--json` | Emit the `sow.cli/v1` envelope | false |

There is no `--pool`, `--match`, or output-format flag.

## Output

```console
sow ls -r pigsty -d el9
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab	rpm:epel-release-0:7-5.noarch	el9	el9	pool/e/epel-release/epel-release-7-5.noarch.rpm
```

| Column | Meaning |
|---|---|
| `SHA256` | Immutable content identity; valid input to `show` and `rm` |
| `COORDINATE` | Canonical `rpm:` or `deb:` package reference |
| `DISTS` | Desired Membership across the selected scope |
| `BUILT_DISTS` | Membership present in the current Built Generation |
| `POOL_PATH` | Repository-relative immutable payload path |

The first line reports `dirty=true` when Desired and Built state differ. An empty `BUILT_DISTS`
field means the package is desired but clients cannot see it yet. Run [`sow build`](/docs/command/build/)
to converge.

An object shared by several selected Dists appears once, with comma-separated membership values.
An empty Dist has a header and no package rows; that is a successful result.

## Selection

`ls` requires an unambiguous Dist set. In a multi-Dist Repository, pass one or more `-d` values or
run from inside `<repo>/dists/<dist>/`.

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

The command takes no write lock and does not hash package files. `--json` returns the same rows in
`result.packages`.

## Examples

List exact references for all objects not yet built:

```bash
sow ls -r pgsql -d el9 --json |
  jq -r '.result.packages[] | select(.built_dists | length == 0) | .sha256'
```

List pool paths in deterministic order:

```bash
sow ls -r pgsql -d el9 --json | jq -r '.result.packages[].pool_path' | sort
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Membership printed, including an empty list |
| `1` | Runtime I/O failure |
| `2` | Usage error, Workspace not found, or implicit Repository/Dist selection is ambiguous |
| `5` | Repository state database unreadable or inconsistent |
| `6` | Explicit Repository or Dist is not configured |

## See also

- [`sow show`](/docs/command/show/) — inspect one listed object
- [`sow where`](/docs/command/where/) — locate an object across the Workspace
- [`sow rm`](/docs/command/rm/) — remove a listed reference from Desired Membership
- [Package References](/docs/reference/package-ref/) — accepted identity forms
