---
title: "Publication & Recovery"
linkTitle: "Publication & Recovery"
date: 2026-08-08
lastmod: 2026-10-13
authors: [Vonng]
description: "How SOW uploads a repository, resumes interrupted publication, and removes unused files."
categories: [Design]
tags: [publish, transaction, object-storage]
url: "/blog/design/publication/"
aliases:
  - "/docs/design/publication/"
weight: 40
icon: fa-solid fa-arrows-rotate
draft: false
---

A build creates a local snapshot (Generation). Publication uploads its files to a target and records progress for recovery.
Each target keeps a checkpoint that identifies its last completed publication.

<span id="ownership-split" data-td-print-local></span>

## State ownership

| Repository records | Target records |
|---|---|
| Packages, Desired state, and Built state | Publication attempts and checkpoints |
| Generations and changesets | Remote inventory |
| Retained package and metadata references | Grace periods and deletion records |

<span id="publication-phases" data-td-print-local></span>
<span id="pointer-order" data-td-print-local></span>

## Publication order

```text
freeze the plan
  -> upload packages
  -> upload immutable metadata
  -> record commit intent
  -> update protocol pointers, one view at a time
  -> verify storage and public URLs
  -> record the applied checkpoint
```

Package uploads create new objects or reuse identical bytes. They cannot overwrite an
immutable path with different content. SOW records commit intent before it changes the
first mutable APT index alias or protocol pointer.

Within a view, referenced content is uploaded before the pointer:

```text
RPM: checksum-named metadata -> repomd.xml.asc -> repomd.xml
APT: by-hash and direct indexes -> Release.gpg -> InRelease/Release
```

During an update, views can briefly use indexes from different builds. A detached signature and its index also change in separate writes.
Clients can therefore need to retry an index refresh. Public verification completes before SOW records the checkpoint.

## Public verification

SOW downloads changed files and affected index entry points through `public_endpoint`, then checks their contents.
Unchanged packages do not need another download.

The public endpoint can still return cached files. SOW waits and retries within `max_cache_ttl`.
If verification fails, SOW does not record a new completed checkpoint.

<span id="recovery-outcomes" data-td-print-local></span>

## Resume or abandon an attempt

Rerun the original `sow publish TARGET` command to resume. Recovery follows the saved plan
rather than starting from a newer local build.

| Saved state | Next action |
|---|---|
| Before commit intent | Retry publication, or use `--abort` to reconcile and abandon the attempt |
| After commit intent | Retry publication to complete the saved update |
| Checkpoint recorded | Finish remaining maintenance; a completed target needs no update |
| Conflicting file identity | Inspect the named file and target configuration before retrying |

`--abort` removes eligible private filesystem staging. It keeps remote objects and records
abandoned uploads so a later attempt can reuse matching bytes.

<span id="durable-target-identity-and-rebind" data-td-print-local></span>

## Target identity

Storage identity consists of the provider, endpoint, region, and bucket. Target identity
also includes the prefix. The first publication binds these values to the Repository.
Later attempts use that binding to find the correct history.

To change the target name, `public_endpoint`, or `max_cache_ttl`, edit `sow.yml` and run
[`sow publish TARGET --rebind`](/docs/command/publish/#rebind-mutable-target-settings).
SOW appends a binding revision. Changes to the Repository, storage identity, or prefix require a new target.

Before changing `max_cache_ttl`, complete pending target maintenance.
For filesystem targets, finish conditional deletion before changing `public_endpoint`.
A shorter TTL does not shorten an already recorded grace period.

<span id="published-pointer-fence" data-td-print-local></span>

## Remove a published view

A configured target with an applied checkpoint prevents withdrawal of its existing Dist,
architecture, or signature pointers. To retire that target, remove its entry from `targets`
in `sow.yml`, then run `sow config check`. This keeps the old remote files and publication
history; it does not delete the remote repository.

You can then change the local Dist configuration and rebuild. To publish the reduced set
of views, configure a new target with a different prefix and update clients to its URL.
`--rebind` cannot change a target prefix. See [`sow publish`](/docs/command/publish/) for
the configuration rules.

<span id="retention-without-payload-copies" data-td-print-local></span>
<span id="remote-deletion-is-a-capability" data-td-print-local></span>

## Retain and collect packages

A retained Generation stores metadata, manifests, and references to packages in the shared
Pool. Local garbage collection checks all of these references:

- current Desired and Built membership;
- retained Generations;
- active operations and recovery journals;
- publication recovery and grace periods.

It removes a package only when no reference remains and the file still matches the recorded
identity. Keeping a Generation therefore keeps its packages without making another package tree.

Filesystem target deletion requires a known inventory, exclusive ownership, and an expired
grace period. SOW conditionally deletes the recorded file, checks public absence, then
records the result. R2 target GC reports candidates and keeps the objects.
