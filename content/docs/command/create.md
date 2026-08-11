---
title: "sow create"
linkTitle: "create"
description: "Generate a flat RPM/DEB repository in an ordinary directory — the Plain mode entry point."
url: "/docs/command/create/"
aliases: ["/docs/reference/cli/create/"]
weight: 100
icon: fa-solid fa-folder-tree
---

`sow create` turns a directory that already contains `.rpm` and `.deb` files into a flat repository
by writing indexes next to the packages. It is the whole of Plain mode: no `sow.yml`, no SQLite, no
Workspace discovery. This page covers the one-pass scan contract, the `--pigsty` completion gate,
and RPM signing with `--sign-with`.

## Synopsis

```text
sow create [DIR] [-j N] [--pigsty] [-S KEY [--overwrite]] [-T DUR | -N] [--json]
```

`DIR` defaults to the current directory.

## Description

`create` reads the top-level regular files in `DIR` and renders the index formats implied by what it
finds: `repodata/` when RPMs are present, `Packages` and `Packages.gz` when DEBs are present, both
when the directory is mixed. All architectures come from the package headers — Plain mode has no
architecture flag and no permit list.

Flat metadata only ever references packages in the same directory. RPM `location` is the bare
basename and DEB `Filename` is `./<basename>`, so both remain relative whether the directory is
exposed as a `file://` source or an HTTP root.

By default `create` does not delete, move, rename, re-sign or rewrite a single package byte. It only
replaces index paths it owns; unknown files are left alone.

## Options

| Flag | Description | Default |
|---|---|---|
| `-j, --jobs N` | Parallel workers for the single package hash/parse pass | logical CPU count |
| `--pigsty` | Enable Pigsty compatibility cleanup and completion marker | off |
| `-S, --sign-with KEY` | Sign unsigned RPMs with a 16/40/64-hex GPG key ID | off |
| `--overwrite` | Re-sign every RPM; requires `--sign-with` | off |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the versioned JSON envelope | false |
| `-h, --help` | Show help | — |

## Scan rules

- Only top-level regular files ending in `.rpm` or `.deb` are considered.
- No recursion, no symlink following, no Workspace config.
- Every valid version enters the index. Two files claiming the same logical coordinate with
  different content is a hard failure.
- A directory with no supported package is rejected in default mode. `--pigsty` accepts an empty
  authoritative set so an interrupted all-package cleanup can converge and write its marker.

```console
sow create /srv/empty
plain: scan /srv/empty: no supported top-level regular RPM or DEB packages
```

## Package I/O and final validation

For the normal unsigned path, each selected package has exactly one full content pass. A worker opens
it, computes SHA-256 once, parses its header/control metadata, and retains the complete parsed result.
RPM XML and DEB `Packages` are rendered from that retained result; neither rendering nor generated
metadata validation reopens package payloads. `--jobs` parallelizes this pass while canonical result
ordering keeps output bytes independent of worker scheduling.

Immediately before publication, `create` relists the top-level package set and compares file identity,
type/mode, size, and mtime with the post-scan snapshot. This is a cheap `stat` check, not a second hash.
A changed set or stat returns integrity error `5` before any staged output is published. Deliberately
preserving inode, size, and mtime while modifying bytes is outside the local cooperative-writer
contract.

Explicit RPM signing is an exception: copying, signing, signature verification, and parsing the final
signed RPM necessarily add reads for packages that are modified.

## Deterministic output and idempotence

The rendered metadata is byte-stable for a given input set: gzip output is deterministic, `repomd.xml`
carries `<revision>0</revision>` and timestamp `0`. Running `create` twice on an unchanged directory
rewrites nothing and reports `noop=true`:

```console
sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=false recovered=false

sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=true recovered=false
```

## The repo_complete gate

Default mode never creates `repo_complete`. If the marker already exists, `create` refuses to write
indexes rather than leaving a stale marker claiming a build that no longer matches:

```console
sow create /srv/pigsty
plain: marker gate /srv/pigsty/repo_complete: repo_complete exists; use --pigsty or remove it explicitly before rebuilding
```

Either re-run with `--pigsty` (which withdraws and republishes the marker in its documented order)
or remove the marker yourself.

## --pigsty

`--pigsty` enables three coupled compatibility actions in one invocation. Their publication order
is marker-gated, but the operation is rebuilt on retry rather than recovered from a journal:

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

Cleanup only touches top-level regular package files that parsed successfully and matched a rule.
Directories and unknown files are never removed by glob.

The publication order matters for callers that gate on the marker: the existing `repo_complete` is
withdrawn *before* indexes switch, matched packages are deleted only after replacement metadata is
installed, and the new marker is written last. A caller must treat a missing marker as incomplete.

{{% alert title="Marker semantics" color="info" %}}
Treat a missing `repo_complete` as "build in progress". That is the contract `--pigsty` is designed
around.
{{% /alert %}}

## Signing RPMs

`-S/--sign-with KEY` is the explicit authorization to modify RPM bytes. `KEY` is exactly 16, 40 or 64
hexadecimal characters; an `0x` prefix is not accepted. SOW normalizes it to
uppercase and passes it to the environment's `rpm --addsign` through the `_gpg_name` macro. The
private key, passphrase, GPG home, pinentry and any extra RPM macros come from your environment —
SOW never receives, persists or echoes a secret.

- Default: only RPMs with no parseable embedded OpenPGP signature are signed. Anything already
  signed keeps its bytes.
- `--overwrite` requires `--sign-with` and switches to `rpm --resign` over every retained RPM.
- Signing happens on a private same-filesystem stage copy. Each result is re-parsed to confirm the
  embedded signature, the signature-neutral digest and NEVRA are unchanged, and rpm-md is generated
  from the final complete bytes.
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

`create` takes a write lock on the target directory and honors `--timeout`/`--no-wait`. All metadata
is written to a private stage and validated before publication begins. The lock coordinates SOW
writers on the local machine; arbitrary external package mutation is unsupported.

Plain create does not create a durable operation journal, rollback pre-images, or recovery trash.
Publication consists of several single-file renames, so a crash may leave a partially replaced set of
derived files. Re-run `sow create` with the intended current options: it discards reserved stale Plain
temporary state and rebuilds all indexes from the packages that currently exist. `recovered` is
always `false`; a rerun is a fresh overwrite build, not replay.

A flat directory has no whole-repository generation pointer, and RPM plus DEB entry points cannot be
swapped in one POSIX rename. Plain therefore does not promise cross-file instantaneous atomicity. Use
`repo_complete` as the `--pigsty` gate, or use Managed mode when transactional recovery is required.

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

Replace a Pigsty plain build with eight workers:

```bash
sow create /www/pigsty -j 8 --pigsty
```

Failure envelope:

```console
sow create /srv/empty --json
{"schema":"sow.cli/v1","command":"create","ok":false,"repository":null,"operation":null,"result":{"dir":"","rpm":0,"deb":0,"kept":null,"removed":null,"marker":false,"noop":false,"recovered":false},"errors":[{"code":6,"class":"rejected","message":"operation rejected: plain: scan /srv/empty: no supported top-level regular RPM or DEB packages"}]}
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Indexes written, or unchanged input produced a no-op |
| `1` | Directory unreadable or missing, package parse failure, renderer failure, signing tool failure |
| `2` | Usage error — `--overwrite` without `--sign-with`, malformed key, `--no-wait` with a non-zero `--timeout` |
| `4` | Directory write lock held and `--no-wait` given or `--timeout` expired |
| `5` | Input set/stat changed before publication, or a controlled output path failed an integrity check |
| `6` | No supported package found, `repo_complete` gate hit, `--sign-with` on a DEB-only directory, coordinate conflict |

## See also

- [Plain Flat Repositories](/docs/feature/plain/) — the design behind `create`
- [Quick Start](/docs/start/quickstart/) — five-minute flat repository walkthrough
- [Repository Layout](/docs/reference/layout/) — what the flat tree looks like
- [Sign Your Repository](/docs/tutorial/signing/) — generating and using a signing key
