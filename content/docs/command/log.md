---
title: "sow log"
linkTitle: "log"
description: "Read the Operation audit ledger, export it as JSONL, and prune eligible terminal records."
url: "/docs/command/log/"
aliases: ["/docs/reference/cli/log/"]
weight: 1900
icon: fa-solid fa-clipboard-list
---

Every write command inside a Repository commits an application-level Operation to that Repository's
SQLite database *before* it produces any external file side effect. That record is what makes crash
recovery possible — and once the Operation reaches a terminal state, the same record is your audit
trail. `sow log` reads it.

## Synopsis

```text
sow log [OPERATION] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME] [--json]
sow log export [FILE] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]
sow log prune BEFORE [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

## Operation lifecycle

Understanding the `state` field is most of understanding the log:

```text
planned → staged → applied → built → done
                        └────────→ done_dirty
   any nonterminal → recovering → built / rolled_back
   pre-apply error  → failed
```

| State | Meaning |
|---|---|
| `planned` | Command, arguments, targets and intended actions are durably recorded |
| `staged` | New packages/metadata written to temporary locations and verified |
| `applied` | Desired state and required private pending payloads committed |
| `built` | The complete static Generation has been switched in |
| `done` | Terminal — a normal successful command |
| `done_dirty` | Terminal — `--skip` was given, so the public tree deliberately stayed behind |
| `failed` | Terminal — the operation failed before `applied`, nothing was committed |
| `rolled_back` | Terminal — a post-`applied` failure the process could safely undo |
| `recovering` | Non-terminal; the next write command must complete or roll it back |

Workspace lifecycle commands (`init`, `repo new`, `repo rm`) use the Workspace file journal instead
and do not appear in a Repository's SQLite log. `dist new`/`dist rm` do appear — the Repository
database already exists at that point.

## sow log

With no argument, prints the 50 most recent Operations, newest first.

```console
sow log -r pigsty
```

Output excerpt, one Operation object from the `operations` array:

```json
{
  "id": "4262183287563704350",
  "kind": "build",
  "state": "done",
  "payload_json": "{\"version\":2,\"repository\":\"pigsty\",\"kind\":\"build\",\"config_sha256\":\"37eb6dcf...\",\"skip\":false,\"dists\":[\"el9\"],\"build_dists\":[\"el9\"],\"manifest_sha256\":\"678beeae...\"}",
  "result_json": "{\"dists\":1,\"dropped_pending\":[]}",
  "created_at": "2026-08-04T04:07:40.334787Z",
  "updated_at": "2026-08-04T04:07:40.907125Z"
}
```

`payload_json` records the intent — including `config_sha256`, the digest of the configuration in
force, and `manifest_sha256` for the resulting Generation. `result_json` records the outcome. A
failed Operation additionally carries `error_class` and `error_message`:

```json
{
  "id": "5995346754219751025",
  "kind": "add",
  "state": "failed",
  "result_json": "{\"accepted\":0,\"failed\":1}",
  "error_class": "rejected",
  "error_message": "no input package was accepted"
}
```

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Show only Operations touching this Dist | all |
| `--json` | Emit the versioned JSON envelope | false |

### One Operation in detail

Pass an Operation ID to get its full state transitions, timing, packages, memberships and file
actions.

```console
sow log 4262183287563704350 -r pigsty
```

Output excerpt:

```json
{
  "duration_ms": 572,
  "events": [
    {"sequence": 0, "state": "planned",  "occurred_at": "2026-08-04T04:07:40.334787Z"},
    {"sequence": 1, "state": "staged",   "occurred_at": "2026-08-04T04:07:40.380963Z"},
    {"sequence": 2, "state": "applied",  "occurred_at": "2026-08-04T04:07:40.386186Z"},
    {"sequence": 3, "state": "built",    "occurred_at": "2026-08-04T04:07:40.904730Z"},
    {"sequence": 4, "state": "done",     "occurred_at": "2026-08-04T04:07:40.907125Z"}
  ],
  "packages": [],
  "memberships": [],
  "files": [
    {"sequence": 0, "action": "update", "phase": "pointer", "path": "dists/el9/aarch64/repodata/repomd.xml", "size": 1511, "sha256": "ef071821e06c9e86ab4f6d2a56906d82bb66df251e79d1086cfd44dc8395513e"},
    {"sequence": 1, "action": "update", "phase": "pointer", "path": "dists/el9/x86_64/repodata/repomd.xml",  "size": 1514, "sha256": "a31e90ec39169f0373b108458908333c96c5f600f3c63a50c44257856f0d2d55"}
  ]
}
```

The `files` array uses the same `phase` vocabulary as
[`sow changes`](/docs/command/changes/): `payload`, `metadata`, `pointer`, `delete`.

Build Operations also contain progress events. They keep the current state and put a
versioned object in `detail_json`:

```json
{
  "state": "applied",
  "detail_json": "{\"version\":1,\"kind\":\"build_progress\",\"phase\":\"rendering\",\"completed\":1,\"total\":2,\"jobs\":8}"
}
```

The phases are `rendering`, `promoting_payload`, `publishing_dists`,
`normalizing_public_tree`, and `finalizing`. A progress row is durable audit data but does
not advance the recovery state machine or force its own SQLite checkpoint.

### Filtering by Dist

`-d` restricts the listing to Operations that touched that Dist — useful when one Repository serves
several distributions:

```bash
sow log -d trixie -r pigsty
```

## sow log export

Writes terminal Operations as JSONL — one complete Operation detail record per line — for archival or
ingestion into a log pipeline.

```console
sow log export /srv/audit/pigsty-ops.jsonl -r pigsty
exported 12 operations to /srv/audit/pigsty-ops.jsonl
```

Omit `FILE`, or pass `-`, to write to stdout:

```bash
sow log export - -r pigsty | gzip > pigsty-ops-$(date +%F).jsonl.gz
```

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Export only Operations touching this Dist | all |

`export` has no `--json`; JSONL *is* its output format.

### It refuses to clobber

An existing target is a rejection, never an overwrite — an audit export must not silently destroy a
previous one:

```console
sow log export /srv/audit/pigsty-ops.jsonl -r pigsty
operation rejected: export target already exists: /srv/audit/pigsty-ops.jsonl
```

`export` also refuses a target whose parent is not a real directory — a symlink, or a directory that
does not exist:

```console
sow log export /tmp/pigsty-ops.jsonl -r pigsty
log export parent is not a real directory
```

On macOS `/tmp` is a symlink to `/private/tmp`, so that refusal fires there. Write to an explicit
real path instead.

## sow log prune

Deletes eligible terminal audit records older than `BEFORE` and safely compacts the database.

```console
sow log prune 2027-01-01 -r pigsty
{"operation":"8150803833883584722","repository":"pigsty","before":"2027-01-01T00:00:00+08:00","pruned":1}
```

The absolute timestamp is echoed back so the local-timezone interpretation is never ambiguous.

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the versioned JSON envelope | false |

`prune` operates at Repository level and does not accept `-d` — pruning half an Operation would
produce a meaningless record.

### BEFORE syntax

`BEFORE` is an ISO-8601 date `YYYY-MM-DD`, interpreted as local midnight, or an RFC 3339 timestamp
with a timezone.

```console
sow log prune yesterday -r pigsty
usage error: BEFORE must be YYYY-MM-DD or an RFC 3339 timestamp with timezone
```

### What prune never deletes

`prune` is conservative by construction. It never removes:

- a non-terminal Operation;
- a record still required for recovery;
- current Package or Membership state;
- a Built Generation or its Changeset.

The `pruned` counter tells you exactly how many records were eligible, which is normally fewer than
the number of Operations older than the cutoff. Log and Changeset live in the same SQLite database,
but they follow different retention rules.

## Examples

Investigate the most recent write:

```bash
sow log -r pgsql --json | jq -r '.result.operations[0] | "\(.id)\t\(.kind)\t\(.state)"'
```

List everything that failed:

```bash
sow log -r pgsql --json | jq -r '.result.operations[] | select(.state=="failed") | "\(.id)\t\(.error_class)\t\(.error_message)"'
```

Archive and shrink, monthly:

```bash
sow log export /srv/audit/pgsql-$(date +%Y%m).jsonl -r pgsql
sow log prune 2026-05-01 -r pgsql
```

Which Operation last touched a Dist:

```bash
sow log -d el9 -r pgsql --json | jq -r '.result.operations[0].id'
```

## Exit codes

| Command | Code | Trigger |
|---|---|---|
| `log` | `0` | Records printed, including an empty ledger |
| `log` | `2` | Usage error (including a non-numeric Operation ID), Workspace not found, or ambiguous selection |
| `log` | `5` | State database unreadable |
| `log` | `6` | The given Operation ID does not exist |
| `log export` | `0` | Export written |
| `log export` | `1` | I/O failure writing the target, or the parent is not a real directory |
| `log export` | `2` | Usage error or ambiguous selection |
| `log export` | `6` | Target already exists |
| `log prune` | `0` | Prune completed, including pruning nothing |
| `log prune` | `2` | Malformed `BEFORE`, `-d` given, or ambiguous selection |
| `log prune` | `4` | Repository lock held and `--no-wait` given or `--timeout` expired |
| `log prune` | `5` | Integrity or recovery error |

## See also

- [Observability & Audit](/docs/feature/audit/) — how `log` fits with `status`, `check` and `changes`
- [Transactions & Recovery](/docs/feature/transactions/) — the journal that the log records
- [sow changes](/docs/command/changes/) — the physical counterpart to a semantic Operation
- [JSON Output](/docs/reference/json/) — the full log result schema
