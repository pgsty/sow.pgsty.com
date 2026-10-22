---
title: "sow repo"
linkTitle: "repo"
description: "Create, list, inspect, migrate, and remove Repositories."
categories: [Command]
tags: [cli, repository, managed]
url: "/docs/command/repo/"
aliases: ["/docs/reference/cli/repo/"]
weight: 400
icon: fa-solid fa-box-archive
---

`sow repo` creates, lists, inspects, upgrades, and removes Repositories. Each Repository stores its packages in `pool/` and its indexes in `dists/`. Packages are shared among Dists in the same Repository.

## Synopsis

```text
sow repo ls [-C DIR] [--json]
sow repo new NAME [-C DIR] [-T DUR | -N] [--json]
sow repo show [NAME] [-C DIR] [-r NAME] [--json]
sow repo migrate [NAME] [--abort] [-j N] [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow repo rm NAME [-f|--force] [-C DIR] [-T DUR | -N] [--json]
```

## Naming

A Repository name must match `[a-z0-9][a-z0-9._-]*` and may not be `.`, `..`, `.sow`, `pool`,
`dists`, or collide with a Workspace reserved file.

```console
sow repo new .sow
operation rejected: managed: operation rejected: name ".sow" must match [a-z0-9][a-z0-9._-]*
```

SOW creates each Repository at `<workspace>/<NAME>/`.

## sow repo ls

Read-only listing of every Repository in the Workspace.

```console
sow repo ls
NAME	PROTECTED	DISTS	GENERATION	STATUS	PACKAGES	MEMBERSHIPS
infra	true	1	1	clean	0	0
pgsql	false	2	2	clean	0	0
```

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `--json` | Output JSON | false |

`STATUS` is one of `clean`, `dirty`, `recovering` or `error`. See
[Transactions & Recovery](/docs/feature/transactions/) for what each one implies for clients.

## sow repo new

Updates `sow.yml`, then creates `<workspace>/<NAME>/{pool,dists}`, the SQLite database and
the private state directory. A new Repository is Generation 0 and clean.

```console
sow repo new pigsty
created pigsty: path=/srv/repo/pigsty protected=false dists=0 generation=0 status=clean packages=0 memberships=0
```

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

Pass the new Repository name as `NAME`.

Running it again on an existing Repository reports the current state without creating
another Repository.

## sow repo show

Read-only detail for one Repository. With `NAME` omitted, the usual
[Repository selection rules](/docs/command/#repository-selection) apply.

```console
sow repo show pigsty
repository pigsty:
  path: /srv/repo/pigsty
  protected: false
  dists: 2
  generation: 6
  desired_revision: 6
  status: clean
  packages: 5
  memberships: 8
  config: {"protected":false,"signing":{"rpm":{"packages":{"mode":"never"}}},"dists":{"el9":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":1,"exclude":[{"kind":["debuginfo","debugsource"]}]},"trixie":{"format":"deb","architectures":["x86_64","aarch64"],"limit":0,"exclude":null}}}
  dirty_reasons: []
  recent_operation: id=4142220455201181493 kind=add state=done error_class= created_at=2026-08-04T04:09:24.995538Z updated_at=2026-08-04T04:09:25.332772Z
```

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select the repository when `NAME` is omitted | selection rules |
| `--json` | Output JSON | false |

If you give both `NAME` and `-r`, use the same name:

```console
sow repo show demo -r empty
operation rejected: repo show NAME "demo" and --repo "empty" select different repositories
```

## sow repo migrate

Use `repo migrate` to upgrade a 0.3 or 0.4 workspace to SOW 0.6.1.
Workspaces already on 0.5.0 or 0.6.0 use schema v13 and need no schema migration. New 0.6.1 repositories also use schema v13.

1. Stop Workspace writers.
2. Back up the whole Workspace, preserving hard links.
3. Migrate each configured Repository.
4. Run `build` and `check` for each Repository.

```bash
rsync -aH /srv/sow/ /srv/sow.backup-before-0.6.1/
sow repo migrate pigsty -C /srv/sow
sow build -r pigsty -C /srv/sow
sow check -r pigsty -C /srv/sow
```

Repeat the last three commands for each Repository. The migration reports `schema_from` and `schema_to`; a repeated migration reports `13 -> 13`. Schema v13 adds pool-path lookup indexes. Migration from v0.3 also applies the intervening state and publication repairs.

Writes require the current schema. Compatible read-only commands can inspect older state without upgrading it. After migration, use SOW 0.5 or later; restore the backup to return to the older schema.

`--abort` abandons an unfinished layout plan before its commit decision. It does not undo a completed schema migration.
For an earlier C2 transition, SOW checks the repository identity and available journal and database control records.
Conflicting records stop the abort. A journal-bound plan also requires its recorded base manifest.

An abort can complete before the first journal or base manifest was written, provided the trusted transition marker already exists.
SOW keeps that marker so another `sow repo migrate NAME` can plan and resume the transition.
After commit intent, only forward recovery is allowed.

SOW moves a nonempty temporary stage intact into `.sow/<repo>/abandoned/`.
It reports retained paths or cleanup problems on stderr and in JSON `warnings`.
A stage-cleanup warning does not prevent abandonment. Inspect the reported paths before removing files you no longer need.
The public tree remains unchanged.

A fresh development-era C2 repository still cannot start a migration.
If an older abort already removed the trusted marker, restore a complete matching backup or import the original packages into a new workspace.

| Flag | Description | Default |
|---|---|---|
| `-j, --jobs N` | Parallel verification/render workers | logical CPUs |
| `--abort` | Abandon a maintenance attempt before its commit decision | false |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select the repository when `NAME` is omitted | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

## sow repo rm

Removes a Repository, including its `sow.yml` entry, database, package files in `pool/`, indexes in `dists/`, and private state.

Without `-f`, only an empty Repository — no Dists, no Memberships, no Package Objects — can be
removed:

```console
sow repo rm infra
removed repository infra
```

```console
sow repo rm pgsql
operation rejected: managed: operation rejected: repository "pgsql" is not empty; use --force
```

```console
sow repo rm pgsql -f
removed repository pgsql
```

| Flag | Description | Default |
|---|---|---|
| `-f, --force` | Remove a non-empty unprotected repository | false |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

### Force removal {#what--f-actually-downgrades}

Use `-f` to remove a non-empty Repository. A protected Repository remains protected when you use `-f`.

## protected

`protected: true` in `sow.yml` blocks Repository deletion outright, `-f` included:

```console
sow repo rm alpha -f
operation rejected: managed: operation rejected: repository "alpha" is protected
```

To remove a protected Repository, set its `protected` value to `false` in `sow.yml`. Run [`sow config check`](/docs/command/config/), then retry the removal.

`protected` applies only to Repository deletion. `add`, `rm`, `build`, and `dist rm` continue to work:

```console
sow dist rm el9 -r alpha -f
removed dist el9 from alpha
```

## Examples

Create the Repositories for a two-tier layout:

```bash
sow repo new infra
sow repo new pgsql
```

Create a Repository without waiting for a held lock:

```bash
sow repo new nightly -N
```

Print each Repository’s name, state, and Generation:

```bash
sow repo ls --json | jq -r '.result.repositories[] | "\(.name)\t\(.status)\tgen=\(.generation)"'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Listed, created, shown, migrated, abandoned a pre-commit transition, or removed; or `repo new` reported an existing Repository |
| `1` | Runtime I/O error creating or removing the tree |
| `2` | Usage error, Workspace not found, or an ambiguous Repository selection |
| `4` | Workspace lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error in the Workspace journal |
| `6` | Invalid name, unknown Repository, non-empty without `-f`, `protected`, or `NAME` conflicting with `-r` |

## See also

- [sow dist](/docs/command/dist/) — the layer below
- [Managed Workspaces](/docs/feature/managed/) — the three-layer model and discovery rules
- [Transactions & Recovery](/docs/feature/transactions/) — lock scopes and the `recovering` state
- [sow.yml Reference](/docs/reference/config/) — `protected` and per-Repository signing
- [Repository Layout](/docs/reference/layout/) — the fixed directory structure
