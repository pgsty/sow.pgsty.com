---
title: "SOW v0.5.0"
linkTitle: "SOW v0.5.0"
date: 2026-09-29T00:00:00+08:00
lastmod: 2026-10-13
authors: [Vonng]
description: "SOW v0.5.0 adds Plain RPM publication timestamps and fixes repository recovery, signing, and package paths."
categories: [Release]
tags: [release, plain, yum, signing, migration]
weight: -10
url: "/blog/release/sow-v0.5.0/"
draft: false
---

SOW 0.5.0 adds publication timestamps for existing YUM repositories and fixes Managed
repository recovery, signing, and package-path handling. It also reduces repeated package
verification during builds.

Install the release from [Download SOW](/download/). If you use a Managed workspace from
0.3 or 0.4, migrate each Repository before further writes.

<span id="upgrade-and-developer-notes"></span>

## Upgrade a Managed workspace

1. Stop commands that write to the workspace.
2. Back up the complete workspace, including `sow.yml`, `.sow/`, and all Repository roots.
3. Install SOW 0.5.0.
4. Migrate, build, and check each Repository. Replace `pgsql` and `/srv/sow` with your names.

```bash
sow repo migrate pgsql -C /srv/sow
sow build -r pgsql -C /srv/sow
sow check -r pgsql -C /srv/sow
```

The migration updates the database to schema v13. Configuration remains `sow/v3`, and the
public layout remains `pool/` plus `dists/`. The first build refreshes RPM authentication
and APT metadata records. Later builds reuse matching RPM verification records.

Use SOW 0.5.0 or newer with the migrated database. For backup and installation steps, see
[Install and upgrade](/docs/start/install/#upgrade-from-04-to-05).

<span id="publication-time-for-an-existing-yum-repository"></span>

## Preserve YUM publication time

EL7 YUM can reject a new `repomd.xml` if its largest data timestamp is older than the
cached value. Changing the checksum, revision, or file modification time does not satisfy
that comparison.

Use the new option when replacing an existing metadata generator:

```bash
# Set PUBLISH_TIME from the repository's publication history.
sow create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
```

| Setting | Result |
|---|---|
| Default | RPM data timestamps remain `0` |
| `--metadata-timestamp SECONDS` | Sets the timestamp of all three RPM data records |
| Accepted value | An integer from `0` to `253402300799` |
| Plain `repomd.xml` revision | Remains `0` |
| Package bytes and DEB indexes | Unchanged by this option |
| Compressed XML and gzip headers | Unchanged when only the timestamp changes |

The option applies to `create`. Managed builds, publication, and RPM leaf export do not
accept it. A repeated build with the same package bytes and options produces the same
metadata; forced package re-signing can change the input bytes.

Keep the highest published timestamp in your maintenance script. Increase it when content
changes, including when you restore an older package set. If a previous conversion reset
timestamps to zero, use the pre-conversion publication history to recover that value.

<span id="validate-the-surrounding-maintenance-workflow"></span>

If clients verify repository signatures, sign the final `repomd.xml` after each change.
`--sign-with` signs RPM packages; it does not sign the index. The
[YUM migration guide](/docs/tutorial/yum-migration/) covers timestamp selection, index
signing, and testing with existing client caches.

## Repository and publication fixes

- Dist removal no longer deletes a package that was later added to another Dist.
- SOW checks signing policies and pool-path conflicts before committing Desired changes.
- Recovery preserves committed package selections and completes interrupted cleanup.
- A published package path stays bound to its content after local garbage collection.
  Publication recovery does not overwrite that path with different bytes.
- File names that differ only by case cannot create a second Pool URL, even for identical
  bytes. Case-insensitive workspaces and filesystem targets also reject directory aliases.
- Concurrent `export rpm-leaf --hardlink` and `check` commands no longer report unchanged
  package bytes as corrupt.
- Local `gc` skips publication records whose packages exist only on the remote target.
- Input paths can use symlinked parent directories. Package files themselves must pass
  the existing file checks.
- SQLite checkpoints delayed by readers no longer turn a completed write into a reported
  failure. macOS writable connections use `fullfsync`.

## Signing and command output

APT signature verification now accepts GnuPG's final-newline convention. New metadata
signatures use SHA-256, and new builds check whether the signing key is currently usable.
Agent signing fixes the signing time and selects the available signing subkey. New APT
publications reject weak signature digests; historical verification keeps its recorded
rules.

`sow repo migrate` reports the old and new schema versions. An unmigrated Repository shows
the migration command. Commands interrupted by SIGINT or SIGTERM return exit code `130`. Rejected `add` batches
show per-file errors. `file://` R2 credentials must point to regular files.

<span id="rpm-dependency-compatibility"></span>

## RPM dependencies

New regression cases cover pre-transaction and post-transaction script requirements,
including combinations used by Cloudberry, Percona, and Grafana packages. Dependency
rendering continues to follow modern createrepo_c behavior. See
[createrepo_c PR #427](https://github.com/rpm-software-management/createrepo_c/pull/427)
for the upstream change.

For package-signing workflows, use RPM format v4. SOW 0.5.0 does not support RPM format v6
signatures. The generated repository metadata uses XML; it does not include SQLite
rpm-md or module streams. See [Compatibility](/docs/reference/compatibility/) for formats
and client coverage.

## Builds and packages

Source builds require Go 1.27.1 or newer. The release uses x/crypto v0.56.0 and
GoReleaser v2.18.2. Archives and native packages include `THIRD_PARTY_NOTICES`.

The release contains four Linux/macOS archives, two RPMs, two DEBs, and `SHA256SUMS`.
Get a specific artifact from the [v0.5.0 release](https://github.com/pgsty/sow/releases/tag/v0.5.0).
Compatibility tests are in `qa/compat/`; performance tests are in `qa/perf/`.
The S3 integration fixture uses a digest-pinned `pgsty/silo` image.
