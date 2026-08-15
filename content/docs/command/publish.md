---
title: "sow publish"
linkTitle: "publish"
description: "Publish the current verified Generation to a configured filesystem or R2 target."
url: "/docs/command/publish/"
weight: 1500
icon: fa-solid fa-cloud-arrow-up
---

`sow publish` delivers one Repository's current Built Generation to a named target from the
`targets:` map in `sow.yml`. The target binds its Repository and provider; the command does not accept
`--repo` or `--dist`.

## Synopsis

```text
sow publish TARGET [--abort] [-C|--workdir DIR] [-T|--timeout DUR | -N|--no-wait] [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `--abort` | Abandon a reconciled attempt that has not reached durable commit intent | false |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-T, --timeout DUR` | Maximum Repository-lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the `sow.cli/v1` envelope | false |

`TARGET` must name a configured `filesystem` or `r2` publication target.

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
sow publish prod
published pgsql generation=00000000000000000012 to prod (filesystem): phase=done objects=184
```

## Abort and recovery

`--abort` is valid only before durable commit intent. SOW reconciles objects already created, keeps
the evidence required for later safety decisions, and abandons the attempt without copying or
deleting more remote objects.

After commit intent, recovery is forward-only. Rerun `sow publish TARGET`; do not use `--abort`.

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
| `1` | Filesystem, provider, network, or verification runtime failure |
| `2` | Usage, Workspace discovery, or invalid `sow.yml` error |
| `4` | Repository write lock unavailable |
| `5` | Local or publication recovery evidence is inconsistent, or source is not deliverable |
| `6` | Target is missing/mismatched/unsafe, or another safety precondition rejects publish/abort |

## See also

- [`sow status`](/docs/command/status/) and [`sow check`](/docs/command/check/) — decide whether the Built Generation is the one you intend to deliver
- [`sow gc`](/docs/command/gc/) — conservative target maintenance
- [`sow.yml` targets](/docs/reference/config/#publication-targets) — provider configuration
- [Publication Model](/docs/design/publication/) — phases, receipts, recovery, and cache grace
