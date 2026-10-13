---
title: "sow init"
linkTitle: "init"
description: "Initialize a Workspace and the Repositories and Dists declared in sow.yml."
categories: [Command]
tags: [cli, managed, config]
url: "/docs/command/init/"
aliases: ["/docs/reference/cli/init/"]
weight: 200
icon: fa-solid fa-seedling
---

`sow init` creates a Workspace with `sow.yml` and private `.sow/` state. If the configuration already declares Repositories and Dists, it creates the missing ones. Run it again to complete initialization after adding declarations.

## Synopsis

```text
sow init [DIR] [--json]
```

`DIR` defaults to the current directory. To initialize another directory, pass its path as `DIR`.

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

`.sow/` stores private state, locks, and recovery records with directory permissions `0700`. Serve the Repository directories over HTTP; keep `.sow/` private.

## Options

| Flag | Description | Default |
|---|---|---|
| `--json` | Output JSON | false |
| `-h, --help` | Show help | — |

## Idempotence rules

A new configuration uses `schema: sow/v3` and architectures `x86_64` and `aarch64`. It declares no Repository. Add one with [`sow repo new`](/docs/command/repo/) or edit `sow.yml` first.

`init` preserves an existing configuration and initializes missing declared objects. It can use a non-empty directory if no file conflicts with a reserved SOW path. When all declared objects are already initialized, the counters are zero.

## Apply a declared configuration {#converging-a-declared-configuration}

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

Every Dist created this way has valid empty indexes. An RPM Dist gets empty `repodata/` in each architecture view. A DEB Dist gets empty `Packages` and `Packages.gz` files, `by-hash` entries, and a `Release` file.

Running it a second time changes nothing:

```console
sow init . --json
{"schema":"sow.cli/v1","command":"init","ok":true,"repository":null,"operation":null,"result":{"workspace":"/srv/repo","config_created":false,"repositories_initialized":0,"dists_initialized":0,"existing":["sow.yml"]},"errors":[]}
```

## Locking and recovery

If initialization is interrupted, rerun `sow init` for the same directory. SOW first completes or rolls back the interrupted operation, then initializes any remaining declared objects. It waits for other Workspace writers to finish.

## Examples

Bootstrap a Workspace and add Repositories by hand:

```bash
mkdir -p /srv/repo
cd /srv/repo
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

Initialize from a config file under version control:

```bash
install -m 0644 sow.yml /srv/repo/sow.yml
sow init /srv/repo
sow config check -C /srv/repo
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Workspace initialized, or already initialized (no-op) |
| `1` | Runtime I/O error writing the config or state directory |
| `2` | Usage error, or an existing `sow.yml` that fails to parse or validate |
| `3` | Partial success — some declared Repositories/Dists were committed and at least one failed |
| `5` | The Workspace journal could not be recovered to a terminal state |
| `6` | An existing file collides with a SOW reserved path |

## See also

- [First Workspace](/docs/start/workspace/) — the ten-minute guided version
- [Managed Workspaces](/docs/feature/managed/) — the three-layer model
- [sow.yml Reference](/docs/reference/config/) — every configuration key
- [sow repo](/docs/command/repo/) and [sow dist](/docs/command/dist/)
- [Repository Layout](/docs/reference/layout/) — what `.sow/` contains
