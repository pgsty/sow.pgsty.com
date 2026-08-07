---
title: "Pool & Architecture Views"
linkTitle: "Pool & Architecture Views"
description: "One package, one owner, many views: how hardlink projection keeps YUM metadata hrefs safe for reposync, why noarch lands in every view, and why the pool must share a filesystem."
url: "/docs/feature/views/"
weight: 400
icon: fa-solid fa-link
---

If you list a Managed repository you will find the same package file at three different paths, and `du` will insist it only occupies space once. That is not an illusion and it is not a symlink. This page explains the projection model — why it exists, what it guarantees, and the one constraint it puts on your filesystem.

## The invariant

**The root pool owns the bytes. Everything under `dists/` is a projection that can be deleted and rebuilt without touching an owned object.**

```text
<repo>/pool/<prefix>/<source>/<file>      canonical object — the owner
<repo>/dists/<dist>/<arch>/pool/...       hardlink alias — a view of the same inode
<repo>/dists/<dist>/<arch>/repodata/...   metadata that references the alias
```

Removing a Dist unlinks its aliases and nothing else. Pool bytes are never deleted as a side effect of Dist maintenance — there is no garbage collection in this release, by design.

## What a built repository looks like

A Repository with one RPM Dist (`el9`) and one DEB Dist (`trixie`), holding three RPMs — one `noarch`, one `x86_64`, one `aarch64` — and two DEBs:

```text
pigsty/
├── pool/
│   ├── p/pev2/pev2-1.23.0-1.noarch.rpm
│   └── x/xray/
│       ├── xray-26.2.6-1.aarch64.rpm
│       ├── xray-26.2.6-1.x86_64.rpm
│       ├── xray_26.2.6-1_amd64.deb
│       └── xray_26.2.6-1_arm64.deb
└── dists/
    ├── el9/
    │   ├── x86_64/
    │   │   ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm      # alias
    │   │   ├── pool/x/xray/xray-26.2.6-1.x86_64.rpm      # alias
    │   │   └── repodata/{<sha256>-*.xml.gz, repomd.xml}
    │   └── aarch64/
    │       ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm      # alias
    │       ├── pool/x/xray/xray-26.2.6-1.aarch64.rpm     # alias
    │       └── repodata/{<sha256>-*.xml.gz, repomd.xml}
    └── trixie/
        ├── Release
        └── main/
            ├── binary-amd64/{Packages, Packages.gz, by-hash/SHA256/…}
            └── binary-arm64/{Packages, Packages.gz, by-hash/SHA256/…}
```

Pool paths follow the Debian convention: `pool/<prefix>/<source>/<filename>`, where `prefix` is the source name's first character — or its first four characters for `lib*` — lowercased. `source` and `filename` keep their original case. RPM source comes from `SOURCERPM`, DEB source from the `Source` field, falling back to the binary name with a recorded warning if absent. That is why `libpq5` ends up under `pool/p/postgresql-18/`, exactly where `reprepro` would put it.

Two Repositories never share a pool, and identical bytes in two Repositories are stored twice. Deduplication happens inside a Repository, never across the ownership boundary.

## Views are hardlinks, and you can prove it

```console
$ stat -f '%i %N' pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
                  dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
                  dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
206233285 pool/p/pev2/pev2-1.23.0-1.noarch.rpm
206233285 dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
206233285 dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

One inode, three names. The link count confirms it:

```console
$ stat -f '%l %N' pool/p/pev2/pev2-1.23.0-1.noarch.rpm
3 pool/p/pev2/pev2-1.23.0-1.noarch.rpm

$ stat -f '%l %N' pool/x/xray/xray-26.2.6-1.x86_64.rpm
2 pool/x/xray/xray-26.2.6-1.x86_64.rpm
```

The `noarch` package has three links — the root pool plus both architecture views. The `x86_64` package has two — the root pool plus the one view it belongs in. These are regular hardlinks, not symlinks: there is no dangling-link failure mode, no path traversal to resolve, and a web server serves them without following anything.

## Neutral packages are projected, not duplicated

`noarch` (RPM) and `all` (DEB) are not a third CPU family. They are **neutral**, and neutrality is a property of the projection, not of the membership:

- One package object, identified by its SHA-256.
- One Dist membership — `(dist, content_sha256)`, unique.
- Rendered into **every** applicable architecture view of that Dist at build time.

So the `x86_64` view contains `x86_64` plus `noarch` packages, the `aarch64` view contains `aarch64` plus `noarch`, and `sow ls` still shows a single row. The database stores the logical family only; nothing is duplicated in state, only in the rendered tree.

A neutral package does not spread to Dists you did not select. `sow add foo.noarch.rpm -d el9` puts it in `el9` and nowhere else, even though `el9-beta` would also accept it.

The `limit` policy counts neutral as its own native architecture, once — see [Membership Policy](/docs/feature/policy/).

## Why the metadata href is `pool/...` and not `../../../pool/...`

Look at what the RPM metadata actually says:

```console
$ gzip -dc dists/el9/x86_64/repodata/*-primary.xml.gz | grep -o '<location href="[^"]*"'
<location href="pool/p/pev2/pev2-1.23.0-1.noarch.rpm"
<location href="pool/x/xray/xray-26.2.6-1.x86_64.rpm"
```

Relative to the view directory, with no `..` component anywhere. Getting here required rejecting the obvious alternative.

The first candidate design skipped the aliases entirely and pointed the `location href` at the shared root pool by computing the depth: `../../../pool/...`. On the surface it worked. In a pinned AlmaLinux 9.8 container, `makecache`, `repoquery`, `download`, and `install` all succeeded against a repository built that way.

`dnf reposync` refused. Its normalized local target escaped the per-repository download root, so it declined to write outside its own directory. That is correct behavior on `reposync`'s part, and it is a layout gate failure on ours: mirroring a repository is a first-class use case, so a design that breaks it is not "mostly compatible", it is rejected.

The replacement is what you see above. The root pool keeps canonical object ownership, each architecture view gets same-filesystem hardlinks for its native plus neutral memberships only, and the metadata uses a `pool/...` href that can never escape the view directory. In the final verification run this passed `makecache`, `repoquery` with location inspection, `download`, `install`, and `reposync` — for a native-plus-`noarch` `x86_64` view, for an `aarch64` view holding only `noarch`, and for a full copy that did not preserve hardlink identity.

The takeaway for you as an operator: a Managed YUM view directory is self-contained. Point a client, a mirror, or a `reposync` job at `dists/<dist>/<arch>/` and nothing it needs lives above that directory.

## APT does not need view aliases

The DEB side solves the same problem differently, because APT already has an archive-root-relative field:

```text
Package: xray
Architecture: amd64
Filename: pool/x/xray/xray_26.2.6-1_amd64.deb
```

`Filename` is resolved against the archive root — the Repository directory that contains both `dists/` and `pool/` — so APT reaches the shared pool directly. That is why `dists/trixie/` has no `pool/` subtree at all, and why the DEB component is fixed at `main` with no per-architecture `Release` stubs: apt does not need them, and `reprepro` generates them only for historical reasons.

The DEB `Release` carries the by-hash declaration:

```text
Origin: SOW
Suite: trixie
Codename: trixie
X-SOW-Generation: 4
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 59b22f5cc246d9a8137327b9eddee4a628df92bab4d6d4597ae024564d4d6e90 372 main/binary-amd64/Packages
 f2093eacfbb5efac8a3f54853e74c122bde97a5005f93940c81dfc5073bcf30f 303 main/binary-amd64/Packages.gz
 …
```

With `Acquire-By-Hash: yes`, apt fetches indexes from `main/binary-amd64/by-hash/SHA256/<hash>` rather than from the mutable `Packages` path — HTTP access logs during verification confirm it actually does. This is what makes an update safe while a build is in flight: a client that already read `Release` continues fetching the exact index bytes that `Release` promised, even if `Packages` has since been replaced. `reprepro` does not support by-hash at all; only `SHA256` is published, with no `MD5Sum` or `SHA1`.

The RPM side gets the same property from checksum-named metadata: `repomd.xml` points at `<sha256>-primary.xml.gz`, and the previous generation's files stay on disk for one more generation. See [Observability & Audit](/docs/feature/audit/).

## Same filesystem is a hard requirement

Hardlinks cannot cross a device boundary. SOW therefore verifies at initialization that the staging area and the target share an `st_dev`, and it will **fail loudly** rather than degrade:

- If `pool/` and `dists/` end up on different mounts, the operation fails. There is no silent copy fallback.
- If the filesystem does not support hardlinks at all, the operation fails.

This is a deliberate refusal. A silent fallback to copying would double the disk footprint of every repository without telling you, and — worse — would break the atomicity guarantee, because a copy is not a rename and cannot be made atomic. A failure you can see and fix beats a size regression you discover three months later.

In practice this means one thing: do not bind-mount, symlink, or otherwise relocate `pool/` or `dists/` out of the repository directory. The layout is fixed for exactly this reason.

## Copying a repository

Aliases are real physical paths, and the changeset treats them that way. `sow changes 0` lists both the pool object and each view alias as separate `payload` entries:

```console
$ sow changes 0
base=0 generation=4 dirty=false
add	payload	dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm	316372	d06d7f23…
add	payload	dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm	316372	d06d7f23…
add	payload	pool/p/pev2/pev2-1.23.0-1.noarch.rpm	316372	d06d7f23…
…
```

The database stores only the logical architecture family; physical paths are derived from the fixed layout, which is why they can be recomputed and verified rather than trusted.

When you copy the repository elsewhere, you have two outcomes and both are functional:

- **Preserving hardlinks** (`rsync -aH`, `cp -al` on the same filesystem, a filesystem-level snapshot): the destination keeps one inode per object. Disk usage matches the source.
- **Not preserving hardlinks** (plain `rsync -a`, `scp -r`, most object-storage sync tools): each alias becomes an independent regular file. You lose capacity deduplication, but every client — including `reposync` — still works exactly the same. This case was verified explicitly.

If the repository is large and mostly `noarch`, the difference is worth measuring before you choose a transport. See [Serve Repositories](/docs/tutorial/serving/).

## Next

- [Membership Policy](/docs/feature/policy/) — what decides which packages get projected at all
- [Transactions & Recovery](/docs/feature/transactions/) — how the projection is committed safely
- [Repository Layout](/docs/reference/layout/) — the complete path reference
- [Compatibility](/docs/reference/compatibility/) — the tested client matrix
