---
title: "Repository Layout"
linkTitle: "Layout"
description: "Locate package files, repository indexes, private state, and publication output."
categories: [Reference]
tags: [repository, pool, dist]
url: "/docs/reference/layout/"
weight: 400
icon: fa-solid fa-folder-tree
---

Serve the complete Managed repository directory: `pool/` plus `dists/`.
Keep workspace configuration and `.sow/` state outside the web server's document root.

<span id="plain-mode" data-td-print-local></span>

## Plain directory

```text
/srv/offline/
├── example-1.0-1.x86_64.rpm
├── example_1.0-1_amd64.deb
├── repodata/
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   └── repomd.xml
├── Packages
├── Packages.gz
└── repo_complete                     # with --pigsty
```

`sow create` writes RPM metadata only when RPMs are present and DEB metadata only when
DEBs are present. RPM locations use a bare basename; DEB locations use `./<basename>`.
A running build uses private `.sow-plain-stage-*` directories. Exclude them from serving
and copying. A later `create` removes stale SOW temporary paths and rebuilds the indexes.

## Managed workspace

```text
<workspace>/
├── sow.yml                           # workspace configuration
├── .sow/                             # private state
│   ├── workspace.lock
│   ├── workspace-ops/
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db
│   └── <repo>/
│       ├── stage/
│       ├── recovery/
│       ├── retained/
│       ├── transitions/
│       └── pending/
└── <repo>/                           # public repository root
    ├── pool/
    └── dists/
```

The database can have SQLite WAL and shared-memory sidecar files.
`.sow/` and pending directories are private (`0700`). Pending payload files use `0644`
so they can be promoted to public paths without changing their mode.

SOW 0.5 uses database schema v13 and configuration schema `sow/v3`. These are separate
version identifiers. Back up the complete workspace before
[`repo migrate`](/docs/command/repo/#sow-repo-migrate). Keep the database with its matching
private and public state; do not edit its schema version or rebuildable cache by hand.

<span id="canonical-pool" data-td-print-local></span>

## Package pool

```text
pool/<prefix>/<source>/<filename>
```

`source` comes from the RPM `SOURCERPM` or DEB `Source` field, normalized to a source
package name. If absent, SOW uses the binary package name. The prefix is the first
character converted to lowercase. If the source starts with lowercase `lib`, use its first
four characters, or the whole name when it is shorter, converted to lowercase.

| Source | Example path |
|---|---|
| `postgresql-18` | `pool/p/postgresql-18/libpq5_18.3-1_amd64.deb` |
| `example` | `pool/e/example/example-1.0-1.x86_64.rpm` |
| `libfoo` | `pool/libf/libfoo/libfoo1_1.0-1_amd64.deb` |

Package objects are immutable. Membership removal leaves the bytes available to built,
retained, recovery, and publication records. [`gc`](/docs/command/gc/) removes them when
those records no longer need them. Each repository owns its own pool.

<span id="rpm-metadata-only-views" data-td-print-local></span>

## RPM Dist

```text
dists/el9/
├── x86_64/repodata/
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   ├── repomd.xml
│   └── repomd.xml.asc                # with metadata signing
└── aarch64/repodata/
    └── ...
```

Architecture views contain metadata only. Each package location points back to the root pool:

```xml
<location href="../../../pool/e/example/example-1.0-1.x86_64.rpm"/>
```

Native packages appear in their matching architecture view. `noarch` packages appear in
all configured views. Previous checksum-named metadata can remain alongside the current
files; `repomd.xml` selects the active set.

For a self-contained directory with local package paths, use
[`export rpm-leaf`](/docs/command/export/).

<span id="deb-views" data-td-print-local></span>

## DEB Dist

```text
dists/trixie/
├── Release
├── InRelease                         # with metadata signing
├── Release.gpg                       # with metadata signing
└── main/
    ├── binary-amd64/
    │   ├── Packages
    │   ├── Packages.gz
    │   └── by-hash/SHA256/<digest>
    └── binary-arm64/
        └── ...
```

`Packages` entries use root-relative archive paths such as
`Filename: pool/e/example/example_1.0-1_amd64.deb`.
`Release` contains SHA-256 manifests and `Acquire-By-Hash: yes`.
Architecture `all` packages appear in each applicable index.

<span id="publication-targets" data-td-print-local></span>

## Publication paths

Both target providers receive the same public layout:

```text
<prefix>/
├── pool/
└── dists/
```

An export has its own package files, metadata, manifest, and `.sow-export.json` completion
marker. It is a separate delivery artifact and is not another Managed repository.

<span id="names-and-serving-boundary" data-td-print-local></span>

## Names and case sensitivity

Repository, Dist, and target names use `[a-z0-9][a-z0-9._-]*`.
Reserved names include `.`, `..`, `.sow`, `pool`, `dists`, `sow.yml`, `workspace.lock`,
`workspace-ops`, and `repo-locks`.

A new pool path that differs only in case from a known full path is rejected, even for
identical bytes. On a case-insensitive filesystem, source directories that differ only
in case also conflict. On a case-sensitive filesystem those source directories can remain
distinct, so check them before moving a repository to a case-insensitive volume.

See [Views](/docs/feature/views/), [Serving](/docs/tutorial/serving/), and
[Platforms](/docs/reference/compatibility/).

<span id="see-also" data-td-print-local></span>
