---
title: "Design Principles"
linkTitle: "Principles"
date: 2026-08-08
lastmod: 2026-10-13
authors: [Vonng]
description: "Why SOW separates package storage, repository builds, and publication."
categories: [Design]
tags: [plain, managed, repository]
url: "/blog/design/principles/"
aliases:
  - "/docs/design/principles/"
weight: 60
icon: fa-solid fa-ruler-combined
draft: false
---

SOW separates package storage, repository builds, and publication. These principles explain
where each kind of state belongs and how operations use it.

<span id="one-owner-for-every-durable-fact" data-td-print-local></span>

## One owner for each record

| Record | Owner |
|---|---|
| Package bytes and identity | Repository |
| Desired membership and Built state | Repository |
| Generations and changesets | Repository |
| Target bindings and revisions | Repository and target |
| Publication attempts and checkpoints | Repository and target prefix |
| Remote inventory and deletion records | Repository and target prefix |

Each Repository stores its own copy of a package. Each publication target stores its own
copy too. This keeps package retention and deletion independent across repositories and targets.

<span id="canonical-data-rebuildable-projections" data-td-print-local></span>

## Store packages; rebuild indexes

In Managed mode, `pool/` holds the package bytes. In Plain mode, the input directory holds
them. Indexes and architecture views describe those packages and can be rebuilt.

Managed garbage collection removes a package only after its active, retained, and recovery
references are gone. Plain mode rebuilds indexes directly from the current directory.

<span id="the-public-tree-is-the-delivery-unit" data-td-print-local></span>

## Serve the complete public tree

A Managed Repository root contains `pool/` and `dists/`. Copy or serve that complete root
so clients can resolve package paths from the indexes. Use `sow export rpm-leaf` when a
consumer needs a self-contained RPM architecture directory.

Keep the workspace's `sow.yml` and `.sow/` outside the HTTP root. They contain configuration,
databases, locks, journals, and recovery files.

<span id="pointers-commit-payloads-prepare" data-td-print-local></span>

## Upload packages before indexes

Publication uses this order:

```text
packages -> immutable metadata -> protocol pointers -> grace period -> eligible deletion
```

Protocol pointers include `repomd.xml`, `Release`, and `InRelease`. SOW uploads referenced
files before updating these pointers. Old files remain through the grace period so clients
with cached indexes can still use them.

<span id="recovery-cost-follows-state-cost" data-td-print-local></span>

## Recover according to the recorded state

After an interrupted Plain build, run `sow create` again. It scans the package directory
and rebuilds the indexes.

A Managed publication records its plan and progress. Before commit intent, SOW can reconcile
an attempt and abandon it. After commit intent, rerun `sow publish TARGET` to complete the
recorded update. Conflicting file identities stop recovery and identify the object to inspect.

<span id="compatibility-is-a-matrix" data-td-print-local></span>
<span id="evidence-never-upgrades-itself" data-td-print-local></span>

## Test the layout with its consumers

A package manager resolves package URLs; a mirror tool can also impose rules on its output
directory. Test the complete Repository and an exported RPM leaf separately. Record the
client version and layout with each result. The [compatibility reference](/docs/reference/compatibility/)
lists automated coverage.

<span id="non-goals-keep-the-model-honest" data-td-print-local></span>

## Keep coordination local

Use one workspace as the writer for each target prefix. SOW coordinates local processes
with locks. It does not arbitrate between independent workspaces.

R2 publication supports incremental uploads. R2 garbage collection reports candidates and
keeps remote files because this backend does not implement the required conditional deletion.
