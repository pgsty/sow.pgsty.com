---
title: "Repository Layout"
linkTitle: "Layout"
description: "Every path SOW creates, the pool grouping rule, name constraints, and what must never be served."
url: "/docs/reference/layout/"
weight: 400
icon: fa-solid fa-folder-tree
---

SOW's on-disk layout is fixed. There is no `path:` setting, no template, and no way to
relocate a repository — every path is derived from the workspace root, a validated name,
and a constant relative segment. This page is the complete map, so you know what to serve,
what to copy, and what to keep private.

## Plain mode

`sow create` writes indexes next to the packages and touches nothing else. The directory
you point it at stays a flat repository: packages and metadata share one level.

```text
/srv/offline/
├── blackbox_exporter-0.28.0-1.x86_64.rpm     # yours, never modified
├── pev2-1.23.0-1.noarch.rpm                  # yours
├── libpq5_18.3-1.pgdg12+1_amd64.deb          # yours
├── repodata/                                 # written by SOW, when RPMs are present
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   └── repomd.xml
├── Packages                                  # written by SOW, when DEBs are present
├── Packages.gz
└── repo_complete                             # only with --pigsty
```

RPM and DEB indexes coexist happily; one `sow create` writes both when both formats are
present. Only the paths above are SOW's — any other file in the directory is left exactly
as it was.

Flat metadata references packages in the same directory, so the repository works
identically over `file://` and over HTTP with the directory as the document root:

```console
# repodata primary.xml — location is a bare basename
<location href="blackbox_exporter-0.28.0-1.x86_64.rpm"

# Packages — Filename is ./basename
Filename: ./libpq5_18.3-1.pgdg12+1_amd64.deb
```

Published files do not inherit your umask. `repodata/` is created `0755`; index files,
`Packages`, `Packages.gz`, and `repo_complete` are `0644`.

While a `sow create` is in flight the directory also contains private working paths, all
prefixed `.sow-plain-`: a stage directory (`.sow-plain-stage-*`), the durable journal
(`.sow-plain-operation.json`), and — under `--pigsty` — a recovery trash
(`.sow-plain-recovery-*`) holding packages that are being removed. They are cleaned up on
success, and on the next run after a crash. Do not serve them and do not copy them.

## Managed mode

A workspace has exactly two things at its root: the configuration file, and the private
state directory. Everything else is a repository, and a repository directory is the unit
you publish.

```text
<workspace>/
├── sow.yml                       # configuration — do not serve
├── .sow/                         # private state — do not serve, do not copy
│   ├── workspace.lock
│   ├── workspace-ops/            # holds active.json during init / repo new / repo rm
│   ├── repo-locks/
│   │   └── <repo>.lock
│   ├── <repo>.db                 # per-repository SQLite (+ -wal and -shm sidecars)
│   └── <repo>/
│       ├── stage/                # metadata built here, then atomically moved into place
│       ├── recovery/             # pre-images and objects awaiting deletion
│       └── pending/              # package bytes added with --skip, named by SHA-256
└── <repo>/                       # ← this is what you serve and rsync
    ├── pool/
    └── dists/
```

The private state directory is mode `0700`. A repository lock lives at a stable path
(`.sow/repo-locks/<repo>.lock`) that never moves, so a repository's private state can be
replaced during recovery without invalidating the lock other processes hold.

Two repositories in one workspace share nothing. Each has its own pool, its own SQLite
database, its own lock, and its own generation counter. Identical package bytes in two
repositories are stored twice — deduplication does not cross the repository boundary.

### Repository

```text
<workspace>/pigsty/
├── pool/
│   ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│   ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
│   ├── libf/libfoo/libfoo1_1.0-1_amd64.deb
│   ├── p/pev2/pev2-1.23.0-1.noarch.rpm
│   └── p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
└── dists/
    ├── el9/       # format: rpm
    └── trixie/    # format: deb
```

`pool/` holds one copy of each package's bytes, shared by every distribution in the
repository. Content in the pool is immutable — a given path always holds the same bytes.
Removing a package from a distribution removes membership, not pool bytes; there is no
garbage collection.

### Pool grouping

```text
pool/<prefix>/<source>/<filename>
```

`source` is the source package name, taken from the RPM `SOURCERPM` header or the DEB
`Source` control field. When the field is missing, the binary package name is used
instead and a warning is recorded. This is why `libpq5` ends up under `postgresql-18`:
that is the source it was built from, and it is the same grouping `reprepro` produces.

`prefix` follows the Debian rule — the first character of the source name, or the first
four characters when the source name begins with `lib`:

| Source | Pool prefix | Example path |
|---|---|---|
| `postgresql-18` | `p` | `pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb` |
| `blackbox_exporter` | `b` | `pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm` |
| `libfoo` | `libf` | `pool/libf/libfoo/libfoo1_1.0-1_amd64.deb` |

The prefix is lowercased ASCII; `source` and `filename` keep their original case. Two
packages whose full pool paths would collide under case-insensitive comparison are
rejected, so a repository built on Linux stays valid when copied to a default macOS
filesystem.

Unlike `reprepro`, there is no component level in the pool — the path is
`pool/<prefix>/<source>/`, not `pool/main/<prefix>/<source>/`.

### RPM distributions

An RPM distribution renders one directory per architecture family, each a complete,
independently consumable repository:

```text
dists/el9/
├── x86_64/
│   ├── repodata/
│   │   ├── <sha256>-primary.xml.gz
│   │   ├── <sha256>-filelists.xml.gz
│   │   ├── <sha256>-other.xml.gz
│   │   ├── repomd.xml
│   │   └── repomd.xml.asc          # only when signing.rpm.metadata.key is configured
│   └── pool/                       # hardlinks into the repository pool
│       ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│       └── p/pev2/pev2-1.23.0-1.noarch.rpm
└── aarch64/
    ├── repodata/ ...
    └── pool/
        ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
        └── p/pev2/pev2-1.23.0-1.noarch.rpm
```

Each view contains its native packages plus every neutral (`noarch`) one. The view's
`pool/` entries are hardlinks to the repository pool — same inode, no extra disk usage:

```console
stat -f "%l links  inode=%i  %N" pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
    dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
    dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm

3 links  inode=206234569  pool/p/pev2/pev2-1.23.0-1.noarch.rpm
3 links  inode=206234569  dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
3 links  inode=206234569  dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

Three links: the root pool plus both views. A native x86_64 package has two — the root
pool and the one view it belongs to.

The reason for this design is client compatibility. Metadata references packages with a
plain relative href containing no `..`:

```xml
<location href="pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm"/>
```

A layout that pointed at `../../../pool/...` also worked for `dnf install`, but
`dnf reposync` rejected it, because the normalized destination escaped the per-repository
download root. Hardlinked views keep every client working, `reposync` included.

Because these are hardlinks, `pool/` and `dists/` must be on the same filesystem. SOW
fails loudly if they are not; it never silently falls back to copying. Copying the
repository with a tool that does not preserve hardlinks (plain `cp -r`, most object-store
uploads) is fine functionally — you just lose the deduplication and pay for the extra
space.

Metadata files are named by their own checksum, so a new generation adds new files rather
than overwriting the ones a client may be mid-download on. `repomd.xml` is the only
mutable pointer, and it is replaced atomically and last. One previous generation's
metadata files are retained; older ones appear in the `delete` phase of `sow changes`.

### DEB distributions

A DEB distribution renders one `binary-<arch>` directory per architecture under the fixed
`main` component. There is no per-view pool — APT resolves `Filename` from the archive
root:

```text
dists/trixie/
├── Release
├── InRelease                       # only when signing.deb.metadata.key is configured
├── Release.gpg                     # ditto
└── main/
    ├── binary-amd64/
    │   ├── Packages
    │   ├── Packages.gz
    │   └── by-hash/
    │       └── SHA256/
    │           ├── <sha256 of Packages>
    │           ├── <sha256 of Packages.gz>
    │           └── ...              # one previous generation is retained
    └── binary-arm64/
        └── ...
```

Note that DEB views use the ecosystem architecture names (`amd64`, `arm64`) while RPM
views use the family names (`x86_64`, `aarch64`). Both come from the same canonical
configuration.

`Packages` entries point into the shared pool relative to the archive root — that is, to
`<repo>/pool/...`, which is why you serve the repository directory and not the
distribution directory:

```console
Filename: pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
```

`Release` advertises by-hash and carries a SHA256 manifest only — no MD5Sum, no SHA1:

```console
Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:07:16 UTC
X-SOW-Generation: 4
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 95e8c59d21d69285ac788bd8ea78b0544b0a1395ae9a0e3a700ec13b420e5c39 2245 main/binary-amd64/Packages
 4d658bdf6a542999f737e5f89e3bdb504c205fb85cda76f3e4b1ef73619c5900 751 main/binary-amd64/Packages.gz
 c924dbbd01d2e14bc3a4892a355b3674cb238f8315e55c609d25043568f59dc8 1122 main/binary-arm64/Packages
 a4289540a3224dbfbdf1c5b23db355c6541df34baf378070a493d9380f03b1ee 668 main/binary-arm64/Packages.gz
```

`by-hash/SHA256/` is what makes an index update safe for a client that fetched `Release`
a moment ago: the old index stays reachable by its digest while the new one is published.
APT 1.2 and later use it automatically.

Empty distributions are still valid distributions. A DEB distribution with no packages
publishes an empty `Packages`, its `.gz`, the by-hash entries, and a signed `Release`; an
RPM distribution publishes empty but consumable `repodata` for each architecture.

## Names

Repository and distribution names must match `[a-z0-9][a-z0-9._-]*`, because each becomes
a directory name that has to behave the same on case-sensitive and case-insensitive
filesystems.

These names are reserved and rejected outright:

| Reserved | Why |
|---|---|
| `.`, `..` | Path traversal |
| `.sow` | Private state directory |
| `pool`, `dists` | Fixed repository subdirectories |
| `sow.yml` | Configuration file |
| `workspace.lock`, `workspace-ops`, `repo-locks` | Workspace state paths |

Two repository names that would collide over the SQLite sidecar names are also rejected —
a repository called `db` and one called `db.db` would fight over `.sow/db.db`:

```console
configuration error: ... repository names "db" and "db.db" collide at reserved state path "db.db"
```

## What to serve and what to hide

{{% alert title="Never expose .sow over HTTP" color="warning" %}}
`.sow/` contains the state databases, locks, staged files, and the pending package store.
Serving it leaks internal state and lets clients fetch packages that were deliberately not
published yet.
{{% /alert %}}

The safe rule is to point your web server at a **repository** directory, not at the
workspace root:

```nginx
# Correct: the document root is one repository
location /pigsty/ {
    alias /srv/repo/pigsty/;
    autoindex on;
}
```

If you must serve the workspace root — for example to expose several repositories under
one prefix — deny the private paths explicitly:

```nginx
location ^~ /.sow  { deny all; }
location = /sow.yml { deny all; }
```

The same split applies to copying. `sow changes 0` lists exactly the files that make up
the current published tree, and every path it prints is under `pool/` or `dists/`.
Neither `sow.yml` nor `.sow/` ever appears, because neither belongs on a mirror.

```bash
# Publish one repository. --hard-links preserves the view deduplication.
rsync -a --hard-links --delete /srv/repo/pigsty/ mirror:/var/www/pigsty/
```

Check that the tree is deliverable before you copy it:

```bash
sow check -r pigsty
```

A `dirty` repository still has a complete, self-consistent published tree from its last
build — it just does not yet reflect your latest changes. `sow check` exits `5` in that
case so a deploy script stops instead of shipping a stale tree by accident.

## See also

- [Pool & Architecture Views](/docs/feature/views/) — why the layout is shaped this way
- [Serve Repositories](/docs/tutorial/serving/) — full web server configuration
- [`sow changes`](/docs/reference/cli/build/) — the exact file list for a delivery
- [Compatibility](/docs/reference/compatibility/) — the filesystem constraints in one place
