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
sow rm centos-release -r pigsty -d el9 -c
{"repository":"pigsty","desired_revision":6,"built_generation":"00000000000000000006","dirty":false,"check":true,"removed":[{"dist":"el9","sha256":"ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16","coordinate":"rpm:centos-release-0:6-0.el6.centos.5.x86_64","name":"centos-release"},{"dist":"el9","sha256":"b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead","coordinate":"rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64","name":"centos-release"}],"dists":["el9"],"changes":[{"op":"add","path":"dists/el9/x86_64/repodata/29eb03d70470cb4ed836017414d6039482e6ee8e4cdfbafe9cc78ba052c8d2dc-filelists.xml.gz","phase":"metadata","size":374,"sha256":"29eb03d70470cb4ed836017414d6039482e6ee8e4cdfbafe9cc78ba052c8d2dc"},{"op":"update","path":"dists/el9/x86_64/repodata/repomd.xml","phase":"pointer","size":1511,"sha256":"ef071821e06c9e86ab4f6d2a56906d82bb66df251e79d1086cfd44dc8395513e"},{"op":"delete","path":"dists/el9/x86_64/repodata/85de802ed1249f8693c973ae44d704e3cc5047da571b52c1ddebc8de35a46b60-primary.xml.gz","phase":"delete"}]}
```

Note both `centos-release` versions matched the bare name. The `changes` array is a real delivery
plan in `payload → metadata → pointer → delete` phase order.

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
sow rm 'rpm:centos-release-0:6-0.el6.centos.5.x86_64' -r pigsty -d el9
{"operation":"1811402670494469758","repository":"pigsty","desired_revision":6,"built_generation":"00000000000000000006","dirty":false,"check":false,"removed":[{"dist":"el9","sha256":"ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16","coordinate":"rpm:centos-release-0:6-0.el6.centos.5.x86_64","name":"centos-release"}],"dists":["el9"],"changes":[...]}
```

Like `sow build` and `sow show`, `rm` prints structured JSON on stdout even without `--json`; adding
`--json` wraps it in the standard envelope.

Removing the last member of a Dist is fine. SOW still renders a valid, signed-if-configured empty
index — an empty `Packages` with a verifiable `InRelease`, or empty per-architecture `repodata/`.

## --skip

`--skip` commits the Desired change and marks the Repository dirty without touching the public tree.
The old Built Generation stays completely self-consistent for clients.

```console
sow rm 'rpm:centos-release-0:6-0.el6.centos.5.x86_64' -r pigsty -d el9 --skip
{"operation":"1811402670494469758","repository":"pigsty","desired_revision":6,"built_generation":"00000000000000000005","dirty":true,"check":false,"removed":[...],"dists":["el9"],"changes":[]}
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
| `3` | Partial batch — at least one reference removed and at least one failed |
| `4` | Repository lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error |
| `6` | A reference matched nothing, or an ambiguous non-bare reference |

## See also

- [Package References](/docs/reference/package-ref/) — the full reference grammar
- [`sow ls`](/docs/command/ls/), [`show`](/docs/command/show/), and [`where`](/docs/command/where/) — finding the exact reference to remove
- [sow add](/docs/command/add/) — the inverse operation
- [sow build](/docs/command/build/) — converging after `--skip`
- [Membership Policy](/docs/feature/policy/) — why removed members do not come back
- [`sow retain`](/docs/command/retain/) and [`sow gc`](/docs/command/gc/) — when bytes can be reclaimed
