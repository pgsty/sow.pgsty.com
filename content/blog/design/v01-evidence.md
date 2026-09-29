---
title: "What SOW v0.1 Actually Proved"
linkTitle: "v0.1 Evidence Ledger"
date: 2026-07-31
lastmod: 2026-08-28
authors: [Vonng]
description: "A curated account of 112 dated v0.1 evidence reports: the real clients, scale, failure, migration, and provider claims they supported—and what they never proved."
categories: [Design]
tags: [history, v0.1, evidence, compatibility, verification]
url: "/blog/design/v01-evidence/"
weight: 90
icon: fa-solid fa-microscope
draft: false
---

> [!IMPORTANT] Version-bound evidence
> Every result on this page belongs to the v0.1 source, layout, fixtures, and
> environment recorded at the time. It does not establish compatibility or
> release readiness for current SOW.

The v0.1 archive contains 112 dated evidence reports from 2026-07-11 through
2026-07-31. Publishing all of them as blog posts would make the public site less useful:
many are narrow fault closures, repeated current-source audits, or transcripts for a
specific implementation seam.

Discarding them would lose something equally important. The reports show which design
decisions came from real clients and counterexamples, which came only from local or mock
tests, and where the team deliberately refused to turn incomplete evidence into a PASS.

This ledger preserves that boundary.

## Evidence timeline

| Window | Reports | What the work concentrated on |
|---|---:|---|
| 2026-07-11 | 3 | Real APT/DNF client baseline, 72,310-package manifest scan, 50k upstream streaming |
| 2026-07-12 | 35 | APT/YUM protocol behavior, CAS/GC, publication ordering, recovery, MinIO, performance, migration, build/supply-chain gates, and cloud harness design |
| 2026-07-13 | 2 | RPM trust closure and selected-set materialization recovery |
| 2026-07-14–16 | 14 | Legacy topology, family migration, physical ownership, full-copy adoption, and package-signature inventory |
| 2026-07-17–20 | 39 | Cloudflare/R2/COS/Edge safety, provider attestation, cutover receipts, configuration bounds, and checkpoint-fenced deletion |
| 2026-07-22 | 10 | Descriptor/path identity across stage, apply, prune, rollback, and residue cleanup |
| 2026-07-26–29 | 7 | Recursive durability, hostile-writer limits, replacement outcomes, preserved audits, and provider corrections |
| 2026-07-30–31 | 2 | Clean-room APT/YUM/asset MVP and final legacy-source baseline |

## What had strong supporting evidence

### Real package clients and large repositories

The first evidence set used real APT and DNF clients rather than validating only generated
XML or text. It also measured scale explicitly:

- [real APT/DNF client compatibility](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-client-compat.md);
- [72,310-package manifest scanning](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-manifest-72k-performance.md);
- [50k upstream streaming](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-upstream-50k-streaming.md);
- separate 50k APT, YUM, materialization, publish-plan, and legacy-adoption runs.

These reports justified streaming and bounded-concurrency requirements. They did not prove
that every later layout inherited the same client behavior or performance.

### Protocol closure and negative counterexamples

Several design changes came from negative proof rather than optimistic implementation:

- [APT fixed-alias negative PoC](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-apt-legacy-fixed-alias-negative-poc.md)
  showed that old client semantics constrained atomic alias claims.
- [YUM raw-alias signature-bridge negative PoC](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-raw-alias-signature-bridge-negative-poc.md)
  separated legacy baseurl compatibility from strong generation-pinned metadata.
- [YUM generation atomicity](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-generation-atomicity.md)
  recorded exactly which pointer behavior could and could not be made atomic.

The lasting lesson is not the V1 URL scheme. It is that a standards-shaped repository and
a specific client transaction are different claims.

### Failure and recovery

The archive exercised interrupted sync, publication, materialization, snapshot, archive,
and remote-restore paths. Later reports bound file operations to descriptors and exact
path identities, then covered rollback, quarantine, and preserved evidence.

Representative records include:

- [publish/recovery adversarial review](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-publish-recovery-adversarial-review.md);
- [selected-set recovery closure](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-13-selected-set-materialization-recovery.md);
- [state-lock and atomic publication](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-19-state-lock-atomic-publication.md);
- [derived-state replacement outcomes](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-28-derived-state-replacement-outcome.md).

This work is why current SOW distinguishes pre-commit abandon, post-intent forward
recovery, and contradictory evidence instead of exposing one generic “retry” path.

### Legacy migration

The migration evidence enumerated old Make targets, physical layouts, repository families,
consumer configuration, package-signature inventory, and rollback. It used read-only
copies and exact receipts before mutation.

That program proved a particular Pigsty cutover path. It did not justify carrying legacy
topology into the permanent product model. Its most valuable result was the discipline:
migration assumptions become explicit data and executable gates, then retire after the
cutover.

### Provider and Edge experiments

The archive contains real and simulated R2, MinIO, Cloudflare, COS, and Edge work. The
stronger reports state exact scope:

- [real R2 storage protocol](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-18-real-r2-storage-protocol.md);
- [R2 publication storage transaction](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-r2-publication-storage-transaction.md);
- [full-provider checkpoint-fenced deletion](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-full-provider-checkpoint-fenced-delete.md);
- Cloudflare bootstrap, private-domain, provider-attestation, and rollback records.

Some cells used owner-designated nonproduction resources; others were offline or mock
validation. A real R2 result never proved COS conditional replacement, EdgeOne cache
behavior, or current SOW's target state machine.

## What the archive did not prove

The evidence set was large, but its own documents retained open boundaries:

- no one PoC established universal APT, DNF, proxy, mirror-tool, or provider compatibility;
- MinIO S3 compatibility did not equal Cloudflare R2 or Tencent COS semantics;
- an accepted design or adversarial review was not implementation evidence;
- a local/mock provider result was not a production deployment;
- a PASS remained attached to its source revision, fixture, URL layout, and environment;
- v0.1 evidence could not validate the later Plain/Managed or single-payload designs.

Those limitations are a feature of the archive, not a defect to edit away.

## What became part of the design method

The evidence program left six durable practices:

1. **Name the evidence layer.** Design, source, unit/fault test, real client, provider,
   artifact, and production are separate.
2. **Retain negative results.** A counterexample often defines a safer product boundary
   more clearly than another successful happy path.
3. **Bind PASS to immutable inputs.** Source revision, container/client version, provider,
   route, and fixture belong with the result.
4. **Test scale as a contract.** Large repositories need measured memory, call count, and
   concurrency behavior.
5. **Retire evidence with its model.** Historical proof remains useful for explanation but
   never silently upgrades a new layout.
6. **Keep build and supply-chain checks standing.** Toolchain portability, dependency
   vulnerability checks, static analysis, dead-code closure, and reproducible delivery are
   continuous release gates rather than one-time cleanup tasks.

These practices now appear in [Design Principles](/blog/design/principles/) and the current
[compatibility reference](/docs/reference/compatibility/).

## Primary source

The immutable [v0.1.0 evidence directory](https://github.com/pgsty/sow/tree/v0.1.0/docs/evidence)
contains every dated report. This article is the maintained interpretation; the raw files
remain the audit trail.

Continue with [The v0.2 Reset](/blog/design/v02-reset/) to see how those lessons were kept
while the product model became much smaller.
