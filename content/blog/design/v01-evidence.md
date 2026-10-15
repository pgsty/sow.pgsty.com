---
title: "What SOW v0.1 Actually Proved"
linkTitle: "v0.1 Evidence Ledger"
date: 2026-07-31
lastmod: 2026-10-13
authors: [Vonng]
description: "A summary of 112 dated v0.1 reports covering client compatibility, scale, recovery, migration, and cloud-provider behavior."
categories: [Design]
tags: [history, v0.1, evidence, compatibility, verification]
url: "/blog/design/v01-evidence/"
weight: 90
icon: fa-solid fa-microscope
draft: false
---

The v0.1 archive contains 112 dated reports from 2026-07-11 through July 31. They record
client tests, scale measurements, failure recovery, migration, and cloud-provider
experiments. This article summarizes the main results and links to representative reports.

Each result belongs to the source revision, fixtures, clients, and environment recorded
in its report. Current compatibility is listed in the
[compatibility reference](/docs/reference/compatibility/).

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

These measurements supported streaming processing and bounded concurrency for large
repositories.

### Protocol limits found in testing {#protocol-closure-and-negative-counterexamples}

Failed experiments identified limits in the proposed protocols:

- [APT fixed-alias negative PoC](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-apt-legacy-fixed-alias-negative-poc.md)
  showed that old client semantics constrained atomic alias claims.
- [YUM raw-alias signature-bridge negative PoC](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-raw-alias-signature-bridge-negative-poc.md)
  separated legacy baseurl compatibility from strong generation-pinned metadata.
- [YUM generation atomicity](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-generation-atomicity.md)
  recorded exactly which pointer behavior could and could not be made atomic.

These experiments showed why protocol syntax and client transactions need separate tests.

### Failure and recovery

The archive exercised interrupted sync, publication, materialization, snapshot, archive,
and remote-restore paths. Later reports bound file operations to descriptors and exact
path identities, then covered rollback, quarantine, and preserved evidence.

Representative records include:

- [publish/recovery adversarial review](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-publish-recovery-adversarial-review.md);
- [selected-set recovery closure](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-13-selected-set-materialization-recovery.md);
- [state-lock and atomic publication](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-19-state-lock-atomic-publication.md);
- [derived-state replacement outcomes](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-28-derived-state-replacement-outcome.md).

These tests led to distinct recovery paths: abandon uncommitted work, complete work after
commit intent, or stop when recorded evidence conflicts.

### Legacy migration

The migration evidence enumerated old Make targets, physical layouts, repository families,
consumer configuration, package-signature inventory, and rollback. It used read-only
copies and exact receipts before mutation.

This work validated a specific Pigsty cutover path. It also established a method: record
migration assumptions as data, check them before each step, and retire the migration code
after the cutover.

### Provider and Edge experiments

The archive contains real and simulated R2, MinIO, Cloudflare, COS, and Edge tests.
Representative reports include:

- [real R2 storage protocol](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-18-real-r2-storage-protocol.md);
- [R2 publication storage transaction](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-r2-publication-storage-transaction.md);
- [full-provider checkpoint-fenced deletion](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-full-provider-checkpoint-fenced-delete.md);
- Cloudflare bootstrap, private-domain, provider-attestation, and rollback records.

<span id="what-the-archive-did-not-prove" data-td-print-local></span>

Some tests used designated nonproduction resources; others ran offline or against mocks.
The reports distinguish these environments. Storage behavior measured on R2, MinIO, or
COS applies to that service and the API tested.

## What became part of the design method

The work established six practices:

1. **State what was tested.** Distinguish source checks, simulated failures, client tests,
   and tests against a real service.
2. **Keep failed test results.** They identify conditions where the design does not work.
3. **Record inputs with each result.** Source revision, container/client version, provider,
   route, and fixture belong with the result.
4. **Measure scale.** Large repositories need measured memory, call count, and
   concurrency behavior.
5. **Test each new layout.** Keep historical results with the model they tested.
6. **Check each release build.** Test supported platforms, scan dependencies, and run static analysis.
   Check that the build can be reproduced.

These practices now appear in [Design Principles](/blog/design/principles/) and the current
[compatibility reference](/docs/reference/compatibility/).

## Primary source

The immutable [v0.1.0 evidence directory](https://github.com/pgsty/sow/tree/v0.1.0/docs/evidence)
contains every dated report, including commands, results, and test conditions.

Continue with [The v0.2 Reset](/blog/design/v02-reset/) to see how those lessons were kept
while the product model became much smaller.
