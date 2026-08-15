---
title: "sow dist"
linkTitle: "dist"
description: "List, create, inspect and remove Dists — the named single-format member set clients actually consume."
url: "/docs/command/dist/"
aliases: ["/docs/reference/cli/dist/"]
weight: 500
icon: fa-solid fa-layer-group
---

A Dist is a named set of packages in exactly one format (`rpm` or `deb`) inside one Repository. It is
what a client points at. A Repository can hold RPM and DEB Dists side by side; they share one `pool/`
but render into completely separate `dists/` subtrees.

## Synopsis

```text
sow dist ls [-C DIR] [-r NAME] [--json]
sow dist new NAME --format rpm|deb [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow dist show NAME [-C DIR] [-r NAME] [--json]
sow dist rm NAME [-f|--force] [-C DIR] [-r NAME] [-T DUR | -N] [--json]
```

## Naming

Dist names follow the same rule as Repository names: `[a-z0-9][a-z0-9._-]*`, excluding `.`, `..`,
`.sow`, `pool` and `dists`.

To SOW the name is an opaque string. `el9`, `trixie`, `el9-beta`, `customer-acme`, `2026-07-31` are
all just names — beta channels, per-customer views and snapshots are naming conventions you impose,
not features SOW models.

## sow dist ls

Read-only flat listing of the selected Repository's Dists.

```console
sow dist ls -r pigsty
NAME	FORMAT	ARCHITECTURES	DESIRED	BUILT	GENERATION	DIRTY	DIRTY_REASONS
el9	rpm	x86_64,aarch64	0	0	1	false	[]
trixie	deb	x86_64,aarch64	0	0	2	false	[]
```

`DESIRED` and `BUILT` are membership counts. When they diverge, `DIRTY_REASONS` says why:

```console
sow dist ls -r demo
NAME	FORMAT	ARCHITECTURES	DESIRED	BUILT	GENERATION	DIRTY	DIRTY_REASONS
el9	rpm	x86_64,aarch64	2	1	4	true	["Desired and Built membership sets differ"]
```

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `--json` | Emit the versioned JSON envelope | false |

Architectures print as canonical families. The JSON output carries both spellings, which is how you
confirm that a DEB Dist renders `binary-amd64` and `binary-arm64`:

```json
"architectures":[{"family":"x86_64","ecosystem_arch":"amd64"},{"family":"aarch64","ecosystem_arch":"arm64"}]
```

## sow dist new

Creates an ordinary, still-editable Dist. The only business argument is `--format`.

```console
sow dist new el9 --format rpm -r pigsty
created el9: format=rpm architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
```

```console
sow dist new trixie --format deb -r pigsty
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=2 dirty=false
```

| Flag | Description | Default |
|---|---|---|
| `--format FORMAT` | Required; `rpm` or `deb` | — |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the versioned JSON envelope | false |

`--format` is mandatory and closed:

```console
sow dist new x -r alpha
usage error: dist new requires --format rpm|deb
```

```console
sow dist new x --format zip -r alpha
usage error: --format must be rpm or deb
```

There is no `--arch`. Architectures are inherited from the Workspace permit list; an advanced user
narrows them per Dist by editing `sow.yml`. Policy (`limit`, `exclude`) is likewise configured in
`sow.yml`, never re-modelled on the command line.

Re-running `dist new` with the same name and the same format converges and reports the current state.
A name collision with a *different* format is rejected:

```console
sow dist new el9 --format deb -r alpha
operation rejected: managed: operation rejected: dist "el9" already exists with format rpm
```

### The three-way transaction

`dist new` is committed across three places at once: the `sow.yml` entry, the Repository database,
and the on-disk tree. It goes through the SQLite Operation Journal (the Repository database already
exists at this point, unlike `repo new`) and produces a new Built Generation with empty indexes.

That means a fresh Dist has a protocol-complete empty surface. An RPM Dist gets an empty
`repodata/` under every architecture view; a DEB Dist gets empty `Packages`, `Packages.gz`,
the `by-hash/SHA256/` entries and `Release`, plus `InRelease`/`Release.gpg` when signing is
configured.

## sow dist show

Read-only detail for one Dist.

```console
sow dist show trixielim -r pgsql
dist trixielim:
  format: deb
  architectures: x86_64,aarch64
  desired_members: 3
  built_members: 3
  generation: 6
  status: clean
  dirty: false
  dirty_reasons: []
```

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `--json` | Emit the versioned JSON envelope | false |

The JSON form additionally exposes `effective_config_sha256`, the digest of the resolved Dist
configuration. That digest is what makes a Dist dirty when you change `limit`, `exclude` or a signing
key — the config identity changed, so the Built Generation no longer matches Desired.

```console
sow dist show el9 -r pgsql --json
{"schema":"sow.cli/v1","command":"dist show","ok":true,"repository":"pgsql","operation":null,"result":{"name":"el9","format":"rpm","architectures":[{"family":"x86_64","ecosystem_arch":"x86_64"},{"family":"aarch64","ecosystem_arch":"aarch64"}],"desired_members":0,"built_members":0,"generation":"00000000000000000001","dirty":false,"status":"clean","effective_config_sha256":"a0b3ae2f943bc4fce951aaadda0fc8fb146ccf7944b0193a0dcc2b86ddc7ce7e","config":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":1,"exclude":[{"kind":["debuginfo","debugsource"]}]}},"errors":[]}
```

```console
sow dist show nope -r demo
operation rejected: managed: operation rejected: dist "nope" does not exist
```

## sow dist rm

Removes a Dist's Membership and derived indexes.

```console
sow dist rm el9 -r pgsql
operation rejected: managed: operation rejected: dist "el9" is not empty; use --force
```

```console
sow dist rm el9 -r pgsql -f
removed dist el9 from pgsql
```

| Flag | Description | Default |
|---|---|---|
| `-f, --force` | Remove membership and indexes but retain pool packages | false |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the versioned JSON envelope | false |

### Dist removal does not delete Pool bytes

Removing a Dist never deletes a package from `pool/`. The whole Dist directory is moved into the
recovery area and removed atomically; the pool is untouched:

```console
sow dist rm el9 -r pgsql -f
removed dist el9 from pgsql

find pgsql -type f
pgsql/pool/e/epel-release/epel-release-7-5.noarch.rpm
```

Orphaned pool objects remain until `sow gc` proves they are unreachable from every safety
root: current, retained, recovery, publication, and any active maintenance operation.

A Repository's `protected: true` blocks Repository deletion only; normal Dist maintenance on a
protected Repository continues to work.

## Examples

Give one Repository an RPM and a DEB face:

```bash
sow dist new el9 --format rpm -r pgsql
sow dist new trixie --format deb -r pgsql
```

Add a beta channel with its own retention policy — create it, then set the policy in `sow.yml` and
converge:

```bash
sow dist new el9-beta --format rpm -r pgsql
$EDITOR sow.yml          # el9-beta: { limit: 0 }
sow config check
sow build -r pgsql -d el9-beta
```

Which Dists are behind their Desired state:

```bash
sow dist ls -r pgsql --json | jq -r '.result.dists[] | select(.dirty) | .name'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Listed, created, shown or removed; or `dist new` converged an existing Dist |
| `1` | Runtime I/O or renderer error creating the empty indexes |
| `2` | Usage error — missing or invalid `--format`, Workspace not found, ambiguous Repository |
| `4` | Repository lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error in the Operation Journal |
| `6` | Invalid name, unknown Dist, format conflict with an existing name, non-empty without `-f` |

## See also

- [sow repo](/docs/command/repo/) — the layer above
- [Pool & Architecture Views](/docs/feature/views/) — how one Dist becomes several client-visible views
- [Membership Policy](/docs/feature/policy/) — configuring `limit` and `exclude`
- [sow build](/docs/command/build/) — converging after a policy edit
- [Repository Layout](/docs/reference/layout/) — the RPM and DEB `dists/` structures
