---
title: "sow init"
linkTitle: "sow init"
description: "Create a Workspace, and converge whatever Repositories and Dists sow.yml already declares."
url: "/docs/reference/cli/init/"
weight: 200
icon: fa-solid fa-seedling
---

`sow init` creates the root `sow.yml` and the private `.sow/` state directory that make a directory a
Workspace. It is also the convergence command for a config you wrote by hand: if `sow.yml` already
declares Repositories and Dists, `init` materializes the ones that don't exist yet and leaves the
finished ones alone.

## Synopsis

```text
sow init [DIR] [--json]
```

`DIR` defaults to the current directory. `init` takes no `-C/--workdir` — the positional argument
already names the target unambiguously.

## Description

A fresh `init` writes a minimal config and the private state directory:

```console
sow init .
initialized /srv/repo: config_created=true repositories_initialized=0 dists_initialized=0
```

```console
cat sow.yml
schema: sow/v3
architectures:
  - x86_64
  - aarch64
```

```console
ls -a /srv/repo
.  ..  .sow  sow.yml
```

`.sow/` holds `workspace.lock`, the `workspace-ops/` durable file journal used by Workspace lifecycle
commands, `repo-locks/`, and later one SQLite database per Repository. It is mode `0700` and must
never be served over HTTP.

## Options

| Flag | Description | Default |
|---|---|---|
| `--json` | Emit the versioned JSON envelope | false |
| `-h, --help` | Show help | — |

## Idempotence rules

`init` is designed to be safe to run repeatedly, in a provisioning script or by hand:

1. **It writes `schema: sow/v3` and the default `architectures: [x86_64, aarch64]`** when creating a
   new config.
2. **It never creates a Repository on its own.** Use [`sow repo new`](/docs/reference/cli/repo/), or
   declare one in `sow.yml` first.
3. **It never overwrites an existing `sow.yml`.** A repeat run reports the current state and lists
   what it found:

   ```console
   sow init .
   initialized /srv/repo: config_created=false repositories_initialized=0 dists_initialized=0
   ```

4. **A non-empty directory can be initialized**, but the run fails if an existing file collides with
   a SOW reserved path.

## Converging a declared configuration

If `sow.yml` already describes Repositories and Dists, `init` creates the missing directory trees,
SQLite databases and empty indexes for them. Already-initialized objects are skipped, so the counters
tell you exactly what this run did.

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]

repos:
  pgsql:
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource]
      trixie:
        format: deb
  infra:
    protected: true
    dists:
      el9:
        format: rpm
```

```console
sow init .
initialized /srv/repo: config_created=false repositories_initialized=2 dists_initialized=3
```

```console
sow repo ls
NAME	PROTECTED	DISTS	GENERATION	STATUS	PACKAGES	MEMBERSHIPS
infra	true	1	1	clean	0	0
pgsql	false	2	2	clean	0	0
```

Every Dist created this way is immediately consumable: an RPM Dist gets an empty `repodata/` per
architecture view, a DEB Dist gets empty `Packages`/`Packages.gz` with `by-hash` plus a `Release`.

Running it a second time changes nothing:

```console
sow init . --json
{"schema":"sow.cli/v1","command":"init","ok":true,"repository":null,"operation":null,"result":{"workspace":"/srv/repo","config_created":false,"repositories_initialized":0,"dists_initialized":0,"existing":["sow.yml"]},"errors":[]}
```

## Locking and recovery

Workspace lifecycle commands — `init`, `repo new`, `repo rm` — run before the target Repository
database exists or after it is deleted, so they use `.sow/workspace.lock` plus the durable file
journal in `.sow/workspace-ops/` rather than a SQLite Operation Journal. An interrupted `init` is
completed or rolled back by the next Workspace lifecycle command.

## Examples

Bootstrap a Workspace and add Repositories by hand:

```bash
mkdir -p /srv/repo && cd /srv/repo
sow init
sow repo new infra
sow repo new pgsql
sow dist new el9 --format rpm -r pgsql
sow dist new trixie --format deb -r pgsql
```

Initialize a directory other than the current one:

```bash
sow init /srv/repo
```

Provision from a config file under version control:

```bash
install -m 0644 sow.yml /srv/repo/sow.yml
sow init /srv/repo
sow config check -C /srv/repo
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Workspace created, or already converged (no-op) |
| `1` | Runtime I/O error writing the config or state directory |
| `2` | Usage error, or an existing `sow.yml` that fails to parse or validate |
| `3` | Partial success — some declared Repositories/Dists were committed and at least one failed |
| `4` | Workspace lock held and the wait was cut short |
| `5` | The Workspace journal could not be recovered to a terminal state |
| `6` | An existing file collides with a SOW reserved path, or a declared name is invalid |

## See also

- [First Workspace](/docs/start/workspace/) — the ten-minute guided version
- [Managed Workspaces](/docs/feature/managed/) — the three-layer model
- [sow.yml Reference](/docs/reference/config/) — every configuration key
- [sow repo](/docs/reference/cli/repo/) and [sow dist](/docs/reference/cli/dist/)
- [Repository Layout](/docs/reference/layout/) — what `.sow/` contains
