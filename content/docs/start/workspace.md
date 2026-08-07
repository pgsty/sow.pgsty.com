---
title: "Your First Workspace"
linkTitle: "First Workspace"
description: "Create a managed workspace with RPM and DEB distributions, add packages, and inspect the result."
url: "/docs/start/workspace/"
weight: 300
icon: fa-solid fa-layer-group
---

This page takes about ten minutes and builds a managed repository from nothing: a
workspace, one repository, an RPM distribution and a DEB distribution inside it, packages
added to both, and a look at what landed on disk. Unlike [plain mode](/docs/start/quickstart/),
a workspace remembers what you asked for — so you add and remove packages by name instead of
by shuffling files around, and SOW rebuilds only what changed.

## 1. Create the workspace

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
```

```console
initialized /srv/sow: config_created=true repositories_initialized=0 dists_initialized=0
```

`init` created two things: `sow.yml`, which is the single source of truth for what this
workspace contains, and a hidden `.sow/` directory holding locks, per-repository SQLite
state, and the operation journal used for crash recovery. You never edit anything under
`.sow/` and you never serve it.

```bash
cat sow.yml
```

```yaml
schema: sow/v2
architectures:
  - x86_64
  - aarch64
```

Two architectures by default. `amd64` and `arm64` are accepted as input aliases and
normalized to `x86_64` and `aarch64` — the canonical family names SOW reports everywhere.

`init` is idempotent. Running it again on an initialized workspace validates what exists
and fills in anything missing, without resetting generations or rewriting bytes.

## 2. Create a repository

```bash
sow repo new pigsty
```

```console
created pigsty: path=/srv/sow/pigsty protected=false dists=0 generation=0 status=clean packages=0 memberships=0
```

A repository is a directory directly under the workspace root, and it owns everything
inside it: its package pool, its published distributions, its own SQLite database, and its
own lock. Two repositories in the same workspace never share package objects — that
isolation is deliberate, so you can delete one without auditing the other.

## 3. Create distributions

A **Dist** is a named set of packages in exactly one format. Give it a name your users will
recognize from the URL, and declare the format up front:

```bash
sow dist new el9 --format rpm -r pigsty
sow dist new trixie --format deb -r pigsty
```

```console
created el9: format=rpm architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=2 dirty=false
```

Both Dists inherit the workspace architecture list, and `sow.yml` now records them:

```yaml
schema: sow/v2
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
```

Empty Dists are already valid repositories. SOW wrote a complete, consumable index tree
for both of them:

```console
pigsty/
├── pool/
└── dists/
    ├── el9/
    │   ├── x86_64/repodata/{repomd.xml, primary, filelists, other}
    │   └── aarch64/repodata/{repomd.xml, primary, filelists, other}
    └── trixie/
        ├── Release
        └── main/
            ├── binary-amd64/{Packages, Packages.gz, by-hash/SHA256/…}
            └── binary-arm64/{Packages, Packages.gz, by-hash/SHA256/…}
```

A client pointed at an empty Dist gets a valid empty package list, not a 404. Note the
naming: RPM views use the canonical family names `x86_64` / `aarch64`, while DEB views use
the Debian ecosystem names `binary-amd64` / `binary-arm64`, because that is what `apt`
expects to fetch.

## 4. Add packages

`sow add` takes file paths. Use `-d` to say which Dist the packages should join:

```bash
sow add pkg/*.rpm -r pigsty -d el9
```

```console
add repository=pigsty operation=6987540345754799180 accepted=4 failed=0 memberships=+4/-0 revision=3 generation=3 dirty=false
item input="pkg/blackbox_exporter-0.28.0-1.aarch64.rpm" status=accepted format=rpm coordinate="blackbox_exporter-0:0.28.0-1.aarch64" sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943 dists=el9:accepted
item input="pkg/blackbox_exporter-0.28.0-1.x86_64.rpm" status=accepted format=rpm coordinate="blackbox_exporter-0:0.28.0-1.x86_64" sha256:5759c643a789631346e3ed315a696a0118f81f7cc3c65e5a4385a876983d3a18 dists=el9:accepted
item input="pkg/pev2-1.23.0-1.noarch.rpm" status=accepted format=rpm coordinate="pev2-0:1.23.0-1.noarch" sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229 dists=el9:accepted
item input="pkg/pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm" status=accepted format=rpm coordinate="pgbouncer-0:1.25.2-43PGDG.rhel9.8.x86_64" sha256:057b821ad82ca49a693aa97ba50c1fc96925b0a58de626f014e07a0c78700e1a dists=el9:accepted
```

Then the DEB side:

```bash
sow add pkg/*.deb -r pigsty -d trixie
```

```console
add repository=pigsty operation=7610015278010066624 accepted=3 failed=0 memberships=+3/-0 revision=4 generation=4 dirty=false
item input="pkg/libpq5_18.3-1.pgdg12+1_amd64.deb" status=accepted format=deb coordinate="libpq5=18.3-1.pgdg12+1:amd64" sha256:4b5262231787caf1f367f5c8705a8a03d3176c31a15e6096946d50514db128be dists=trixie:accepted
item input="pkg/libpq5_18.3-1.pgdg12+1_arm64.deb" status=accepted format=deb coordinate="libpq5=18.3-1.pgdg12+1:arm64" sha256:cadeb9294901ac5ae6228bd3471c444cc288d9894af0dd0730909596d9dfcefb dists=trixie:accepted
item input="pkg/pev2_1.23.0_all.deb" status=accepted format=deb coordinate="pev2=1.23.0:all" sha256:11e05aa5bf0e049097ab885ab61e41d8c72094a8e912cab613d9bb1719bb6bf9 dists=trixie:accepted
```

Read the per-item lines. Each one reports the logical **coordinate** SOW derived from the
package itself — NEVRA for RPM, `name=version:arch` for DEB — and the SHA-256 of the exact
bytes. Coordinates come from the RPM header and the Debian control file, never from the
filename, so a renamed package is still indexed as what it actually is.

`dirty=false` on the summary line means the published tree was rebuilt before the command
returned. By default `add` builds; pass `--skip` if you would rather batch several changes
and run `sow build` once at the end.

Adding the same package again reports `status=reused` and does not advance the generation.
Adding a package that is already an object but belongs to a different Dist reuses the same
bytes and records a second membership.

## 5. Look at the pool

Every accepted package is stored once, under the repository's `pool/`:

```console
pigsty/pool/
├── b/blackbox_exporter/
│   ├── blackbox_exporter-0.28.0-1.aarch64.rpm
│   └── blackbox_exporter-0.28.0-1.x86_64.rpm
└── p/
    ├── pev2/
    │   ├── pev2-1.23.0-1.noarch.rpm
    │   └── pev2_1.23.0_all.deb
    ├── pgbouncer/
    │   └── pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
    └── postgresql-18/
        ├── libpq5_18.3-1.pgdg12+1_amd64.deb
        └── libpq5_18.3-1.pgdg12+1_arm64.deb
```

The grouping is Debian's: first letter, then source package. `libpq5` sits under
`p/postgresql-18/` because that is the `Source` field in its control file, which is exactly
where `reprepro` would put it. RPMs group by package name.

Pool contents are immutable. Removing a package from a Dist removes its *membership*; the
bytes stay in the pool, so re-adding it later costs nothing.

## 6. Look at the published tree

```console
pigsty/dists/
├── el9/
│   ├── x86_64/
│   │   ├── pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│   │   ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm
│   │   ├── pool/p/pgbouncer/pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
│   │   └── repodata/{repomd.xml, …}
│   └── aarch64/
│       ├── pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
│       ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm
│       └── repodata/{repomd.xml, …}
└── trixie/
    ├── Release
    └── main/
        ├── binary-amd64/{Packages, Packages.gz, by-hash/SHA256/…}
        └── binary-arm64/{Packages, Packages.gz, by-hash/SHA256/…}
```

Each RPM architecture view contains its native packages plus the `noarch` ones — `pev2`
appears in both. Those view files are hardlinks to the root pool, not copies, so the
`noarch` package has a link count of three (root pool plus two views) and occupies disk
space once:

```bash
stat -c '%h %n' pigsty/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

```console
3 pigsty/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

This is why `pool/` and `dists/` must share a filesystem. It also means package locations
in `repodata` are plain relative paths like `pool/p/pev2/…` with no `..` escaping the view
root, which is what lets `dnf reposync` mirror the repository correctly.

The DEB side does not need view directories: `Packages` carries a `Filename:` field
pointing at the repository pool directly.

```console
Filename: pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
```

`Release` lists a SHA-256 for every index file and advertises `Acquire-By-Hash: yes`, so
`apt` fetches indexes from the `by-hash/SHA256/` directory and never trips over an index
that changed mid-download:

```console
Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:06:41 UTC
X-SOW-Generation: 4
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 b7a9ab7d083b89342a9895963814be117d6a387f73f7305b0d6dc47d7718eb07 1483 main/binary-amd64/Packages
 668058912c3cb51fed9074063de1a0233514c8340a2fe90136ad3f4670a06db4 828 main/binary-amd64/Packages.gz
 7b2a1c5dd08eaeb02540d6b7eeef454311179a86347a0e3900114b28a6b9dcde 1483 main/binary-arm64/Packages
 25191436907e80a72594e642408b5cea3e68bc1b979df5b7cd556d9e36296402 827 main/binary-arm64/Packages.gz
```

## 7. Check the state

`sow status` is the cheap read. It never hashes the tree, never repairs anything, and
never builds:

```bash
sow status
```

```console
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4 dirty_dists= pending=0/0 locked=false
```

`ready_to_copy=true` is the signal you want before an `rsync`: the published tree is
complete and internally consistent, so copying it now yields a working repository.

`sow check` is the expensive read — a full eight-layer proof that walks configuration,
database schema, package bytes, memberships, indexes, signatures, and the generation
manifest:

```bash
sow check
```

```console
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=72
package-bytes	ok=true	checked=7
desired-membership	ok=true	checked=7
index	ok=true	checked=2
signature	ok=true	checked=11
generation-manifest	ok=true	checked=4
```

That run took 0.15 seconds on this repository. `check` verifies; it never repairs. If it
finds the repository dirty or damaged it says so and exits non-zero — see
[Exit Codes](/docs/reference/exit-codes/).

Two more quick views:

```bash
sow repo ls
sow dist ls
```

```console
NAME	PROTECTED	DISTS	GENERATION	STATUS	PACKAGES	MEMBERSHIPS
pigsty	false	2	4	clean	7	7

NAME	FORMAT	ARCHITECTURES	DESIRED	BUILT	GENERATION	DIRTY	DIRTY_REASONS
el9	rpm	x86_64,aarch64	4	4	3	false	[]
trixie	deb	x86_64,aarch64	3	3	4	false	[]
```

And the package list for one Dist:

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:5759c643a789631346e3ed315a696a0118f81f7cc3c65e5a4385a876983d3a18	rpm:blackbox_exporter-0:0.28.0-1.x86_64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229	rpm:pev2-0:1.23.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.23.0-1.noarch.rpm
sha256:057b821ad82ca49a693aa97ba50c1fc96925b0a58de626f014e07a0c78700e1a	rpm:pgbouncer-0:1.25.2-43PGDG.rhel9.8.x86_64	el9	el9	pool/p/pgbouncer/pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
```

## Selecting what to operate on

Most commands need to know which workspace, repository, and Dist you mean. The rules are
short:

- **Workspace** — commands search upward from the current directory. `-C DIR` searches
  upward from `DIR` instead, and fails rather than falling back to the current directory.
- **Repository** — `-r NAME`, or the repository containing the current directory, or the
  only repository if there is exactly one.
- **Dist** — `-d NAME`, repeatable. Omit it only when the choice is unambiguous.

When SOW cannot infer a choice, it refuses instead of guessing:

```bash
sow ls
```

```console
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

## Serving it

Point your web server at the repository directory — `/srv/sow/pigsty` here — and the URLs
fall out of the layout:

- `http://host/pigsty/dists/el9/x86_64/` as a `dnf` `baseurl`
- `deb http://host/pigsty trixie main` as an `apt` source

Do not expose the workspace root: `sow.yml` and `.sow/` are private state.
[Serve Repositories](/docs/tutorial/serving/) has a complete Nginx configuration.

## Next steps

- [Core Concepts](/docs/start/concepts/) — Desired vs Built, generations, and when a Dist goes dirty.
- [Build a YUM Repository](/docs/tutorial/yum-repo/) and [Build an APT Repository](/docs/tutorial/apt-repo/) — production walkthroughs with client configuration.
- [Sign Your Repository](/docs/tutorial/signing/) — GPG for metadata and package payloads.
- [Membership Policy](/docs/feature/policy/) — keep only the newest N versions, exclude by pattern.
- [`sow.yml` Reference](/docs/reference/config/) — every configuration field.
