---
title: "Plain Flat Repositories"
linkTitle: "Plain Flat Repositories"
description: "Build flat RPM and DEB indexes, repeat interrupted builds, and use signing or the Pigsty marker."
categories: [Feature]
tags: [plain, rpm, deb]
url: "/docs/feature/plain/"
weight: 200
icon: fa-solid fa-folder-open
---

Use `sow create` to build indexes for a directory of RPM or DEB packages. It writes the
indexes beside the packages. It does not read `sow.yml` or create a state database.

```bash
sow create /srv/offline
```

<span id="contract" data-td-print-local></span>
<span id="scan-and-output-rules" data-td-print-local></span>

## Inputs and outputs

SOW scans top-level regular files with `.rpm` or `.deb` suffixes. It does not recurse or
follow package symlinks. Package names, versions, and architectures come from package
headers. SOW rejects source RPMs (`src` and `nosrc`).

| Input | Generated files |
|---|---|
| RPM | `repodata/repomd.xml` and gzip-compressed `primary`, `filelists`, and `other` XML |
| DEB | `Packages` and `Packages.gz` |
| Both formats | Both sets of indexes |

RPM locations use the package basename. DEB `Filename` values use `./<basename>`.
SOW includes all valid versions. Different bytes with the same package coordinate cause
a conflict. SOW rejects a directory with no supported packages, except when `--pigsty`
finishes an interrupted cleanup.

By default, package files and unrelated files stay unchanged. If a format disappears, SOW removes its old generated indexes.
For RPMs, it keeps the current and immediately previous checksum-named metadata sets. It removes older SOW-shaped metadata and replaces incomplete output. If `repodata/` contains non-SOW files such as SQLite databases, modulemd, comps, or `.asc` signatures, `sow create` removes those foreign files and reports them in `dropped_metadata` (`--json`) and as a stderr warning.
Generated directories use `0755`; generated files use `0644`.

<span id="the-one-pass-pipeline" data-td-print-local></span>
<span id="what-the-final-stat-check-proves" data-td-print-local></span>
<span id="determinism-and-no-op" data-td-print-local></span>

## Build and repeat

The normal unsigned build reads each selected package once to calculate SHA-256 and
parse its metadata. `--jobs` controls this work and defaults to the logical CPU count.
SOW renders and validates the indexes from those parsed facts.

Before replacing the indexes, SOW checks the package list, file identity, mode, size,
and modification time again. Keep other programs from changing packages during the build.
A changed snapshot stops publication with exit code `5`.

Identical package bytes and options produce identical metadata. If the generated files
already match, the command reports `noop=true` in text output or `noop: true` in JSON and leaves them in place.

RPM metadata uses revision `0` and data timestamp `0` by default. Set a publication time
when updating an existing repository used by EL7 YUM:

```bash
sow create /srv/offline --metadata-timestamp 1791849600
```

The timestamp changes `repomd.xml` only. It does not change the compressed XML, package
bytes, or DEB indexes. Maintain a timestamp that advances from the existing repository;
see [YUM migration](/docs/tutorial/yum-migration/).

<span id="publication-and-interruption-semantics" data-td-print-local></span>

A small `.sow-plain-rpm-history.json` file tracks RPM metadata retention.
Unchanged builds keep the same previous index. Keep this file when copying a directory that you will rebuild.
Package retention remains the operator's responsibility. See [RPM index retention](/docs/command/create/#keep-the-previous-rpm-indexes).

## Prune superseded RPMs

Use [`sow prune`](/docs/command/prune/) to keep only the highest EVR per RPM `(name, arch)` in a Plain directory:

```bash
sow prune /srv/offline --check
sow prune /srv/offline
```

`sow prune` compares versions with native `rpmvercmp` rules, including `~` pre-release and `^` post-release caret sorting. It updates `repodata/` before removing superseded `.rpm` files so clients never observe metadata that points to missing packages. If the directory already contains `repo_complete`, `sow prune` refreshes that marker automatically. Unlike `sow create`, `sow prune` refuses to run when `repodata/` contains foreign non-SOW metadata files.

## Interrupted builds

SOW stages and checks metadata before it replaces public files. The replacements do not
form one transaction across all RPM and DEB files. An interruption can leave mixed or
incomplete indexes.

Run the same `sow create` command again. It removes its stale temporary files and rebuilds
from the packages currently in the directory. Plain mode has no operation journal;
the JSON field `recovered` is always `false`.

For a live service, build in a separate directory and switch the complete directory into
service after the command succeeds. Use [Managed mode](/docs/feature/managed/) when you
need recorded membership, generations, and transaction recovery.

<span id="the---pigsty-marker-gate" data-td-print-local></span>

## Pigsty cleanup and completion marker

```bash
sow create /srv/offline --pigsty
```

`--pigsty` removes DEB `i386` packages and Patroni 3.0.4 packages according to parsed
package facts. It does not remove an RPM solely because its architecture is
`i386`, `i486`, `i586`, or `i686`.

SOW retains documentation packages such as `annobin-docs` unless they match those cleanup rules.

After updating indexes and removing the selected packages, SOW writes `repo_complete`.
Each line contains a SHA-256, two spaces, and a retained package basename, sorted by basename.

SOW removes an existing marker before replacing public files and writes the new marker
last. Consumers that use this convention must wait for the marker. If the build stops
without a marker, rerun with `--pigsty`. A plain invocation without `--pigsty` refuses to
rebuild a directory that already contains `repo_complete`.

<span id="explicit-rpm-signing" data-td-print-local></span>

## RPM package signing

```bash
sow create /srv/offline --sign-with 6D5C5A26C36B1F73
```

This option signs RPMs that have no parseable embedded signature. Add `--overwrite` to
re-sign every retained RPM. It requires the host `rpm` command and a usable GPG key.
SOW signs and checks staged copies, then replaces the package files before their indexes.
This path reads package bytes more than once.

For a protected key, pass `--passfile PATH` or set
`SOW_GPG_PASSFILE`. `--sign-with` is still required to enable signing.
See [Password files](/docs/reference/config/#passfile) for the exact file format;
Plain mode does not read the Managed `sow.yml` configuration.

Plain mode does not sign repository metadata. See [Signing](/docs/feature/signing/) for
Managed metadata signing and package-signing policy.

<span id="locking-and-scope" data-td-print-local></span>

## Concurrent commands

`sow create` locks the target directory and its parent. Use `-N` to fail immediately if
another SOW writer holds the lock, or `-T 30s` to wait up to 30 seconds. The default waits
until the lock becomes available.

See [`sow create`](/docs/command/create/) for all options and result fields.

<span id="next" data-td-print-local></span>
