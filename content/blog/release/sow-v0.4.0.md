---
title: "SOW v0.4.0"
linkTitle: "SOW v0.4.0"
date: 2026-08-24T00:00:00+08:00
authors: [Vonng]
description: "SOW v0.4.0 makes Managed verification single-pass, adds independently verified RPM trust rings and safe publication-target rebinding, and hardens migration, recovery, and public delivery checks."
categories: [Release]
tags: [release, managed, signing, publish, migration]
weight: 1
url: "/blog/release/sow-v0.4.0/"
draft: false
---

SOW 0.4.0 is an integrity and recovery release for Managed repositories. It makes
the deep checker's I/O contract explicit, prevents RPM trust from being assembled
across unrelated keys, adds an audited way to correct mutable publication-target
settings, and closes the remaining v0.3 migration and interrupted-publication gaps.

Plain repository behavior and the public `pool/ + dists/` layout do not change.

## Upgrade from 0.3

> [!IMPORTANT] Migrate every v0.3 Repository explicitly
> Stop all Workspace writers, back up the Workspace, install 0.4.0, and run
> `sow repo migrate REPOSITORY`
> once for each Repository before ordinary reads or writes. The migration is
> explicit and one-way; do not reopen a migrated database with SOW 0.3.

```bash
cp -a /srv/sow /srv/sow.backup-before-0.4.0
sow repo migrate pigsty -C /srv/sow
sow repo migrate pgsql -C /srv/sow
sow check -r pigsty -C /srv/sow
sow check -r pgsql -C /srv/sow
```

Schema v11 repairs the v0.3 Dist lifecycle case that could leave a Repository marked
clean while another Dist remained dirty. Repository status is now derived in the same
transaction that changes its Dists. The migration also repairs publication and signer
evidence without inventing a historical signing identity: an identity that v0.3 never
recorded remains explicitly unverified and cannot become a retained trust assertion.

Schema v12 backfills an append-only publication-target binding ledger. Initial binds,
migration backfills, and later operator-confirmed rebinds are separate immutable
revisions.

## One authenticity pass per physical payload

Every `sow check` now performs exactly one authoritative content hash for each unique
physical package payload, even when its cached fingerprint still matches. Evidence is
bound to device, inode, size, mtime, and ctime, and to the descriptor that was actually
read. Hard links to the same physical object can share the proof; a replacement or
concurrent identity change invalidates it and fails closed.

The same authenticated evidence is reused while validating retained Generations, walking
the final manifest, and producing `sow changes`. Retaining several Generations or adding
more Dists therefore does not multiply payload hashing. DEBs and unsigned RPMs require
one full payload stream; a signed RPM uses at most one additional main-header-to-EOF
signature stream, independent of the number of Dists or trust rings.

Package-facts reads are likewise scoped to the selected digest set in bounded,
deterministic SQLite batches. A warm 64 MiB build performs no package-body read.
Fingerprint drift and a missing facts row share one authoritative payload pass instead
of triggering separate scans.

## Independent RPM trust rings

Embedded RPM signatures are verified against each candidate trust ring independently.
Every recognized signature packet must verify inside one ring, and at least one verified
path must authenticate the payload. This preserves support for historical CentOS v3/v4
signatures and deliberately dual-signed packages while preventing a retained single-key
claim from being assembled out of packet-by-key successes from different rings.

The current policy ring, each retained single-key ring, and the combined trusted ring all
consume the same signature stream. Adding keys changes authorization decisions, not the
number of package reads.

## Safe target rebind and public verification

`sow publish TARGET --rebind` is the explicit operator-confirmed path for correcting a
target's mutable configuration while preserving its storage identity and recovery state.

| May change with `--rebind` | Requires a new target |
|---|---|
| target name | Repository identity |
| `public_endpoint` | provider or storage `endpoint` |
| `max_cache_ttl` | region, bucket, or `prefix` |

An ordinary publish reports the mismatch and points to `--rebind`; it never silently
adopts the new values. Rebind uses the same exclusive locks as publish, appends an audit
revision, and can resume an active commit-intent attempt forward. TTL changes are refused
while target maintenance is pending, and a filesystem public endpoint cannot change
during conditional-delete maintenance. Historical grace deadlines are never shortened.

Filesystem and R2 HTTP(S) public endpoints now share one hardened verifier. Response
headers and body idle progress have separate deadlines, so a large body may stream for
longer than two minutes as long as it continues making progress. Ordinary canonical GETs
remain authoritative; no-cache requests only prompt revalidation. Stale content and 404s
honor `max_cache_ttl`, 408/425/429/5xx responses get a short bounded retry window, and an
oversized response fails closed. Filesystem absence requires canonical 404/410 visibility.
R2 remote deletion remains deliberately disabled and report-only.

Prospective filesystem target paths are also checked for aliases before a durable bind,
including case aliases on case-insensitive volumes. A failed preflight leaves no binding
row and creates no target prefix.

## Recovery, CLI, and implementation cleanup

- Incremental publication recovery accepts only the exact old checkpoint or target
  Generation bytes at each pointer. Unknown or third identities still fail closed.
- Routine publication verifies the exact changed object set rather than downloading the full
  public Generation. No-op and applied-checkpoint recovery reuse complete private inventory
  evidence, while target GC scans only the protocol pointers it needs.
- R2 operations use phase-specific header/idle deadlines, bounded conditional multipart
  upload, retryable reads and writes, and a whole-object SHA-256 check before multipart
  completion.
- Generation signer rows are now an exact manifest side table across partial builds,
  Dist changes, migration, retention, and local GC.
- Repeating a default `sow add` converges a selected Dist left dirty by an earlier
  `--skip` or configuration change, even when the package object itself is reused.
- `sow rm --check` shares the mutating configuration guard and returns an exact no-write
  preview; its result no longer depends on the scratch filesystem device.
- Every Managed command now has a human-readable renderer. `--json` retains the stable
  `sow.cli/v1` envelope, including committed partial results and diagnostic check/preview
  results on failure.
- The retired APT v1 builder, external sort, empty-Dist implementation, and Git-tracked
  by-hash ledger have been removed. Current Plain and Managed APT parsing/rendering remain
  covered.

## Verification and artifacts

The release gates cover the full Go test suite, vet, staticcheck, dead-code reachability,
vulnerability and RPM-fork provenance checks, race tests, Linux amd64/arm64 builds, and
the deterministic payload/facts I/O contracts above. The release binaries were built
with Go 1.27.0 from source tag `v0.4.0`; the module accepts Go 1.27.0 or newer.

The release set contains four Linux/macOS archives, two RPMs, two DEBs, and
`SHA256SUMS`. Every archive contains `sow`, `README.md`, `CHANGELOG.md`, and `LICENSE`;
native Linux packages install the Apache-2.0 license with the binary.

## Get the release

Use the [download page](/download/) for platform-specific commands and verified digests,
or inspect the [GitHub release](https://github.com/pgsty/sow/releases/tag/v0.4.0).
After installation, run `sow version`, migrate each v0.3 Repository, and finish with
`sow check` before publication.

The maintained contracts are documented in [Managed Workspaces](/docs/feature/managed/),
[Signing Model](/docs/feature/signing/), and
[Publication & Recovery](/docs/design/publication/).
