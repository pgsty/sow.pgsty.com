---
title: "Your First Workspace"
linkTitle: "First Workspace"
description: "Create a workspace, organize RPM and DEB packages, and check the repository."
categories: [Start]
tags: [managed, repository, dist, generation]
url: "/docs/start/workspace/"
weight: 300
icon: fa-solid fa-layer-group
---

This example creates a Managed repository with two named package sets, called Dists:
`el9` for RPMs and `bookworm` for DEBs. Use an empty, writable `/srv/sow` directory, or
substitute another path.

{{% steps %}}

## Initialize the workspace {#1-initialize-the-workspace}

```bash
sow init /srv/sow
cd /srv/sow
```

`init` creates:

```text
/srv/sow/
├── sow.yml   # configuration; schema: sow/v3
└── .sow/     # private state managed by SOW
```

Edit `sow.yml` when you need to change configuration. SOW manages the private `.sow/`
directory. You can repeat `init` without resetting existing packages or state.

## Create a Repository and two Dists {#2-create-a-repository-and-two-dists}

```bash
sow repo new local
sow dist new el9 --format rpm
sow dist new bookworm --format deb
```

Each Dist has one package format. `dist new` creates empty indexes for `x86_64` and
`aarch64` by default. Both Dists share the Repository's `pool/` directory.

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

## Add packages {#3-add-packages}

Select the target Dist explicitly:

```bash
sow add /path/to/packages/*.rpm -d el9
sow add /path/to/packages/*.deb -d bookworm
```

Replace the input paths with real package files. SOW reads package identity and architecture, stores each accepted file in `local/pool/`, updates membership, and builds the affected Dists. Later builds use the pool, so the original input files are no longer needed by SOW.

## Inspect and verify {#4-inspect-and-verify}

```bash
sow status
sow ls -d el9
sow ls -d bookworm
sow check
```

`ls` lists the packages in each Dist. `status` should report `clean` and
`ready_to_copy=true`. A successful `check` confirms that the files match the recorded build.

## Serve the Repository {#5-serve-the-repository}

Publish the complete `/srv/sow/local` directory so clients can reach both indexes and package files. Keep the workspace configuration and `.sow/` outside the server root.

Follow [Serve Repositories](/docs/tutorial/serving/) to publish with Nginx. The [YUM](/docs/tutorial/yum-repo/) and [APT](/docs/tutorial/apt-repo/) tutorials show client configuration, including the trust settings for unsigned repositories.

{{% /steps %}}

## Batch later updates

When you need to add several batches, use `--skip` and build once at the end:

```bash
sow add /path/to/more/*.rpm -d el9 --skip
sow build
```

While membership changes await a build, `sow status` reports `dirty` and `ready_to_copy=false`.


## Selection rules

The commands above find the workspace from the current directory and select its only
Repository. From another directory, use `-C /srv/sow`. With multiple Repositories, add
`-r local`. Use `-d NAME` to select a Dist; repeat it to select several.

See [selection rules](/docs/command/#repository-selection) for discovery and defaults.

## Next

- [Core Concepts](/docs/start/concepts/)
- [Build a YUM Repository](/docs/tutorial/yum-repo/)
- [Build an APT Repository](/docs/tutorial/apt-repo/)
- [`sow.yml` Reference](/docs/reference/config/)
