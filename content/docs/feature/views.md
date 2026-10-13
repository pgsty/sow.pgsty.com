---
title: "Pool & Metadata Views"
linkTitle: "Pool & Views"
description: "Share package files across RPM and APT views, export RPM leaves, and deliver complete repositories."
categories: [Feature]
tags: [pool, dist, rpm, deb]
url: "/docs/feature/views/"
weight: 400
icon: fa-solid fa-layer-group
---

<span id="the-invariant"></span>

A Managed repository stores each package object once under `pool/`. Its Dists and
architecture views contain indexes that refer to those package bytes.

```text
<repo>/pool/                              package files
<repo>/dists/<rpm-dist>/<arch>/repodata/   RPM metadata
<repo>/dists/<deb-dist>/main/binary-*/     APT metadata
```

The storage boundary is one repository. The same package in another repository or
publication target occupies that repository's or target's namespace.

<span id="what-a-built-repository-looks-like"></span>
<span id="rpm-views-use-computed-parent-relative-hrefs"></span>
<span id="why-views-contain-metadata-only"></span>
<span id="neutral-packages-are-selected-not-duplicated"></span>

## RPM views

An RPM Dist has one metadata directory per configured architecture:

```text
demo/
├── pool/
│   ├── e/example/example-1.0-1.x86_64.rpm
│   └── d/demo-data/demo-data-1.0-1.noarch.rpm
└── dists/el9/
    ├── x86_64/repodata/
    │   ├── <sha256>-primary.xml.gz
    │   ├── <sha256>-filelists.xml.gz
    │   ├── <sha256>-other.xml.gz
    │   └── repomd.xml
    └── aarch64/repodata/
        └── ...
```

The `x86_64` view includes `x86_64` and `noarch` packages. The `aarch64` view includes
`aarch64` and `noarch` packages. Both views refer to the same `noarch` file.

A package location is relative to the architecture directory:

```xml
<location href="../../../pool/d/demo-data/demo-data-1.0-1.noarch.rpm"/>
```

Point the client at `dists/el9/x86_64/`, and serve the complete `demo/` directory so that
the relative package location resolves. `sow check` verifies that indexed locations stay
inside the repository and resolve to the expected package objects.

## APT views

APT indexes use paths relative to the repository root:

```text
Filename: pool/e/example/example_1.0-1_amd64.deb
```

Each configured architecture has `Packages`, `Packages.gz`, and SHA-256 by-hash entries
under `dists/<dist>/main/binary-<arch>/`. The Dist root contains `Release` and, when
signed, `InRelease` and `Release.gpg`.

`all` packages appear in each applicable architecture index while their payload remains
one pool object. There are no per-view package copies or per-architecture `Release` files.

<span id="ordinary-clients-and-reposync-are-different-contracts"></span>

## Export for `dnf reposync`

Default `dnf reposync` rejects Managed RPM locations that climb above its per-repository
download directory. Create a standalone leaf for that workflow:

```bash
sow export rpm-leaf el9 x86_64 /srv/exports/el9-x86_64 -r demo
```

The export has local package paths, its own repodata, a manifest, and a `.sow-export.json`
completion marker. Choose a destination outside the repository and all configured
filesystem publication roots.

The default copies files. `--hardlink` requires the same filesystem and makes exported
packages share the source inode; keep those files read-only. An export does not create
Dist membership or a retained generation and is not input to `sow publish`.

<span id="copy-and-publication"></span>

## Deliver the complete repository

Use a configured publication target for live updates. For another transport, copy the
complete settled `pool/ + dists/` tree into a separate staging directory, verify the copy,
then switch it into service. Keep package URLs referenced by cached indexes reachable
until those caches expire. See [Serving](/docs/tutorial/serving/) for a complete transfer procedure.
Copying only an RPM architecture directory leaves its package locations unresolved.

`sow changes 0` lists each package under `pool/` once, followed by metadata and client
pointers. It lists local files; `sow publish` manages target progress and cache handling.

See [Repository layout](/docs/reference/layout/),
[Serving](/docs/tutorial/serving/), and [`export`](/docs/command/export/).

<span id="next"></span>
