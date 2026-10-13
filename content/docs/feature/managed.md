---
title: "Managed Workspaces"
linkTitle: "Managed Workspaces"
description: "Workspace structure, package membership, configuration, discovery, and initialization."
categories: [Feature]
tags: [managed, repository, dist, generation]
url: "/docs/feature/managed/"
weight: 300
icon: fa-solid fa-sitemap
---

Use Managed mode for repositories that receive regular updates. SOW records package
membership, applies Dist policy, builds metadata, and keeps operation history.

<span id="the-three-tiers"></span>

## Workspace, repository, and Dist

```text
Workspace
└── Repository
    └── Dist
        └── Architecture view
```

| Term | Purpose |
|---|---|
| Workspace | Holds `sow.yml`, private `.sow/` state, and the allowed architecture families |
| Repository | Owns one package pool, Dists, a SQLite database, generations, and publication state |
| Dist | Selects a named set of packages in one format: `rpm` or `deb` |
| Architecture view | Presents a Dist's packages to clients of one architecture |

A repository can contain RPM and DEB Dists. Dist names such as `el9`, `trixie`, and
`el9-beta` are labels you choose; they do not inspect operating-system compatibility or
create a promotion workflow.

One package can belong to several Dists in the same repository without another payload
copy. An architecture-neutral package has one membership per Dist and appears in each
applicable architecture view. Separate repositories keep separate package objects.

<span id="the-layout"></span>

## Public files and private state

```text
<workspace>/
├── sow.yml
├── .sow/
│   ├── workspace.lock
│   ├── workspace-ops/
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db
│   └── <repo>/
│       ├── stage/
│       ├── recovery/
│       ├── pending/
│       ├── retained/
│       └── transitions/
└── <repo>/
    ├── pool/
    └── dists/
```

Serve or publish the complete `<workspace>/<repo>/` directory. Keep `sow.yml` and `.sow/`
private. Back up configuration, private state, and package files together when you need
to preserve a working workspace. See [Repository layout](/docs/reference/layout/).

<span id="sowyml-drives-everything"></span>
<span id="protected-repositories"></span>

## Create and configure

```bash
sow init /srv/repo
sow repo new demo -C /srv/repo
sow dist new el9 --format rpm -r demo -C /srv/repo
sow dist new trixie --format deb -r demo -C /srv/repo
```

The initial configuration uses `schema: sow/v3` and architecture families
`[x86_64, aarch64]`. `init` creates no repository unless one is already declared in the
configuration. Repository and Dist lifecycle commands update `sow.yml` for you.

Edit `sow.yml` to set architecture restrictions, membership policy, signing, or publication
targets. Then validate the configuration:

```bash
sow config check -C /srv/repo
sow config show --all -C /srv/repo
```

The parser rejects unknown fields. `config check` also compares configuration with
initialized state and resolves signing references. `config show --all` expands defaults.
Configuration accepts `amd64` and `arm64` as aliases for `x86_64` and `aarch64`.
DEB indexes use the native names `amd64` and `arm64`.

To prevent removal of a repository, set `protected: true` on it. This blocks `repo rm`,
including `-f`; package and Dist changes remain available.

<span id="empty-has-a-valid-protocol-surface"></span>

## Desired state and built state

Desired state records which packages should belong to each Dist. Built state records the
last completed metadata generation.

By default, `add` and `rm` update membership and build the affected output. With `--skip`,
they update membership without building. New package bytes stay in private `pending/`
until a build promotes them to the pool.

```bash
sow add ./incoming/ -C /srv/repo -r demo -d el9 --skip
sow status -C /srv/repo -r demo
sow build -C /srv/repo -r demo
sow check -C /srv/repo -r demo
```

A `dirty` repository needs a build. Its public tree still represents the previous built
generation. Policy, architecture, or signing changes can also make a Dist dirty.
Removing an architecture still referenced by membership or built state is rejected.

Every new Dist starts with valid empty indexes for its architectures. Metadata signing,
when configured, applies to empty Dists too. Removing the last member leaves empty indexes.

<span id="discovery-which-workspace"></span>

## Find the workspace

Managed commands search for the nearest ancestor `sow.yml`:

1. Start at `-C/--workdir DIR`, if supplied; otherwise start at the current directory.
2. If no workspace is found, search from `$SOW_DIR`.
3. If neither search succeeds, report a discovery error.

The first configuration found is used, even if it contains an error. `--workdir` changes
workspace discovery, not the process directory. Relative input paths still refer to your
current directory:

```bash
sow add ./build/example.rpm -C /srv/repo -r demo -d el9
```

A symlink can be a search starting point, but the search follows the supplied path's
ancestors. A symlink within the workspace prevents implicit repository or Dist selection.
Use the physical workspace path and explicit `-r` and `-d` when needed.

Plain `sow create` does not use workspace discovery.

<span id="selection-which-repository-which-dist"></span>

## Select a repository and Dist

Repository selection uses the first available choice:

1. Explicit `-r/--repo NAME`.
2. The repository containing the discovery starting directory.
3. The only repository in the workspace.

`add`, `rm`, and `ls` select Dists in this order:

1. Explicit `-d` options; repeat the option to select several Dists.
2. The Dist containing the discovery starting directory.
3. The only Dist in the selected repository.

If more than one choice remains, the command requires an explicit selection.

`build`, `check`, and `status` default to all Dists in the selected repository.
`show` searches that repository; `where` searches all repositories. Use `-d` to narrow
commands that accept it. See [Commands](/docs/command/) for each command's selection rules.

<span id="state-database-and-package-facts"></span>
<span id="init-converges-it-does-not-reset"></span>

## Repeat initialization or upgrade

Rerunning `init` fills in missing declared repositories and Dists. It checks existing
initialized state without resetting generations. After adding an architecture to an
existing Dist, run `build` to create its new view.

If initialization commits some objects and then fails, it returns exit `3` and reports
what completed. Resolve the error and rerun `init`.

SOW 0.5 uses database schema v13. Back up older workspaces and use
[`sow repo migrate`](/docs/command/repo/#sow-repo-migrate) for supported upgrades.
Do not change the SQLite schema version by hand.

The database also caches parsed package facts. Warm builds can reuse those facts and
file fingerprints; `sow check` reads and hashes package bytes for a full consistency check.

See [Policy](/docs/feature/policy/), [Views](/docs/feature/views/), and
[Transactions and recovery](/docs/feature/transactions/) for the next steps.

<span id="next"></span>
