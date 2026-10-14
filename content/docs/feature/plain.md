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

<span id="contract"></span>
<span id="scan-and-output-rules"></span>

## Inputs and outputs

SOW scans top-level regular files with `.rpm` or `.deb` suffixes. It does not recurse or
follow package symlinks. Package names, versions, and architectures come from package
headers. Source RPMs (`src` and `nosrc`) are rejected.

| Input | Generated files |
|---|---|
| RPM | `repodata/repomd.xml` and gzip-compressed `primary`, `filelists`, and `other` XML |
| DEB | `Packages` and `Packages.gz` |
| Both formats | Both sets of indexes |

RPM locations use the package basename. DEB `Filename` values use `./<basename>`.
All valid versions are included. Different bytes with the same package coordinate cause
a conflict. A directory with no supported packages is rejected, except when `--pigsty`
finishes an interrupted cleanup.

By default, package files and unrelated files stay unchanged. If a format disappears,
SOW removes its old generated indexes. It also removes obsolete SOW-shaped RPM metadata
and replaces incomplete output from an earlier run. Generated directories use `0755`;
generated files use `0644`.

<span id="the-one-pass-pipeline"></span>
<span id="what-the-final-stat-check-proves"></span>
<span id="determinism-and-no-op"></span>

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

<span id="publication-and-interruption-semantics"></span>

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

<span id="the---pigsty-marker-gate"></span>

## Pigsty cleanup and completion marker

```bash
sow create /srv/offline --pigsty
```

`--pigsty` removes DEB `i386` packages and Patroni 3.0.4 packages according to parsed
package facts. It does not remove an RPM solely because its architecture is
`i386`, `i486`, `i586`, or `i686`.

Documentation packages such as `annobin-docs` are retained unless they match those cleanup rules.

After updating indexes and removing the selected packages, SOW writes `repo_complete`.
Each line contains a SHA-256, two spaces, and a retained package basename. Lines are
sorted by basename.

SOW removes an existing marker before replacing public files and writes the new marker
last. Consumers that use this convention must wait for the marker. If the build stops
without a marker, rerun with `--pigsty`. A plain invocation without `--pigsty` refuses to
rebuild a directory that already contains `repo_complete`.

<span id="explicit-rpm-signing"></span>

## RPM package signing

```bash
sow create /srv/offline --sign-with 6D5C5A26C36B1F73
```

This option signs RPMs that have no parseable embedded signature. Add `--overwrite` to
re-sign every retained RPM. It requires the host `rpm` command and a usable GPG key.
SOW signs and checks staged copies, then replaces the package files before their indexes.
This path reads package bytes more than once.

Plain mode does not sign repository metadata. See [Signing](/docs/feature/signing/) for
Managed metadata signing and package-signing policy.

<span id="locking-and-scope"></span>

## Concurrent commands

`sow create` locks the target directory and its parent. Use `-N` to fail immediately if
another SOW writer holds the lock, or `-T 30s` to wait up to 30 seconds. The default waits
until the lock becomes available.

See [`sow create`](/docs/command/create/) for all options and result fields.

<span id="next"></span>
