---
title: "sow status"
linkTitle: "status"
description: "Read repository state, pending data, and lock activity."
categories: [Command]
tags: [cli, managed, audit]
url: "/docs/command/status/"
weight: 1100
icon: fa-solid fa-gauge-high
---

`sow status` reports whether a Repository needs a build, how much pending data it holds, and whether a writer is active. It reads stored state without hashing package files. Use [`sow check`](/docs/command/check/) to verify file contents.

## Synopsis

```text
sow status [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Restrict status to these Dists; repeatable | all Dists |
| `--json` | Output JSON | false |

## Repository states

SOW records the intended package set as Desired state and the last build as a Built Generation.

| State | Meaning | Next step |
|---|---|---|
| `clean` | Desired state matches Built state | Run `check` before copying the Repository |
| `dirty` | Desired and Built state differ, commonly after `--skip` or a config change | Run `build` to apply the changes |
| `recovering` | A local Repository operation was interrupted | Run `build` to recover it |
| `error` | State, files, or recovery records need attention | Read `dirty_reasons`, then run `check` and `log` |

## Output

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

The human line reports:

- Repository state and `ready_to_copy`;
- Desired Revision and current Built Generation;
- affected Dists;
- pending object count and bytes;
- write-lock state.

The JSON result additionally includes `dirty_reasons` and the most recent Operation:

```json
{
  "repository": "demo",
  "status": "dirty",
  "ready_to_copy": false,
  "desired_revision": 5,
  "built_generation": "00000000000000000004",
  "dirty_dists": ["el9"],
  "dirty_reasons": ["dist el9 Desired and Built membership sets differ"],
  "pending": {"count": 1, "bytes": 19776},
  "repository_locked": false
}
```

`ready_to_copy` summarizes the recorded state. When it is false, `dirty_reasons` explains why. [`sow check`](/docs/command/check/) performs the file-content validation.

Pending repository maintenance also affects Dist status, even when Desired and Built memberships match.
Inspect `dirty_reasons` and the pending operation, then follow the recovery command it identifies.
The same condition appears in `dist ls` and `dist show`.

## Reading stored state {#read-only-contract}

`status` reports stored state without migrating or repairing it. It can read database schemas v6, v12, and the current v13. Unsupported or unreadable state returns `5`. Before writing to an older Workspace, back it up and run [`sow repo migrate`](/docs/command/repo/#sow-repo-migrate) for each Repository.

## Exit behavior

`status` returns `0` for every readable state, including `dirty`, `recovering`, and `error`. Scripts
should inspect the structured state rather than treating those conditions as command failures.

| Code | Trigger |
|---|---|
| `0` | Repository state is readable |
| `1` | Runtime I/O failure |
| `2` | Usage error, Workspace not found, or implicit Repository selection is ambiguous |
| `5` | State database unreadable or inconsistent |
| `6` | Explicit Repository or Dist is not configured |

## See also

- [`sow build`](/docs/command/build/) — build pending Repository changes
- [`sow check`](/docs/command/check/) — validate the repository before delivery
- [`sow log`](/docs/command/log/) — inspect the recent Operation reported here
- [Transactions & Recovery](/docs/feature/transactions/) — state transitions and pointer safety
