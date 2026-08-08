---
title: "Design Evolution"
linkTitle: "Design Evolution"
description: "The path from the v0.1.0 repository experiment, through the unreleased C2 prototype, to the current v0.2.0 single-payload architecture."
url: "/docs/design/evolution/"
weight: 600
icon: fa-solid fa-timeline
---

SOW's historical documents describe several materially different systems. Git history was
cleaned up so the public version sequence is now simple: **v0.1.0** is the research
baseline and **v0.2.0** is the current product. C2 existed between them as a development
layout, but it was never a separately released product version.

## Timeline

| Line | Primary problem | Physical model | Disposition |
|---|---|---|---|
| v0.1.0 (2026-07-31) | absorb Pigsty's existing APT/YUM trees and explore remote publication | Git/CAS, route-aware projections, edge/provider contracts | historical research baseline |
| Unreleased C2 prototype | deliver a compact Plain + Managed local repository manager and make default EL `reposync` work | root Pool plus view-local RPM hardlinks | migration input only; not the current layout |
| v0.2.0 (2026-08-08) | keep one canonical payload per Repository/prefix and add target-scoped publication | root Pool plus metadata-only views, explicit export, filesystem/R2 targets | current release line |

There is no v1 product release and no v0.3 product line. Lower-level identifiers such as
`sow.cli/v1`, `single-payload-v1`, and `sow-rpm-leaf-v1` are wire or layout schema names,
not Git tags.

## What survived v0.1.0

The v0.1.0 program explored repository adoption, remote publication, provider fencing,
edge authorization, migration, recovery, and large-repository evidence. Its exact
Git/CAS/route model was replaced, but several principles survived:

- identity is bound to final bytes;
- configuration, local state, public state, and provider state have separate owners;
- publication is an ordered recoverable transaction, not an `rclone` side effect;
- destructive work requires exact inventory and provider evidence;
- every claim names its source revision, environment, and verification layer.

The original PRDs, ADRs, reviews, and dated evidence remain available from the v0.1.0 tag
and Git history. They are forensic inputs, not current command or layout documentation.

## The C2 prototype and `reposync`

The pre-release C2 layout tested a Repository with a canonical root Pool and view-local
RPM hardlink aliases:

```text
pool/...                              canonical package
dists/el9/x86_64/pool/...             hardlink alias
dists/el9/x86_64/repodata/...         href="pool/..."
```

This made each RPM architecture leaf self-contained and allowed default EL `reposync` to
mirror it. It also depended on same-filesystem hardlinks for local deduplication. Once the
same tree was copied to object storage, every alias became another complete object, so the
layout violated the stronger one-payload publication boundary.

The C2 result remains useful compatibility evidence for that prototype. It is not evidence
that the current canonical Repository supports default `reposync`.

## Why v0.2.0 uses one payload

v0.2.0 makes one canonical payload per Repository/publish prefix an invariant. RPM views
contain metadata only and compute the relative path back to the root Pool:

```text
pool/...                              only package payload
dists/el9/x86_64/repodata/...         href="../../../pool/..."
```

APT already uses archive-root-relative `Filename` values, so it naturally shares the same
Pool. A complete `pool/ + dists/` Repository can be copied, archived, or uploaded without
depending on inode identity. When a self-contained RPM leaf is required, `sow export
rpm-leaf` creates an explicit external copy (or an opt-in trusted hardlink export) with a
visible duplication cost.

## Migration boundary

Some development workspaces were created with `schema: sow/v2` and the C2 physical
layout. v0.2.0 creates `schema: sow/v3`. Read-only discovery can recognize the predecessor,
but ordinary writers never upgrade it implicitly. Only `sow repo migrate` enters the
journaled transition:

```text
planned -> staged -> commit_intent -> pointer_rollforward
        -> grace -> alias_delete -> final_manifest -> done
```

Before commit intent, `sow repo migrate --abort` may restore C2. After commit intent,
recovery is forward-only. Legacy aliases remain through the grace window for clients
holding old metadata, then are deleted from an exact recorded inventory without touching
the root Pool.

On a provider without safe conditional delete, move to a fresh non-overlapping prefix and
retire the old prefix as a whole. SOW never invents evidence that an old remote tree was
physically deduplicated.

## History policy

Historical files explain decisions; maintained pages explain the product. Do not rewrite
an old test result to match a new implementation. Record new behavior in the current docs
and CHANGELOG, while using version tags and Git history for the original evidence.
