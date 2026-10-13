---
title: "SOW v0.1 Decision Ledger: What Survived and What Was Retired"
linkTitle: "v0.1 Decision Ledger"
date: 2026-07-12
lastmod: 2026-10-13
authors: [Vonng]
description: "All 44 surviving v0.1 architecture decisions: their original purpose and how each changed after the repository model reset."
categories: [Design]
tags: [history, v0.1, adr, decision, migration]
url: "/blog/design/v01-decisions/"
weight: 100
icon: fa-solid fa-list-check
draft: false
---

The v0.1.0 tag contains 44 architecture decision records (ADRs), numbered 0001 through
0045; 0006 is absent. Each ADR records a problem, the decision made at the time, and the
conditions that implementation had to meet. This table shows what happened to those
decisions after the repository model changed.

| Fate | Meaning |
|---|---|
| **Retained** | The principle remains in current SOW with substantially the same boundary. |
| **Evolved** | The problem remains, but ownership or implementation changed. |
| **Migration history** | The decision governed the Pigsty/V1 cutover. |
| **Retired** | The decision belonged to the removed Git/CAS/Route/Edge model. |

Decision dates run from 2026-07-11 through July 28. ADR-0035 also has amendments from
July 29 and July 31. Most early ADRs entered Git together on July 19, after implementation
had begun. ADR-0032 is summarized without a direct link because it names obsolete
infrastructure details.

## Core state, publication, and trust

| ADR | Original decision | Later fate |
|---|---|---|
| [0001](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0001-core-contracts.md) | Git was canonical state, SHA-256 CAS owned package bytes, refs expressed views/history, and publication used target sagas. | **Evolved.** Git/CAS/Route ownership retired; single ownership, pointer-last publication, independent target state, and evidence gates survived. |
| [0002](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0002-publication-routes-and-compatibility-gates.md) | Public routes, immutable generations, and client/provider compatibility had separate acceptance gates. | **Evolved.** Route machinery retired; protocol/client/provider evidence remains separate. |
| [0003](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0003-snapshot-generation-copy-and-retention.md) | Snapshots required verified generation copies and inventory-bound retention. | **Evolved.** CopyObject snapshot trees retired; retained generations now store metadata and reference sets without payload copies. |
| [0004](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0004-edge-token-verifier-deployment-contract.md) | Edge token verification and deployment had one versioned cross-provider contract. | **Retired.** Edge entitlement is no longer part of the SOW repository engine. |
| [0005](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0005-legacy-make-target-dispositions.md) | Every legacy Make target was mapped to SOW, retirement, or policy rejection. | **Migration history.** The mapping completed its cutover role and left the active product. |
| [0007](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0007-pro-oss-unified-repository.md) | Public and gated packages shared one canonical repository instead of a separate Pro bucket. | **Retired.** The commercial Edge topology left product scope; the more general single-owner lesson remains. |
| [0008](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0008-gc-reachability-and-confirmation.md) | GC followed complete reachability and required explicit confirmation for destructive work. | **Evolved.** Current GC checks references and exact identity. The old `--apply --confirm` interface retired; remote deletion also checks cache grace and provider capability. |
| [0009](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0009-forward-only-remote-generation-restore.md) | Once a remote generation became visible, recovery rolled forward rather than inventing rollback. | **Retained.** Commit intent remains the boundary between abandon/reconcile and forward-only recovery. |
| [0010](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0010-repository-signing-identity-and-rotation-boundary.md) | Metadata signing bound exact public/private identities and treated rotation as a repository-wide transition. | **Evolved.** Current signer evidence and trust-ring rules preserve exact identity without the V1 ref topology. |
| [0011](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0011-evidence-bound-remote-deletion.md) | Remote deletion required target ownership, inventory, checkpoint, grace, and conditional-delete evidence. | **Retained.** R2 remains report-only because it cannot satisfy the required atomic delete capability. |
| [0012](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0012-private-origin-deployment-contract.md) | Private origins, cache topology, and exact purge mapping were explicit deployment contracts. | **Retired.** CDN/private-origin deployment is outside current SOW. |
| [0013](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0013-persisted-publication-plans-are-untrusted.md) | A persisted plan was recovery input to revalidate, never authority to replay blindly. | **Retained.** Managed recovery still rebinds plans, files, target identity, and public evidence. |
| [0014](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0014-rpm-provenance-signature-evidence-boundary.md) | RPM provenance recorded exact packet evidence and distinguished ingestion policy from historical proof. | **Evolved.** Current package authentication and independent trust rings replace the V1 receipt encoding. |
| [0015](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0015-target-identity-and-published-ref-state.md) | Configuration named a target; published refs and checkpoints belonged to canonical state. | **Retained.** Target-neutral generations and target-prefix attempts/checkpoints remain separate owners. |
| [0016](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0016-frozen-vendor-sdk-boundary.md) | Cloud adapters used concrete, bounded SDK/API contracts instead of a generic provider abstraction. | **Evolved.** Concrete provider boundaries survived; V1 Edge/COS details retired. |
| [0017](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0017-rpm-package-keyring-and-cryptographic-verification.md) | Accepted RPM signatures had to close against a stable repository keyring and opened payload identity. | **Evolved.** v0.4 independent multi-ring verification strengthens the same trust boundary. |
| [0018](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0018-selected-set-local-materialization-transaction.md) | A selected package set staged, validated, committed, and recovered as one bounded local transaction. | **Evolved.** Managed operations use recovery journals. Plain stages metadata and replaces pointers last; an interrupted Plain build is rebuilt. |

## Legacy topology, compatibility, and migration

| ADR | Original decision | Later fate |
|---|---|---|
| [0019](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0019-frozen-el7-yum-metadata-compatibility.md) | EL7 metadata format and compressor behavior were frozen for legacy consumers. | **Migration history.** Current compatibility documentation, not this freeze, defines supported platforms. |
| [0020](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0020-legacy-physical-topology-and-route-ownership.md) | Every legacy physical path and selector group received an explicit owner. | **Migration history.** It prevented ambiguous cutover but is not a current repository model. |
| [0021](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0021-frozen-cross-el-yum-infra-compatibility-projection.md) | Cross-EL `yum/infra/{arch}` projections were reproduced with exact frozen evidence. | **Migration history.** The special projection left active product scope. |
| [0022](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0022-package-repository-history-continuity.md) | Package history could not be broken merely because physical ownership moved. | **Evolved.** Generations, retained references, and migration journals now preserve continuity without V1 routes. |
| [0023](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0023-canonical-git-object-integrity.md) | Canonical Git objects were rebound to exact bytes before admission and use. | **Evolved.** Git authority retired; descriptor/path/digest identity checks remain. |
| [0024](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0024-materialized-route-read-capabilities.md) | Materialized route receipts acted as narrow read/retirement capabilities. | **Evolved.** Route receipts retired; capability-bound inspection and deletion survived. |
| [0025](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0025-state-lock-process-instance-lease.md) | Locks bound an exact process instance and stable lock inode rather than elapsed time. | **Evolved.** Stable lock inodes and rejection of timeout-based lock stealing survived; the V1 process-instance lease mechanism did not. |
| [0026](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0026-offline-archive-projection-intent.md) | Offline archive creation used a durable intent and strict archive admission. | **Retired.** Offline archive projection left current SOW scope. |
| [0027](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0027-legacy-package-adoption-admission-and-canonicalization.md) | Legacy bytes entered canonical state only after exact path, package, and provenance admission. | **Migration history.** The adoption program completed; strict package admission remains in narrower form. |
| [0028](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0028-control-only-deb-inspection.md) | DEB inspection opened only the control archive needed for metadata and rejected ambiguous containers. | **Retained.** Narrow parsing and bounded input remain part of the APT package boundary. |
| [0029](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0029-client-support-floor-and-el8-freeze-version.md) | Client floors and the EL8 freeze were explicit owner policy, not inferred from code. | **Migration history.** Current platform policy lives in the compatibility reference and release notes. |
| [0030](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0030-audit-bound-legacy-yum-missing-body-prune.md) | Missing legacy YUM bodies could be repaired only from a reviewed blocker-set digest. | **Migration history.** The narrow negative-provenance exception did not become a general ignore flag. |
| [0031](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0031-legacy-pro-gated-activation-and-checksum-repair.md) | Gated legacy content required exact checksum repair and activation evidence. | **Retired.** Pro activation left product scope; fail-closed repair remained a general lesson. |

## Provider and Edge control plane

| ADR | Original decision | Later fate |
|---|---|---|
| 0032 | Only one exact owner-designated Cloudflare test tuple could bypass normal production rejection. | **Retired.** It was a narrow historical test exception, never a general deployment rule. |
| [0033](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0033-provider-scoped-readiness-registry.md) | Read-only provider readiness had its own registry and ownership evidence. | **Retired.** Provider bootstrap registry left current SOW. |
| [0034](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0034-cloudflare-nonproduction-worker-bootstrap.md) | Worker bootstrap used leases, two-phase recovery, exact resources, and reversible state. | **Retired.** Cloudflare deployment is no longer repository-engine responsibility. |
| [0035](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0035-cloudflare-provider-attestation-and-log-sink-lease.md) | Provider identity, runtime bindings, log sink, and lease ownership were attested before use. | **Retired.** The exact Edge control plane left product scope. |
| [0036](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0036-provider-delete-capability-and-checkpoint-fenced-fallback.md) | R2 lacked conditional DeleteObject, so an explicit `checkpoint-fenced` unconditional-delete fallback was allowed behind a deterministic capability probe and repeated identity/fence proofs. | **Evolved; fallback not inherited.** Capability probing and fail-closed defaults survived, but current SOW disables R2 remote deletion and keeps target GC report-only. |
| [0037](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0037-pre-upload-confidential-edge-denial-attestation.md) | Gated publication had to prove denial at the Edge before uploading confidential bytes. | **Retired.** Edge access control is now an external deployment responsibility. |
| [0038](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0038-yum-consumer-preflight-receipt.md) | YUM cutover required an expiring receipt bound to exact endpoints, generation, and trust bytes. | **Migration history.** It made a dangerous consumer cutover auditable and then retired. |
| [0039](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0039-caret-url-wire-canonicalization.md) | Caret had one canonical URL spelling across Go, Edge, logs, and origin routing. | **Evolved.** The route was retired; canonical encode-once path handling remains. |

## Bounded configuration and derived-state recovery

| ADR | Original decision | Later fate |
|---|---|---|
| [0040](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0040-bounded-configuration-topology.md) | Configuration cardinality and expanded topology were bounded before allocation or execution. | **Retained.** Current parsers and state wires keep explicit size/cardinality limits. |
| [0041](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0041-preserved-projection-orphan-quarantine.md) | Unknown final projection stages were preserved for audit rather than guessed away. | **Evolved.** Current recovery still preserves contradictory evidence and fails closed. |
| [0042](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0042-derived-state-replacement-outcome.md) | Derived-state replacement had explicit success, rollback, preserved, and blocked outcomes. | **Evolved.** Managed journals record operation phases; recovery stops when recorded state and files disagree. |
| [0043](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0043-derived-state-hostile-writer-admission.md) | File mutation checked descriptor identity and defined the limit against a hostile writer using the same OS user. | **Retained.** Path checks reject identity changes; OS permissions remain the boundary against other writers. |
| [0044](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0044-preserved-projection-audit-retirement.md) | Preserved audit copies could be retired only through an exact capability and confirmation token. | **Evolved.** The V1 command retired; exact capability-bound deletion remains a design rule. |
| [0045](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0045-generic-derived-state-residue-recovery.md) | Unjournaled residue had a bounded classifier and could never be silently adopted or deleted. | **Retained.** Current recovery distinguishes known state, safe residue, and contradictory evidence. |

## The pattern behind the ledger

The decisions that continued share a few rules:

- Give each fact one owner.
- Check exact identity before mutation.
- Prepare immutable content before committing pointers.
- Recover forward after commit intent.
- Check references and deletion conditions before removing data.
- Set input limits and define the product scope.
- Record compatibility against the client and provider tested.

Their current implementation is described in [Design Principles](/blog/design/principles/),
[System Model](/blog/design/model/), and [Publication & Recovery](/blog/design/publication/).

The [v0.1.0 ADR directory](https://github.com/pgsty/sow/tree/v0.1.0/docs/adr)
remains the immutable primary source. The next article summarizes the separate
[v0.1 evidence record](/blog/design/v01-evidence/).
