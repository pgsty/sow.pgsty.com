---
title: "SOW v0.6.0"
linkTitle: "SOW v0.6.0"
date: 2026-10-17T00:00:00+08:00
lastmod: 2026-10-17
authors: [Vonng]
description: "SOW 0.6.0 keeps previous Plain RPM indexes, records Managed publication times, strengthens verification and recovery, and reduces repeated I/O."
categories: [Release]
tags: [release, plain, managed, recovery, signing, performance]
weight: -20
url: "/blog/release/sow-v0.6.0/"
---

SOW 0.6.0 improves repository updates, file verification, and recovery after an interruption.
It keeps the current command set, configuration format, and public repository layout.
A Managed workspace already on 0.5.0 needs no database migration.

This note covers the changes since 0.5.0. Use the [installation guide](/docs/start/install/) for upgrade steps
and the [download page](/download/) for release availability.

## Changes for repository operators

| Area | Change in 0.6.0 | Effect on your workflow |
|---|---|---|
| Plain RPM updates | Keep current and immediately previous checksum-named metadata | Clients can finish fetching metadata referenced by the previous index |
| Managed builds | Record one publication time for metadata and signatures | Recovery preserves the original time; unchanged builds keep their existing output |
| File verification | Check file identity throughout authenticated reads | Replaced or rewritten files are detected, including rewrites that restore the modification time |
| Signing keys | Read complete OpenPGP key bundles | All supplied trusted keys are considered; malformed input is rejected |
| State and recovery | Preserve locks, consistent reads, and committed results | Maintenance errors do not make completed changes appear to have rolled back |
| Large repositories | Reuse verified data and limit parallel work | Builds, imports, checks, and publication avoid repeated work |

## Plain RPM updates keep the previous indexes

A client first downloads `repomd.xml`, then requests the metadata files named inside it.
An update between those requests could previously remove the old metadata files before the client fetched them.

Plain `sow create` now keeps the current and immediately previous checksum-named RPM metadata sets.
An unchanged run does not advance this window. Older metadata can be removed after the next changed index.

The small `.sow-plain-rpm-history.json` file records the retained references.
Keep it when copying a directory for further builds. It is not an operation journal; interrupted Plain builds still recover by rerunning `create`.

This window does not retain removed package files or cover every client cache lifetime.
For caches that span several updates, keep the required packages and metadata in your publication layer.
The [YUM migration guide](/docs/tutorial/yum-migration/) explains publication order, signatures, and cached clients.

Plain timestamps remain explicit. `--metadata-timestamp` still defaults to `0`.
Keep the greatest published timestamp when replacing another generator or restoring older package content.

## Managed builds keep one publication time

A new Managed build records one UTC time, with whole-second precision, before it publishes the affected Dist indexes.
The same value supplies APT `Release` dates, RPM `repomd.xml` data timestamps, and metadata signature times.
RPM `revision` remains the Generation number.

The chosen time respects previous build times and the selected signing key's activation time.
An unusable or not-yet-valid key causes an error. Keep the host clock correct.

Recovery reuses the recorded time. It rejects a changed time before publishing further Dist entry points.
A no-op build creates no new Generation and does not refresh timestamps or signatures.

This behavior applies to new metadata-building operations, including automatic builds from `add` and `rm`, and new Dists.
Layout migration and older journals keep their previous timestamp rules.
Standalone `export rpm-leaf` output still uses RPM data timestamp `0`.

An `rm --check` preview remains read-only. It predicts membership, paths, actions, and the resulting revision and Generation.
Execution chooses its own publication time. Time-dependent bytes, hashes, and sizes can therefore differ from the preview.

## Verify the file that was actually read

Metadata and package checks now bind the digest to the opened file's identity before and after reading.
The same checks apply to fast validation and reused verification results.
They detect file replacement and same-size rewrites, including changes that restore the original modification time.

Concurrent hard-link creation can change file attributes without changing package bytes.
SOW handles this case and retains the identity from the successful verification.
This keeps read-only hard-link exports compatible with repository checks.

Path traversal also checks that opened entries match the entries inspected earlier.
Parent directories need traversal permission; they no longer need directory-listing permission merely to reach a known child.
Package files still need read access, and controlled paths still reject unsafe symlinks and file types.

## Read complete signing-key bundles

A trusted-key file can contain several public keys or consecutive armored key blocks.
SOW now reads the complete input instead of stopping after the first block.
It rejects malformed, truncated, or unsupported key material instead of silently skipping it.

A signing `key` reference must still identify exactly one primary key.
Put bundles in `trusted_keys`; use one signing identity for each metadata or package-signing setting.
The [signing reference](/docs/feature/signing/) describes both cases.

## Keep state and recovery results consistent

SQLite identity checks now preserve locks held by existing connections.
Composite repository queries read related state from one database snapshot.
Eligible WAL databases undergo validation once per open, avoiding repeated full validation during one connection's work.

A database commit can succeed before a later checkpoint or cleanup fails.
SOW now preserves the committed command result in that case.
Inspect the result, `sow status`, and `sow log` before retrying; a nonzero exit does not prove rollback.

Dist status also reports unfinished repository maintenance, including local GC and log pruning.
Matching Desired and Built package counts no longer hide this pending work.
Removal logs preserve policy-driven outcomes as well as explicitly selected removals.

For an already-started development-era C2 layout transition, `repo migrate --abort` keeps the trusted transition marker.
It can also finish before the first journal or base manifest exists.
If a journal binds a plan, SOW verifies that plan against its recorded base manifest and rejects conflicting control records.

A nonempty temporary migration stage moves intact into `.sow/<repo>/abandoned/`.
The command reports the retained path or cleanup problem in stderr and JSON `warnings`.
Stage-cleanup warnings do not prevent abandonment. The public tree remains unchanged.
Once selected, the Repository name remains available in migration failure responses.

A fresh C2 repository still cannot start a migration.
An older abort that already removed its trusted marker requires a matching backup or a new workspace.
See [`repo migrate`](/docs/command/repo/#sow-repo-migrate) for the supported recovery paths.

## Reduce repeated work

The release reduces I/O without adding another full repository scan or recovery state machine:

- Reuse authenticated DEB bytes for parsing and checking within the same operation.
- Reuse current payload and Dist verification results where their file identities still match.
- Reuse verified RPM export output instead of reading the same copy again.
- Avoid duplicate writes while staging imports and remove an unused initial output-tree hash.
- Query memberships for the selected packages and reuse package data already loaded for the operation.
- Keep package-staging workers independent and bounded by the requested concurrency.

`sow check` still reads and hashes each unique physical package on every run.
These changes do not turn it into a fingerprint-only check.

R2 inventory checks now use at most eight concurrent HEAD requests per page.
The queued work and completed results stay bounded, including cancellation and failures.
Upload retries no longer restart the idle timeout merely by seeking in the source file.
Actual transfer progress is required. R2 garbage collection remains report-only.

## Build, packaging, and validation

Source builds require **Go 1.27.2 or newer**. Quality checks use staticcheck 0.8.2.
Upstream verification for the patched RPM parser also works when Go selected a downloaded toolchain.

The release targets remain Linux and macOS on `amd64` and `arm64`.
Packaging produces four archives, two RPMs, two DEBs, and `SHA256SUMS`.
Archives and packages retain their license files and third-party notices.
Deterministic source delivery excludes local agent instructions from the delivered product source.

Regression tests cover file replacement, restored modification times, concurrent hard links, and complete key bundles.
They also cover commit cancellation, post-commit failures, metadata-time recovery, migration abort, Plain index retention, and bounded R2 requests.
The release also removes unused code and brittle Go runtime I/O instrumentation.

Local release checks covered the macOS and Linux suites, race checks, APT/DNF integration, and S3-compatible transport.
They also covered 50,000-package RPM metadata generation, packaging, and an upgrade from the published 0.5.0 binary.
Use your actual package clients and publication target for deployment acceptance.

## Upgrade from 0.5.0

Database schema **v13**, configuration schema **`sow/v3`**, and the public **`pool/ + dists/`** layout remain unchanged.

1. Stop workspace writers.
2. Back up the complete workspace, preserving hard links.
3. Install SOW 0.6.0.
4. Run these commands for each Repository:

```bash
sow version
sow build -C /srv/sow -r REPOSITORY
sow check -C /srv/sow -r REPOSITORY
```

Replace `REPOSITORY` and `/srv/sow` with your values.
A current 0.5.0 repository needs no schema migration or forced rebuild; `build` reports a no-op.
Publish only when you intend to deliver a new Built Generation to a configured target.

For 0.3 or 0.4 workspaces, run `sow repo migrate REPOSITORY` before building.
See the [complete upgrade procedure](/docs/start/install/#upgrade-to-060).
