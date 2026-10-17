---
title: "sow log"
linkTitle: "log"
description: "Inspect, export, and prune operation records."
categories: [Command]
tags: [cli, audit]
url: "/docs/command/log/"
aliases: ["/docs/reference/cli/log/"]
weight: 1900
icon: fa-solid fa-clipboard-list
---

`sow log` lists Repository operations and shows the details of one operation. Use `log export` to archive completed records as JSONL. Use `log prune` to remove eligible old records from the database.

## Synopsis

```text
sow log [OPERATION] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME] [--json]
sow log export [FILE] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]
sow log prune BEFORE [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

## sow log

With no argument, prints the 50 most recent Operations, newest first.

```console
sow log -r pigsty --json
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
| `--json` | Output JSON | false |

### One Operation in detail

Pass an Operation ID for a summary. Add `--json` to read the full transitions, timing, package, membership, and file records under `result.detail`.

```console
sow log 4262183287563704350 -r pigsty --json
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

The phases are `rendering`, `promoting_payload`, `publishing_dists`, `normalizing_public_tree`, and `finalizing`. Use them to follow long builds.

New metadata-building operations also record `publication_time` in `payload_json`.
It is a UTC timestamp with whole-second precision. Recovery reuses it for metadata and signatures.
Older journals and layout migrations can omit this field.

### Filtering by Dist

`-d` restricts the listing to Operations that touched that Dist — useful when one Repository serves
several distributions:

```bash
sow log -d trixie -r pigsty
```

## Operation lifecycle

The `state` field shows how far an operation has progressed:

```text
planned → staged → applied → built → done
                        └────────→ done_dirty
   any nonterminal → recovering → built / done / done_dirty / rolled_back / failed
   pre-apply error  → failed
```

| State | Meaning |
|---|---|
| `planned` | Command, arguments, targets and intended actions are durably recorded |
| `staged` | New packages/metadata written to temporary locations and verified |
| `applied` | Desired state and required private pending payloads committed |
| `built` | The complete static Generation has been switched in |
| `done` | Terminal — a normal successful command |
| `done_dirty` | Operation ended with changes that still need a build, usually after `--skip` |
| `failed` | Terminal — the operation failed before `applied`, nothing was committed |
| `rolled_back` | Terminal — recovery abandoned the operation before it changed Desired state, for example a `planned` operation left by an interrupted command |
| `recovering` | Non-terminal; the next write command must complete or roll it back |

The Repository log includes `dist new` and `dist rm`. Workspace operations (`init`, `repo new`, `repo rm`) use separate recovery records and do not appear here.

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

### Output path {#it-refuses-to-clobber}

Choose a new filename in an existing directory. `log export` returns `6` if the file already exists. Its immediate parent must be a real directory, not a symbolic link. On macOS, use `/private/tmp/file.jsonl` instead of `/tmp/file.jsonl`.

## sow log prune

Deletes eligible completed operation records older than `BEFORE` and reclaims database space. If another reader is using the database, record deletion can finish while space reclamation waits. The result then reports `compaction_deferred: true`. Close the reader and rerun `prune` to reclaim the space.

```console
sow log prune 2027-01-01 -r pigsty
pruned log repository=pigsty operation=8150803833883584722 before=2026-12-31T16:00:00.000000000Z operations=1
```

The output shows the cutoff in UTC (this example uses a workstation at UTC+8). When a reader defers space reclamation, a second line reads
`log deletion committed; space reclamation deferred while the database is busy`; with `--json`
the journal ID and `compaction_deferred` appear in `result`.

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

`prune` applies to the whole Repository and does not accept `-d`.

### BEFORE syntax

`BEFORE` is an ISO-8601 date `YYYY-MM-DD`, interpreted as local midnight, or an RFC 3339 timestamp
with a timezone.

```console
sow log prune yesterday -r pigsty
usage error: BEFORE must be YYYY-MM-DD or an RFC 3339 timestamp with timezone
```

### Records kept by prune {#what-prune-never-deletes}

`prune` keeps:

- a non-terminal Operation;
- a record still required for recovery;
- current Package or Membership state;
- a Built Generation or its Changeset.

The `pruned` counter reports the number of deleted operation records.

## Examples

Investigate the most recent write:

```bash
sow log -r pgsql --json | jq -r '.result.operations[0] | "\(.id)\t\(.kind)\t\(.state)"'
```

Find failed operations among the 50 most recent records:

```bash
sow log -r pgsql --json | jq -r '.result.operations[] | select(.state=="failed") | "\(.id)\t\(.error_class)\t\(.error_message)"'
```

Archive records, then remove those older than a chosen date:

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
| `log` | `6` | The given Operation ID does not exist, or several different `-d` values were given |
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
- [sow changes](/docs/command/changes/) — compare files between builds
- [JSON Output](/docs/reference/json/) — the full log result schema
