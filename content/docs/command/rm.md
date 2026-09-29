---
title: "sow rm"
linkTitle: "rm"
description: "Remove Desired Membership from selected Dists, with a no-write preview mode."
categories: [Command]
tags: [cli, managed, policy]
url: "/docs/command/rm/"
aliases: ["/docs/reference/cli/rm/"]
weight: 700
icon: fa-solid fa-minus
---

`sow rm` takes packages out of the Desired Membership of the Dists you select and, by default,
rebuilds the affected indexes immediately. It does not delete bytes from `pool/` — membership and
content are separate concepts, and reclamation is the separate conservative `sow gc` operation.

## Synopsis

```text
sow rm PACKAGE... [-c|--check] [--skip] [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

## Options

| Flag | Description | Default |
|---|---|---|
| `-c, --check` | Preview only; compute and print the plan without writing anything | off |
| `--skip` | Update Desired state only; do not build | off |
| `-j, --jobs N` | Parallel workers | logical CPU count |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Select a distribution; repeatable | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the versioned JSON envelope | false |

`--check` and `--skip` are mutually exclusive:

```console
sow rm epel-release -c --skip
usage error: --check and --skip are mutually exclusive
```

## Package references

`PACKAGE` accepts five forms. The full grammar and disambiguation rules are on
[Package References](/docs/reference/package-ref/); the short version:

| Form | Example |
|---|---|
| Content hash | `sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab` |
| RPM coordinate | `rpm:epel-release-0:7-5.noarch` |
| DEB coordinate | `deb:libpq5=18.3-1:amd64` |
| Full filename | `epel-release-7-5.noarch.rpm` |
| Bare binary name | `epel-release` |

A bare name means *every version and native architecture of that name* in the selected Dists — that
is what makes `sow rm patroni` a useful takedown command. An ambiguous short reference that is not a
bare name fails and lists the candidates instead of guessing.

[`sow ls`](/docs/command/ls/) prints exact `sha256:` references and canonical coordinates,
so you never have to assemble one by hand.

A reference matching nothing is a rejection, not a silent success:

```console
sow rm nosuch -r pigsty -d el9
operation rejected: managed: operation rejected: package reference not found: package reference "nosuch" matches no Desired Membership
```

There is no `--allow-empty`, no `--all`, no `--yes` and no `--source-list`.

## Preview with --check

`-c/--check` computes exactly what would be removed, what policy would then decide, and which files
an immediate build would touch — and writes nothing at all.

```console
sow rm centos-release -r demo -d el9 -c
preview repository=demo operation= dists=el9 memberships=2 revision=2 generation=00000000000000000003 dirty=false changes=2
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead
change op=update phase=pointer path="dists/el9/aarch64/repodata/repomd.xml" size=1509 sha256:1cfe38698967d11384f1a985618d75f5e690d1284accf951262fc663fa9afc81
change op=update phase=pointer path="dists/el9/x86_64/repodata/repomd.xml" size=1509 sha256:1cfe38698967d11384f1a985618d75f5e690d1284accf951262fc663fa9afc81
```

Note both `centos-release` versions matched the bare name. The `change` lines are a real delivery
plan in `payload → metadata → pointer → delete` phase order. Use `--json` when another program needs
the corresponding `removed[]` and `changes[]` arrays.

Preview uses the same candidate-configuration and integrity preflight as the mutation. A preview
that fails that guard is not evidence that the write would succeed.

`--check` deliberately does not take the write lock. Combining it with lock flags is a usage error,
so nobody can believe a preview is queueing behind a writer:

```console
sow rm centos-release -r pigsty -d el9 -c -T 5s
usage error: rm --check does not accept --timeout or --no-wait
```

## Default behavior: remove and rebuild

Without `--check` or `--skip`, `rm` commits the Desired change and rebuilds every affected Dist
before returning. Pool objects stay on disk.

```console
sow rm 'rpm:centos-release-0:6-0.el6.centos.5.x86_64' -r demo -d el9
removed repository=demo operation=2283442100870457321 dists=el9 memberships=1 revision=2 generation=00000000000000000003 dirty=false changes=8
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
```

The summary is followed by one `change` line per affected file (eight in this run). Add `--json` to
receive the same result as a stable standard envelope.

Removing the last member of a Dist is fine. SOW still renders a valid, signed-if-configured empty
index — an empty `Packages` with a verifiable `InRelease`, or empty per-architecture `repodata/`.

## --skip

`--skip` commits the Desired change and marks the Repository dirty without touching the public tree.
The old Built Generation stays completely self-consistent for clients.

```console
sow rm 'rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64' --skip -r demo -d el9
removed repository=demo operation=314678479940914827 dists=el9 memberships=1 revision=4 generation=00000000000000000004 dirty=true changes=0
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead
```

```console
sow status -r pigsty
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5 dirty_dists=el9 pending=0/0 locked=false
```

`changes` is empty because nothing was built. Run [`sow build`](/docs/command/build/) to
converge.

## Policy interaction

Removals are Desired-state edits, so policy is re-evaluated over the resulting candidate set — a
removal will never resurrect a package that `limit` previously pushed out. If you remove `libpq5
18.3-1` from a `limit: 1` Dist, `18.2-1` does not come back; add it again explicitly.

## Examples

Safe takedown — preview first, then execute:

```bash
sow rm patroni -r pgsql -d el9 -c
sow rm patroni -r pgsql -d el9
```

Remove one exact object from two Dists at once:

```bash
sow rm sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab -r pgsql -d el9 -d el9-beta
```

Batch several removals, then rebuild once:

```bash
sow rm old-tool legacy-agent -r pgsql -d el9 --skip
sow build -r pgsql -d el9
sow check -r pgsql
```

Feed the preview plan to another tool:

```bash
sow rm patroni -r pgsql -d el9 -c --json | jq -r '.result.changes[] | "\(.phase)\t\(.op)\t\(.path)"'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Memberships removed and rebuilt, or a `--check` preview printed |
| `1` | Runtime I/O or renderer failure |
| `2` | Usage error — `--check` with `--skip`, `--check` with lock flags, ambiguous selection, Workspace not found |
| `4` | Repository lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error |
| `6` | A reference matched nothing, or a non-bare reference was ambiguous; the whole batch is rejected and no memberships are removed |

## See also

- [Package References](/docs/reference/package-ref/) — the full reference grammar
- [`sow ls`](/docs/command/ls/), [`show`](/docs/command/show/), and [`where`](/docs/command/where/) — finding the exact reference to remove
- [sow add](/docs/command/add/) — the inverse operation
- [sow build](/docs/command/build/) — converging after `--skip`
- [Membership Policy](/docs/feature/policy/) — why removed members do not come back
- [`sow retain`](/docs/command/retain/) and [`sow gc`](/docs/command/gc/) — when bytes can be reclaimed
