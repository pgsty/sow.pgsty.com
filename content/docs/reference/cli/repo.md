---
title: "sow repo"
linkTitle: "sow repo"
description: "List, create, inspect and remove Repositories — the lock, transaction and Generation boundary."
url: "/docs/reference/cli/repo/"
weight: 400
icon: fa-solid fa-box-archive
---

A Repository owns one `pool/`, one `dists/`, one SQLite database and one private state directory. It
is the boundary of locking, transaction recovery, Generation numbering and Changesets — nothing is
deduplicated across Repositories and no cross-Repository commit is atomic. `sow repo` manages that
boundary.

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

You cannot choose the path. A Repository always lives at `<workspace>/<NAME>/`.

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
| `--json` | Emit the versioned JSON envelope | false |

`STATUS` is one of `clean`, `dirty`, `recovering` or `error`. See
[Transactions & Recovery](/docs/feature/transactions/) for what each one implies for clients.

## sow repo new

Atomically updates `sow.yml`, then creates `<workspace>/<NAME>/{pool,dists}`, the SQLite database and
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
| `--json` | Emit the versioned JSON envelope | false |

`repo new` takes the Workspace lock, not a Repository lock — the Repository database does not exist
yet. It does not accept `-r`; the positional argument already names the target.

Running it again on an existing Repository is a converging no-op that reports the current state, so
it is safe in a provisioning script.

## sow repo show

Read-only detail for one Repository. With `NAME` omitted, the usual
[Repository selection rules](/docs/reference/cli/#repository-selection) apply.

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
| `--json` | Emit the versioned JSON envelope | false |

If you give both `NAME` and `-r`, they must agree; disagreement fails before any state is read:

```console
sow repo show demo -r empty
operation rejected: repo show NAME "demo" and --repo "empty" select different repositories
```

## sow repo migrate

Migrates a repository created by the unreleased C2 prototype from view-local RPM aliases
to the v0.2.0 single-payload layout. It rewrites RPM metadata to reach the root `pool/`,
records a durable transition, advances the Generation, and changes `schema: sow/v2` to
`schema: sow/v3`.

```bash
sow repo migrate pigsty
```

The operation is resumable. Before durable commit intent, `--abort` abandons the staged
transition and leaves the live repository unchanged. After commit intent the transition is
forward-only; rerun `repo migrate` until its grace and cleanup conditions complete.

| Flag | Description | Default |
|---|---|---|
| `-j, --jobs N` | Parallel verification/render workers | logical CPUs |
| `--abort` | Abandon a pre-commit migration | false |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select the repository when `NAME` is omitted | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the versioned JSON envelope | false |

New v0.2.0 workspaces already use the single-payload layout and do not need migration.

## sow repo rm

Removes a Repository: its `sow.yml` entry, database, `pool/`, `dists/` and private state. It never
follows symlinks and never steps outside the fixed Repository path.

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
| `--json` | Emit the versioned JSON envelope | false |

### What -f actually downgrades

`-f` only relaxes the *emptiness* precondition. It does not bypass path safety, symlink refusal, or
the `protected` gate.

## protected

`protected: true` in `sow.yml` blocks Repository deletion outright, `-f` included:

```console
sow repo rm alpha -f
operation rejected: managed: operation rejected: repository "alpha" is protected
```

To remove a protected Repository you must edit `sow.yml`, pass
[`sow config check`](/docs/reference/cli/config/), and try again. There is no `--yes` and no
temporary override.

`protected` scopes to Repository deletion only. Package-level work on a protected Repository is
unaffected — `add`, `rm`, `build`, and even `dist rm`, all continue to work:

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

Fail fast in a cron job rather than queue behind another writer:

```bash
sow repo new nightly -N || echo "another writer holds the workspace lock"
```

Audit every Repository in one line each:

```bash
sow repo ls --json | jq -r '.result.repositories[] | "\(.name)\t\(.status)\tgen=\(.generation)"'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Listed, created, shown or removed; or `repo new` converged an existing Repository |
| `1` | Runtime I/O error creating or removing the tree |
| `2` | Usage error, Workspace not found, or an ambiguous Repository selection |
| `4` | Workspace lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error in the Workspace journal |
| `6` | Invalid name, unknown Repository, non-empty without `-f`, `protected`, or `NAME` conflicting with `-r` |

## See also

- [sow dist](/docs/reference/cli/dist/) — the layer below
- [Managed Workspaces](/docs/feature/managed/) — the three-layer model and discovery rules
- [Transactions & Recovery](/docs/feature/transactions/) — lock scopes and the `recovering` state
- [sow.yml Reference](/docs/reference/config/) — `protected` and per-Repository signing
- [Repository Layout](/docs/reference/layout/) — the fixed directory structure
