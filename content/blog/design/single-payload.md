---
title: "Why SOW Uses One Payload Tree per Repository"
linkTitle: "Single-Payload Repository"
date: 2026-08-05
lastmod: 2026-08-28
authors: [Vonng]
description: "The decision to replace RPM view-local package hardlinks with one canonical pool and metadata-only views."
categories: [Design]
tags: [repository, pool, rpm, apt, compatibility, decision]
url: "/blog/design/single-payload/"
aliases:
  - "/docs/design/single-payload/"
weight: 70
icon: fa-solid fa-layer-group
draft: false
---

This decision was drafted on 2026-08-05 during the pre-v0.2 release design consolidation
and shipped in SOW v0.2.0 on 2026-08-08. It remains the layout contract in v0.3 and v0.4.
It records an architecture choice, not a blanket compatibility claim: protocol closure,
ordinary package clients, mirror tools, static hosting, and object storage are verified as
separate evidence layers.

## Decision

Each SOW Repository owns one public tree:

```text
<repository>/
  pool/                         # canonical package bytes
  dists/
    <dist>/
      <architecture>/           # protocol metadata only
```

A Package Object has one canonical payload path inside one Repository. Adding the same
object to several Dists or architecture views adds membership and metadata references; it
does not create another canonical package file.

The complete `pool/ + dists/` root is the supported copy, static-hosting, authorization,
and publication unit. A single architecture leaf is a client view, not an independently
owned repository.

## From the C2 development layout to v0.2.0

An earlier pre-release C2 development layout stored each package once in a root Pool, then
created package hardlinks inside RPM views. This gave selected `reposync` clients a
self-contained leaf without duplicating local bytes.

The local inode optimization did not survive the full delivery model:

- object storage expands each path into a separate key, so aliases duplicate payloads;
- archives and cross-filesystem copies can expand or lose hardlink identity;
- a view-local package path looks canonical even though ownership remains at Repository scope;
- retention and garbage collection risk treating link count as product state;
- preserving mirror-tool behavior would force the canonical tree to follow one client's
  local-output assumptions.

Before v0.2.0 was tagged, the final single-payload design removed package aliases from
canonical RPM views. The archived C2 documents remain accurate for that development line,
but they do not describe the v0.2.0 release tag.

## How metadata reaches the Pool

APT already treats `Filename` as an archive-root-relative path, so a package entry names its
canonical path directly:

```text
Filename: pool/p/pkg/pkg_1.0_amd64.deb
```

For RPM, each `<location href>` is computed from the actual view directory to the canonical
Pool path:

```text
view:    dists/el9/x86_64/
payload: pool/p/pkg/pkg-1.0-1.x86_64.rpm
href:    ../../../pool/p/pkg/pkg-1.0-1.x86_64.rpm
```

The renderer and checker share the same path function. It normalizes Repository-relative
paths, computes literal parent navigation, escapes data bytes exactly once, resolves the
result against a directory URI, and requires the round trip to land on the original Pool
path without leaving the Repository.

This keeps the public tree relocatable. The same bytes can be copied under another
filesystem directory, HTTP origin, bucket, or prefix without rewriting metadata, provided
the relative relationship between `pool/` and `dists/` is preserved.

## Rejected alternatives

| Alternative | Why it is not canonical |
|---|---|
| Package hardlink/copy in every RPM view | Creates path aliases and duplicate object keys; makes a filesystem optimization look like durable ownership |
| Symlinked payloads | Not portable to object storage and unsafe across static servers, archives, and trust boundaries |
| Leading `/pool/...` href | Different clients interpret it as host-root or repository-relative; it also breaks non-root prefixes |
| Absolute URL or `xml:base` | Binds metadata to one origin and prevents unchanged relocation |
| CDN rewrite or redirect objects | Makes an external router part of repository correctness |
| Workspace- or bucket-global CAS | Introduces cross-Repository ownership, locking, retention, and deletion coordination that SOW does not promise |

## Mirror-tool compatibility is an export concern

An ordinary package client only needs to resolve metadata references and fetch package
bytes. A mirror tool may additionally insist that every package be stored below the view
directory it was given. Those are different contracts.

SOW does not distort the canonical Repository to make every mirror tool happy. When an
operator needs a standalone RPM leaf, `sow export rpm-leaf` creates an external
compatibility artifact with regenerated leaf-local metadata. Copy is the default;
`--hardlink` is an explicit same-filesystem optimization for a controlled, read-only
boundary. The export is not a Generation, publication source, membership owner, or garbage
collection root.

Client and mirror-tool results remain in the
[compatibility matrix](/docs/reference/compatibility/). A successful structural
[`sow check`](/docs/command/check/) proves path, digest, and closure invariants; it does
not silently upgrade an unrun client or provider cell to PASS.

## Consequences

- Package identity, membership, Generation, retention, and local GC stay Repository-scoped.
- Publication attempts, checkpoints, remote inventory, grace, and deletion evidence stay
  target-prefix-scoped.
- Every canonical file maps one-to-one to a static object key.
- Payload deletion follows reference closure and exact identity, never inode link count.
- Copying only an RPM architecture leaf is unsupported; copy the Repository root or create
  an explicit leaf export.

The current mechanism is documented in
[Pool & Metadata Views](/docs/feature/views/), while [System Model](/blog/design/model/)
and [Publication & Recovery](/blog/design/publication/) define the surrounding ownership
and lifecycle contracts.
