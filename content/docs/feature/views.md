---
title: "Pool & Metadata Views"
linkTitle: "Pool & Views"
description: "One package, one owner, metadata-only APT/RPM views: canonical pool addressing, neutral packages, relocation, and the explicit reposync export."
url: "/docs/feature/views/"
aliases:
  - "/docs/design/single-payload/"
weight: 400
icon: fa-solid fa-layer-group
---

## The invariant

Within one Repository, every live Package Object has one canonical payload path under
`pool/`. Dists and architecture views own metadata, not aliases of package bytes:

```text
<repo>/pool/...                              canonical package payloads
<repo>/dists/<rpm-dist>/<arch>/repodata/... RPM metadata only
<repo>/dists/<deb-dist>/main/binary-*/...   APT metadata only
```

The same digest in another Repository or publication prefix is a separately owned object.
SOW deliberately does not turn local deduplication into shared distributed ownership.

## What a built Repository looks like

An RPM Dist with one `x86_64` package and one `noarch` package has this shape:

```text
demo/
├── pool/
│   ├── c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
│   └── e/epel-release/epel-release-7-5.noarch.rpm
└── dists/el9/
    ├── aarch64/repodata/
    │   ├── <sha256>-primary.xml.gz
    │   ├── <sha256>-filelists.xml.gz
    │   ├── <sha256>-other.xml.gz
    │   └── repomd.xml
    └── x86_64/repodata/
        ├── <sha256>-primary.xml.gz
        ├── <sha256>-filelists.xml.gz
        ├── <sha256>-other.xml.gz
        └── repomd.xml
```

There is no `dists/.../pool/` subtree. Content-addressed metadata from a retained live
generation may coexist with the current files; `repomd.xml` is the pointer that selects
the active set.

## RPM views use computed parent-relative hrefs

rpm-md resolves each package `<location href>` relative to the architecture view. SOW
computes the path from that view to the canonical Pool object:

```xml
<location href="../../../pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm"/>
<location href="../../../pool/e/epel-release/epel-release-7-5.noarch.rpm"/>
```

The depth is derived from the actual view root, not copied from a hostname or hard-coded
deployment path. `sow check` resolves and normalizes each href, rejects escapes outside the
Repository, and proves that it reaches the expected Pool object.

The complete Repository root is therefore the client and delivery boundary. Point DNF at
`dists/el9/x86_64/`, but serve or copy the parent Repository that also contains `pool/`.

## Why views contain metadata only

Copying each package into every architecture view would create extra object keys and
uploads on storage systems without inode identity. SOW therefore gives payload ownership
to the Repository Pool and lets indexes project membership. A complete copy, archive, or
publication preserves that contract without depending on hardlinks.

The one-copy boundary is one Repository or one publication prefix—not a Workspace,
bucket, account, or fleet. Identical packages in separate Repositories or targets retain
separate owners.

## Neutral packages are selected, not duplicated

An `x86_64` view selects `x86_64 + noarch`; an `aarch64` view selects `aarch64 + noarch`.
The neutral package remains one Pool object. Each view gets its own metadata record whose
location resolves to that same object.

DEB works the same way at the archive-root level: `all` packages appear in each applicable
`Packages` index, while `Filename: pool/...` points to one canonical payload.

## APT views

APT already defines `Filename` relative to the archive root:

```text
Filename: pool/p/postgresql-18/libpq5_18.3-1_amd64.deb
```

SOW renders `Packages`, `Packages.gz`, and `by-hash` entries under
`dists/<dist>/main/binary-<arch>/`. `Release`, `InRelease`, and `Release.gpg` are the
protocol pointers and signatures. There is no per-view package alias and no per-architecture
`Release` stub.

## Ordinary clients and `reposync` are different contracts

The canonical layout is designed for package clients that consume the complete Repository
and honor relative protocol paths. Default EL `dnf reposync` has a different contract: its
safe-write check rejects a package
location that normalizes above the per-repository download directory. This is an explicit
unsupported combination; use an exported leaf for that workflow.

When a self-contained RPM leaf is required, create it outside the Repository and every
configured filesystem publication root:

```bash
sow export rpm-leaf el9 x86_64 /srv/exports/el9-x86_64
```

The export contains its own package tree, repodata, manifest, and `.sow-export.json`
completion marker. Copy is the default. `--hardlink` is an explicit same-filesystem,
trusted read-only optimization. The export is not Membership, Generation, publication
input, or a garbage-collection root.

## Copy and publication

Canonical correctness does not depend on inode identity. Prefer a configured publication
target. If another transport is required, copy the complete settled `pool/ + dists/` tree
with `rsync`, `cp`, or tar into an offline staging location, verify it, and switch it into
service atomically. Never update the live tree file by file. Copying only one RPM
architecture leaf is not supported because its metadata intentionally references the
sibling root Pool.

`sow changes` lists each payload once under `pool/`, followed by metadata and pointers:

```text
add  payload   pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm  ...
add  payload   pool/e/epel-release/epel-release-7-5.noarch.rpm                  ...
add  metadata  dists/el9/x86_64/repodata/<sha256>-primary.xml.gz               ...
add  pointer   dists/el9/x86_64/repodata/repomd.xml                            ...
```

There are no package-payload entries under `dists/`.

## Next

- [Managed Workspaces](/docs/feature/managed/) — ownership and Generation state
- [Platforms & Integrations](/docs/reference/compatibility/) — tested and unsupported combinations
- [Serve Repositories](/docs/tutorial/serving/) — HTTP, copies, and publication targets
- [Repository Layout](/docs/reference/layout/) — exact public and private paths
