---
title: "sow gc"
linkTitle: "gc"
description: "Reclaim unused local packages or maintain a publication target."
categories: [Command]
tags: [cli, gc, retention, publish]
url: "/docs/command/gc/"
weight: 1700
icon: fa-solid fa-recycle
---

Run `sow gc` to reclaim local package files that are no longer needed. Run `sow gc TARGET` to maintain a configured publication target. Filesystem targets can delete eligible objects; R2 targets only report candidates.

## Synopsis

```text
sow gc          [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
sow gc TARGET   [-C|--workdir DIR]                  [-T|--timeout DUR | -N|--no-wait] [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository for local GC only | selection rules |
| `-T, --timeout DUR` | Maximum Repository-lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

`gc TARGET -r NAME` is a usage error because the target already binds a Repository. `--dist` is not
accepted in either mode.

## Local GC

Run local GC after the Repository has a completed, clean build. If it is dirty, run `sow build` first. GC deletes a pool package only when none of these records references it:

- current Desired or Built membership, or prior Built membership kept for older clients;
- explicit [`retain`](/docs/command/retain/) records;
- recovery and non-terminal Operation state;
- publication records;
- active maintenance work.

The operation is journaled. When payloads are removed, the Repository advances to a new Generation.
When nothing is eligible, it is an idempotent no-op.

```console
sow gc -r pgsql
local gc pgsql: generation=00000000000000000013 objects=4 bytes=1834200
```

## Target GC

Target GC waits for the configured cache grace period and checks which objects are still needed:

| Provider | Behavior |
|---|---|
| `filesystem` | After the grace period, conditionally delete eligible objects, verify that their public URLs are absent, and record the result |
| `r2` | Save a report of eligible objects; leave the objects in storage |

```console
sow gc prod
target gc pgsql/prod (filesystem): phase=done candidates=14 deleted=8 retained=6 pending=0
```

A no-op means no maintenance is due.

## Exit behavior

| Code | Trigger |
|---|---|
| `0` | GC completed or nothing was eligible |
| `1` | Filesystem, provider, network, or runtime failure |
| `2` | Usage, Workspace discovery, invalid `sow.yml`, or implicit Repository ambiguity |
| `4` | Repository write lock unavailable |
| `5` | Recovery, state, receipt, or manifest evidence is inconsistent |
| `6` | Explicit Repository/target is not configured or safe, or deletion is rejected by a safety precondition |

## See also

- [`sow retain`](/docs/command/retain/) — protect package files from local GC
- [`sow publish`](/docs/command/publish/) — create target checkpoints and receipts
- [Publication Model](/blog/design/publication/) — provider guarantees and cache grace
