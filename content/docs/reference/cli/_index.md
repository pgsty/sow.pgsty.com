---
title: "CLI Commands"
linkTitle: "CLI Commands"
description: "Complete reference for every sow command, plus the global conventions they all share."
url: "/docs/reference/cli/"
weight: 100
icon: fa-solid fa-terminal
---

Every `sow` subcommand is documented here: syntax, flags, behavior, real transcripts and exit codes.
This page covers what they all have in common — how a Workspace is discovered, how a Repository and
Dist are selected, how locking works, and what `--json` emits — so the individual pages don't repeat
it.

## Command index

`sow` has exactly two isolated execution paths. `sow create` is Plain mode: no Workspace, no config
file, no database. Everything else is Managed mode and runs inside a Workspace.

| Command | Mode | Purpose |
|---|---|---|
| [`sow create [DIR]`](/docs/reference/cli/create/) | Plain | Generate a flat RPM/DEB repository in place |
| [`sow init [DIR]`](/docs/reference/cli/init/) | Managed | Initialize a Workspace and converge declared Repositories/Dists |
| [`sow config check`](/docs/reference/cli/config/) | Managed | Validate `sow.yml` read-only |
| [`sow config show`](/docs/reference/cli/config/) | Managed | Print the effective configuration |
| [`sow repo ls\|new\|show\|migrate\|rm`](/docs/reference/cli/repo/) | Managed | Manage Repositories and migrate the pre-release C2 layout |
| [`sow dist ls\|new\|show\|rm`](/docs/reference/cli/dist/) | Managed | Manage Dists |
| [`sow add PATH...`](/docs/reference/cli/add/) | Managed | Add packages to Desired Membership |
| [`sow rm PACKAGE...`](/docs/reference/cli/rm/) | Managed | Remove Desired Membership |
| [`sow ls` / `show` / `where`](/docs/reference/cli/query/) | Managed | Query membership and locate packages |
| [`sow build` / `status` / `check` / `changes`](/docs/reference/cli/build/) | Managed | Converge, inspect, verify and diff |
| [`sow publish TARGET`](/docs/reference/cli/publication/) | Managed | Publish a verified Generation to a configured target |
| [`sow retain add\|ls\|rm`](/docs/reference/cli/publication/) | Managed | Manage explicit retained-Generation roots |
| [`sow gc [TARGET]`](/docs/reference/cli/publication/) | Managed | Collect local payloads or maintain one publication target |
| [`sow export rpm-leaf`](/docs/reference/cli/publication/) | Managed | Build a standalone RPM compatibility leaf |
| [`sow log` / `log export` / `log prune`](/docs/reference/cli/log/) | Managed | Operation audit ledger |

## Global syntax

```bash
sow [OPTIONS] COMMAND [ARGS]
```

Running `sow` with no arguments prints the command list and exits `0`. `sow help COMMAND` and
`sow help COMMAND SUBCOMMAND` print per-command usage. `sow version` and `sow --version` print the
binary identity:

```console
sow version
sow 0.2.0 darwin/arm64 go1.26.5
```

There is no global `--format`, `--yes`, `--dry-run`, `-q/-v` or `--config`. An unknown flag is a
usage error, never silently ignored.

## Workspace discovery

Managed commands look for the nearest ancestor directory containing `sow.yml`, in this order:

1. `-C/--workdir DIR` — start the upward search at `DIR`.
2. Otherwise start at the current working directory.
3. If neither found one, start at the directory named by the `SOW_DIR` environment variable.
4. Still nothing: fail with exit code `2`.

The search stops at the first `sow.yml` it finds and never crosses past that Workspace.

`--workdir` only moves the *discovery start directory*. It does not `chdir`, so relative `PATH`,
`DIR` and `FILE` arguments still resolve against your real working directory.

```console
sow status
workspace discovery error: managed: workspace discovery or configuration error: workspace not found (searched cwd="/home/vonng"); run sow init or set --workdir/SOW_DIR
```

`sow create` does not participate in discovery at all.

## Repository selection

Commands that need one Repository resolve it in this order:

1. Explicit `-r/--repo NAME`.
2. The starting directory is inside `<workspace>/<repo>/`.
3. The Workspace contains exactly one Repository.
4. Otherwise fail with exit code `2` and list the candidates.

```console
sow status
workspace discovery error: managed: workspace discovery or configuration error: workspace has multiple repositories (infra, pgsql); select one with --repo
```

`repo new` and `repo rm` take the name as a positional argument and do not accept `-r`.
`sow where` searches every Repository by default and uses `-r` only to narrow.

## Dist selection

Commands that need one or more Dists resolve them in this order:

1. One or more explicit `-d/--dist NAME` (the flag is repeatable).
2. The starting directory is inside `<workspace>/<repo>/dists/<dist>/`.
3. The selected Repository has exactly one Dist.
4. Otherwise fail with exit code `2` and list the candidates.

`build`, `check` and `status` default to *all* Dists of the selected Repository when `-d` is absent.
`add`, `rm` and `ls` require an unambiguous Dist set:

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

`sow changes` operates on the whole Repository Generation and rejects `-d` outright.

## Locking

Every command that takes a write lock accepts `-T/--timeout DUR` and `-N/--no-wait`. The lock scope
is the Repository — except `init`, `repo new` and `repo rm`, which lock the Workspace.

| Flag | Default | Meaning |
|---|---|---|
| `-T, --timeout DUR` | `0` | Maximum wait for the lock; `0` waits indefinitely. Go duration syntax (`500ms`, `30s`, `5m`, `1h`). |
| `-N, --no-wait` | false | Fail immediately if the lock is held. |

The two are mutually exclusive when `--timeout` is non-zero. Failing to acquire the lock exits `4`:

```console
sow build -N
lock unavailable: managed: lock unavailable
```

Read-only commands never take the write lock. `sow status` still reports lock state, and marks the
Repository as not ready to copy while somebody else is writing:

```console
sow status
repository=pigsty status=clean ready_to_copy=false revision=6 generation=6 dirty_dists= pending=0/0 locked=true
```

## Parallelism

`-j/--jobs N` appears only on commands that actually parse packages, hash bytes, render indexes or
verify: `create`, `repo migrate`, `add`, `rm`, `build`, `check`. It defaults to the logical CPU
count and must be at least `1`.

```console
sow check -j 0
usage error: --jobs must be an integer greater than or equal to 1
```

Parallelism never changes output ordering, selection results, version comparison or Changeset
content.

## JSON output

`--json` emits one versioned envelope on stdout. Human-readable diagnostics still go to stderr.

```json
{
  "schema": "sow.cli/v1",
  "command": "add",
  "ok": true,
  "repository": "demo",
  "operation": "1430722512865805553",
  "result": {},
  "errors": []
}
```

`ok` is false whenever the exit code is non-zero, but `result` is still fully populated — a partial
batch lists every committed item alongside every failure. Each `errors[]` entry carries `code`,
`class` and `message`:

```json
{"code": 3, "class": "partial", "message": "managed: batch partially succeeded"}
```

Per-command result schemas are in [JSON Output](/docs/reference/json/).

Three commands print structured JSON on stdout even *without* `--json`, because their result has no
compact tabular form: `sow build`, `sow rm` and `sow show`. Adding `--json` wraps them in the
standard envelope.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success or idempotent no-op |
| `1` | Runtime I/O, parser, renderer or signing error |
| `2` | Usage, Workspace discovery or configuration error |
| `3` | Partial success — at least one item committed, at least one failed |
| `4` | Write lock unavailable (`--no-wait`, or timeout expired) |
| `5` | Integrity/recovery error, or `check` ruling the tree not deliverable |
| `6` | Expected rejection — conflict, protected, no match, incompatible architecture |

Full trigger tables with transcripts are in [Exit Codes](/docs/reference/exit-codes/).
