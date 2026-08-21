---
title: "Repository Layout"
linkTitle: "Layout"
description: "Public and private paths, including the canonical pool and metadata-only views."
categories: [Reference]
tags: [repository, pool, dist]
url: "/docs/reference/layout/"
weight: 400
icon: fa-solid fa-folder-tree
---

SOW has one fixed Managed layout: package payloads live once under `pool/`, while
`dists/` contains metadata-only client views. The complete repository directory is the
unit to serve, copy, or publish.

## Plain mode

`sow create` writes indexes next to existing packages and leaves every unrelated file
unchanged:

```text
/srv/offline/
├── blackbox_exporter-0.28.0-1.x86_64.rpm
├── libpq5_18.3-1.pgdg12+1_amd64.deb
├── repodata/
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   └── repomd.xml
├── Packages
├── Packages.gz
└── repo_complete                         # only with --pigsty
```

Flat RPM metadata uses a bare package basename; flat DEB metadata uses `./<filename>`.
While a build is active, `.sow-plain-stage-*` contains private generated output. Plain has no
durable journal or recovery state; a later create discards stale reserved temporary paths and
rebuilds. Never serve or copy those temporary paths.

## Managed workspace

```text
<workspace>/
├── sow.yml                               # configuration; keep private
├── .sow/                                 # database, locks, stage/recovery; keep private
│   ├── workspace.lock
│   ├── workspace-ops/
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db
│   └── <repo>/
│       ├── stage/
│       ├── recovery/
│       └── pending/
└── <repo>/                               # publish this complete directory
    ├── pool/
    └── dists/
```

Repositories do not deduplicate across repository boundaries. `.sow/` and the pending
directory are private (`0700`). Pending payload files use their final public mode (`0644`),
so promotion can be a namespace-only operation. Private state may contain unpublished bytes,
credentials-derived state, and recovery data.

`<repo>.db` and its rebuildable package-facts cache are private. Neither changes the public
repository layout or the `sow/v3` configuration identifier.

## Canonical pool

Each package payload has one canonical path:

```text
pool/<prefix>/<source>/<filename>
```

The source comes from RPM `SOURCERPM` or DEB `Source`; SOW falls back to the binary
package name when the source is absent. The prefix is the first lower-case character,
or the first four characters for names beginning with `lib`:

| Source | Example |
|---|---|
| `postgresql-18` | `pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb` |
| `blackbox_exporter` | `pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm` |
| `libfoo` | `pool/libf/libfoo/libfoo1_1.0-1_amd64.deb` |

Pool objects are immutable. Removing distribution membership does not immediately remove
their bytes; unreachable payloads are handled by `sow gc` only after every safety root —
current, retained, recovery, publication, and any active maintenance operation — has been
considered.

## RPM metadata-only views

```text
<repo>/
├── pool/
│   ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│   └── p/pev2/pev2-1.23.0-1.noarch.rpm
└── dists/el9/
    ├── x86_64/repodata/
    │   ├── <sha256>-primary.xml.gz
    │   └── repomd.xml
    └── aarch64/repodata/
        ├── <sha256>-primary.xml.gz
        └── repomd.xml
```

There is no `dists/<dist>/<arch>/pool/`. Native packages appear only in their matching
architecture metadata; `noarch` packages appear in every architecture view. rpm-md
points back to the canonical pool:

```xml
<location href="../../../pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm"/>
```

The layout requires a client that honors relative rpm-md locations across the complete
Repository root. Default `dnf reposync` rejects the parent-traversing href because its
download destination escapes the view root. When a downstream tool requires a
self-contained leaf, create one explicitly with:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

The export has a local `pool/` and rewritten hrefs; it is a compatibility artifact, not
the canonical managed repository.

## DEB views

```text
dists/trixie/
├── Release
├── InRelease                         # when metadata signing is configured
├── Release.gpg                       # when metadata signing is configured
└── main/
    ├── binary-amd64/
    │   ├── Packages
    │   ├── Packages.gz
    │   └── by-hash/SHA256/<digest>
    └── binary-arm64/
        └── ...
```

`Packages` records refer to the same canonical pool from the archive root:

```text
Filename: pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
```

`Release` uses SHA256 manifests and advertises `Acquire-By-Hash: yes`. Checksum-named
rpm-md files and APT by-hash entries keep the preceding metadata reachable while the
mutable pointer is replaced last.

## Publication targets

Both `filesystem` and `r2` targets receive the same logical public tree beneath their
configured prefix:

```text
<prefix>/
├── pool/
└── dists/
```

The published unit is always the whole repository namespace. Do not publish only one
RPM architecture directory because its hrefs deliberately refer to the root pool.

## Names and serving boundary

Repository and distribution names must match `[a-z0-9][a-z0-9._-]*`. `.`, `..`, `.sow`,
`pool`, `dists`, `sow.yml`, `workspace.lock`, `workspace-ops`, and `repo-locks` are
reserved where applicable. Case-insensitive pool-path collisions are rejected so output
remains portable between Linux and default macOS filesystems.

> [!WARNING] Never expose .sow
> Point your web server at `<workspace>/<repo>/`, not at the workspace root. The public
> repository needs both `pool/` and `dists/`; the private `.sow/` directory must stay hidden.

## See also

- [Views and One-Copy Storage](/docs/feature/views/)
- [Publication Model](/docs/design/publication/)
- [Serve Repositories](/docs/tutorial/serving/)
