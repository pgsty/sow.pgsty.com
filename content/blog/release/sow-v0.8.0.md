---
title: "SOW v0.8.0"
linkTitle: "SOW v0.8.0"
date: 2026-11-23T00:35:20+08:00
lastmod: 2026-11-23
authors: [Vonng]
description: "Reclaim expired R2 objects on demand, sign with mounted secrets, and maintain large RPM and DEB repositories with fewer reads."
categories: [Release]
tags: [release, r2, gc, signing, recovery]
weight: -60
url: "/blog/release/sow-v0.8.0/"
release_url: https://github.com/pgsty/sow/releases/tag/v0.8.0
---

{{< release-card >}}

SOW 0.8.0 lets operators reclaim expired objects on R2 and use mounted secrets for signing. Large Managed repositories need fewer storage requests during publication and can reclaim local packages in batches. The database stays at schema v13.

## Reclaiming R2 objects {#r2-gc}

`sow gc TARGET` still writes a candidate report by default. Add `--delete` to act on an earlier report or run deletion directly. Before removing an object, SOW rechecks active publications, cache grace, object size, SHA-256 metadata, and ETag. It then verifies storage absence and a public HTTP 404 or 410 and records a causal-epoch deletion receipt.

```bash
sow gc prod --json
sow gc prod --delete --json
```

Keep the target prefix under one workspace's exclusive control. If deletion is interrupted, rerun with `--delete`; running without `--delete` rejects an unfinished conditional-delete report. A package republished after an earlier report receives the protection of its new publication, and republishing identical bytes stays idempotent. See [target GC](/docs/command/gc/#target-gc).

## Signing and package formats {#signing}

- External password files, key files, and trusted keyrings can use symlinks, including Kubernetes Secret mounts. Every hop must stay outside the workspace. Plain `create` applies the same rule at the flat repository root. Temporary RPM passfile scratch files are zero-overwritten before removal, and `GNUPGHOME` is forwarded to `rpmsign` when set.
- Plain `create --sign-with` cryptographically verifies the resulting OpenPGP package signature. New Managed RPM metadata publications (`repomd.xml.asc`) now enforce SHA-256+ digests alongside APT metadata. RPM and APT readers also enforce stricter signature framing and header validation.
- DEB control archives support uncompressed tar, gzip, bzip2, xz, and zstd. SOW drops `control.tar.lzma` decompression and removes the unmaintained `kjk/lzma` and `pault.ag/go/debian/deb` dependencies; repack any binary DEB that uses `control.tar.lzma` before importing it.

## Publication, recovery, and CLI {#recovery}

- R2 reuses the recorded SHA-256 of an unchanged immutable `pool/` object when the listed path, size, and ETag match. Filesystem publication reuses verified hashes within a session and prunes empty `pool/` and `dists/` parent directories after conditional deletes.
- Local GC processes large backlogs in bounded batches and automatically replays interrupted `retain-remove-*` tombstones (`sow check` surfaces unfinished ones). SQLite batches membership and publication updates, and reopened writer connections retain WAL persistence and immediate transactions.
- Plain `create` and `prune` release the parent directory lock after binding so sibling directories run concurrently. `create` rejects running inside a managed `.sow` workspace ancestor or over an interrupted `.sow-prune-repo-complete` marker without `--pigsty`. Managed recovery unifies `workspace.lock` -> `repo.lock` ordering for `dist new`, `dist rm`, and `repo migrate`.
- Read-only inspection commands (`config check`, `repo ls`, `repo show`, `dist ls`, `dist show`) work on frozen `sow/v2` workspaces. `log prune --json` populates top-level `operation`, `where -r NAME --json` populates top-level `repository`, and workspace discovery surfaces a hint when `sow.yaml` is present without `sow.yml`.

## Toolchain and dependencies {#dependencies}

Source builds require **Go 1.27.4 or newer**. CI adds macOS contract tests and signed Managed APT/DNF container tests alongside the pinned Silo `20261112` publication suite.

| Component | 0.7.1 | 0.8.0 |
|---|---|---|
| Go | 1.27.4 | 1.27.4 |
| AWS SDK S3 | 1.114.10 | 1.116.0 |
| modernc/sqlite | 1.62.0 | 1.63.0 |
| modernc/libc | 1.81.0 | 1.82.12 |
| klauspost/compress | 1.20.4 | 1.20.5 |
| golang.org/x/crypto | 0.58.0 | 0.59.0 |
| pault.ag/go/debian | 0.21.3 | 0.21.4 |
| GoReleaser | 2.20.1 | 2.20.3 |
{.wide .expand}

## Upgrade and downloads {#upgrade}

Stop workspace writers and back up the complete workspace with hard links preserved. **If local GC was interrupted on 0.7.1, complete `sow gc -r REPOSITORY -C WORKSPACE` with the 0.7.1 binary before replacing it.** Its recovery plan may contain an empty `manifest` array that needs the old reader. Then install 0.8.0 and run `sow build` and `sow check` for each repository. Workspaces on 0.5.0 through 0.7.1 already use schema v13. See the [upgrade guide](/docs/start/install/#upgrade-to-080).

Linux and macOS archives, Linux RPM and DEB packages, and their checksums are on the [download page](/download/). See the [full changelog](https://github.com/pgsty/sow/compare/v0.7.1...v0.8.0).

{{< release-assets src="release/sow-v0.8.0-checksums.txt" group="auto" >}}{{< /release-assets >}}
