---
title: "sow retain"
linkTitle: "retain"
description: "Add, list, and remove explicit retained-Generation roots for local garbage collection."
categories: [Command]
tags: [cli, retention, generation]
url: "/docs/command/retain/"
weight: 1600
icon: fa-solid fa-box-archive
---

`sow retain` manages explicit local Generation roots. `retain add` can freeze only the current Built
Generation; after later builds make it historical, its required package payloads remain protected.

## Synopsis

```text
sow retain add GENERATION [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
sow retain ls             [-C|--workdir DIR] [-r|--repo NAME] [--json]
sow retain rm GENERATION  [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

`GENERATION` must be a decimal integer greater than zero.

## retain add

Requires `GENERATION` to equal the current Built Generation, verifies it, freezes its manifest under
private Workspace state, and adds an explicit GC root. Older Generations cannot be recreated after
the fact with `retain add`.

```console
sow retain add 12 -r pgsql
retained generation 00000000000000000012: /srv/sow/.sow/pgsql/retained/00000000000000000012
```

The retained record protects payloads; it does not switch the current view or publish anything.
Adding an already retained Generation is idempotent only when the verified record agrees with current
evidence.

## retain ls

Lists explicit retained records. It is read-only and therefore accepts neither lock options nor
`--dist`.

```console
sow retain ls -r pgsql
GENERATION	RECORD_IDENTITY	PATH
00000000000000000012	678beeae...	/srv/sow/.sow/pgsql/retained/00000000000000000012
```

An empty list is a successful result.

## retain rm

Removes only the explicit retained root:

```console
sow retain rm 12 -r pgsql
removed retained generation 00000000000000000012
```

It does not delete package bytes. Removing a Generation that is not retained is an idempotent no-op.
A later local [`sow gc`](/docs/command/gc/) may reclaim payloads only if no other safety root reaches
them.

## Options

| Flag | Commands | Meaning |
|---|---|---|
| `-C, --workdir DIR` | all | Workspace discovery start directory |
| `-r, --repo NAME` | all | Select a Repository |
| `-T, --timeout DUR` | `add`, `rm` | Maximum write-lock wait |
| `-N, --no-wait` | `add`, `rm` | Fail immediately when locked |
| `--json` | all | Emit the `sow.cli/v1` envelope |

## Exit behavior

| Code | Trigger |
|---|---|
| `0` | Requested operation completed, including an empty list |
| `1` | Filesystem or runtime I/O failure |
| `2` | Invalid Generation syntax, discovery error, or implicit Repository selection is ambiguous |
| `4` | Write lock unavailable for `add` or `rm` |
| `5` | Generation manifest or Repository state is inconsistent |
| `6` | Explicit Repository is not configured, `retain add` does not name the current Built Generation, or another safety rule rejects the request |

## See also

- [`sow gc`](/docs/command/gc/) — consumes retention roots
- [`sow changes`](/docs/command/changes/) — inspect a Built Generation delta
- [Repository Layout](/docs/reference/layout/) — private retained-record location
