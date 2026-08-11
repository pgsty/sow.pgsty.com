---
title: "SOW v0.3.0"
linkTitle: "SOW v0.3.0"
date: 2026-08-10
author: "Ruohang Feng"
description: "SOW v0.3.0 reduces package work across Plain and Managed repositories, adds cached package facts and bounded commits, tightens durability, and consolidates release quality gates."
categories: [release]
tags: [Release, sow]
weight: 5
url: "/blog/release/sow-v0.3.0/"
draft: false
---

SOW 0.3.0 is a performance, durability, and product-focus release. Plain repository
generation completes with one package-content pass. Managed repositories avoid
per-object membership queries, reuse authenticated package facts, and promote payloads
in bounded group commits. The shipping binary and its release pipeline are also
consolidated around the repository workflows that SOW supports.

## Plain: one package-content pass

The default unsigned `sow create` path hashes and parses each RPM or DEB once, with
parallelism controlled by `--jobs`. Metadata is rendered from the retained inspection
result. Before publication, SOW performs one final package-set and file-`stat` snapshot
check, catching concurrent input changes without reading and hashing every package again.

Plain metadata is rebuildable derived state. The implementation does not create an
operation journal, recovery trash, rollback pre-images, or repeated package hashes. If a
run is interrupted, rerun `sow create` and SOW reconstructs the metadata from the package
directory.

Pigsty preprocessing retains RPMs whose headers report `i386`, `i486`, `i586`, or
`i686`, so those packages remain in repository metadata and the `repo_complete` checksum
manifest. The intended DEB `i386` and exact Patroni 3.0.4 filters still apply.

## Managed: scale without relaxing integrity

Membership tables have reverse indexes by package SHA-256, and Desired and Built
Membership are expanded with one ordered bulk projection instead of one query per
object. In the project benchmark, listing a 5,000-object Dist fell from about 4.1
seconds to 33 milliseconds. A 50,000-object Dist completes in roughly 300 milliseconds
instead of exceeding ten minutes.

A rebuildable package-facts cache is keyed by immutable package SHA-256. Ingest
authenticates and parses each new RPM or DEB once and retains the view-independent facts
needed to render metadata. Builds bulk-load those facts, match them in memory, and lazily
rebuild missing or corrupt rows from authenticated package bytes.

On an unchanged Pool, warm builds validate payloads with device, inode, size, mtime, and
ctime fingerprints and avoid package-body reads. Fingerprint drift triggers one
authoritative SHA-256 pass and repairs the cache path. `sow check` remains the explicit
full cryptographic audit. RPM metadata artifacts and DEB architecture indexes use
bounded `--jobs` concurrency, Generation manifest and changeset rows are inserted in
batches, and final normalization reuses its descriptor snapshot instead of scanning the
Pool again.

## Bounded commits and observable builds

Managed payload promotion is a bounded, single-writer group commit. Each batch handles
at most 512 objects or 1 GiB: SOW creates the public Pool links, persists the distinct
target directories, removes the pending names, and then persists the shared pending
directory. A crash therefore leaves a recoverable pending-only, exact dual-link, or
Pool-only state; durable loss of both names remains an integrity failure.

Pending payloads use their final `0644` mode inside the private `0700` pending
directory, making promotion a namespace operation. The pending-source guard records
object identity without holding one descriptor per package for the whole build, keeping
descriptor use bounded. Publication also persists each target directory entry before
unlinking its source name.

Long builds append structured `build_progress` events for rendering, payload promotion,
Dist publication, normalization, and finalization. These events are visible in
`sow log` and do not add a database checkpoint to each phase, so progress reporting
cannot turn a successful build into a failed one.

## Focused publication and runtime

The R2 publication transport is limited to the storage primitives SOW uses:
list, head, get, and conditional put. Remote garbage collection remains report-only and
does not delete objects. Unused cloud-control, CDN, Edge-worker, migration-program, and
alternate runtime paths have been removed from the active tree, leaving one repository
core behind the production CLI. The default `go test ./...` run therefore covers the
complete active implementation.

## Correctness and release quality

- Local GC safely removes a unique case-folded Pool alias recorded by a Generation,
  which matters on case-insensitive filesystems. Path, size, and digest must still
  identify the same immutable object; ambiguous or drifted aliases fail closed.
- Every archive includes `LICENSE`. RPM and DEB packages declare Apache-2.0 and install
  the license at `/usr/share/licenses/sow/LICENSE` and
  `/usr/share/doc/sow/copyright`.
- CI enforces formatting, module tidiness, vet, static analysis, dead-code checks,
  performance-test compilation, the full test suite, race tests, clean-delivery checks,
  and package snapshots.
- Integration gates exercise the production binary in a clean-room mixed RPM/DEB
  workflow, an exact unsigned Plain APT install on Ubuntu 22.04, DNF signature-transition
  probes on AlmaLinux 8/9/10, and conditional S3 operations against pinned MinIO.
- The published release contains macOS and Linux archives for amd64 and arm64, RPM and
  DEB packages for both Linux architectures, and `SHA256SUMS`.

## Get the release

Use the [download page](/download/) for platform-specific commands, or inspect every
asset on the [GitHub release](https://github.com/pgsty/sow/releases/tag/v0.3.0). After
installation, run `sow version` to verify the selected binary.

The operating contracts are documented in [Plain Mode](/docs/feature/plain/),
[Managed Mode](/docs/feature/managed/), and
[Platforms & Integrations](/docs/reference/compatibility/).
