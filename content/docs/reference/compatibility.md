---
title: "Compatibility"
linkTitle: "Compatibility"
description: "Which clients consume SOW repositories, which platforms run the binary, and the constraints you must respect."
url: "/docs/reference/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

SOW writes standard rpm-md and Debian archive metadata, so the question is not whether a
client *can* read it but which clients have actually been verified against it. This page
lists the tested matrix, the platforms the binary runs on, and the handful of constraints
that will bite you if you ignore them.

## Package manager clients

Every row below was exercised end to end against a repository built by SOW: refresh the
index, list packages, and install one.

| Client | Version | Result |
|---|---|---|
| AlmaLinux 10 `dnf` | dnf4 | `makecache` and `install` with `repo_gpgcheck=1` and `gpgcheck=1` |
| AlmaLinux 9 `dnf` | dnf4 | Same |
| AlmaLinux 8 `dnf` | dnf4 | Same |
| CentOS 7 `yum` | 3.4.3 | `makecache` and package listing, including correct multi-version NEVRA ordering |
| Debian 13 `apt` | 3.0.3 | `update` with `InRelease` verification and by-hash fetching, then `install` |
| Debian 12 `apt` | 2.6.1 | Same; also verified against a plain flat repository |
| `dnf reposync` | EL9 | Complete mirror of the pool-based layout |

Both signature checks were on for the RPM tests: `repo_gpgcheck=1` verifies
`repodata/repomd.xml.asc`, and `gpgcheck=1` verifies the package signatures. For APT,
`Signed-By` verification of `InRelease` was used, and HTTP logs confirm `apt` fetched its
indexes through `by-hash/SHA256/` rather than the direct paths.

CentOS 7's `yum` 3.4.3 is the oldest client tested. It predates by-hash and does not need
it — the RPM side has no equivalent mechanism, and checksum-named metadata files serve the
same purpose.

Plain flat repositories built with `sow create` are consumable by `dnf`, `yum`, and `apt`
over both `file://` and `http://`.

{{% alert title="Flat repositories and APT" color="info" %}}
A flat repository has no `Release` file, so `apt` will not verify it. Mark the source
`[trusted=yes]`, or use a managed distribution with metadata signing when authenticity
matters.
{{% /alert %}}

## Platforms

The binary is built with `CGO_ENABLED=0` and has no runtime library dependencies.

| OS | `amd64` | `arm64` |
|---|---|---|
| Linux | supported | supported |
| macOS (Darwin) | supported | supported |

Windows is not supported. SOW depends on POSIX advisory locks (`flock`), hardlinks, and
atomic `rename`, and there is no portable equivalent.

Building a repository on macOS and serving it from Linux is a supported workflow. To keep
it portable, SOW rejects any pool path that would collide under case-insensitive
comparison, so a repository built on case-sensitive Linux stays valid when copied to a
default macOS filesystem.

## Filesystem requirements

**Local POSIX filesystems only.** SOW is not tested on and does not claim support for NFS
or other network filesystems, which do not provide the locking and durability semantics
its transaction model depends on. Build locally, then copy the result wherever you like.

**`pool/` and `dists/` must share one filesystem.** Architecture views project the pool
with hardlinks, which cannot cross a device boundary. If they are on different
filesystems, SOW fails loudly rather than silently copying:

```text
<repo>/pool/...                                 # canonical bytes
<repo>/dists/<dist>/x86_64/pool/...             # hardlink, same inode
```

In practice this only matters if you mount a separate volume under a repository. The
staging directory is placed on the same filesystem as the target for the same reason —
that is what makes the final `rename` atomic.

Copying a repository elsewhere has no such requirement. A tool that does not preserve
hardlinks turns each alias into an independent regular file: functionally identical for
clients, just larger on disk. Use `rsync --hard-links` to keep the deduplication.

## Metadata SOW does not emit

A few things traditional tools produce are deliberately absent. All of them are optional
for every client tested above.

| Not generated | Consequence |
|---|---|
| SQLite repodata (`primary.sqlite.bz2` and friends) | None. `dnf` and `yum` use the XML metadata; the SQLite variants have been optional for years. |
| `modulemd` | Modular streams are out of scope. Non-modular packages are unaffected. |
| zchunk metadata | `dnf` falls back to full metadata downloads, which is its normal behavior when zchunk is absent. |
| `MD5Sum` and `SHA1` in `Release` | Requires a client that accepts a SHA256-only manifest. Every tested `apt` does. |
| `MD5sum` and `SHA1` fields in `Packages` | Same — `SHA256` is present and sufficient. |
| Per-architecture `Release` stubs under `binary-<arch>/` | `apt` does not require them; `reprepro` writes them, SOW does not. |
| Source indexes (SRPM, DSC) | Binary packages only. |

Taking `Release` and `Packages` together, a DEB distribution publishes exactly this and
nothing more:

```console
Acquire-By-Hash: yes
SHA256:
 95e8c59d21d69285ac788bd8ea78b0544b0a1395ae9a0e3a700ec13b420e5c39 2245 main/binary-amd64/Packages
 4d658bdf6a542999f737e5f89e3bdb504c205fb85cda76f3e4b1ef73619c5900 751 main/binary-amd64/Packages.gz
```

## by-hash and older APT

Managed DEB distributions always publish `by-hash/SHA256/` and advertise
`Acquire-By-Hash: yes`. This is what makes an index update safe for a client that fetched
`Release` a moment earlier: the old index stays reachable by digest while the new one is
published.

APT 1.2 (2015) and later use by-hash automatically. Older clients ignore the field and
fetch `main/binary-<arch>/Packages` directly, which SOW also always writes — so they work,
just without the update-race protection.

`reprepro` does not support by-hash at all, which is one practical reason to migrate.

## External tools

SOW does not invoke `createrepo_c`, `dpkg-scanpackages`, `modifyrepo_c`, or `repo2module`.
RPM headers and Debian control files are parsed in-process, and all metadata is rendered
in-process.

Exactly two operations reach outside the binary:

| Operation | Requires | Notes |
|---|---|---|
| RPM package signing | `rpm` and a working GPG environment | Plain `create --sign-with`, and managed `signing.rpm.packages.mode` set to `fill` or `always`. Signing always happens on a private staged copy. |
| Metadata signing with `agent://` | `gpg` with a running agent | Only for `agent://` key references. |

Metadata signing with a `file://` or `env://` key is done in-process, so a repository with
signed `InRelease` and `repomd.xml.asc` needs no external tooling at all.

## Version

The compatibility results on this page were produced with:

```bash
sow version
```

```console
sow 0.2.0-dev darwin/arm64 go1.26.5
```

Repository output is deterministic: fixed timestamps, fixed compression parameters, and
stable ordering mean the same inputs and configuration produce byte-stable metadata.
Re-running `sow create` over an unchanged directory is a no-op that rewrites nothing.

## See also

- [Installation](/docs/start/install/) — platform matrix and how to build from source
- [Repository Layout](/docs/reference/layout/) — where the hardlink constraint comes from
- [Migrate from createrepo_c / reprepro](/docs/tutorial/migration/) — feature-level comparison
- [Serve Repositories](/docs/tutorial/serving/) — client configuration for `dnf` and `apt`
