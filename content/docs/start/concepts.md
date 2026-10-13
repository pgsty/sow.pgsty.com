---
title: "Core Concepts"
linkTitle: "Core Concepts"
description: "The SOW model: Plain and Managed execution, pools and views, Desired Membership, and Built Generations."
categories: [Start]
tags: [plain, managed, repository, dist]
url: "/docs/start/concepts/"
weight: 400
icon: fa-solid fa-diagram-project
---

<span id="choose-a-mode"></span>

## Choose a mode {#plain-or-managed}

| Need | Plain | Managed |
|---|---|---|
| Build indexes from a package directory | `sow create DIR` | Import packages with `sow add` |
| Keep configuration and package membership | Directory contents are the state | `sow.yml` and private SQLite databases |
| Organize packages | One flat directory; RPM and DEB can coexist | Named Dists; one format per Dist |
| Publish architecture views | No | Yes |
| Apply filters and version limits | Pigsty conventions with `--pigsty` | Configurable per Dist |
| Sign RPM packages | Yes | Yes |
| Sign repository metadata | Sign separately | Configure keys in `sow.yml` |
| Track generations and publication | Manage these outside SOW | Built in |

Use Plain when the directory already contains the packages you want to publish. Use Managed when SOW should track membership and maintain the repository over time.

<span id="workspace-repository-and-dist"></span>

## Workspace, Repository, and Dist {#managed-hierarchy}

```text
Workspace                    /srv/sow
├── sow.yml                  configuration
├── .sow/                    private state
└── Repository               /srv/sow/local
    ├── pool/                package files
    └── dists/
        └── Dist             a named RPM or DEB package set
            └── views        metadata for each architecture
```

A **workspace** holds configuration and private state for one or more repositories.

A **Repository** owns a package pool, Dists, build history, and publication targets. Serve its complete `pool/` and `dists/` tree. Keep `sow.yml` and `.sow/` outside the HTTP document root.

A **Dist** selects packages of one format. For example, `el9` can contain RPMs and `bookworm` can contain DEBs. You choose the names; SOW does not check whether a package is compatible with the operating system named by its Dist.

An **architecture view** contains metadata for one architecture. SOW includes neutral RPM `noarch` and DEB `all` packages in each applicable view.

<span id="store-each-package-once"></span>

## Store each package once {#one-canonical-payload}

SOW identifies a **package object** by the SHA-256 of the complete package file. It reads the package name, version, and architecture from package metadata.

Within a Repository, each accepted package has one path under `pool/`. Multiple Dists can refer to that path. Separate repositories have separate pools.

RPM metadata uses relative paths back to the pool. APT `Packages` entries use paths relative to the Repository root. Keep the complete Repository tree together when you serve or copy it.

Some mirror tools, including default `dnf reposync`, reject the parent-relative RPM paths. Use [`sow export rpm-leaf`](/docs/command/export/) to create a standalone RPM repository for those tools.

<span id="desired-membership-and-built-generations"></span>

## Desired membership and built generations {#desired-and-built}

**Desired membership** is the package set selected for each Dist. A **Generation** identifies
a completed build and its file manifest. **Built Generation** is the current completed
build. Package files stay in the shared pool; each build does not create another copy.

```text
add / rm → Desired membership → build → Built Generation
```

`add` and `rm` normally update membership and build the affected Dists in one command. With `--skip`, they update membership only. Run `sow build` after a batch of skipped changes, or after changing build or signing configuration.

| Command | Use |
|---|---|
| `sow status` | Read the current state and `ready_to_copy` value |
| `sow check` | Check package files, indexes, signatures, and recorded state without changing them |
| `sow changes [BASE_GENERATION]` | List file changes from a recorded generation to the current build |
| `sow publish TARGET` | Check and publish the current build to a configured target |

<span id="understand-repository-state"></span>

## Understand repository state {#transactions-and-failure-states}

| State | Meaning | Next action |
|---|---|---|
| `clean` | Membership and configuration match the built output | Ready for `check` or publication |
| `dirty` | Membership or configuration needs a build | Run `build`, then `check` |
| `recovering` | An interrupted operation needs recovery | Follow the error and [recovery steps](/docs/reference/troubleshooting/#a-command-was-interrupted) |
| `error` | Stored state or files conflict | Inspect the reported error and operation log |

Use [`sow log`](/docs/command/log/) to inspect failed or interrupted operations.

## Continue

- [Managed Workspaces](/docs/feature/managed/)
- [Pool & Architecture Views](/docs/feature/views/)
- [Transactions & Recovery](/docs/feature/transactions/)
- [Publication & Recovery](/blog/design/publication/)
