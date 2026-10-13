---
title: "sow retain"
linkTitle: "retain"
description: "Keep or release the package files needed by a Generation."
categories: [Command]
tags: [cli, retention, generation]
url: "/docs/command/retain/"
weight: 1600
icon: fa-solid fa-box-archive
---

`sow retain` protects the package files needed by a selected Generation from local GC. Add the current Built Generation before a later build replaces it. Retention preserves package files and a frozen manifest; it does not restore or publish an older repository view.

## Synopsis

```text
sow retain add GENERATION [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
sow retain ls             [-C|--workdir DIR] [-r|--repo NAME] [--json]
sow retain rm GENERATION  [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

`GENERATION` must be a decimal integer greater than zero.

## retain add

Pass the current Built Generation number. SOW verifies the Generation, saves its manifest, and records that GC must keep its package files. Add this record before building a newer Generation.

```console
sow retain add 12 -r pgsql
retained generation 00000000000000000012: /srv/sow/.sow/pgsql/retained/00000000000000000012
```

Adding the same Generation again changes nothing if its retained record still passes verification.

## retain ls

Lists retained records for the Repository.

```console
sow retain ls -r pgsql
GENERATION	RECORD_IDENTITY	PATH
00000000000000000012	678beeae...	/srv/sow/.sow/pgsql/retained/00000000000000000012
```

An empty list is a successful result.

## retain rm

Removes the retention record for a Generation:

```console
sow retain rm 12 -r pgsql
removed retained generation 00000000000000000012
```

It does not delete package bytes. Removing a Generation that is not retained is an idempotent no-op.
A later local [`sow gc`](/docs/command/gc/) can reclaim these packages when no other state or operation needs them.

If a retained record is damaged, `retain rm`, `retain ls`, local `gc`, and `check` report the error. The `retained` layer in `check` identifies the affected Generation. To discard that damaged record:

1. Stop Workspace writers.
2. Move `.sow/<repo>/retained/<GENERATION>` to a backup location outside the Workspace.
3. Run `sow check` again.

Moving the record also removes its protection against GC.

## Options

| Flag | Commands | Meaning |
|---|---|---|
| `-C, --workdir DIR` | all | Workspace discovery start directory |
| `-r, --repo NAME` | all | Select a Repository |
| `-T, --timeout DUR` | `add`, `rm` | Maximum write-lock wait |
| `-N, --no-wait` | `add`, `rm` | Fail immediately when locked |
| `--json` | all | Output JSON |

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

- [`sow gc`](/docs/command/gc/) — reclaim packages that no retained state needs
- [`sow changes`](/docs/command/changes/) — inspect a Built Generation delta
- [Repository Layout](/docs/reference/layout/) — private retained-record location
