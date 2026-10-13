---
title: "SOW v0.2.0"
linkTitle: "SOW v0.2.0"
date: 2026-08-08
authors: [Vonng]
description: "SOW v0.2.0 introduced Plain and Managed RPM/DEB repositories, signing, publication, retained generations, and RPM leaf export."
categories: [Release]
tags: [release, managed, signing, publish, generation]
weight: 10
url: "/blog/release/sow-docs-launch/"
---

SOW 0.2.0 introduced Plain and Managed workflows for RPM and DEB repositories. It builds static package repositories with one Go executable on Linux or macOS.

This page describes the 0.2.0 release. Use the [current documentation](/docs/) for installation and operations today.

<span id="two-operating-modes"></span>

## Build a flat repository

Plain mode indexes RPM and DEB files at the top level of a directory:

```bash
sow create /srv/repo
```

For RPMs, it writes `repodata/`. For DEBs, it writes `Packages` and `Packages.gz`. A mixed directory gets both. Plain mode uses the directory contents as its state and needs no workspace or database.

The release also added `--sign-with` to sign unsigned RPM packages. Use `--overwrite` to replace existing RPM signatures. Plain mode does not generate or sign an APT `Release` file.

<span id="lifecycle-controls"></span>

## Manage a repository over time

Managed mode records package membership and builds named Dists:

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow check -r pigsty
```

Each Repository stores a package file once under `pool/`. Its Dists contain RPM or APT metadata under `dists/`. Builds record generations so SOW can report changes and retain selected repository states.

Version 0.2.0 added:

- `sow/v3` configuration and package membership policies;
- metadata signing for RPM and APT, plus RPM package signing;
- `status`, `check`, `changes`, and operation logs;
- recoverable publication to filesystem and R2 targets;
- retained generations and local garbage collection;
- `rpm-leaf` export for tools that need a standalone RPM directory.

Serve or publish the complete Repository tree so metadata can reach the shared package pool. `sow publish` manages upload order and recovery for configured targets. R2 cleanup reports candidates without deleting remote objects.

<span id="compatibility-evidence"></span>

## Release testing and source

The release added APT/DNF and S3-compatible integration workflows, plus a tag-driven GoReleaser pipeline for Linux/macOS archives and Linux RPM/DEB packages. Historical code and tests are available under the [v0.2.0 source tag](https://github.com/pgsty/sow/tree/v0.2.0).

For the current release, use [Download](/download/). Current client and storage coverage is listed in [Platforms & Integrations](/docs/reference/compatibility/).
