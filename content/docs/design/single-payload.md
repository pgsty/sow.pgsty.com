---
title: "Single-Payload Repository"
linkTitle: "Single-Payload Layout"
description: "How v0.2.0 keeps one canonical package path per Repository and renders metadata-only APT and RPM views."
url: "/docs/design/single-payload/"
weight: 300
icon: fa-solid fa-box-archive
---

The v0.2.0 layout has one precise objective: within one Repository and within each publish
prefix, every live Package Object has exactly one payload path.

{{% alert title="Current release layout" color="primary" %}}
This is the canonical v0.2.0 layout. Workspaces created by the unreleased C2 prototype use
`schema: sow/v2` and require explicit `sow repo migrate`; new workspaces use `sow/v3`.
Read [Design Evolution](/docs/design/evolution/) before migrating a C2 workspace.
{{% /alert %}}

## Canonical tree

```text
<repo>/
├── pool/                                      # canonical package payloads
│   └── <prefix>/<source>/<filename>
└── dists/                                     # metadata-only projections
    ├── <rpm-dist>/<arch>/repodata/
    └── <deb-dist>/<component>/binary-<arch>/
```

There is no canonical `release/`, `reposync/`, per-view `pool/`, per-generation package
tree, or snapshot package tree. `pool/ + dists/` is the complete relocation and publication
unit.

The one-copy boundary is a Repository or one target prefix — not a Workspace, bucket,
account, or fleet. Identical packages in different Repositories or targets remain separate
objects with separate owners.

## APT addressing

APT already defines package filenames relative to the archive root:

```text
Filename: pool/p/postgresql-18/libpq5_18.3-1_amd64.deb
```

The client starts from the Repository root that contains both `dists/` and `pool/`.
Therefore many suites and architecture indexes can reference one canonical DEB without a
package alias. `Acquire-By-Hash: yes` gives indexes immutable lookup paths while `Release`
and `InRelease` remain the commit pointers.

The `Filename` value is an archive path spelling, not a pre-encoded URL. URI encoding is
applied exactly once by the retrieval layer.

## RPM addressing

RPM metadata resolves `<location href>` relative to the architecture view. In v0.2.0, the
renderer computes a relative path from the actual view root to the canonical Pool object:

```text
dists/el9/x86_64/repodata/primary.xml.gz
  location href="../../../pool/p/pev2/pev2-1.23.0-1.noarch.rpm"
```

The depth is computed, not hard-coded. The checker resolves the href, normalizes it with
POSIX URL semantics, and proves that it lands on the expected canonical object inside the
same Repository. Absolute `/pool/...` URLs, deployment hostnames, absolute `xml:base`,
redirect objects, and edge rewrites are not allowed to carry correctness.

The HTTP client may normalize dot segments before sending a request; the canonical object
key itself never contains `.` or `..`. Proxy and object-store behavior still requires its
own compatibility gate.

## Why package hardlinks disappeared

The unreleased C2 prototype projected RPM packages into every architecture view with
hardlinks. On one POSIX filesystem those paths shared an inode, so local disk cost stayed low and default EL
`reposync` worked. Object storage has no inode identity: each alias path becomes another
full object and another upload. Dist, architecture, generation, and snapshot count would
therefore multiply remote payload storage.

v0.2.0 makes filesystem implementation details irrelevant to canonical correctness. A normal
copy, tar archive, or object-store upload must preserve behavior even when hardlinks do not
exist.

## Relocation contract

Supported handoff copies the complete settled Repository root:

1. bind one immutable Built Generation;
2. copy every regular file in `pool/ + dists/`;
3. verify path, size, and SHA-256 against that Generation;
4. expose the destination only after closure passes.

Copying only `dists/<dist>/<arch>/` is not supported because its metadata intentionally
references the sibling root Pool.

## Compatibility export

When an operator needs a self-contained RPM leaf for default `reposync` or another legacy
tool, v0.2.0 creates an explicit external export:

```text
sow export rpm-leaf DIST ARCH DIR
```

The export lives outside the canonical Repository and every configured publish prefix.
Copy is the default. Hardlink mode is opt-in, same-filesystem, and suitable only for a
trusted read-only disposable tree. The export does not become Membership, Generation,
publish input, or a garbage-collection root.

This makes duplication an explicit compatibility cost instead of a hidden property of the
canonical Repository.
