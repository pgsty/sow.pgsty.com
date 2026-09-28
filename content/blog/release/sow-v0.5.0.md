---
title: "SOW v0.5.0"
linkTitle: "SOW v0.5.0"
date: 2026-09-28T00:00:00+08:00
authors: [Vonng]
description: "SOW v0.5.0 adds explicit publication timestamps for Plain RPM repositories, preserves deterministic builds, and documents migration from existing YUM maintenance workflows."
categories: [Release]
tags: [release, plain, yum, signing, migration]
weight: -10
url: "/blog/release/sow-v0.5.0/"
draft: false
---

SOW 0.5.0 focuses on adopting SOW for existing flat YUM repositories. The main addition is
`sow create --metadata-timestamp SECONDS`: publishers can retain a valid publication time
when replacing another metadata generator, including repositories used by EL7 YUM clients.

See [Download SOW](/download/) for installation options and the
[upgrade guide](/docs/start/install/#upgrade-from-04-to-05) for an existing workspace.

## Publication time for an existing YUM repository

EL7 YUM compares the largest metadata timestamp in a downloaded `repomd.xml` with its
cached copy. If the new index has an older timestamp, YUM can reject it and retain the
cached index. A new checksum, a different revision, or a newer file modification time
does not satisfy this comparison.

Plain `create` previously always wrote zero data timestamps. That is reproducible, but
it is unsuitable as a drop-in replacement for a published index with positive timestamps.
Version 0.5 adds an explicit way to choose the publication time:

```bash
# PUBLISH_TIME is chosen by the publisher from its recorded publication history.
sow create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
```

`SECONDS` is an integer from `0` to `9223372036854775807`. Negative, malformed, overflowing,
or duplicate values are usage errors. The option belongs to `create`; it is not a
Managed `build`, `publish`, or RPM leaf-export option.

| Property | Behavior in 0.5 |
|---|---|
| Default data timestamp | Still `0` |
| Explicit timestamp | Written to the three RPM `repomd.xml` data records |
| `repomd.xml` revision | Still `0` in Plain mode |
| RPM bytes and package timestamps | Unchanged by this option |
| Compressed XML and gzip headers | Unchanged when only this option changes |
| DEB indexes | Unchanged by this option |
| Repeated metadata build | Same package bytes and options produce the same metadata and a no-op; forced re-signing is a separate package mutation |

SOW does not read the wall clock or maintain a publication clock on the caller's behalf.
A maintenance wrapper should retain an external high-water mark, preserve a valid index
and signature for unchanged content, and advance the time for real updates. Restoring old
package content is a new publication and must not restore an older publication time.
If an earlier conversion has already reset the live timestamp to zero, include trusted
pre-conversion backups when reconstructing that high-water mark.

Changing `repomd.xml` invalidates its old detached signature. The publisher must sign and
verify the new index before exposing it. `--sign-with` signs RPM packages; it does not
sign `repomd.xml`. The [migration guide](/docs/tutorial/yum-migration/) covers the complete
sequence and the boundary between the SOW command and the surrounding maintenance flow.

## RPM dependency compatibility

The dependency projection keeps the modern createrepo_c treatment of pre-transaction and
post-transaction script requirements. New regression cases cover those phases alone and
in the combinations seen in Cloudberry, Percona, and Grafana packages.

This is additional coverage, not a change to dependency parsing or a rollback to
createrepo_c 0.20.1 output. A difference in the number of dependency rows or `pre="1"`
attributes is not by itself evidence of missing dependencies. The relevant upstream change
is [createrepo_c PR #427](https://github.com/rpm-software-management/createrepo_c/pull/427).

## What the maintenance integration verified

The accompanying Pigsty maintenance work exercised 10 flat repositories: eight PGSQL
EL7–10 architecture leaves and two INFRA architecture leaves, containing 17,571 RPMs.
The timestamp repair left all 17,343 PGSQL RPMs and their compressed XML unchanged. Two
previously unsigned INFRA packages were signed. A subsequent maintenance run promoted
zero files across all 10 repositories.

Cached-client acceptance covered EL7 on both architectures and EL8, EL9, and EL10 on
arm64. Each environment moved from an old index to the repaired repository and then to
another content generation, using the same URL and repository ID without clearing metadata
cache. All 10 transitions passed index checks, actual package download, and signature
verification with both package and repository checks enabled.

These results describe that tested maintenance integration. They are not a claim that
every RPM was installed or that every possible YUM/DNF configuration was tested. The
wrapper's persistent clock, signature reuse, and selective re-signing are not new built-in
`sow create` features. Plain mode also remains a flat, multi-file rebuild: it does not
generate legacy SQLite metadata or module streams, and it does not provide an atomic
whole-repository switch.

## Upgrade and developer notes

- Upgrading an existing 0.4 Managed workspace adds no database migration. Schema v12,
  `sow/v3` configuration, and the public `pool/ + dists/` layout are unchanged. A workspace
  still on 0.3 must complete the [existing explicit migration](/docs/command/repo/#sow-repo-migrate).
- Maintained documentation is consolidated on this site. Compatibility and performance
  checks now live in `qa/compat/` and `qa/perf/`; shared RPM fixtures live in
  `internal/testdata/`. The clean-delivery manifests follow those paths.
- Go 1.27.0 remains the minimum source toolchain. No dependency or toolchain upgrade is
  part of the changes after v0.4.0.
- Local release-readiness checks passed: the full Go suite, race checks, static analysis,
  vulnerability and upstream-provenance checks, deterministic source delivery, four
  Linux/macOS archive builds, and two RPM/two DEB builds with package-content verification.

For a new flat directory, the existing `sow create DIR` workflow remains valid. For a
published YUM repository, start with [Migrating an Existing YUM Repository](/docs/tutorial/yum-migration/)
and verify that the binary's `create --help` lists `--metadata-timestamp` before switching
the maintenance command.
