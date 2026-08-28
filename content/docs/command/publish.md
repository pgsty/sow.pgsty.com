---
title: "sow publish"
linkTitle: "publish"
description: "Publish the current verified Generation to a configured filesystem or R2 target."
categories: [Command]
tags: [cli, publish, object-storage, filesystem]
url: "/docs/command/publish/"
weight: 1500
icon: fa-solid fa-cloud-arrow-up
---

`sow publish` delivers one Repository's current Built Generation to a named target from the
`targets:` map in `sow.yml`. The target binds its Repository and provider; the command does not accept
`--repo` or `--dist`.

## Synopsis

```text
sow publish TARGET [--abort | --rebind] [-C|--workdir DIR] [-T|--timeout DUR | -N|--no-wait] [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `--abort` | Abandon a reconciled attempt that has not reached durable commit intent | false |
| `--rebind` | Confirm and record permitted target name/public endpoint/cache-TTL changes | false |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-T, --timeout DUR` | Maximum Repository-lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the `sow.cli/v1` envelope | false |

`TARGET` must name a configured `filesystem` or `r2` publication target. `--abort` and
`--rebind` are mutually exclusive.

## Publication protocol

Before delivery, SOW requires a completed Built Generation and verifies that the public tree is the
exact frozen Generation manifest. It then plans and applies objects in this order:

1. immutable payloads;
2. checksum-addressed metadata;
3. mutable protocol pointers;
4. verification and durable checkpoint.

The exact object set, receipts, phase, and commit intent are recorded so an interrupted publication
can be reconciled. Repeating a publication already at the current Generation is an idempotent no-op.

```console
sow publish local
published demo generation=00000000000000000005 to local (filesystem): phase=grace objects=14
sow publish local
publication demo generation=00000000000000000005 to local is already current (noop)
```

## Rebind mutable target settings

The first successful publish durably binds a Repository, storage namespace, and target identity.
Later configuration drift is rejected rather than silently adopted. When the diagnostic explicitly
points to `--rebind`, review the edit and confirm it with:

```bash
sow publish prod --rebind
```

If the map key itself was renamed, invoke the new target name. Rebind preserves active attempt and
checkpoint identities and appends an immutable operator-confirmed binding revision.

| May change | Immutable; configure a new target |
|---|---|
| target name | Repository identity |
| `public_endpoint` | provider, storage `endpoint`, or region |
| `max_cache_ttl` | bucket or `prefix` |

Rebind takes the same Workspace and Repository locks as publication and rechecks the immutable
fields inside the database transaction. It may resume an active commit-intent attempt forward.
It refuses a TTL change while target maintenance is pending, and refuses a filesystem
`public_endpoint` change during conditional-delete maintenance. A first bind must use ordinary
`publish`, not `--rebind`.

## Abort and recovery

`--abort` is valid only before durable commit intent. SOW reconciles objects already created, keeps
the evidence required for later safety decisions, and abandons the attempt without copying or
deleting more remote objects.

After commit intent, recovery is forward-only. Rerun `sow publish TARGET`; do not use `--abort`.

## Public visibility checks

Provider storage success is not enough: publication verifies the canonical `public_endpoint` before
recording its checkpoint. HTTP(S) targets use ordinary GET as the final authority. A no-cache probe
may accelerate revalidation, but only a later ordinary GET can pass. Stale content and missing
objects are retried up to `max_cache_ttl`; 408, 425, 429, and 5xx failures get a short bounded retry
window. Header wait and body idle progress have separate deadlines, and an oversized body fails
closed.

Filesystem targets may use `file://` or HTTP(S). Their conditional-deletion absence check requires
the exact file identity for `file://`, or canonical 404/410 visibility for HTTP(S). R2 requires an
HTTP(S) public endpoint; R2 target GC remains report-only and does not perform remote deletion.

## Safety boundaries

- SOW publishes only configured targets; there is no arbitrary destination argument.
- Unbuilt Desired changes are never included. A dirty Repository can therefore publish its previous
  complete Built Generation; run `build` first when the target must reflect current Desired state.
- Layout transitions and contradictory recovery evidence block publication. Decidable unfinished
  Dist work is recovered before the source Generation is selected.
- Object order protects package-manager pointers from referencing absent content.
- Publication does not make an external web server, bucket policy, DNS route, or cache correct; those
  remain deployment concerns.

## Exit behavior

| Code | Trigger |
|---|---|
| `0` | Publication completed or target was already current |
| `1` | Filesystem, provider, network, verification, or binding conflict (including required rebind) |
| `2` | Usage, Workspace discovery, or invalid `sow.yml` error |
| `4` | Repository write lock unavailable |
| `5` | Local or publication recovery evidence is inconsistent, or source is not deliverable |
| `6` | Target is missing/unsafe, or another safety precondition rejects publish/abort/rebind |

## See also

- [`sow status`](/docs/command/status/) and [`sow check`](/docs/command/check/) — decide whether the Built Generation is the one you intend to deliver
- [`sow gc`](/docs/command/gc/) — conservative target maintenance
- [`sow.yml` targets](/docs/reference/config/#publication-targets) — provider configuration
- [Publication Model](/blog/design/publication/) — phases, receipts, recovery, and cache grace
