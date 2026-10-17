---
title: "Observability & Audit"
linkTitle: "Observability & Audit"
description: "Inspect state, verify repository content, compare generations, and read operation history."
categories: [Feature]
tags: [audit, transaction]
url: "/docs/feature/audit/"
weight: 800
icon: fa-solid fa-magnifying-glass-chart
---

Use `status` to inspect state, `check` to verify a repository, `changes` to list file
changes, and `log` to read operation history.

| Command | Answers |
|---|---|
| `status` | Does the repository need a build or recovery? Is a writer active? |
| `check` | Are state, package bytes, indexes, and signatures consistent and ready for delivery? |
| `changes` | Which local files changed between built generations? |
| `log` | Which operations ran, and what did they change? |
| `retain ls` | Which generations are explicitly retained? |

These commands do not modify repository contents.

<span id="status-cheap-state" data-td-print-local></span>

## Inspect state

```bash
sow status -r demo
```

The result includes Desired revision, built generation, dirty Dists, pending package
count and bytes, writer-lock state, and `ready_to_copy`.

| State | Meaning |
|---|---|
| `clean` | Desired and built state agree |
| `dirty` | Membership or configuration needs a build |
| `recovering` | Recorded work needs recovery or cleanup |
| `error` | Recorded state or file evidence has an unresolved error |

`status` reports state without hashing the public tree. For `dirty`, run `build`.
For `recovering` or `error`, follow the diagnostic and
[recovery procedure](/docs/feature/transactions/#recover-an-interrupted-operation).
Run `check` before delivery.

<span id="check-delivery-proof" data-td-print-local></span>

## Verify the repository

```bash
sow check -r demo
```

A normal check reports nine layers:

| Layer | Checks |
|---|---|
| `config` | Configuration and effective Dist settings |
| `state` | SQLite schema and relational state |
| `public-modes` | Public file and directory permissions |
| `retained` | Retained generation records and metadata |
| `package-bytes` | Pool and pending bytes against recorded SHA-256 |
| `desired-membership` | Package identity, architecture, and membership |
| `index` | Index contents and referenced files |
| `signature` | Configured metadata and RPM package signatures |
| `generation-manifest` | Built file manifest against the public tree |

An unfinished layout transition instead reports `config`, `state`, `public-modes`, and
`layout-transition`. Complete or abort that migration as directed by
[`repo migrate`](/docs/command/repo/#sow-repo-migrate).

`check` reads and hashes each unique physical package regardless of cached fingerprints.
It does not repair files. A dirty or recovering repository fails readiness even if its
previous built tree remains consistent.

<span id="changes-generation-difference" data-td-print-local></span>

## Compare generations

```bash
sow changes -r demo
sow changes 0 -r demo
sow changes 42 -r demo --json
```

No base compares with the previous built generation. Base `0` lists the complete current
tree. Base `42` compares recorded generation 42 with the current one.
Rows contain the action, phase, repository-relative path, size, and SHA-256 as applicable.

This comparison does not inspect a publication target. Use `sow publish TARGET` to update
that target and resume interrupted transfers. Use target GC to reclaim remote objects.

<span id="generation-retention-and-gc" data-td-print-local></span>

## Retain generations and collect unused packages

`retain add` accepts the current built generation only. If `status` reports generation 42,
retain it before a later build replaces it:

```bash
sow retain add 42 -r demo
sow retain ls -r demo
```

The command verifies the generation and saves its metadata and references. Package files
remain in the shared pool. When generation 42 is no longer needed, remove its retention
record with `sow retain rm 42 -r demo`. Then run `sow gc -r demo` to collect unused bytes.
Local `gc` requires a clean repository; build pending changes first. It preserves packages
needed by Desired, built, and previous-client membership records, retained generations,
recovery, or publication state. See [`gc`](/docs/command/gc/) for the complete rules.

The previous-generation metadata kept during ordinary builds is separate from explicit
retention. For target cleanup, run `sow gc TARGET`. Filesystem targets support conditional
deletion after cache grace; R2 targets report candidates without deleting them.

<span id="operation-log" data-td-print-local></span>

## Read and export the log

```bash
sow log -r demo
sow log OPERATION -r demo
sow log export operations.jsonl -r demo
sow log prune 2026-01-01 -r demo
```

The log records operation state, times, package results, membership changes, and file
changes where applicable. An operation detail can include build-progress events.

`log export` writes JSON Lines to a new file or stdout. `log prune` accepts a date or
RFC 3339 timestamp and removes eligible terminal audit records. Required recovery records
and generation manifests remain available.

See [JSON output](/docs/reference/json/) for scripts and
[Transactions and recovery](/docs/feature/transactions/) for interrupted operations.

<span id="operational-pattern" data-td-print-local></span>
<span id="see-also" data-td-print-local></span>
