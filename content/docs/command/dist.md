---
title: "sow dist"
linkTitle: "dist"
description: "Create, list, inspect, and remove RPM or DEB distributions."
categories: [Command]
tags: [cli, dist, managed]
url: "/docs/command/dist/"
aliases: ["/docs/reference/cli/dist/"]
weight: 500
icon: fa-solid fa-layer-group
---

`sow dist` manages the distributions that clients use. Each Dist contains either RPM or DEB packages. Dists in one Repository share `pool/` and have separate indexes under `dists/`.

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

Choose names that identify your distributions or channels, such as `el9`, `trixie`, or `el9-beta`. SOW does not infer package format or policy from the name.

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
| `--json` | Output JSON | false |

The table shows architecture families. JSON also shows the package ecosystem names.
This excerpt contains the `architectures` field from one entry in `result.dists`; the DEB
view directories are `binary-amd64` and `binary-arm64`:

```json
{
  "architectures": [
    {"family": "x86_64", "ecosystem_arch": "amd64"},
    {"family": "aarch64", "ecosystem_arch": "arm64"}
  ]
}
```

## sow dist new

Create a Dist with `--format rpm` or `--format deb`.

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
| `--json` | Output JSON | false |

`--format` is required and accepts only `rpm` or `deb`:

```console
sow dist new x -r alpha
usage error: dist new requires --format rpm|deb
```

```console
sow dist new x --format zip -r alpha
usage error: --format must be rpm or deb
```

A new Dist inherits the Workspace architectures. Edit `sow.yml` to select a subset or set `limit` and `exclude`, then run `sow config check` and `sow build`.

If the name and format already exist, `dist new` reports the current state.
Using the same name with a different format is rejected:

```console
sow dist new el9 --format deb -r alpha
operation rejected: managed: operation rejected: dist "el9" already exists with format rpm
```

### Creation and recovery {#the-three-way-transaction}

`dist new` updates `sow.yml` and builds the new Dist. If it is interrupted, run `sow build` to recover the operation.

The new Dist has valid empty indexes. An RPM Dist gets empty `repodata/` in each architecture view. A DEB Dist gets empty `Packages` and `Packages.gz` files, `by-hash/SHA256/` entries, and a `Release` file. When signing is configured, it also gets `InRelease` and `Release.gpg`.

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
| `--json` | Output JSON | false |

JSON also includes `effective_config_sha256`, the digest of the resolved Dist configuration.
Changing `limit`, `exclude`, or a signing key can make the current configuration differ
from the Built Generation. SOW then marks the Dist dirty until it is rebuilt.

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
| `--json` | Output JSON | false |

### Dist removal does not delete Pool bytes

SOW removes the Dist’s configuration, membership, and indexes. Package files remain in `pool/`:

```console
sow dist rm el9 -r pgsql -f
removed dist el9 from pgsql

find pgsql -type f
pgsql/pool/e/epel-release/epel-release-7-5.noarch.rpm
```

Run [`sow gc`](/docs/command/gc/) to reclaim package files when no current or retained state needs them.

If a configured target has published this Dist, removal is rejected. See
[Removing a published view](/docs/command/publish/#removing-a-published-view).

A Repository's `protected: true` blocks Repository deletion only; normal Dist maintenance on a
protected Repository continues to work.

## Examples

Create an RPM Dist and a DEB Dist in one Repository:

```bash
sow dist new el9 --format rpm -r pgsql
sow dist new trixie --format deb -r pgsql
```

Create a beta Dist, set its package-retention policy in `sow.yml`, then rebuild it:

```bash
sow dist new el9-beta --format rpm -r pgsql
$EDITOR sow.yml          # el9-beta: { limit: 0 }
sow config check
sow build -r pgsql -d el9-beta
```

List Dists that need a build:

```bash
sow dist ls -r pgsql --json | jq -r '.result.dists[] | select(.dirty) | .name'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Listed, created, shown or removed; or `dist new` reported an existing Dist |
| `1` | Runtime I/O or renderer error creating the empty indexes |
| `2` | Usage error — missing or invalid `--format`, Workspace not found, ambiguous Repository |
| `4` | Workspace or Repository lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error in the Operation Journal |
| `6` | Invalid name, unknown Dist, format conflict with an existing name, non-empty without `-f` |

## See also

- [sow repo](/docs/command/repo/) — the layer above
- [Pool & Architecture Views](/docs/feature/views/) — how one Dist becomes several client-visible views
- [Membership Policy](/docs/feature/policy/) — configuring `limit` and `exclude`
- [sow build](/docs/command/build/) — rebuild after a policy edit
- [Repository Layout](/docs/reference/layout/) — the RPM and DEB `dists/` structures
