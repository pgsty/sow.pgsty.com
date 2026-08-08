---
title: "Build a YUM Repository"
linkTitle: "Build a YUM Repository"
description: "Create a managed RPM repository with per-architecture views, noise filtering, and a working dnf client configuration."
url: "/docs/tutorial/yum-repo/"
weight: 100
icon: fa-solid fa-box-open
---

This tutorial builds a production-shaped RPM repository from scratch. By the end you will have a
workspace holding a `pigsty` repository with an `el9` Dist, two architecture views rendered from
one package pool, debuginfo noise filtered out, only the newest version of each package kept,
and a `.repo` file that `dnf` accepts.

Plan for about fifteen minutes. Every command runs locally; nothing talks to the network.

## Before you start

You need three things.

**SOW on your PATH.** Check it:

```bash
sow version
```

```console
sow 0.2.0 darwin/arm64 go1.26.5
```

If that fails, see [Installation](/docs/start/install/).

**Some RPM files.** Anything works — packages you built, packages you downloaded, or a directory
you already ship. This tutorial uses nine RPMs spanning `x86_64`, `aarch64`, and `noarch`,
including two versions of `etcd` and a pair of debuginfo packages, because those are the cases
that make the interesting behaviour visible.

**A directory you can write to.** The workspace holds everything; nothing is written outside it.

{{% alert title="Plain mode is simpler" color="info" %}}
If you only need to index one directory of RPMs in place, you do not need any of this. Run
`sow create /path/to/dir` and you are done — see [Quick Start](/docs/start/quickstart/). Managed
mode is what you want when the repository has a lifecycle: multiple architectures, membership
rules, signing, auditing, incremental delivery.
{{% /alert %}}

## Step 1: Create the workspace

A workspace is one directory containing `sow.yml` plus the state directory `.sow/`. Everything
else lives under it.

```bash
mkdir -p ~/repo && cd ~/repo
sow init .
```

```console
initialized /home/you/repo: config_created=true repositories_initialized=0 dists_initialized=0
```

`sow init` wrote a minimal `sow.yml`:

```yaml
schema: sow/v3
architectures:
  - x86_64
  - aarch64
```

Those two architectures are the permitted set for the whole workspace. A package whose native
architecture is not listed is rejected rather than silently widening your configuration.

`sow init` is idempotent. Running it again on the same directory converges rather than failing,
so it is safe in provisioning scripts.

## Step 2: Create the repository

A Repository owns a package pool, a set of Dists, and its own SQLite state. It is also the
boundary for locking, transactions, and generations.

```bash
sow repo new pigsty
```

```console
created pigsty: path=/home/you/repo/pigsty protected=false dists=0 generation=0 status=clean packages=0 memberships=0
```

You now have `~/repo/pigsty/`, which is the directory you will eventually serve over HTTP. The
internal state lives in `~/repo/.sow/`, one level up — it never ends up inside anything you
publish.

## Step 3: Create the RPM Dist

A Dist is a named, single-format set of packages. Create one for Enterprise Linux 9:

```bash
sow dist new el9 --format rpm -r pigsty
```

```console
created el9: format=rpm architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
```

The Dist inherited both workspace architectures. Look at what it produced:

```bash
find pigsty -type f | sort
```

```console
pigsty/dists/el9/aarch64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz
pigsty/dists/el9/aarch64/repodata/8402c28c7c848d02a6ef5c728a8741a2d402792bf9dc4a62ec0657912f4c1719-filelists.xml.gz
pigsty/dists/el9/aarch64/repodata/c16c7739903ecd19f56b49c14f11710643f6de391d13646c22ce95c6910d6106-other.xml.gz
pigsty/dists/el9/aarch64/repodata/repomd.xml
pigsty/dists/el9/x86_64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz
pigsty/dists/el9/x86_64/repodata/8402c28c7c848d02a6ef5c728a8741a2d402792bf9dc4a62ec0657912f4c1719-filelists.xml.gz
pigsty/dists/el9/x86_64/repodata/c16c7739903ecd19f56b49c14f11710643f6de391d13646c22ce95c6910d6106-other.xml.gz
pigsty/dists/el9/x86_64/repodata/repomd.xml
```

An empty Dist is already a valid repository. Each architecture view has complete `repodata` that
`dnf makecache` will accept — clients do not have to wait for your first package. Metadata files
are named by their own SHA-256, and `repomd.xml` is the only pointer.

## Step 4: Add packages

Point `sow add` at a file, several files, or a directory. Directories are scanned at the top
level only; pass `-R` to recurse.

```bash
sow add ~/packages/rpm -d el9
```

```console
add repository=pigsty operation=4475889911918567992 accepted=9 failed=0 memberships=+9/-0 revision=2 generation=2 dirty=false
item input="/home/you/packages/rpm/armadillo-10.8.2-3.el9.x86_64.rpm" status=accepted format=rpm coordinate="armadillo-0:10.8.2-3.el9.x86_64" sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2 dists=el9:accepted
item input="/home/you/packages/rpm/blackbox_exporter-0.28.0-1.aarch64.rpm" status=accepted format=rpm coordinate="blackbox_exporter-0:0.28.0-1.aarch64" sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-3.5.12-1.el8.x86_64.rpm" status=accepted format=rpm coordinate="etcd-0:3.5.12-1.el8.x86_64" sha256:bc795bdd732112c36eecffa1e6f94f6c093f5deca56d71d0026ec61e89893f91 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-3.5.30-1.el9.x86_64.rpm" status=accepted format=rpm coordinate="etcd-0:3.5.30-1.el9.x86_64" sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a dists=el9:accepted
item input="/home/you/packages/rpm/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm" status=accepted format=rpm coordinate="etcd-debuginfo-0:3.3.11-4.el8.x86_64" sha256:3dcee7ab93e67cf5ec4cd6a2dff2c1e4f8d189cc1751654d2fb75503cee96475 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-debugsource-3.3.11-4.el8.x86_64.rpm" status=accepted format=rpm coordinate="etcd-debugsource-0:3.3.11-4.el8.x86_64" sha256:f6020dbfd40c3d68c3dc1adefbfd39f304944c7c8268c4e206139ca589d02110 dists=el9:accepted
item input="/home/you/packages/rpm/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm" status=accepted format=rpm coordinate="patroni-0:4.1.4-1PGDG.rhel9.6.noarch" sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6 dists=el9:accepted
item input="/home/you/packages/rpm/pev2-1.22.0-1.noarch.rpm" status=accepted format=rpm coordinate="pev2-0:1.22.0-1.noarch" sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b dists=el9:accepted
item input="/home/you/packages/rpm/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm" status=accepted format=rpm coordinate="pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64" sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607 dists=el9:accepted
```

Several things happened in that one command, all inside a single transaction.

The format and architecture came from the RPM header, not the filename. A binary RPM renamed to
`*.src.rpm` is still indexed by its real architecture; a package whose header says `src` is
rejected outright.

Each package got a **coordinate** — its NEVRA, like `etcd-0:3.5.30-1.el9.x86_64` — and a
SHA-256 that identifies the exact bytes. Both are printed so you can copy them into later
commands without hand-assembling anything.

`add` built the public tree before returning. `dirty=false` and `generation=2` mean the
repository on disk is complete right now. That is the default; you can defer the build with
`--skip`, which we use in Step 7.

Confirm:

```bash
sow status
```

```console
repository=pigsty status=clean ready_to_copy=true revision=2 generation=2 dirty_dists= pending=0/0 locked=false
```

`ready_to_copy=true` is the field to script against. It means the `pool/` and `dists/`
directories are a coherent set you can rsync as-is.

## Step 5: Read the layout

Two structures came out of that add. Look at the pool first:

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2	rpm:armadillo-0:10.8.2-3.el9.x86_64	el9	el9	pool/a/armadillo/armadillo-10.8.2-3.el9.x86_64.rpm
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:bc795bdd732112c36eecffa1e6f94f6c093f5deca56d71d0026ec61e89893f91	rpm:etcd-0:3.5.12-1.el8.x86_64	el9	el9	pool/e/etcd/etcd-3.5.12-1.el8.x86_64.rpm
sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a	rpm:etcd-0:3.5.30-1.el9.x86_64	el9	el9	pool/e/etcd/etcd-3.5.30-1.el9.x86_64.rpm
sha256:3dcee7ab93e67cf5ec4cd6a2dff2c1e4f8d189cc1751654d2fb75503cee96475	rpm:etcd-debuginfo-0:3.3.11-4.el8.x86_64	el9	el9	pool/e/etcd/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm
sha256:f6020dbfd40c3d68c3dc1adefbfd39f304944c7c8268c4e206139ca589d02110	rpm:etcd-debugsource-0:3.3.11-4.el8.x86_64	el9	el9	pool/e/etcd/etcd-debugsource-3.3.11-4.el8.x86_64.rpm
sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6	rpm:patroni-0:4.1.4-1PGDG.rhel9.6.noarch	el9	el9	pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm
sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b	rpm:pev2-0:1.22.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.22.0-1.noarch.rpm
sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607	rpm:pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64	el9	el9	pool/p/pgbouncer/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm
```

The pool path is `pool/<prefix>/<source>/<filename>`. For RPMs the source comes from the
`SOURCERPM` header, so `etcd-debuginfo` and `etcd-debugsource` sit next to `etcd` in
`pool/e/etcd/`. The pool is flat with respect to Dists: one object, one location, however many
Dists reference it.

### Metadata-only architecture views

Each Dist renders one metadata view per architecture. `x86_64` metadata contains native
`x86_64` packages plus `noarch`; `aarch64` contains native `aarch64` plus `noarch`.
There are no RPM files beneath `dists/`:

```bash
find pigsty/dists/el9 -type f | sort
```

```console
pigsty/dists/el9/aarch64/repodata/<sha256>-filelists.xml.gz
pigsty/dists/el9/aarch64/repodata/<sha256>-other.xml.gz
pigsty/dists/el9/aarch64/repodata/<sha256>-primary.xml.gz
pigsty/dists/el9/aarch64/repodata/repomd.xml
pigsty/dists/el9/x86_64/repodata/<sha256>-filelists.xml.gz
pigsty/dists/el9/x86_64/repodata/<sha256>-other.xml.gz
pigsty/dists/el9/x86_64/repodata/<sha256>-primary.xml.gz
pigsty/dists/el9/x86_64/repodata/repomd.xml
```

The shipped layout points every package back to the one canonical pool:

```bash
gzip -dc pigsty/dists/el9/x86_64/repodata/*-primary.xml.gz | grep -o '<location href="[^"]*"'
```

```console
<location href="../../../pool/a/armadillo/armadillo-10.8.2-3.el9.x86_64.rpm"
<location href="../../../pool/e/etcd/etcd-3.5.30-1.el9.x86_64.rpm"
<location href="../../../pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm"
```

Ordinary `dnf makecache`, `repoquery`, `download`, and `install` resolve these paths.
Default `dnf reposync` does not: its safe-write check refuses a target above its leaf
download root. Create a self-contained compatibility artifact when needed:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

That export receives a local `pool/`, rewritten metadata, a manifest, and a
`.sow-export.json` completion marker. It does not change the canonical repository.

## Step 6: Filter the noise

Right now the repository ships debuginfo packages and two versions of `etcd`. Both are usually
wrong for a delivery repository. Membership policy lives in `sow.yml`, not on the command line,
so the rules are reviewable and reproducible.

Edit `~/repo/sow.yml`:

```yaml
schema: sow/v3
architectures:
  - x86_64
  - aarch64

repos:
  pigsty:
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource]
```

`limit: 1` keeps the newest version of each `(name, native architecture)` pair, compared with
RPM's own EVR rules. `exclude` drops packages by classification; `kind` is derived from the
binary name suffix, so `-debuginfo` and `-debugsource` are recognized without you writing globs.

Validate before you touch the tree:

```bash
sow config check
```

```console
configuration valid: /home/you/repo repositories=1 dists=1
```

The configuration is valid, but the built tree no longer matches it:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=2 generation=2 dirty_dists=el9 pending=0/0 locked=false
```

`dirty` means the desired state moved ahead of what is on disk. The old tree is still complete
and still serves correctly — clients see the previous generation until you converge.

```bash
sow build
```

```console
{"operation":"2673156477918637099","repository":"pigsty","dists":["el9"],"desired_revision":3,"built_generation":3,"noop":false,"dirty":false}
```

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2	rpm:armadillo-0:10.8.2-3.el9.x86_64	el9	el9	pool/a/armadillo/armadillo-10.8.2-3.el9.x86_64.rpm
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a	rpm:etcd-0:3.5.30-1.el9.x86_64	el9	el9	pool/e/etcd/etcd-3.5.30-1.el9.x86_64.rpm
sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6	rpm:patroni-0:4.1.4-1PGDG.rhel9.6.noarch	el9	el9	pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm
sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b	rpm:pev2-0:1.22.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.22.0-1.noarch.rpm
sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607	rpm:pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64	el9	el9	pool/p/pgbouncer/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm
```

Six members instead of nine. The two debuginfo packages and the older `etcd` are gone from the
indexes. Their bytes stay in `pool/` — SOW removes membership, not payload — so nothing is
destroyed by a policy change you might want to reverse.

Now re-run the same `add` and watch how policy reports itself:

```bash
sow add ~/packages/rpm -d el9
```

```console
add repository=pigsty operation=3213883523634766313 accepted=6 failed=0 memberships=+0/-0 revision=3 generation=3 dirty=false
item input="/home/you/packages/rpm/armadillo-10.8.2-3.el9.x86_64.rpm" status=reused format=rpm coordinate="armadillo-0:10.8.2-3.el9.x86_64" sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2 dists=el9:accepted
item input="/home/you/packages/rpm/blackbox_exporter-0.28.0-1.aarch64.rpm" status=reused format=rpm coordinate="blackbox_exporter-0:0.28.0-1.aarch64" sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-3.5.12-1.el8.x86_64.rpm" status=excluded format=rpm coordinate="etcd-0:3.5.12-1.el8.x86_64" sha256:bc795bdd732112c36eecffa1e6f94f6c093f5deca56d71d0026ec61e89893f91 dists=el9:limited
item input="/home/you/packages/rpm/etcd-3.5.30-1.el9.x86_64.rpm" status=reused format=rpm coordinate="etcd-0:3.5.30-1.el9.x86_64" sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a dists=el9:accepted
item input="/home/you/packages/rpm/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm" status=excluded format=rpm coordinate="etcd-debuginfo-0:3.3.11-4.el8.x86_64" sha256:3dcee7ab93e67cf5ec4cd6a2dff2c1e4f8d189cc1751654d2fb75503cee96475 dists=el9:excluded
item input="/home/you/packages/rpm/etcd-debugsource-3.3.11-4.el8.x86_64.rpm" status=excluded format=rpm coordinate="etcd-debugsource-0:3.3.11-4.el8.x86_64" sha256:f6020dbfd40c3d68c3dc1adefbfd39f304944c7c8268c4e206139ca589d02110 dists=el9:excluded
item input="/home/you/packages/rpm/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm" status=reused format=rpm coordinate="patroni-0:4.1.4-1PGDG.rhel9.6.noarch" sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6 dists=el9:accepted
item input="/home/you/packages/rpm/pev2-1.22.0-1.noarch.rpm" status=reused format=rpm coordinate="pev2-0:1.22.0-1.noarch" sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b dists=el9:accepted
item input="/home/you/packages/rpm/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm" status=reused format=rpm coordinate="pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64" sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607 dists=el9:accepted
```

Nothing changed: `memberships=+0/-0`, `generation=3` unchanged. Re-adding the same package is a
stable no-op, which is what you want from a nightly job. Per-package outcomes are explicit:
`reused` for bytes already present, `excluded` for a rule hit, and per-Dist `limited` for a
version pushed out by `limit`.

{{% alert title="Policy does not resurrect" color="warning" %}}
Relaxing a rule later does not bring old members back. Raising `limit` or deleting an `exclude`
entry stops future removals, but the packages already dropped must be re-added explicitly. This
is deliberate: SOW never guesses which historical bytes you meant to publish.
{{% /alert %}}

## Step 7: Batch changes without republishing

`add` and `rm` build by default. When you are staging a large batch, defer the build with
`--skip` and converge once at the end.

```bash
sow add ~/packages/gdal311-3.11.0-2.rhel9.x86_64.rpm -d el9 --skip
```

```console
add repository=pigsty operation=7821893517298386853 accepted=1 failed=0 memberships=+1/-0 revision=4 generation=3 dirty=true
item input="/home/you/packages/gdal311-3.11.0-2.rhel9.x86_64.rpm" status=accepted format=rpm coordinate="gdal311-0:3.11.0-2.rhel9.x86_64" sha256:9d245f1e2c5e44543e834f2cbff4d57a11938cb3040577cbb0f12edb0fa1baeb dists=el9:accepted
```

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=el9 pending=1/497416 locked=false
```

The new package is durably stored in a private pending area (`pending=1/497416` — one object,
497 KB). The public tree has not changed by a single byte; clients still see generation 3.

`sow check` is the gate that refuses to let you publish a half-staged tree:

```bash
sow check
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=4 generation=3
config	ok=true	checked=3
state	ok=true	checked=1
public-modes	ok=true	checked=64
package-bytes	ok=true	checked=10
desired-membership	ok=true	checked=7
index	ok=true	checked=1
signature	ok=true	checked=18
generation-manifest	ok=true	checked=3
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

Exit code `5`. Every layer verified clean — nothing is broken — but the tree is not deliverable
because the desired state is ahead of it. Converge:

```bash
sow build -d el9
sow status
```

```console
{"operation":"8823464502290701703","repository":"pigsty","dists":["el9"],"desired_revision":4,"built_generation":4,"noop":false,"dirty":false}
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4 dirty_dists= pending=0/0 locked=false
```

## Step 8: Configure the dnf client

Publish `~/repo/pigsty/` over HTTP — see [Serve Repositories](/docs/tutorial/serving/) for a
tested Nginx configuration. Assume it is reachable at `https://repo.example.com/pigsty/`.

The repository URL is the architecture view: `dists/<dist>/$basearch`. On Enterprise Linux
`$basearch` expands to exactly `x86_64` or `aarch64`, which is why the RPM views use those
names — one `.repo` file covers both architectures.

Write `/etc/yum.repos.d/pigsty.repo`:

{{< tabpane persist="header" >}}
{{< tab header="EL8 / EL9 / EL10" lang="ini" >}}
[pigsty-el9]
name=Pigsty EL9 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch
enabled=1
gpgcheck=0
repo_gpgcheck=0
metadata_expire=300
{{< /tab >}}
{{< tab header="EL8 / EL9 / EL10 (signed)" lang="ini" >}}
[pigsty-el9]
name=Pigsty EL9 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
metadata_expire=300
{{< /tab >}}
{{< tab header="CentOS 7 (yum)" lang="ini" >}}
[pigsty-el7]
name=Pigsty EL7 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el7/$basearch
enabled=1
gpgcheck=0
repo_gpgcheck=0
{{< /tab >}}
{{< /tabpane >}}

The first tab is what works right now, because you have not signed anything yet. Use it to get
the plumbing right, then switch to the second tab after following
[Sign Your Repository](/docs/tutorial/signing/) — that tutorial covers generating the key,
publishing `RPM-GPG-KEY-pigsty`, and what `gpgcheck` and `repo_gpgcheck` each verify.

`metadata_expire=300` is a convenience while you iterate. Raise it once the repository settles.

## Step 9: Verify from a client

```bash
dnf clean all
dnf makecache
dnf repoquery --repo=pigsty-el9 --queryformat '%{name}-%{evr}.%{arch}'
dnf install -y pev2
```

`makecache` fetching `repomd.xml` and the three checksum-named files means the metadata is
well-formed. `repoquery` returning your package list means `primary.xml.gz` parsed correctly.
`install` succeeding means the `location href` values resolved.

This configuration has been verified against AlmaLinux 8, 9, and 10 with dnf4, and against
CentOS 7 with yum 3.4.3, which parses multi-version NEVRA lists correctly. The full matrix is in
[Compatibility](/docs/reference/compatibility/).

### Build a reposync-compatible leaf

Do not point default `dnf reposync` at the canonical metadata-only view. Export a leaf,
serve or copy that directory, and verify it independently:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
find /srv/export/el9-x86_64 -maxdepth 2 -type d | sort
```

The exported `repodata/` uses local `pool/...` hrefs and is intended specifically for
tools that require a self-contained repository root.

## Where to go next

{{< doc-cards cols="2" >}}
{{< doc-card title="Build an APT Repository" link="/docs/tutorial/apt-repo/" >}}
Add a DEB Dist to the same repository. One pool, two ecosystems.
{{< /doc-card >}}
{{< doc-card title="Sign Your Repository" link="/docs/tutorial/signing/" >}}
Turn on `gpgcheck` and `repo_gpgcheck` for real.
{{< /doc-card >}}
{{< doc-card title="Serve Repositories" link="/docs/tutorial/serving/" >}}
A tested Nginx configuration and an offline copy procedure.
{{< /doc-card >}}
{{< doc-card title="Membership Policy" link="/docs/feature/policy/" >}}
Every `exclude` field, the `kind` enumeration, and how `limit` compares versions.
{{< /doc-card >}}
{{< /doc-cards >}}

For command syntax and exit codes, see [CLI Commands](/docs/reference/cli/) and
[Exit Codes](/docs/reference/exit-codes/). For the complete directory tree including the
internals under `.sow/`, see [Repository Layout](/docs/reference/layout/).
