---
title: "Capability Overview"
linkTitle: "Capability Overview"
description: "What SOW covers across both execution paths, both package formats, signing, and platforms — and how it compares to createrepo_c and reprepro."
url: "/docs/feature/overview/"
weight: 100
icon: fa-solid fa-table-list
---

SOW is a self-contained software repository manager: a single static Go binary (`CGO_ENABLED=0`) that creates and maintains APT (DEB) and YUM (RPM) repositories on Linux and macOS. It does not call `createrepo_c`, `dpkg-scanpackages`, `reprepro`, or `modifyrepo_c`, and it does not run a daemon. This page is the map of what it covers; the rest of this section explains how each piece works.

The current release is `sow 0.2.0-dev`.

## Two execution paths

SOW gives you two ways to build a repository, and they are deliberately isolated from each other. Nothing is shared between them except the low-level package parsers, renderers, version comparators, locks, and safe file primitives.

| | Plain mode | Managed mode |
|---|---|---|
| Entry command | `sow create` | `sow init` / `repo` / `dist` / `add` / `build` |
| Input | one directory of `.rpm` / `.deb` files | packages added by path into a workspace |
| Layout produced | flat — packages and index in the same directory | Debian-style `pool/` plus `dists/` publication views |
| Persistent state | none (a transient journal during the operation only) | `sow.yml` plus one SQLite database per repository |
| Configuration | none — no config file is read | `sow.yml`, strictly validated |
| Multi-architecture | all architectures land in one flat index | one rendered view per architecture per Dist |
| History | none | monotonic generations and an operation ledger |
| Comparable to | `createrepo_c` + `dpkg-scanpackages` | `reprepro` |

Plain mode is the right choice when you have a directory of packages and want an index over it. Managed mode is the right choice when the same repository is going to be updated repeatedly over months, by policy, with an audit trail.

Neither path knows anything about remote endpoints. A finished repository directory is just files — you serve it with any web server or copy it with `rsync`. See [Serve Repositories](/docs/tutorial/serving/).

## Format coverage

| Capability | RPM / YUM | DEB / APT |
|---|---|---|
| Index files generated | `repodata/` with `primary`, `filelists`, `other` and `repomd.xml` | `Packages`, `Packages.gz`, `Release` |
| Checksums | SHA-256, checksum-named metadata files | SHA-256 only (no MD5Sum/SHA1) |
| Package facts read from | RPM header (never the filename) | `control` in the `.deb` archive |
| Coordinate (identity) | NEVRA | `name=version:arch` |
| Architecture views (Managed) | `x86_64`, `aarch64` | `binary-amd64`, `binary-arm64` |
| Architecture-neutral packages | `noarch` | `all` |
| by-hash index fetch | not applicable | yes, `Acquire-By-Hash: yes` |
| Metadata signature | `repodata/repomd.xml.asc` | `InRelease` and `Release.gpg` |
| Package signature | embedded OpenPGP signature, `fill` / `always` modes | not applicable |

A single command handles both formats at once. In Plain mode, a directory containing both `.rpm` and `.deb` files produces `repodata/` and `Packages` in one operation. In Managed mode, one Repository can own an RPM Dist and a DEB Dist that share the same `pool/`.

## Signing coverage

There are two independent trust chains, configured separately. See [Signing Model](/docs/feature/signing/) for the full picture.

| Chain | Plain mode | Managed mode | Verified by the client with |
|---|---|---|---|
| Repository metadata | not available | `signing.rpm.metadata.key`, `signing.deb.metadata.key` | dnf `repo_gpgcheck=1`, apt `Signed-By` |
| RPM package bodies | `create -S KEY [--overwrite]` | `signing.rpm.packages.mode: fill \| always` | dnf `gpgcheck=1` |

Metadata keys given as `file://` or `env://` are used by an in-process Go signer, so no external tool is needed. RPM package signing and `agent://` key references call the `rpm` and `gpg` binaries in your environment.

## Platform coverage

The binary builds for `darwin` and `linux` on `amd64` and `arm64`. There is no runtime dependency on a package manager, a database server, or a Python stack.

The only external programs SOW will ever invoke are `rpm` (for RPM package signing) and `gpg` (for `agent://` key references). A repository that uses no signing, or uses `file://`/`env://` metadata keys only, needs nothing installed beyond the `sow` binary itself.

One hard requirement applies to Managed mode: a repository's `pool/` and its `dists/` views must live on the same POSIX filesystem, because views are hardlink projections. Crossing a device boundary is a hard failure, never a silent copy. See [Pool & Architecture Views](/docs/feature/views/).

## Client compatibility

Every combination below was exercised against a real client:

| Client | Version | Result |
|---|---|---|
| AlmaLinux 8 / 9 / 10 `dnf` | dnf4 | `makecache` and `install` with `repo_gpgcheck=1` and `gpgcheck=1` |
| CentOS 7 `yum` | 3.4.3 | `makecache` and correct multi-version NEVRA listing |
| Debian 13 `apt` | 3.0.3 | `update` with InRelease verification and by-hash fetch, then `install` |
| Debian 12 `apt` | 2.6.1 | same, plus flat repositories via `[trusted=yes]` |
| `dnf reposync` | EL9 | complete mirror following the `pool/` layout |

The full matrix, including the by-hash requirement of APT ≥ 1.2, is in [Compatibility](/docs/reference/compatibility/).

## Compared with createrepo_c and reprepro

These are the tools SOW is measured against. The comparison below reflects side-by-side runs over the same package sets, not documentation claims.

| Dimension | SOW | createrepo_c | reprepro |
|---|---|---|---|
| RPM metadata | `primary`/`filelists`/`other`, semantically equivalent | baseline | — |
| sqlite repodata | not generated (explicit non-goal) | generated by default | — |
| DEB `Packages` fields | equivalent, SHA-256 only | — | baseline, emits MD5Sum + SHA1 + SHA256 |
| by-hash | supported (`Acquire-By-Hash: yes`) | — | **not supported** |
| Pool layout | `pool/<prefix>/<source>/` (no component level) | — | `pool/main/<prefix>/<source>/` |
| Per-architecture `Release` stubs | not generated (apt does not need them) | — | generated |
| Platforms | Linux and macOS, single binary | Linux in practice | Linux only |
| Transactions and crash recovery | journal with roll-forward/rollback | none | database is fragile |
| Audit | operation ledger with JSONL export | none | limited logging |

Two details are worth spelling out, because they surprise people migrating:

Against `createrepo_c` on 9 test packages and 87 real production packages, every field in `primary`, `filelists`, and `other` matched semantically — name, arch, EVR, checksum, sizes, provides, requires flags, files, changelog, header range. The single divergence: when an RPM header lists `/bin/sh` twice in both a pre and a non-pre context, SOW keeps one entry and `createrepo_c` keeps both.

Against `dpkg-scanpackages`, the `Packages` fields match, except that SOW emits only `SHA256` — modern APT clients need nothing else — and omits absent fields such as `Section` entirely rather than writing an empty value.

If you are moving an existing repository over, read [Migrate from createrepo_c / reprepro](/docs/tutorial/migration/) first; taking over a directory in place leaves the old tool's files on disk for you to remove.

## Performance anchors

Measured on macOS arm64, cold:

| Operation | Scale | Wall time |
|---|---|---|
| `sow create` | 9 RPMs | 0.31 s |
| `sow create` | 87 RPMs, 2.9 GB (full SHA-256) | 10.7 s |
| `sow add` + automatic build | 9 RPMs, 31 MB | ~1.3 s |
| `sow check` (all eight layers) | 16-package workspace | 0.12 s |

Commands that parse, hash, render, or verify accept `-j/--jobs N`, defaulting to the logical CPU count. Parallelism never changes the output: final serialization runs in a fixed order, so the same input always produces the same bytes.

## Deliberate non-goals

These are not missing features waiting to be built. They are excluded by design, and no empty command or hidden flag pretends otherwise:

- modulemd generation, injection, or passthrough
- sqlite repodata and zchunk
- SRPM / DSC source indexes
- remote publishing, CDN, object storage, or endpoint configuration of any kind
- multi-writer and multi-host operation
- garbage collection, cross-repository deduplication
- a serving daemon or a web UI
- building packages

SOW manages repositories on local disk and hands you a directory. What transports that directory is your choice.

## Next

- [Plain Flat Repositories](/docs/feature/plain/) — what `sow create` does, step by step
- [Managed Workspaces](/docs/feature/managed/) — the three-tier model
- [Core Concepts](/docs/start/concepts/) — the shorter mental model, if you have not read it yet
