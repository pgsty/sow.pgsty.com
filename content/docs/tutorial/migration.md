---
title: "Migrate from createrepo_c / reprepro"
linkTitle: "Migrate from createrepo_c / reprepro"
description: "Take over an existing repository in place or move a reprepro archive into a workspace, with a real side-by-side of what changes."
url: "/docs/tutorial/migration/"
weight: 500
icon: fa-solid fa-right-left
---

You already have a repository. This tutorial replaces the tool that builds it without breaking
the clients that consume it — including the leftover files nobody warns you about and the layout
differences you should know before, not after.

Two paths, depending on what you have. Read the one that matches, then the comparison at the end.

## Choose your target

| You have | Migrate to | Read |
|---|---|---|
| `createrepo_c` on a directory of RPMs | Plain mode, in place | [Path A](#path-a-createrepo_c-in-place) |
| `dpkg-scanpackages` on a flat DEB directory | Plain mode, in place | [Path A](#path-a-createrepo_c-in-place) |
| A reprepro archive with `pool/` and `dists/` | Managed workspace | [Path B](#path-b-reprepro-to-a-workspace) |
| `createrepo_c` plus scripts for multiple architectures | Managed workspace | [Path B](#path-b-reprepro-to-a-workspace) |

Plain mode is the drop-in replacement: same directory, same URLs, one command instead of a
toolchain. Managed mode is a change of shape — a workspace, a pool, per-architecture views — and
gives you membership policy, transactional builds, and an audit trail. Migrate to Plain first if
you just want the dependency gone; move to Managed when the repository's lifecycle is what hurts.

## Path A: createrepo_c, in place {#path-a-createrepo_c-in-place}

`sow create` indexes a directory of packages exactly where they sit. Nothing moves, nothing is
renamed, and no package is deleted.

### The starting state

A repository built by `createrepo_c 0.20.1`:

```bash
ls repodata
```

```console
6167bcf3bf31ac553056a6c60004f52f33391fcf4a0d67fa12e3b812e2c85541-primary.sqlite.bz2
796b249defdd03d9775a6c23db45a09215af2d88aabeadca123f237127d6a5ef-filelists.xml.gz
bf4a15eb0869179894d9c80cd4326dc4c5a562434f4d282ad26d5617062d16cb-other.xml.gz
c29e1e85aa291940096864c80fedcb7e7f53723913a9551b16c29f4ae39373a3-primary.xml.gz
c8ed67b5858a8eca91f6a760412c04f8f1d7be441e2b0b98722350f2929965c2-other.sqlite.bz2
fbb08a2d958c266757ab4eee4aec65ee15973cb9d13f67d0c16265afe52309b1-filelists.sqlite.bz2
repomd.xml
```

```bash
grep -o 'type="[a-z_]*"' repodata/repomd.xml | sort -u
```

```console
type="filelists_db"
type="filelists"
type="other_db"
type="other"
type="primary_db"
type="primary"
```

Six data entries: the three XML indexes plus three SQLite databases. SOW does not generate the
SQLite ones — that is a deliberate non-goal, not a gap. Every dnf and yum release still receiving
updates falls back to the XML indexes when `*_db` entries are absent.

### Take it over

```bash
sow create /srv/yum
```

```console
created /srv/yum: rpm=3 deb=0 signed=0 removed=0 marker=false noop=false recovered=false
```

`removed=0` is the guarantee: no package was touched. `signed=0` because no `--sign-with` was
given, so no RPM was re-signed either.

### What is on disk now

```bash
ls repodata
```

```console
6167bcf3bf31ac553056a6c60004f52f33391fcf4a0d67fa12e3b812e2c85541-primary.sqlite.bz2
796b249defdd03d9775a6c23db45a09215af2d88aabeadca123f237127d6a5ef-filelists.xml.gz
bf4a15eb0869179894d9c80cd4326dc4c5a562434f4d282ad26d5617062d16cb-other.xml.gz
c29e1e85aa291940096864c80fedcb7e7f53723913a9551b16c29f4ae39373a3-primary.xml.gz
c8ed67b5858a8eca91f6a760412c04f8f1d7be441e2b0b98722350f2929965c2-other.sqlite.bz2
c92f116ebd1c410ed2433551357c5bd66153e4bdc27f1668ac84cb892fbc22b1-other.xml.gz
f7d8b4a3b21af9298a9888aede0de034690ff5bddc2a1aa52f858345b8e4897a-primary.xml.gz
fbb08a2d958c266757ab4eee4aec65ee15973cb9d13f67d0c16265afe52309b1-filelists.sqlite.bz2
fd91d28cf6b949747fc38ef391122dd10cbb3e1e14ec4b295629b004627d39e3-filelists.xml.gz
repomd.xml
```

**Ten files where there were seven.** SOW added its three indexes and left all six of
`createrepo_c`'s in place. This is not an oversight — SOW does not delete bytes it did not write.
The rule keeps a failed or interrupted run from destroying a working repository, and it is the
same rule that makes `--pigsty` the only mode that removes packages.

The new `repomd.xml` is a clean replacement that references only the new files:

```bash
grep -o 'type="[a-z_]*"' repodata/repomd.xml | sort -u
```

```console
type="filelists"
type="other"
type="primary"
```

```bash
grep -o '<location href="[^"]*"' repodata/repomd.xml
```

```console
<location href="repodata/f7d8b4a3b21af9298a9888aede0de034690ff5bddc2a1aa52f858345b8e4897a-primary.xml.gz"
<location href="repodata/fd91d28cf6b949747fc38ef391122dd10cbb3e1e14ec4b295629b004627d39e3-filelists.xml.gz"
<location href="repodata/c92f116ebd1c410ed2433551357c5bd66153e4bdc27f1668ac84cb892fbc22b1-other.xml.gz"
```

The repository is already correct and serving. The stale files are dead weight — nothing points
at them, and a client that never saw the old `repomd.xml` will never ask for them.

### Clean up the leftovers

This is the one manual step in Path A. The safe rule is: delete every file in `repodata/` that
the current `repomd.xml` does not reference.

```bash
cat > prune-legacy-repodata.sh <<'SH'
#!/bin/sh
# Delete every repodata file the current repomd.xml no longer references.
set -eu
cd "${1:-.}/repodata"
grep -o 'href="repodata/[^"]*"' repomd.xml | sed 's|.*repodata/||; s|"$||' > .keep
printf 'repomd.xml\n' >> .keep
for f in *; do
  [ "$f" = ".keep" ] && continue
  grep -qxF "$f" .keep || { echo "removing $f"; rm -f "$f"; }
done
rm -f .keep
SH
chmod +x prune-legacy-repodata.sh
sh prune-legacy-repodata.sh /srv/yum
```

```console
removing 6167bcf3bf31ac553056a6c60004f52f33391fcf4a0d67fa12e3b812e2c85541-primary.sqlite.bz2
removing 796b249defdd03d9775a6c23db45a09215af2d88aabeadca123f237127d6a5ef-filelists.xml.gz
removing bf4a15eb0869179894d9c80cd4326dc4c5a562434f4d282ad26d5617062d16cb-other.xml.gz
removing c29e1e85aa291940096864c80fedcb7e7f53723913a9551b16c29f4ae39373a3-primary.xml.gz
removing c8ed67b5858a8eca91f6a760412c04f8f1d7be441e2b0b98722350f2929965c2-other.sqlite.bz2
removing fbb08a2d958c266757ab4eee4aec65ee15973cb9d13f67d0c16265afe52309b1-filelists.sqlite.bz2
```

```bash
ls /srv/yum/repodata
```

```console
c92f116ebd1c410ed2433551357c5bd66153e4bdc27f1668ac84cb892fbc22b1-other.xml.gz
f7d8b4a3b21af9298a9888aede0de034690ff5bddc2a1aa52f858345b8e4897a-primary.xml.gz
fd91d28cf6b949747fc38ef391122dd10cbb3e1e14ec4b295629b004627d39e3-filelists.xml.gz
repomd.xml
```

Run this once, right after the first `sow create`. Every subsequent run is self-cleaning: SOW
knows which files it wrote and replaces them.

{{% alert title="Wait for clients to catch up" color="warning" %}}
If clients may have cached the old `repomd.xml`, wait one `metadata_expire` interval before
pruning. Delete the files it names while a client still holds it and that client gets a 404
instead of a graceful refresh.
{{% /alert %}}

### Confirm it is stable

```bash
sow create /srv/yum
```

```console
created /srv/yum: rpm=3 deb=0 signed=0 removed=0 marker=false noop=true recovered=false
```

`noop=true` means nothing changed. Output is deterministic — the same packages produce
byte-identical metadata, with a fixed `<revision>` and zeroed timestamps — so re-running is free
and diffable. A cron job that used to invoke `createrepo_c` becomes:

```bash
sow create /srv/yum
```

### Flat DEB directories

The same command handles `dpkg-scanpackages` output, and a directory containing both formats in
one pass:

```bash
sow create /srv/mixed
```

`Packages` and `Packages.gz` are rewritten, gzip content matching the plain file exactly. The
fields match `dpkg-scanpackages` with two differences: no `MD5sum` or `SHA1` (SHA-256 is what
modern clients verify), and fields the package does not declare are omitted rather than emitted
empty.

### What Plain mode does not carry over

`modulemd` and module metadata, SQLite repodata, `zchunk`, `comps`/`groups`, and SRPM source
indexes are non-goals — they are not planned and not partially implemented. If your repository
publishes AppStream modules or comps groups, Plain mode cannot replace `createrepo_c` for it
today.

## Path B: reprepro, to a workspace {#path-b-reprepro-to-a-workspace}

reprepro maintains a Berkeley DB alongside the tree. SOW cannot read that database, and there is
no import command — but you do not need one. The packages in `pool/` are the whole state that
matters, and `sow add` re-derives everything else from the package headers.

### The starting state

```bash
cd /srv/apt && find pool dists -type f | sort
```

```console
dists/trixie/main/binary-amd64/Packages
dists/trixie/main/binary-amd64/Packages.gz
dists/trixie/main/binary-amd64/Release
dists/trixie/main/binary-arm64/Packages
dists/trixie/main/binary-arm64/Packages.gz
dists/trixie/main/binary-arm64/Release
dists/trixie/Release
pool/main/a/agentsview/agentsview_0.37.5-1_amd64.deb
pool/main/a/agentsview/agentsview_0.37.5-1_arm64.deb
pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb
pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb
pool/main/c/caddy/caddy_2.11.4-1_amd64.deb
pool/main/c/caddy/caddy_2.11.4-1_arm64.deb
pool/main/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
pool/main/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb
```

### Build the workspace and import

```bash
mkdir -p ~/repo && cd ~/repo
sow init .
sow repo new archive
sow dist new trixie --format deb -r archive
```

```console
initialized /home/you/repo: config_created=true repositories_initialized=0 dists_initialized=0
created archive: path=/home/you/repo/archive protected=false dists=0 generation=0 status=clean packages=0 memberships=0
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
```

Name the Dist after the codename your clients already write in their sources line, so nothing
changes on their side.

Then point `sow add` at the old pool with `-R` to recurse:

```bash
sow add /srv/apt/pool -R -d trixie
```

```console
add repository=archive operation=2553339663345297053 accepted=8 failed=0 memberships=+8/-0 revision=2 generation=2 dirty=false
item input="/srv/apt/pool/main/a/agentsview/agentsview_0.37.5-1_amd64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:amd64" sha256:9f489369bbff02cde4b09397b91bbf367429d8e8cd9d97fc75ba5ea79bb9225a dists=trixie:accepted
item input="/srv/apt/pool/main/a/agentsview/agentsview_0.37.5-1_arm64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:arm64" sha256:164fbda74eb82cedacc42902387aa0552c72286dc9e8daa964f2f09e356b3324 dists=trixie:accepted
item input="/srv/apt/pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:amd64" sha256:1ca6db58a2ca839d1bc1e0f843e971c049f664388c111af5481015baeb9bb120 dists=trixie:accepted
item input="/srv/apt/pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:arm64" sha256:dd3d06c3b32017b47b721e02b24954dab6179399c3cecc2ce7c5c9a27510f3f3 dists=trixie:accepted
item input="/srv/apt/pool/main/c/caddy/caddy_2.11.4-1_amd64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:amd64" sha256:79de4b2dda79161164b9b437a0f6d4339c1236f806e5750e8e488fa1e0ede679 dists=trixie:accepted
item input="/srv/apt/pool/main/c/caddy/caddy_2.11.4-1_arm64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:arm64" sha256:3a21855bb702ffaaafa30f2b626808b43e220ea26cf53ed2ea5aabed0f1aa1dc dists=trixie:accepted
item input="/srv/apt/pool/main/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb" status=accepted format=deb coordinate="libpq5=18.4-1.pgdg24.04+1:arm64" sha256:923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21 dists=trixie:accepted
item input="/srv/apt/pool/main/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb" status=accepted format=deb coordinate="postgresql-client-common=291.pgdg24.04+1:all" sha256:8cae086c805e44272004d111f9f1177789dc14f0bcd07fd901471915a4eed001 dists=trixie:accepted
```

The old tree is untouched — `add` reads its inputs and copies them. Keep it until you have
verified the new one.

### Compare the pools

```bash
cd ~/repo/archive && find pool -name "*.deb" | sort
```

```console
pool/a/agentsview/agentsview_0.37.5-1_amd64.deb
pool/a/agentsview/agentsview_0.37.5-1_arm64.deb
pool/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb
pool/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb
pool/c/caddy/caddy_2.11.4-1_amd64.deb
pool/c/caddy/caddy_2.11.4-1_arm64.deb
pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
pool/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb
```

Every path is identical to reprepro's except for one missing segment: reprepro writes
`pool/main/p/postgresql-18/…`, SOW writes `pool/p/postgresql-18/…`. Both derive the grouping the
same way — Debian prefix rule, then source package name — and both put `libpq5` under
`postgresql-18` because that is its `Source:` field.

**SOW has no component level in the pool.** The component is fixed at `main`, so a directory
named after it carries no information. The consequence for migration is concrete: `Filename`
values change, which means clients must fetch the new indexes rather than reusing cached ones.
Since a new `Release` is published with new hashes anyway, this happens on the next `apt update`
and requires nothing from you — but it does mean you cannot serve the new indexes over the old
pool directory, or vice versa.

### Verify before cutting over

```bash
sow check
```

```console
repository=archive status=clean ready_to_copy=true revision=2 generation=2
config	ok=true	checked=3
state	ok=true	checked=1
public-modes	ok=true	checked=41
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=8
index	ok=true	checked=1
signature	ok=true	checked=1
generation-manifest	ok=true	checked=2
```

Serve the new tree on a temporary URL, point one client at it, run `apt update` and install
something. Then swap the document root and delete the old tree — not before.

### Index differences

reprepro's `Release` publishes four digests and per-architecture `Release` stubs:

```console
Codename: trixie
Date: Tue, 04 Aug 2026 04:33:33 UTC
Architectures: amd64 arm64
Components: main
Description: legacy reprepro archive
MD5Sum:
 a4b9d08caee42b0a2764d4d0ab58c914 3670 main/binary-amd64/Packages
 1fab9172bc826e3054cf6661138732b4 10240 main/binary-amd64/Packages.gz
 b2424f6aef8e120796d78fbabf067a86 73 main/binary-amd64/Release
 …
```

SOW's publishes SHA-256 only, and adds `Acquire-By-Hash: yes` — see
[Build an APT Repository](/docs/tutorial/apt-repo/) for the full file. It emits no
`main/binary-*/Release` stubs; APT does not need them, and reprepro's contain three lines of
information already present in the Dist `Release`.

Per-package, the difference is the same story:

```console
# reprepro
Package: libpq5
Source: postgresql-18
Filename: pool/main/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
Size: 248592
SHA256: 923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21
SHA1: bbbbcd35976ba44fdf423553b59cc3679c4f2183
MD5sum: 3f234b897f88f495314768956a73a055

# sow
Package: libpq5
Source: postgresql-18
Filename: pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
Size: 248592
SHA256: 923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21
```

Same size, same SHA-256, different `Filename`, no weak digests.

### Habits that change

| reprepro | SOW |
|---|---|
| `reprepro includedeb trixie foo.deb` | `sow add foo.deb -d trixie` |
| `reprepro remove trixie foo` | `sow rm foo -d trixie` |
| `reprepro list trixie` | `sow ls -d trixie` |
| `reprepro check` | `sow check` |
| `Limit:` in `conf/distributions` | `limit:` per Dist in `sow.yml` |
| `FilterList` / `FilterFormula` | `exclude:` rules in `sow.yml` |
| `SignWith:` in `conf/distributions` | `signing.deb.metadata.key` in `sow.yml` |
| `--export=never` then `reprepro export` | `--skip` then `sow build` |
| `reprepro _listchecksums` | `sow changes BASE` |

reprepro's database has no counterpart you need to manage: SOW's SQLite state is derived from the
packages and the configuration, and `sow check` proves it still matches the tree.

## Full comparison

Measured against `createrepo_c 0.20.1` and reprepro on identical package sets.

| | SOW | createrepo_c | reprepro |
|---|---|---|---|
| RPM metadata | `primary`/`filelists`/`other`, semantically equivalent | baseline | — |
| SQLite repodata | not generated (non-goal) | generated by default | — |
| DEB `Packages` fields | equivalent, SHA-256 only | — | baseline (MD5 + SHA1 + SHA256) |
| `by-hash` indexes | supported (`Acquire-By-Hash: yes`) | — | **not supported** |
| Pool layout | `pool/<c>/<source>/` | — | `pool/main/<c>/<source>/` |
| Per-arch `Release` stubs | not generated (APT does not need them) | — | generated |
| Platforms | Linux and macOS, single static binary | Linux in practice | Linux |
| Transactions | journal with forward-complete and rollback | none | database can be corrupted |
| Audit | operation ledger plus JSONL export | none | limited logging |
| Dependencies | none | C libraries: libxml2, libcurl, sqlite, … | Berkeley DB, gpgme, libarchive |

RPM metadata was compared field by field on 9 synthetic and 87 real production packages:
name, arch, EVR, checksums, sizes, provides, requires flags, files, changelog, and header ranges
all match. One difference showed up: where an RPM header lists `/bin/sh` twice in both a pre and
a non-pre context, SOW keeps one entry.

## What does not migrate

These are non-goals, not roadmap items:

- `modulemd` / AppStream module metadata, and `repo2module` / `modifyrepo_c` workflows
- SQLite repodata and `zchunk`
- SRPM and DSC source indexes
- remote publishing, CDN or object-storage endpoints
- multi-host or multi-writer operation
- snapshots, freezes, and channels
- a web UI or any long-running service
- building packages

SOW builds and manages repositories on a local POSIX filesystem, with one writer at a time. If a
requirement above is load-bearing for you, keep the tool that provides it.

## Where to go next

{{< doc-cards cols="2" >}}
{{< doc-card title="Build a YUM Repository" link="/docs/tutorial/yum-repo/" >}}
The full managed RPM workflow, once Plain mode is not enough.
{{< /doc-card >}}
{{< doc-card title="Build an APT Repository" link="/docs/tutorial/apt-repo/" >}}
Pool layout, `by-hash`, and client configuration in detail.
{{< /doc-card >}}
{{< doc-card title="Capability Overview" link="/docs/feature/overview/" >}}
Everything SOW does, in one table, with the comparison to traditional tools.
{{< /doc-card >}}
{{< doc-card title="Compatibility" link="/docs/reference/compatibility/" >}}
The tested client matrix and platform requirements.
{{< /doc-card >}}
{{< /doc-cards >}}
