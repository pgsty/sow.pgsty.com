---
title: "Compatibility"
linkTitle: "Compatibility"
description: "Verified package clients, release platforms, reposync boundaries, and publication-provider status for SOW 0.2.0."
url: "/docs/reference/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

SOW 0.2.0 writes standard rpm-md and Debian archive metadata. This page separates normal
client consumption from compatibility exports and separates integration evidence from
provider-specific production validation.

## Package manager clients

The maintained client matrix exercises index refresh, package discovery, and install:

| Client | Tested behavior |
|---|---|
| AlmaLinux 8 / 9 / 10 `dnf` | `makecache` and install, including repository and package signature checks |
| CentOS 7 `yum` 3.4.3 | metadata and package listing, including multi-version NEVRA ordering |
| Debian 12 / 13 `apt` | signed `InRelease`, by-hash index fetch, and install |

Plain repositories from `sow create` are consumable by `dnf`, `yum`, and `apt` over
`file://` and HTTP. A flat APT repository has no signed `Release`; use `[trusted=yes]` or
use a signed managed distribution when authenticity matters.

## Canonical RPM layout and reposync

Ordinary DNF/YUM consumption is supported against metadata-only views. Default
`dnf reposync` is **not** supported against that canonical view because rpm-md package
hrefs use `../../../pool/...` and the mirror tool rejects destinations outside its leaf
download root.

For a downstream mirror workflow, create an explicit self-contained artifact:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

The export rewrites hrefs to a local `pool/`. Treat export verification separately from
canonical repository verification; exporting does not change the managed repository.

## Binary platforms

Release archives are built with `CGO_ENABLED=0` for:

| OS | `amd64` | `arm64` |
|---|---|---|
| Linux | supported | supported |
| macOS (Darwin) | supported | supported |

Linux also receives RPM and DEB packages. Windows is not supported: the workspace model
depends on POSIX advisory locks and atomic rename semantics.

## Filesystem boundary

Build managed repositories on a local POSIX filesystem. SOW does not claim NFS or other
network-filesystem correctness because its transaction model depends on local locking,
fsync, and rename behavior. The canonical v0.2.0 layout does not require hardlinks between
`pool/` and `dists/`; the earlier view-local hardlink layout was an unreleased prototype.

Once committed, the complete public repository can be copied normally or published with
SOW. Preserve `pool/` and `dists/` together.

## Publication providers

| Provider | v0.2.0 status |
|---|---|
| `filesystem` | implemented, including conditional lifecycle maintenance after grace and absence checks |
| `r2` | implemented through the S3-compatible API; Integration CI exercises the path with pinned MinIO |
| Cloudflare R2 production account | provider-specific authorization, credentials, and hosted behavior must be verified in that environment |
| R2 deletion | deliberately disabled; `sow gc TARGET` persists a report-only candidate set and never deletes objects |

This distinction matters: a green S3-compatible integration test is implementation
evidence, not proof that a particular Cloudflare account or public CDN is configured.

## Metadata SOW intentionally omits

| Not generated | Consequence |
|---|---|
| SQLite repodata | DNF/YUM use the XML metadata |
| `modulemd` | modular streams are out of scope |
| zchunk | clients download normal compressed metadata |
| MD5/SHA1 DEB manifests | SHA256 is required |
| source-package indexes | v0.2.0 manages binary packages |

Managed DEB views publish `by-hash/SHA256/`; RPM views use checksum-named metadata files.
Both keep immutable metadata reachable while the mutable pointer changes.

## External tools

Metadata generation and parsing are in-process. RPM package signing requires `rpm` and a
working GPG environment. `agent://` metadata keys require `gpg` with an agent; `file://`
and `env://` metadata signing is in-process.

## Version

```console
$ sow version
sow 0.2.0 darwin/arm64 go1.26.5
```

The exact OS, architecture, and Go version reflect the binary being run. Release identity
is `v0.2.0`; names such as `sow.cli/v1`, `sow/v3`, and `sow/export/v1` are protocol or
schema identifiers, not product versions.

## See also

- [Repository Layout](/docs/reference/layout/)
- [Configuration](/docs/reference/config/)
- [CLI: Publish, Retain, GC, and Export](/docs/reference/cli/publication/)
