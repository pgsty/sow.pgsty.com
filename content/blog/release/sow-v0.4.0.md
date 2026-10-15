---
title: "SOW v0.4.0"
linkTitle: "SOW v0.4.0"
date: 2026-08-24
authors: [Vonng]
description: "SOW v0.4.0 reduces repeated verification, verifies RPM key sets independently, adds target rebinding, and improves migration and publication recovery."
categories: [Release]
tags: [release, managed, signing, publish, migration]
weight: 1
url: "/blog/release/sow-v0.4.0/"
draft: false
---

SOW 0.4.0 improved Managed repository verification and recovery. `check` reads each physical package once for its content hash. RPM verification keeps separate trust decisions for separate key sets. Publication targets can change their public URL or cache lifetime through an audited rebind operation.

Plain behavior and the public `pool/` and `dists/` layout stayed the same. This page describes version 0.4.0; use the [installation guide](/docs/start/install/) to upgrade to the current release.

<span id="upgrade-from-03" data-td-print-local></span>

## Upgrade from 0.3 to 0.4

Stop workspace writers and back up the complete workspace, preserving hard links. Install 0.4.0, then migrate each configured Repository before continuing maintenance:

```bash
set -euo pipefail
rsync -aH /srv/sow/ /srv/sow.backup-before-0.4.0/
sow repo migrate pigsty -C /srv/sow
sow repo migrate pgsql -C /srv/sow
sow check -r pigsty -C /srv/sow
sow check -r pgsql -C /srv/sow
```

The example has repositories named `pigsty` and `pgsql`; use the names from your `sow.yml`. Keep the backup for rollback because SOW 0.3 cannot open the migrated database.

Schema v11 fixed a 0.3 status bug: a Repository could appear clean while one of its Dists remained dirty. Status is now updated in the transaction that changes the Dists. Migration also repairs recorded publication and signer information. A historical signing identity that was never recorded remains unverified.

Schema v12 added an append-only history of publication-target bindings. Initial bindings, migration backfills, and later rebinds have separate revisions.

<span id="one-authenticity-pass-per-physical-payload" data-td-print-local></span>

## One content hash per physical package

Each `sow check` performs one complete content hash for each unique physical package, including files whose cached fingerprint still matches. Hard links to the same file share that result. SOW ties verification to the file it read and detects replacements or changes during the check.

The same result is reused when checking retained generations, the final manifest, and changes. Adding Dists or retained generations does not multiply package hashing. DEBs and unsigned RPMs need one full read. A signed RPM uses at most one additional read from the main header to the end of the file for signature verification.

Package-cache queries are limited to the selected digests and run in bounded SQLite batches. A warm build of the 64 MiB test package reads no package content. A changed fingerprint and missing cache row share one verification pass.

<span id="independent-rpm-trust-rings" data-td-print-local></span>

## Verify each RPM trust set separately

RPM signature packets are checked against each candidate key set independently. Every recognized packet must verify within that set, and at least one verified signature must authenticate the payload.

This supports historical CentOS signatures and deliberately dual-signed packages. It also prevents SOW from combining partial successes across unrelated key sets into a false single-key verification result.

The current policy keys, retained-generation keys, and combined trusted keys use the same signature read. Additional keys change trust decisions without adding package reads.

<span id="safe-target-rebind-and-public-verification" data-td-print-local></span>

## Update publication-target settings

Use `sow publish TARGET --rebind` to update mutable target settings while preserving its storage identity and recovery state:

| May change with `--rebind` | Requires a new target |
|---|---|
| Target name | Repository identity |
| `public_endpoint` | Provider or storage `endpoint` |
| `max_cache_ttl` | Region, bucket, or `prefix` |

A normal publish reports changed settings and requests `--rebind`. Rebind takes the publication locks, records a revision, and can resume an interrupted publication after its commit decision. Pending cleanup restricts TTL and filesystem public-URL changes. Previously recorded cache deadlines remain in effect.

<span id="recovery-cli-and-implementation-cleanup" data-td-print-local></span>

## Check public files and recover interrupted uploads

Filesystem and R2 HTTP(S) checks now use separate deadlines for response headers and stalled bodies. Large files can take more than two minutes as long as data continues to arrive.

SOW checks the ordinary client URL. Stale content and 404 responses wait up to `max_cache_ttl`; temporary 408, 425, 429, and 5xx responses use a shorter retry window. Oversized responses fail verification. Filesystem cleanup checks for a public 404 or 410 after deletion. R2 cleanup remains report-only.

Other publication changes include:

- Check filesystem path aliases before creating a target binding, including case aliases on case-insensitive volumes.
- Resume an interrupted pointer update when it contains the recorded old or new bytes. Report unexpected content for investigation.
- Verify the changed public objects instead of downloading the complete generation on every publication.
- Use retryable reads and writes, idle timeouts, and bounded conditional multipart uploads for R2. Check the whole-object SHA-256 before completing an upload.

## CLI and maintenance fixes

- Repeating `sow add` builds a selected Dist left dirty by `--skip` or a configuration change, even if the package is already in the pool.
- `sow rm --check` uses the same configuration checks as removal and returns a read-only preview.
- Every Managed command has readable text output. The `sow.cli/v1` JSON format preserves partial or diagnostic results when a command fails.
- Signer records stay consistent through partial builds, Dist changes, migration, retention, and garbage collection.
- Retired APT builder, external-sort, empty-Dist, and Git-tracked by-hash code was removed.

<span id="verification-and-artifacts" data-td-print-local></span>

## Build and release checks

The release used Go 1.27.0, up from Go 1.26.5 in 0.3. AWS SDK, SQLite, compression, and cryptography dependencies were updated. Build checks pinned staticcheck v0.8.1, deadcode v0.49.0, and govulncheck v1.7.0.

Release checks covered Go tests, static analysis, vulnerability and RPM-fork source checks, race tests, Linux amd64/arm64 builds, and the package-read limits described above.

The release includes four Linux/macOS archives, two RPMs, two DEBs, and `SHA256SUMS`. Archives contain `sow`, `README.md`, `CHANGELOG.md`, and `LICENSE`. Linux packages install the license with the executable.

<span id="get-the-release" data-td-print-local></span>

## Get version 0.4.0

Use the [v0.4.0 GitHub release](https://github.com/pgsty/sow/releases/tag/v0.4.0) for this version's artifacts and checksums. Run `sow version` after installation, then follow the migration steps above for a 0.3 workspace.

For a new installation today, use the [current download page](/download/). Current behavior is documented in [Managed Workspaces](/docs/feature/managed/), [Signing Model](/docs/feature/signing/), and [Publication & Recovery](/blog/design/publication/).
