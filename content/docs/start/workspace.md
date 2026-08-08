---
title: "Your First Workspace"
linkTitle: "First Workspace"
description: "Create a new v0.2.0 workspace with RPM and DEB Dists, add packages, and verify the public tree."
url: "/docs/start/workspace/"
weight: 300
icon: fa-solid fa-layer-group
---

Managed mode keeps configuration, membership, generations, and audit state. This example
starts from an empty directory.

## 1. Initialize the workspace

```bash
sow init /srv/sow
cd /srv/sow
```

`init` creates:

```text
/srv/sow/
├── sow.yml   # configuration; schema: sow/v3
└── .sow/     # SQLite state, locks, staging, recovery, journals
```

Do not edit or serve `.sow/`. `init` is idempotent: rerunning it validates and converges
declared repositories and Dists; it does not reset a valid workspace.

The default architecture families are `x86_64` and `aarch64`. Configuration accepts
`amd64` and `arm64` as aliases and normalizes them to those family names.

## 2. Create a Repository and two Dists

```bash
sow repo new local
sow dist new el9 --format rpm
sow dist new bookworm --format deb
```

A Repository owns one public `pool/ + dists/` tree and one private state database. A Dist
has exactly one format. `dist new` materializes a valid empty view, so empty clients receive
an empty index instead of a 404.

The public layout is now:

```text
/srv/sow/local/
├── pool/
└── dists/
    ├── el9/
    │   ├── x86_64/repodata/
    │   └── aarch64/repodata/
    └── bookworm/
        ├── Release
        └── main/
            ├── binary-amd64/{Packages,Packages.gz,by-hash/}
            └── binary-arm64/{Packages,Packages.gz,by-hash/}
```

## 3. Add packages

Select the target Dist explicitly:

```bash
sow add /path/to/packages/*.rpm -d el9
sow add /path/to/packages/*.deb -d bookworm
```

SOW reads identity and architecture from the package itself, stores accepted bytes under
`local/pool/`, updates Desired Membership, and builds affected Dists before returning.
The package path is only an input; later builds use the managed pool.

Use `--skip` to stage several membership changes without rebuilding each time, then
converge once:

```bash
sow add /path/to/more/*.rpm -d el9 --skip
sow build
```

While Desired Membership is ahead of the Built Generation, the Repository is `dirty` and
`ready_to_copy=false`.

## 4. Inspect and verify

```bash
sow status
sow ls -d el9
sow ls -d bookworm
sow check
```

`status` is a cheap state read. `check` is the delivery gate: it verifies configuration,
retained roots, state, public modes, package bytes, Desired Membership, indexes,
signatures, and the Generation manifest. It writes nothing. Only a clean Repository that
passes all layers returns success.

To see normalized configuration and defaults:

```bash
sow config show --all
```

## 5. Serve the Repository

The public unit is `/srv/sow/local`, not the workspace root. Serve that directory at a
stable URL prefix; do not expose `sow.yml` or `.sow/`.

- DNF base URL: `https://repo.example.com/local/dists/el9/x86_64/`
- APT source: `deb https://repo.example.com/local bookworm main`

For a safe Nginx and filesystem-publication workflow, continue with
[Serve Repositories](/docs/tutorial/serving/).

## Selection rules

- Workspace: search upward from the current directory, or start from `-C DIR`.
- Repository: `-r NAME`, the containing Repository, or the only configured Repository.
- Dist: `-d NAME`, repeatable; omission is accepted only when the command can resolve an
  unambiguous scope.

Ambiguity is an error; SOW does not pick an arbitrary Repository or Dist.

## Next

- [Core Concepts](/docs/start/concepts/)
- [Build a YUM Repository](/docs/tutorial/yum-repo/)
- [Build an APT Repository](/docs/tutorial/apt-repo/)
- [`sow.yml` Reference](/docs/reference/config/)
