---
title: "SOW v0.7.1"
linkTitle: "SOW v0.7.1"
date: 2026-11-11T22:00:00+08:00
lastmod: 2026-11-11
authors: [Vonng]
description: "SOW 0.7.1 upgrades to Go 1.27.4, refreshes dependencies, and fixes recovery, package validation, and S3/R2 handling."
categories: [Release]
tags: [release, recovery, rpm, s3]
weight: -50
url: "/blog/release/sow-v0.7.1/"
release_url: https://github.com/pgsty/sow/releases/tag/v0.7.1
---

{{< release-card >}}

SOW 0.7.1 updates the Go toolchain and dependencies. It also fixes recovery, package validation, RPM export, and S3/R2 handling.

Download the release from [GitHub](https://github.com/pgsty/sow/releases/tag/v0.7.1) or the [Download page](/download/).

These notes cover changes since **0.7.0**. Database schema **v13**, configuration schema **sow/v3**, the CLI, and the public repository layout remain compatible. Workspaces on **0.5.0 through 0.7.0** need no schema migration.

## Recovery and repository state {#recovery}

- Recover interrupted legacy `dist.new` and `dist.init` operations when effective signing is absent.
- Preserve unproven C2 migration stage files intact under `.sow/<repo>/abandoned/` and report their location. Empty stages are removed, repeated recovery is safe, and local GC can proceed. Inspect the reported files before removing them.
- Reopen directory cursors between deletion batches so cleanup completes on macOS APFS and BSD filesystems.
- Keep multi-statement SQLite reads in one read-only transaction. Split large Dist membership queries below SQLite's parameter limit.
- Normalize legacy repository time records with fractional seconds and reject years outside `1..9999`.

## Package validation and RPM export {#packages}

- Reject RPM v6 consistently in Plain `create`, every `prune` path, and Managed ingestion.
- Limit decompressed DEB control archives and APT/RPM metadata streams, including oversized PAX headers.
- Recognize Linux `renameat2` unsupported-operation errors and retain the portable fallback.
- Allow `export rpm-leaf` when an unrelated filesystem publication target is unmounted. Physical path overlap is still rejected.
- Use the selected Dist's recorded build publication time for the exported metadata signature. A later build of another Dist no longer changes that time. The exported `repomd.xml` data timestamp remains `0`.
- Accept repeated package inputs when `sow add` receives both explicit files and their parent directory.

## S3 and R2 {#s3-r2}

The updated AWS SDK retries bodyless HTTP 429 responses. SOW preserves the HTTP error classification when those retries are exhausted.

SOW also finds HTTP status codes inside joined errors. An HTTP 404 during multipart abort means the upload is already removed. Error XML responses for listing and multipart operations now have size limits.

## Toolchain and dependencies {#dependencies}

Source builds require **Go 1.27.4 or newer**. All 35 required module versions were checked against the latest available versions during release preparation.

| Component | 0.7.0 | 0.7.1 |
|---|---|---|
| Go | 1.27.3 | 1.27.4 |
| AWS SDK core / S3 | 1.47.8 / 1.114.9 | 1.48.0 / 1.114.10 |
| Smithy | 1.28.8 | 1.28.9 |
| klauspost/compress | 1.20.3 | 1.20.4 |
| modernc/libc | 1.80.1 | 1.81.0 |
| golang.org/x/sys | 0.49.0 | 0.50.0 |
| GoReleaser | 2.20.0 | 2.20.1 |
{.wide .expand}

AWS internals, pprof, `x/mod`, `x/sync`, and modernc compiler dependencies are also updated. The local RPM parser security patch is retained. Third-party notices match the new release builds.

## Upgrade {#upgrade}

Stop workspace writers and back up the complete workspace with hard links preserved. Install 0.7.1, then build and check each configured Repository:

```bash
sow version
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

An unchanged build is a no-op. Workspaces from 0.3 or 0.4 still need `sow repo migrate REPOSITORY` first. Plain repositories have no database migration.

SOW 0.6.1 and older cannot read configurations containing `passfile`. Remove those fields before downgrading. RPM v6 remains unsupported.

The release includes four Linux/macOS archives, two RPMs, two DEBs, and `SHA256SUMS`. See the [upgrade guide](/docs/start/install/#upgrade-to-071) and [complete changes](https://github.com/pgsty/sow/compare/v0.7.0...v0.7.1).

{{< release-assets src="release/sow-v0.7.1-checksums.txt" group="auto" >}}{{< /release-assets >}}
