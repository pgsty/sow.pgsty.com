---
title: "SOW v0.6.1"
linkTitle: "SOW v0.6.1"
date: 2026-10-22T20:30:00+08:00
lastmod: 2026-10-22
authors: [Vonng]
description: "SOW 0.6.1 updates Go to 1.27.3, refreshes dependencies, and fixes invalid-input diagnostics without changing workspace formats."
categories: [Release]
tags: [release, maintenance, dependencies]
weight: -30
url: "/blog/release/sow-v0.6.1/"
---

SOW 0.6.1 is a maintenance release with updated dependencies and clearer error messages.
It keeps the CLI, database schema **v13**, configuration **sow/v3**, and public repository layout.
Workspaces already on 0.5.0 or 0.6.0 need no schema migration.

Get the packages and archives from the [download page](/download/), with checksums from the
[v0.6.1 release](https://github.com/pgsty/sow/releases/tag/v0.6.1).

## Toolchain and dependencies

Source builds now require **Go 1.27.3 or newer**. All release binaries were built with Go 1.27.3.
The release updates the libraries used for encryption, S3 access, compression, SQLite, and Debian package parsing.

| Dependency | Version |
|---|---|
| ProtonMail go-crypto | 1.5.2 |
| AWS SDK for Go / S3 | 1.47.3 / 1.114.4 |
| klauspost/compress | 1.20.3 |
| modernc SQLite / libc | 1.61.0 / 1.79.0 |
| pault.ag/go/debian | 0.21.1 |
| go.yaml.in/yaml/v3 | 3.0.5 |
| golang.org/x/crypto / x/sys | 0.58.0 / 0.49.0 |

YAML parsing moves to the module maintained by the YAML organization. Existing `sow.yml` files use the same format.
The RPM parser retains its existing local security patches.
Updated third-party notices ship with every archive and Linux package.

## Maintenance fixes

- Invalid paths and OpenPGP armor now produce useful diagnostics instead of `%!w(<nil>)`.
  The fixes cover log export, RPM metadata generation, signature validation, and workspace checks.
  The same invalid inputs remain rejected.
- CI snapshot packages read their version from the Makefile, removing a hard-coded version.
  Release tools and GitHub Actions are updated, including GoReleaser 2.18.3, deadcode 0.52.0, and govulncheck 1.9.0.

## Upgrade

Stop workspace writers and back up the complete workspace before replacing the executable.
Install 0.6.1, then build and check each Repository:

```bash
sow version
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

Replace `REPOSITORY` with a name from `sow.yml`. An unchanged repository reports a no-op build and keeps its Generation and timestamps.
See the [installation guide](/docs/start/install/#upgrade-to-061) for package commands and migration from 0.3 or 0.4.

Release validation covered package tests, race checks, APT/DNF clients, S3-compatible transport, and 50,000-package RPM metadata generation.
Upgrade and rollback checks used RPM/DEB workspaces created by the published 0.6.0 binary, operated by 0.6.1, then reopened by 0.6.0.

## Vulnerability scan result

Source analysis and a control build with symbols found no affected symbols or imported packages.
[GO-2026-5932](https://pkg.go.dev/vuln/GO-2026-5932) concerns the unused legacy `golang.org/x/crypto/openpgp` package.
SOW uses the maintained ProtonMail fork; the legacy package is absent from all four release-target import graphs.

Release binaries have their symbol tables removed. For these binaries, `govulncheck -mode=binary` falls back to module-level precision and reports that notice.
This explains why its binary scan differs from the source scan.

The release includes Linux and macOS archives for `amd64` and `arm64`, two RPMs, two DEBs, and `SHA256SUMS`.
See the [complete changes](https://github.com/pgsty/sow/compare/v0.6.0...v0.6.1) for the source diff.
