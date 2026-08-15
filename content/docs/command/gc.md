---
title: "sow gc"
linkTitle: "gc"
description: "Collect unreachable local payloads or perform conservative maintenance for one publication target."
url: "/docs/command/gc/"
weight: 1700
icon: fa-solid fa-recycle
---

`sow gc` has two deliberately separate modes. With no positional target it collects unreachable
local pool payloads. With `TARGET` it maintains one configured publication target.

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
| `--json` | Emit the `sow.cli/v1` envelope | false |

`gc TARGET -r NAME` is a usage error because the target already binds a Repository. `--dist` is not
accepted in either mode.

## Local GC

Local GC deletes only pool payloads unreachable from every safety root:

- the current Built Generation;
- explicit [`retain`](/docs/command/retain/) records;
- recovery and non-terminal Operation state;
- publication attempts and evidence;
- active maintenance work.

The operation is journaled. When payloads are removed, the Repository advances to a new Generation.
When nothing is eligible, it is an idempotent no-op.

```console
sow gc -r pgsql
local gc pgsql: generation=00000000000000000013 objects=4 bytes=1834200
```

## Target GC

Target maintenance is provider-specific and uses publication checkpoints, absence evidence, and
configured cache grace:

| Provider | Behavior |
|---|---|
| `filesystem` | Conditionally delete eligible objects only after grace and recorded storage/public absence checks |
| `r2` | Persist an exact report-only retained-candidate set; never issue object deletion |

```console
sow gc prod
target gc pgsql/prod (filesystem): phase=done candidates=14 deleted=8 retained=6 pending=0
```

A no-op means no maintenance is due, not that the target was exhaustively revalidated.

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

- [`sow retain`](/docs/command/retain/) — create and remove explicit local roots
- [`sow publish`](/docs/command/publish/) — create target checkpoints and receipts
- [Publication Model](/docs/design/publication/) — provider guarantees and cache grace
