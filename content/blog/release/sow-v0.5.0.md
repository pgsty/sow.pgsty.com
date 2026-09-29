---
title: "SOW v0.5.0"
linkTitle: "SOW v0.5.0"
date: 2026-09-29T00:00:00+08:00
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

`SECONDS` is an integer from `0` to `253402300799`. Negative, malformed, overflowing,
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

## Repository and publication fixes

This release prevents historical Dist-removal cleanup from deleting a package that has
been re-added to another Dist. Signing-policy and pool-path checks now reject incompatible
inputs before committing Desired changes, and interrupted operations from earlier binaries
have bounded recovery paths that preserve committed data and still reject altered bytes.

Published payload paths cannot be reused for different content, even after local GC.
Publication recovery never overwrites an immutable payload. Reader-held SQLite snapshots
no longer turn a durable write into a reported checkpoint failure. External input paths
can traverse symlink ancestors while package leaves retain their existing checks.

APT metadata verification accepts GnuPG's final-newline convention without ignoring other
content differences. Newly generated GPG metadata signatures use SHA-256 regardless of
local GPG preferences, and new metadata builds require a currently usable signing key.
Archives and native packages now include third-party license notices.

Pool paths are compared case-insensitively even for identical bytes, so a file name that
differs only by case cannot become a second URL. On case-insensitive filesystems SOW also
rejects source directories that differ only by case, in the workspace and before any upload
to a filesystem target. Concurrent `export rpm-leaf --hardlink` runs and `check` no longer
report unchanged Pool bytes as an integrity failure. Local `gc` ignores publication inventory
entries that exist only remotely, such as payloads retained by report-only R2 maintenance.

`sow repo migrate` reports the schema change, and an unmigrated Repository names the command to
run. Exit `130` is reserved for the command's own interruption. `file://` R2 credentials must
be regular files, and a v0.4.0 add that omitted a non-empty, fully excluded Dist now recovers
on the next build.

## Validate the surrounding maintenance workflow

A migration should exercise each deployed YUM/DNF version and architecture with an existing
metadata cache. Keep the same URL and repository ID, move from the old index to the SOW
index and then to another content generation, and verify index refresh, actual package
download, and the configured package and repository signature checks. Retain the commands,
source revision, input manifests, and results with any claimed package or transition counts.

The wrapper's persistent clock, signature reuse, and selective re-signing are not new
built-in `sow create` features. Plain mode remains a flat, multi-file rebuild: it does not
generate legacy SQLite metadata or module streams, and it does not provide an atomic
whole-repository switch.

## Upgrade and developer notes

- Upgrading a 0.3 or 0.4 Managed workspace requires a backup and explicit
  [`sow repo migrate`](/docs/command/repo/#sow-repo-migrate). Schema v13 indexes candidate
  pool paths; `sow/v3` configuration and the public `pool/ + dists/` layout are unchanged.
  Then build and check each Repository: affected RPM authentication and APT metadata
  contracts refresh once, and subsequent unchanged RPMs reuse matching Built evidence.
- Cancellation records a terminal failure before cleaning uncommitted package bytes;
  commands interrupted with Ctrl-C return 130. Empty, fully excluded additions recover
  without stranding the Repository. Long readers can defer post-prune space reclamation.
- Agent metadata signing freezes time and pins the actual usable subkey after one small
  probe per identity/time. New APT publication rejects weak signature digests while
  historical verification and frozen recovery keep their original meaning.
- Maintained documentation is consolidated on this site. Compatibility and performance
  checks now live in `qa/compat/` and `qa/perf/`; shared RPM fixtures live in
  `internal/testdata/`. The clean-delivery manifests follow those paths.
- Source builds now require Go 1.27.1. The dependency graph uses x/crypto v0.56.0,
  and release workflows pin GoReleaser v2.18.2 and its action commit.
- The S3-compatible integration test runs against a digest-pinned `pgsty/silo` image, the
  MinIO-compatible object store maintained by PGSTY, because the upstream `minio/minio`
  image is no longer available on Docker Hub.
- RPM format v6 signatures are not supported in 0.5.0; use RPM format v4 packages for
  package-signing workflows.
- The 2026-09-29 source `govulncheck` found no reachable vulnerabilities. A required module
  still carries advisory `GO-2026-5932`, but the current code does not import its affected
  package; scans of stripped binaries can still report the module match. This does not
  claim that all required modules are advisory-free; scan the final release commit again.
- Before tagging, require the full Go suite, race checks, static analysis, vulnerability
  and upstream-provenance checks, deterministic source delivery, client integration, and
  archive/package verification for the final release revision. Local validation does not
  replace successful CI and Integration runs for that exact commit.

For a new flat directory, the existing `sow create DIR` workflow remains valid. For a
published YUM repository, start with [Migrating an Existing YUM Repository](/docs/tutorial/yum-migration/)
and verify that the binary's `create --help` lists `--metadata-timestamp` before switching
the maintenance command.
