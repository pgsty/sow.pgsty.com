---
title: "sow status"
linkTitle: "status"
description: "Read Repository convergence, readiness, pending payload, recent Operation, and lock state without deep verification."
categories: [Command]
tags: [cli, managed, audit]
url: "/docs/command/status/"
weight: 1100
icon: fa-solid fa-gauge-high
---

`sow status` is the cheap Repository health query. It reads state but does not hash files, verify
signatures, recover Operations, build metadata, or take the write lock.

## Synopsis

```text
sow status [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Restrict status to these Dists; repeatable | all Dists |
| `--json` | Emit the `sow.cli/v1` envelope | false |

## Repository states

Every Repository tracks a Desired Revision in SQLite and the Built Generation represented by its
public `dists/` tree.

| State | Meaning | Public view |
|---|---|---|
| `clean` | Desired state matches Built state | current, complete Generation |
| `dirty` | Desired state is ahead, commonly after `--skip` or a config change | previous complete Generation |
| `recovering` | A non-terminal Operation must be recovered by the next write command | last completed protocol pointer |
| `error` | Automatic recovery cannot choose safely | last completed view; no overwrite attempted |

Dirty never means a half-written repository. Readers see either the old complete view or the new
complete view because protocol pointers are switched last.

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

`ready_to_copy=false` is a hard warning. `true` is only a cheap state result, not a byte-level proof;
run [`sow check`](/docs/command/check/) before delivery.

## Read-only contract

`status` never migrates or repairs state. If the Repository database cannot be read safely,
the command exits `5`; run the maintenance command named by the diagnostic before retrying.

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

- [`sow build`](/docs/command/build/) — converge a dirty Repository
- [`sow check`](/docs/command/check/) — use a full integrity/readiness gate
- [`sow log`](/docs/command/log/) — inspect the recent Operation reported here
- [Transactions & Recovery](/docs/feature/transactions/) — state transitions and pointer safety
