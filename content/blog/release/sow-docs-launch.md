---
title: "SOW 0.2: Documentation Preview"
linkTitle: "SOW 0.2 Documentation Preview"
date: 2026-08-04
author: "Ruohang Feng"
description: "The SOW documentation site goes live: two repository engines, a tested client compatibility matrix, and four sections of docs."
categories: [release]
tags: [Release, sow]
weight: 10
url: "/blog/release/sow-docs-launch/"
---

**Published:** 2026-08-04 · **Version:** `sow 0.2.0-dev`

SOW is a self-contained package repository manager from [Pigsty](https://pigsty.io). It
is one static Go binary that creates and maintains APT (DEB) and YUM (RPM) repositories
on Linux and macOS, and it does the whole job itself: `createrepo_c`,
`dpkg-scanpackages`, `reprepro`, and `modifyrepo_c` are never invoked. There is no daemon,
no database server, and nothing to install alongside it. The name is the verb — you sow
packages into a repository, and the repository grows.

## Two engines, one binary

`sow create` is the flat path. Point it at a directory that already holds `.rpm` or
`.deb` files and it writes the indexes in place — `repodata/` for RPM, `Packages` and
`Packages.gz` for DEB, both in the same directory if the directory holds both. No
workspace, no config file, no state. The same input bytes produce the same output bytes,
and running it twice is a no-op.

The managed path is for repositories you keep. A workspace holds repositories; a
repository holds dists; a dist is a named set of members in a single format. Payloads
live once in a Debian-style `pool/`, and each architecture view is a hardlink projection
of that pool rather than a second copy. Membership is a desired set that you edit with
`add` and `rm`; `build` turns it into a published generation. Between them sits an
explicit dirty state, so you always know whether what is on disk matches what you asked
for. Writes go through a journal, so a machine that dies mid-`add` recovers on the next
write command instead of leaving a half-written tree.

## Verified against real clients

The compatibility matrix in the docs is measured, not asserted. Repositories produced by
SOW have been consumed end to end by AlmaLinux 8, 9, and 10 with `dnf` (with both
`gpgcheck=1` and `repo_gpgcheck=1`), by CentOS 7 with `yum` 3.4.3 including correct
multi-version NEVRA resolution, and by Debian 12 (`apt` 2.6.1) and Debian 13 (`apt`
3.0.3) with `InRelease` signature verification and `by-hash` fetching. `dnf reposync` on
EL9 mirrors the pool layout cleanly. Flat repositories are consumable over both `file://`
and `http://`. Notably, SOW emits `Acquire-By-Hash: yes` — something reprepro does not
support at all.

## What the documentation covers

The site is organized into four sections. [Getting Started](/docs/start/) installs the
binary, publishes a repository in five minutes, and lays out the mental model.
[Tutorials](/docs/tutorial/) walk end to end through YUM and APT repositories, GPG
signing, serving over Nginx, and migrating off createrepo_c or reprepro.
[Features](/docs/feature/) explains how it works — pools and architecture views,
membership policy, the two signing trust chains, transactions and recovery, and the audit
trail. [Reference](/docs/reference/) is the lookup layer: every command, the full
`sow.yml` schema, package reference grammar, exit codes, repository layouts, JSON output,
and the compatibility matrix.

Scope is deliberately narrow, and the non-goals are stated rather than deferred: SOW does
not build packages, does not publish to remote object storage or a CDN, does not support
multiple concurrent writers, and does not generate modulemd, sqlite repodata, zchunk, or
source package indexes.

Start at the [Quick Start](/docs/start/quickstart/), or grab a binary from the
[download page](/download/).
