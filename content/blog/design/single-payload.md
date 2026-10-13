---
title: "Why SOW Uses One Payload Tree per Repository"
linkTitle: "Single-Payload Repository"
date: 2026-08-05
lastmod: 2026-10-13
authors: [Vonng]
description: "One package pool per repository, with metadata-only distribution views that share its files."
categories: [Design]
tags: [repository, pool, rpm, apt, compatibility, decision]
url: "/blog/design/single-payload/"
aliases:
  - "/docs/design/single-payload/"
weight: 70
icon: fa-solid fa-layer-group
draft: false
---

This decision was drafted on 2026-08-05 and shipped in SOW v0.2.0 on 2026-08-08.
SOW 0.5.0 still uses this layout. Each Repository stores one package tree and lets its
distribution views reference that tree.

## Decision

Each SOW Repository owns one public tree:

```text
<repository>/
  pool/                         # package files
  dists/
    <dist>/
      <architecture>/           # RPM metadata only
```

The diagram shows an RPM view. APT indexes use `dists/<dist>/main/binary-<architecture>/`;
its `Release` files sit at `dists/<dist>/`.

A package object has one payload path inside one Repository. Adding the same object to
several Dists or architecture views adds membership and metadata references.

The complete `pool/ + dists/` root is the supported copy, static-hosting, authorization,
and publication unit. A single architecture leaf is a client view, not a complete package repository.

## From the C2 development layout to v0.2.0

An earlier pre-release C2 development layout stored each package once in a root Pool, then
created package hardlinks inside RPM views. This gave selected `reposync` clients a
self-contained leaf without duplicating local bytes.

Hardlinks saved local disk space, but had costs elsewhere:

- object storage expands each path into a separate key, so aliases duplicate payloads;
- archives and cross-filesystem copies can expand or lose hardlink identity;
- a package path inside a view looks independent, although the Repository still owns the file;
- retention and garbage collection can confuse link counts with package references;
- the repository layout has to follow a particular mirror tool's output-directory rules.

Before v0.2.0 was tagged, the final single-payload design removed package aliases from
RPM views. The archived C2 documents describe that development line.

## How metadata reaches the Pool

APT already treats `Filename` as an archive-root-relative path, so a package entry names its
pool path directly:

```text
Filename: pool/p/pkg/pkg_1.0_amd64.deb
```

For RPM, each `<location href>` is computed from the actual view directory to the
Pool path:

```text
view:    dists/el9/x86_64/
payload: pool/p/pkg/pkg-1.0-1.x86_64.rpm
href:    ../../../pool/p/pkg/pkg-1.0-1.x86_64.rpm
```

The renderer and checker share the same path function. It calculates the relative path and escapes the file name.
It then resolves the result and checks that it points to the original package inside the Repository.

This keeps the public tree relocatable. Keep the relative locations of `pool/` and `dists/` when you copy the repository.
Then the same metadata works under another filesystem directory, HTTP origin, bucket, or prefix.

## Rejected alternatives

| Alternative | Why it was not used |
|---|---|
| Package hardlink/copy in every RPM view | Creates path aliases and duplicate object keys |
| Symlinked payloads | Object storage does not support them; static servers and archives handle them differently |
| Leading `/pool/...` href | Different clients interpret it as host-root or repository-relative; it also breaks non-root prefixes |
| Absolute URL or `xml:base` | Binds metadata to one origin and prevents unchanged relocation |
| CDN rewrite or redirect objects | Requires extra routing configuration for the repository |
| Workspace- or bucket-global pool | Requires cross-Repository coordination for locks, retention, and deletion |

## Mirror-tool compatibility is an export concern

An ordinary package client only needs to resolve metadata references and fetch package
bytes. A mirror tool may additionally insist that every package be stored below the view
directory it was given.

For consumers that require a standalone RPM leaf, use `sow export rpm-leaf`. It creates
a directory outside the Repository with package files and regenerated local metadata. Copy is the default.
Use `--hardlink` on the same filesystem and keep exported package files read-only, because
writing through a hardlink also changes the Pool file. The export is not a Generation, publication source, membership owner, or garbage
collection root.

Client and mirror-tool results remain in the
[compatibility matrix](/docs/reference/compatibility/). Use
[`sow check`](/docs/command/check/) to verify local paths, digests, and file references.
Use the listed client tests to check package installation and mirroring.

## Consequences

- Package identity, membership, Generation, retention, and local GC stay Repository-scoped.
- Publication attempts, checkpoints, remote inventory, grace, and deletion evidence stay
  target-prefix-scoped.
- Each package file maps to one static object key.
- Before deleting a payload, check its references and file identity. Do not use hardlink count
  to determine whether it is still needed.
- Copy the Repository root, or use the export command to create a standalone RPM architecture directory.

The current mechanism is documented in
[Pool & Metadata Views](/docs/feature/views/), while [System model](/blog/design/model/)
and [Publication and recovery](/blog/design/publication/) define the surrounding ownership
and lifecycle rules.
