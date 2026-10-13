---
title: "sow ls"
linkTitle: "ls"
description: "List Desired packages and their Built locations."
categories: [Command]
tags: [cli, managed]
url: "/docs/command/ls/"
weight: 800
icon: fa-solid fa-list
---

`sow ls` lists packages in the selected Dists' Desired membership. Each row also shows the package's Desired and Built locations across the Repository. Use it to obtain package references for `show` or `rm`.

## Synopsis

```text
sow ls [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Select a Dist; repeatable | [selection rules](/docs/command/#dist-selection) |
| `--json` | Output JSON | false |

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
| `DISTS` | Desired membership across the Repository |
| `BUILT_DISTS` | Membership present in the current Built Generation |
| `POOL_PATH` | Repository-relative immutable payload path |

The first line reports whether the selected Dists are dirty. Configuration changes can make them dirty even when membership counts match.

`-d` selects rows by Desired membership. The `DISTS` and `BUILT_DISTS` columns then show all locations of each returned package in the Repository. A package removed with `rm --skip` is absent from this list even while an older Built index still contains it. An empty `BUILT_DISTS` means no local Built Dist currently includes that package.

Each package appears once, with multiple Dists separated by commas. An empty Dist produces a successful result with no package rows.

## Selection

`ls` requires an unambiguous Dist set. In a multi-Dist Repository, pass one or more `-d` values or
run from inside `<repo>/dists/<dist>/`.

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

With `--json`, the same rows appear in `result.packages`.

## Examples

List exact references for all objects not yet built:

```bash
sow ls -r pgsql -d el9 --json |
  jq -r '.result.packages[] | select(.built_dists | length == 0) | "sha256:" + .sha256'
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
