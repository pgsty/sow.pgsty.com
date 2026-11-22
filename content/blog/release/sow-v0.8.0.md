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

`sow gc TARGET` still writes a candidate report by default. Add `--delete` to act on an earlier report or run deletion directly. Before removing an object, SOW rechecks active publications, cache grace, object size, SHA-256 metadata, and ETag. It then verifies storage absence and a public HTTP 404 and records the deletion.

```bash
sow gc prod --json
sow gc prod --delete --json
```

Keep the target prefix under one workspace's exclusive control. If deletion is interrupted, rerun with `--delete`. A package republished after an earlier report receives the protection of its new publication. See [target GC](/docs/command/gc/#target-gc).

## Signing and package formats {#signing}

- External password files, key files, and trusted keyrings can use symlinks, including Kubernetes Secret mounts. Every hop must stay outside the workspace. Plain `create` applies the same rule at the flat repository root.
- Plain `create --sign-with` verifies the resulting OpenPGP package signature. RPM and APT metadata readers also check signature framing and reject malformed headers more consistently.
- DEB control archives support uncompressed tar, gzip, bzip2, xz, and zstd. Repack any binary DEB that uses `control.tar.lzma` before importing it.

## Publication and recovery {#recovery}

- R2 can reuse the recorded SHA-256 of an unchanged immutable object when the listed path, size, and ETag match. Filesystem publication reuses verified hashes within a session.
- Local GC processes large backlogs in bounded batches. SQLite now batches membership and publication updates, and reopened writer connections retain their WAL settings.
- Plain `create` and `prune` can operate on sibling directories while another repository is busy. Managed recovery fixes lock ordering for an interrupted repository removal.

## Upgrade and downloads {#upgrade}

Stop workspace writers and back up the complete workspace with hard links preserved. **If local GC was interrupted on 0.7.1, complete `sow gc -r REPOSITORY -C WORKSPACE` with the 0.7.1 binary before replacing it.** Its recovery plan may contain an empty `manifest` array that needs the old reader. Then install 0.8.0 and run `sow build` and `sow check` for each repository. Workspaces on 0.5.0 through 0.7.1 already use schema v13. See the [upgrade guide](/docs/start/install/#upgrade-to-080).

Source builds use Go 1.27.4. This release updates the S3 SDK to v1.116.0, SQLite driver to v1.63.0, `x/crypto` to v0.59.0, and GoReleaser to v2.20.3. Linux and macOS archives, Linux RPM and DEB packages, and their checksums are on the [download page](/download/). See the [full changelog](https://github.com/pgsty/sow/compare/v0.7.1...v0.8.0).

{{< release-assets src="release/sow-v0.8.0-checksums.txt" group="auto" >}}{{< /release-assets >}}
