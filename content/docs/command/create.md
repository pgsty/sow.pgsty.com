---
title: "sow create"
linkTitle: "create"
description: "Generate RPM and DEB indexes beside package files."
categories: [Command]
tags: [cli, plain, rpm, deb]
url: "/docs/command/create/"
aliases: ["/docs/reference/cli/create/"]
weight: 100
icon: fa-solid fa-folder-tree
---

`sow create` writes RPM and DEB indexes beside the package files in a directory. Use it for a flat repository that does not need a managed Workspace. `DIR` defaults to the current directory.

## Synopsis

```text
sow create [DIR] [-j N] [--metadata-timestamp SECONDS] [--pigsty] [-S KEY [--overwrite]] [-T DUR | -N] [--json]
```

## Description

`create` reads the top-level regular package files in `DIR`. For RPMs, it generates `repodata/`. For DEBs, it generates `Packages` and `Packages.gz`. A mixed directory gets both formats. Architectures come from the package headers; Plain mode accepts all architectures found in the packages.

Indexes use relative package paths: the filename for RPM, and `./<filename>` for DEB. Serve the package directory through HTTP or use it as a local `file://` source.

By default, `create` updates its indexes and preserves the package files. `--pigsty` can delete matching packages, and `--sign-with` can replace RPMs with signed copies.

## Options

| Flag | Description | Default |
|---|---|---|
| `-j, --jobs N` | Parallel package-processing workers | logical CPU count |
| `--metadata-timestamp SECONDS` | Unix seconds from `0` to `253402300799` for RPM repomd data timestamps; leaves DEB, package times and gzip headers unchanged | `0` |
| `--pigsty` | Enable Pigsty compatibility cleanup and completion marker | off |
| `-S, --sign-with KEY` | Sign unsigned RPMs with a GPG key ID or fingerprint | off |
| `--overwrite` | Re-sign every RPM; requires `--sign-with` | off |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |
| `-h, --help` | Show help | — |

## Scan rules

- Only top-level regular files ending in `.rpm` or `.deb` are considered.
- No recursion, no symlink following, no Workspace config.
- Every valid version enters the index. Two files claiming the same logical coordinate with
  different content is a hard failure.
- A directory with no supported package is rejected in default mode. `--pigsty` accepts an empty
  package set so rerunning an interrupted cleanup can finish and write its marker.

```console
sow create /srv/empty
plain: scan /srv/empty: no supported top-level regular RPM or DEB packages
```

## Package I/O and final validation

Keep the input directory unchanged while `create` runs. SOW scans the packages, then checks for file changes before replacing the indexes. A detected change returns exit code `5`. Use `--jobs` to set the number of parallel package-processing workers.

## Deterministic output and idempotence

Without forced package re-signing, the rendered metadata is byte-stable for a given input set
and timestamp: gzip output is deterministic.
`repomd.xml` carries `<revision>0</revision>` and data timestamps defaulting to `0`;
`--metadata-timestamp` overrides the latter. Repeating the same options on an unchanged directory
rewrites nothing and reports `noop=true`:

```console
sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=false recovered=false

sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=true recovered=false
```

## The repo_complete gate

If the directory contains `repo_complete`, use `--pigsty` to refresh it with the indexes. Running without `--pigsty` returns an error:

```console
sow create /srv/pigsty
plain: marker gate /srv/pigsty/repo_complete: repo_complete exists; use --pigsty or remove it explicitly before rebuilding
```

To keep using the completion marker, rerun with `--pigsty`. If you no longer use it, move the marker out of the directory first.

## Publication time for existing YUM repositories

`--metadata-timestamp` sets the RPM repomd data timestamps. It does not change package files, compressed XML streams, or DEB indexes. The default is `0`, and the accepted range is `0..253402300799` Unix seconds. This option was added in SOW 0.5.0.

EL7 YUM rejects metadata whose maximum data timestamp is older than its cached copy. When replacing an existing metadata generator, choose a timestamp at least as large as the highest value previously published. For changed content, advance it by at least one second to distinguish updates.

```bash
sow create /srv/flat --metadata-timestamp "${PUBLISH_TIME:?Set the publication time}"
```

Record the publication time and pass it on every update. Omitting the option resets it to `0`. Restoring older package content is a new publication, so keep the timestamp increasing. Use seconds, not milliseconds, and avoid future dates.

If clients verify `repomd.xml.asc`, regenerate that signature after repomd changes. `create` neither signs repomd nor updates or removes its old detached signature.

See [Migrating an Existing YUM Repository](/docs/tutorial/yum-migration/) for the complete procedure.

## --pigsty

`--pigsty` applies these cleanup rules and writes a completion marker:

1. Delete DEB packages whose parsed architecture is `i386`. RPMs are not removed merely for
   carrying an `i386/i486/i586/i686` architecture.
2. Delete RPM/DEB whose binary package name is exactly `patroni` and whose upstream version is
   exactly `3.0.4`. RPM compares `VERSION`, ignoring epoch and release; DEB strips epoch and Debian
   revision first. `3.0.4+foo` is not a match.
3. After all indexes render successfully, write `repo_complete`: the SHA-256 of every remaining
   top-level RPM/DEB, sorted by basename byte order, formatted `<sha256><two spaces><basename>`.

```console
sow create /srv/pigsty --pigsty
created /srv/pigsty: rpm=2 deb=0 signed=0 removed=2 marker=true noop=false recovered=false
```

```console
cat /srv/pigsty/repo_complete
b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead  centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab  epel-release-7-5.noarch.rpm
```

Cleanup applies only to top-level regular package files that parsed successfully and matched a rule.

Documentation packages such as `annobin-docs` are retained unless they match one of those rules.

SOW removes the existing `repo_complete` before replacing indexes. It then deletes the packages matched by the cleanup rules and writes the new marker last. A missing marker means the build is incomplete.

## Signing RPMs

`-S/--sign-with KEY` signs RPM package files through the local RPM/GPG environment. Use a 16-digit hexadecimal key ID or a 40- or 64-digit fingerprint. An optional `0x` or `0X` prefix is accepted. Configure the private key and passphrase in that environment before running the command.

- Default: only RPMs with no parseable embedded OpenPGP signature are signed. Anything already
  signed keeps its bytes.
- `--overwrite` requires `--sign-with` and switches to `rpm --resign` over every retained RPM.
- SOW signs a temporary copy, checks that package identity and content are unchanged, then replaces the original RPM. The indexes describe the final signed file.
- At least one top-level RPM must remain after `--pigsty` cleanup, and `rpm` must be on `PATH`.

```console
sow create /srv/flat -S 0123456789ABCDEF --overwrite
plain: sign rpm epel-release-7-5.noarch.rpm: rpm executable is required for --sign-with
```

```console
sow create /srv/deb-only -S 0123456789ABCDEF
plain: sign rpm: --sign-with requires at least one retained top-level RPM package
```

```console
sow create /srv/flat --overwrite
usage error: --overwrite requires --sign-with
```

```console
sow create /srv/flat -S ZZZZ
usage error: --sign-with must be a 16, 40, or 64 hexadecimal GPG key ID/fingerprint
```

## Locking, staging and overwrite rebuild

`create` locks the target directory while it updates the indexes. Use `--timeout` or `--no-wait` to control lock waiting.

An interruption can leave only part of the index set updated. Rerun `sow create` with the same intended options to rebuild from the current packages. Plain mode rebuilds from scratch; the result field `recovered` remains `false`.

For `--pigsty`, expose the repository only after `repo_complete` appears. Use Managed mode when you need journaled recovery.

## Examples

Index a mixed directory:

```console
sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

```console
ls /srv/flat
centos-release-6-0.el6.centos.5.x86_64.rpm
centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
epel-release-7-5.noarch.rpm
libpq5_18.3-1_amd64.deb
Packages
Packages.gz
repodata
```

Machine-readable result:

```console
sow create /srv/flat --json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,"result":{"dir":"/srv/flat","rpm":3,"deb":1,"kept":["centos-release-6-0.el6.centos.5.x86_64.rpm","centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm","epel-release-7-5.noarch.rpm","libpq5_18.3-1_amd64.deb"],"removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

Build a Pigsty flat repository with eight workers and a publication time chosen from its history:

```bash
sow create /www/pigsty -j 8 --pigsty --metadata-timestamp "${PUBLISH_TIME:?Set the verified publication time}"
```

The caller records this time and signs the resulting `repomd.xml` when clients require it.

Failure envelope:

```console
sow create /srv/empty --json
{"schema":"sow.cli/v1","command":"create","ok":false,"repository":null,"operation":null,"result":null,"errors":[{"code":6,"class":"rejected","message":"operation rejected: plain: scan /srv/empty: no supported top-level regular RPM or DEB packages"}]}
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Indexes written, or unchanged input produced a no-op |
| `1` | Directory unreadable or missing, package parse failure, renderer failure, signing tool failure |
| `2` | Usage error — invalid or repeated timestamp, `--overwrite` without `--sign-with`, malformed key, `--no-wait` with a non-zero `--timeout` |
| `4` | Directory write lock held and `--no-wait` given or `--timeout` expired |
| `5` | Input set/stat changed before publication, or a controlled output path failed an integrity check |
| `6` | No supported package found, `repo_complete` gate hit, `--sign-with` on a DEB-only directory, coordinate conflict |

## See also

- [Plain Flat Repositories](/docs/feature/plain/) — the design behind `create`
- [Quick Start](/docs/start/quickstart/) — five-minute flat repository walkthrough
- [Repository Layout](/docs/reference/layout/) — what the flat tree looks like
- [Sign Your Repository](/docs/tutorial/signing/) — generating and using a signing key
- [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) — replacing an existing metadata generator
