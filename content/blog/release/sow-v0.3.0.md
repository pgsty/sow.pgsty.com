---
title: "SOW v0.3.0"
linkTitle: "SOW v0.3.0"
date: 2026-08-10
authors: [Vonng]
description: "SOW v0.3.0 reduces repeated package reads and database queries, batches package commits, and adds build progress events."
categories: [Release]
tags: [release, plain, managed, transaction]
weight: 5
url: "/blog/release/sow-v0.3.0/"
draft: false
---

SOW 0.3.0 reduced repeated package reads and database queries. Plain generation uses one pass over package content. Managed builds cache parsed package data and commit new pool files in batches. This release also removed retired runtime and publication code.

<span id="plain-one-package-content-pass" data-td-print-local></span>

## Plain: read each package once

The default unsigned `sow create` path hashes and parses each RPM or DEB once. `--jobs` controls parallel work. SOW renders metadata from the parsed results, then checks that the package set and file attributes still match before writing the indexes.

An interrupted Plain build can be rerun from the package directory. Version 0.3 removed its operation journal, rollback copies, and repeated package hashing; Managed recovery remained unchanged.

Pigsty preprocessing now keeps RPMs whose headers report `i386`, `i486`, `i586`, or `i686`. They remain in the repository metadata and `repo_complete` checksum manifest. The DEB `i386` and exact Patroni 3.0.4 filters remain in place.

<span id="managed-scale-without-relaxing-integrity" data-td-print-local></span>

## Managed: fewer queries and package reads

Membership tables gained reverse indexes by package SHA-256. SOW now loads Desired and Built membership in one ordered query instead of querying each object. In the project's benchmark, listing a 5,000-object Dist fell from about 4.1 seconds to 33 milliseconds. A 50,000-object Dist completed in under a second.

Schema v10 added a rebuildable cache of parsed package data, keyed by package SHA-256. Import verifies and parses a new package, then saves the data needed to render its metadata. Builds load this data in batches. Missing or damaged cache entries are rebuilt from verified package files.

For an unchanged pool, warm builds use device, inode, size, modification time, and change time to recognize unchanged files. A changed fingerprint triggers a full SHA-256 check. `sow check` continues to read and verify the complete package content.

RPM metadata and DEB architecture indexes use bounded `--jobs` concurrency. Generation manifests and change records are written in batches.

<span id="bounded-commits-and-observable-builds" data-td-print-local></span>

## Batch commits and build progress

Managed builds move packages into the public pool in batches of up to 512 objects or 1 GiB. SOW persists each destination directory before removing pending names. Recovery handles an interrupted batch whether a package exists in the pending directory, the pool, or both.

Pending files use their final `0644` mode inside a private `0700` directory. Builds no longer hold a file descriptor for every pending package throughout the operation, which reduces resource use in large repositories.

Long builds write `build_progress` events for rendering, package promotion, Dist publication, normalization, and finalization. Use `sow log` to inspect this progress.

<span id="focused-publication-and-runtime" data-td-print-local></span>

## One active repository implementation

The release removed the retired V1 CLI and runtime, cloud/CDN publication code, Edge worker, completed migration program, and their obsolete tests. The active CLI uses one repository implementation.

R2 publication keeps the storage operations SOW needs: list, HEAD, GET, and conditional PUT. Remote garbage collection reports candidates without deleting them.

<span id="correctness-and-release-quality" data-td-print-local></span>

## Other changes

- Local garbage collection handles a unique recorded pool-path alias on case-insensitive filesystems. It checks the package path, size, and digest before removal.
- Archives include `LICENSE`. RPM and DEB packages install Apache-2.0 license files at `/usr/share/licenses/sow/LICENSE` and `/usr/share/doc/sow/copyright`.
- CI covers formatting, module consistency, static analysis, dead-code checks, tests, race detection, source delivery, and package builds.
- Integration tests cover mixed RPM/DEB workflows and an unsigned Plain APT installation on Ubuntu 22.04.
  They also test DNF signature transitions on AlmaLinux 8/9 and `pgsty/el10`, plus conditional S3 operations against a pinned MinIO version.

<span id="get-the-release" data-td-print-local></span>

## Get version 0.3.0

Use the [v0.3.0 GitHub release](https://github.com/pgsty/sow/releases/tag/v0.3.0) for that version's Linux/macOS archives, Linux RPM/DEB packages, and `SHA256SUMS`. Run `sow version` after installation. The source tag requires Go 1.26.5 or newer.

For a new installation today, use the [current download page](/download/). Current behavior is documented in [Plain Mode](/docs/feature/plain/), [Managed Workspaces](/docs/feature/managed/), and [Platforms & Integrations](/docs/reference/compatibility/).
