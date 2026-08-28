---
title: "Coordinated Publication Decision"
linkTitle: "Publication Decision"
date: 2026-08-14
lastmod: 2026-08-24
authors: [Vonng]
description: "The v0.4.0 decision to keep SOW's native publication providers, and the earlier rclone proposal that did not ship."
categories: [Design]
tags: [publish, transaction, object-storage, decision]
url: "/blog/design/coordinated-publication/"
aliases:
  - "/docs/design/coordinated-publication/"
weight: 10
icon: fa-solid fa-cloud-arrow-up
draft: false
---

> [!IMPORTANT] Decision finalized for SOW 0.4.0
> An earlier version of this record proposed an rclone executor, `publish --dry-run`, and a
> separate `sow audit` command. None of those surfaces shipped in 0.4.0. SOW has no
> rclone dependency, `publish` has no `--dry-run`, and `sow audit` is not a command.

This page preserves the decision boundary so a historical proposal cannot be mistaken for the
current product. The normative behavior is documented in
[`sow publish`](/docs/command/publish/) and
[Publication & Recovery](/blog/design/publication/).

## Decision

SOW 0.4.0 keeps its native `filesystem` and `r2` publication providers. SOW owns both the
Repository meaning and the transport operations needed to preserve it:

- the frozen Generation and exact change plan;
- create-only immutable objects and conditional mutable writes;
- durable commit intent and deterministic pointer order;
- attempt, checkpoint, inventory, grace, and recovery evidence;
- provider verification and canonical public visibility checks.

The public guarantee remains deliberately narrow: publication is ordered, restartable, and
eventually converges to one frozen Generation. It is not an atomic transaction across all object
keys, and it does not create DNS, bucket policy, CDN configuration, or client trust policy.

## Why the executor proposal was not adopted

A generic bulk-copy executor would introduce another versioned dependency while weakening the
one-to-one relationship between a planned object and its conditional-write receipt. It would also
require a second checkpoint identity model for providers whose bulk tool cannot preserve SOW's
per-object SHA-256 metadata.

The 0.4 work instead hardened the existing, smaller transport boundary: bounded conditional
multipart upload, phase-specific header and idle-progress deadlines, retryable replay-safe
operations, exact changed-closure verification, and a shared public HTTP verifier. This preserved
the existing checkpoint model and avoided a transport migration disguised as a routine upgrade.

## What 0.4.0 shipped

### Native incremental publication

`publish` computes the exact Generation delta, writes payload and checksum-addressed metadata
before pointers, persists commit intent, advances views in deterministic order, verifies provider
and public evidence, and records an Applied Checkpoint. A current target is an idempotent no-op.

### Operator-confirmed rebind

`publish TARGET --rebind` can revise the target name, `public_endpoint`, or `max_cache_ttl` while
preserving stable storage and target identities. Storage endpoint, provider, region, bucket,
Repository, and prefix require a new target. Every accepted rebind appends an immutable audit
revision and retains forward recovery for an active commit-intent attempt.

### Hardened public visibility

Filesystem and R2 HTTP(S) targets share canonical-GET verification, cache-TTL handling for stale
content, short bounded transient retries, independent header/body-idle deadlines, and an oversize
guard. Filesystem conditional deletion additionally waits for canonical public 404/410 evidence.
R2 deletion remains disabled and report-only.

## Operator workflow

```bash
sow build -r pgsql
sow check -r pgsql
sow changes -r pgsql
sow publish prod
```

`changes` is the read-only local Generation delta; it is not a remote dry run. `publish` accepts
only a configured target and owns the remote preflight. Use `--json` for machine-readable results.

If configuration drift is reported, inspect the fields first. Use `--rebind` only for a permitted
mutable correction; create a new target for any storage or prefix change.

## Recovery decision

```text
Was durable commit intent recorded?
├── no  -> rerun publish, or reconcile and publish --abort
└── yes -> rerun publish; forward recovery is the only legal direction
```

Repeating the original command is the resume operation. There is no `--resume` flag. Contradictory
attempt, checkpoint, provider, or public evidence fails closed rather than selecting a convenient
history.

## Explicit boundaries

- There is no full-prefix remote `sow audit` command. `sow check` proves the local Repository;
  normal publication proves its exact changed closure and affected public pointers.
- R2 target GC records exact report-only candidates and never deletes remote objects.
- Multiple independent writers, distributed locking, automatic cache purge, DNS management, and
  arbitrary executor plugins are outside the current contract.
- A successful provider write is not package-manager acceptance. Run the deployed dnf/APT client
  and signing policy as a separate release gate.

## References

- [Current Publication & Recovery model](/blog/design/publication/)
- [Current `sow publish` command](/docs/command/publish/)
- [Platforms & Integrations](/docs/reference/compatibility/)
