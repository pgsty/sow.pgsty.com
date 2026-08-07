---
title: "Design Evolution"
linkTitle: "Design Evolution"
description: "The path from the V1 repository experiment through v0.2 C2 views to the 0.3 single-payload architecture."
url: "/docs/design/evolution/"
weight: 600
icon: fa-solid fa-timeline
---

SOW's old documents came from three materially different systems. Preserving them without
a version boundary made contradictory statements look simultaneous. This page keeps the
useful decisions while making their scope explicit.

## Timeline

| Line | Primary problem | Physical model | Disposition |
|---|---|---|---|
| V1 experiment (July 2026) | absorb Pigsty's existing APT/YUM trees and remote publishing workflow | Git/CAS, route-aware projections, edge/provider contracts | archived research and implementation evidence |
| v0.2.0 | ship a compact local Plain + Managed repository manager | root Pool plus C2 view-local RPM hardlinks | released; operational docs remain live |
| 0.3 development | publish one canonical payload per Repository/target prefix | root Pool plus metadata-only views and target-scoped publication | implemented in source; release evidence pending |

## What survived V1

The broad V1 program explored repository adoption, remote publication, provider fencing,
edge authorization, migration, recovery, and large-repository evidence. Much of its exact
Git/CAS/route model was replaced, but several principles survived:

- identity must be bound to final bytes;
- configuration, local state, public state, and provider state need separate owners;
- publication is an ordered recoverable transaction, not an `rclone` side effect;
- destructive remote work requires exact inventory and provider evidence;
- a claim must name its source revision, environment, and verification layer.

The old PRDs, 45 ADRs, implementation prompts, migration runbooks, and dated evidence are
sealed in the source archive. They are not current command or layout documentation.

## Why v0.2 chose C2

v0.2 narrowed the product to a local single-binary manager with two isolated paths:
`sow create` for flat repositories and a Managed Workspace for Package Objects, Dists,
membership, signing, transactional builds, checks, and logs.

For RPM views, tests showed that parent-relative hrefs worked for normal DNF but failed
default EL `reposync`. Because mirroring was then a release gate, v0.2 chose view-local
hardlink aliases:

```text
pool/...                              canonical package
dists/el9/x86_64/pool/...             hardlink alias
dists/el9/x86_64/repodata/...         href="pool/..."
```

This was a sound decision for the stated v0.2 contract. It passed the relevant real-client
matrix and kept local disk deduplicated on a same-filesystem POSIX tree.

## Why 0.3 reverses that decision

The layout becomes expensive when the same tree is published to object storage. Hardlink
identity disappears, so every Dist/architecture alias uploads as another full object.
Retention and snapshots would amplify the same package again.

0.3 changes the priority: one canonical payload per Repository/prefix is now invariant;
default `reposync` against the canonical tree is no longer promised. A self-contained RPM
leaf becomes an explicit external export with a visible duplication cost.

```text
pool/...                              only package payload
dists/el9/x86_64/repodata/...         computed href="../../../pool/..."
```

This is not a correction to v0.2 history. It is a new contract optimized for a different
delivery boundary.

## Migration boundary

0.3 reads frozen v0.2 configuration/state for discovery and status, but ordinary writers
do not upgrade it implicitly. Only explicit `sow repo migrate` enters the journaled
C2-to-single transition:

```text
planned -> staged -> commit_intent -> pointer_rollforward
        -> grace -> alias_delete -> final_manifest -> done
```

Before commit intent, `repo migrate --abort` may restore C2. After commit intent, recovery
is forward-only. Legacy aliases remain through grace for clients holding old metadata, then
are deleted from an exact recorded inventory without touching the root Pool.

On a remote provider without safe conditional delete, migration uses a fresh empty prefix
and an external route/cutover decision. The old prefix is retired as a whole; SOW does not
pretend it was physically deduplicated.

## Archive policy

Historical files are preserved because they explain decisions and provide dated evidence,
not because every file deserves a navigation entry. The source archive is immutable in
spirit:

- do not edit an old PASS to match a new implementation;
- add a new versioned result instead;
- preserve negative PoCs, since rejected alternatives explain the chosen design;
- use this site for maintained design and user documentation;
- use Git history and the sealed archive for forensic detail.

This separation leaves one place to learn the product without discarding the reasoning
that produced it.
