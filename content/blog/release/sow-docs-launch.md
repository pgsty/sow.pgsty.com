---
title: "SOW v0.2.0: Single-Payload Repositories"
linkTitle: "SOW v0.2.0"
date: 2026-08-08
author: "Ruohang Feng"
description: "SOW v0.2.0 establishes the single-payload layout, explicit publication targets, retention, GC, and RPM compatibility exports."
categories: [release]
tags: [Release, sow]
weight: 10
url: "/blog/release/sow-docs-launch/"
---

**Documentation published:** 2026-08-08 · **Version:** `sow 0.2.0` · **Release:** GitHub draft

SOW is a self-contained package repository manager from [Pigsty](https://pigsty.io). One
static Go binary creates and maintains APT (DEB) and YUM (RPM) repositories on Linux and
macOS without invoking `createrepo_c`, `dpkg-scanpackages`, or `reprepro`.

## The v0.2.0 layout

Managed repositories now have one canonical payload owner. Every package body appears
once beneath `pool/`; `dists/` contains metadata-only APT and RPM views. rpm-md reaches the
root pool through a computed relative href, while APT uses archive-root `Filename` values.

This replaces the view-local hardlink C2 prototype. That prototype was never a public
product release. The public version history is v0.1.0 followed by v0.2.0; names such as
`sow.cli/v1` and `sow/v3` are wire/schema identifiers, not product versions.

Default `dnf reposync` rejects the canonical parent-relative href. v0.2.0 keeps the
single-payload repository as the source of truth and adds an explicit compatibility path:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

## Publication and lifecycle

Managed workspaces can define `filesystem` and S3-compatible `r2` targets, then publish a
verified Generation with `sow publish TARGET`. Attempts are resumable; pre-commit attempts
can be explicitly abandoned, while post-commit recovery is forward-only.

`sow retain` creates and removes explicit retained-Generation roots. Local `sow gc`
collects only payloads unreachable from all safety roots. Target GC is provider-specific:
filesystem deletion is conditional after grace and absence checks; R2 is deliberately
report-only and never deletes objects.

## Verification boundary

The client matrix covers AlmaLinux 8/9/10 DNF, CentOS 7 YUM, and Debian 12/13 APT. The
Integration workflow also exercises real APT/DNF clients and S3-compatible publication
against pinned MinIO. A provider integration test is not proof that a particular public
R2 account or CDN is configured; hosted deployment remains a separate check.

The current v0.2.0 draft contains Linux and macOS archives for amd64 and arm64, `1PGSTY`
Linux RPM and DEB packages, and `SHA256SUMS`. Public availability begins only after an
operator publishes that draft. SOW does not build repository payload packages,
publish a container image, coordinate multiple writers, act as a CDN, or generate
modulemd, SQLite repodata, zchunk, or source-package indexes.

Start at the [Quick Start](/docs/start/quickstart/), review the
[design history](/docs/design/evolution/), or use the [CLI reference](/docs/reference/cli/).
