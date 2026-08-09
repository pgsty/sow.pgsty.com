---
title: "Compatibility"
linkTitle: "Compatibility"
description: "The exact v0.2.0 build, client, mirror-tool, filesystem, and publication evidence."
url: "/docs/reference/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

This page reports evidence, not inferred compatibility. Metadata syntax, a clean-room CLI
run, a real package client, a mirror tool, and a storage provider are separate checks.

## Current automated evidence

| Surface | Environment | What the active check proves | What it does not prove |
|---|---|---|---|
| v0.2.0 CLI clean room | Linux CI | builds the production binary; creates mixed Plain RPM/DEB metadata; initializes `sow/v3`; creates empty RPM/DEB Dists; adds fixtures; runs query, build, check, changes, config, and log commands | no real package-manager client or remote Provider |
| Plain APT client | Ubuntu 22.04 container | current `sow create` output over HTTP; `apt update`, discovery, exact-version install; unsigned flat source with `[trusted=yes]` | Managed APT, `Release` signatures, or `by-hash` consumption |
| RPM detached-signature probe | AlmaLinux 8, 9, 10 containers | real DNF behavior while `repomd.xml` and its detached signature are changed serially | current Managed CLI layout, package install, package signatures, or `sow export rpm-leaf` |
| S3-compatible protocol fixture | pinned MinIO | the separate `internal/publish` provider implementation's S3 operations and conditional-delete failure behavior | the current `internal/v2/managed` `sow publish r2` CLI path or a Cloudflare R2 account |

The distinction in the last two rows is intentional. They are useful protocol evidence,
but must not be advertised as end-to-end product compatibility.

## Current client claims

- **Verified:** a Plain DEB repository from the v0.2.0 CLI is consumable and installable by
  Ubuntu 22.04 APT over HTTP when explicitly trusted.
- **Format implemented, current full-client gate absent:** Plain and Managed rpm-md output;
  Managed APT `Release`/`by-hash`; metadata and RPM payload signatures.
- **Not claimed by the active matrix:** CentOS 7, Debian 12/13, DNF against the canonical
  Managed Repository, signed Managed APT installation, or a complete signed DNF install.

These absences mean unverified in the current gate, not known incompatible.

## Canonical RPM layout and `reposync`

Managed RPM views contain metadata only. Package hrefs resolve from the architecture
repository base `dists/DIST/ARCH/` back to the Repository pool, for example:

```text
../../../pool/p/package/package.rpm
```

rpm-md package locations are relative URLs. Default `dnf reposync` applies a leaf-root
safety check and rejects this parent traversal, so the canonical Managed view is explicitly
unsupported as a default `reposync` source.

Create a self-contained artifact when that contract is required:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

The export rewrites package hrefs to a local `pool/` and does not modify the Repository.
The active Integration workflow does not currently run a real `reposync` client against
this export, so treat that final client gate as unverified.

## Binary platforms

The release configuration builds `CGO_ENABLED=0` archives for:

| OS | `amd64` | `arm64` |
|---|---:|---:|
| Linux | built | built |
| macOS (Darwin) | built | built |

Linux RPM and DEB packages are also staged. Windows is not supported. A build target is
not proof of every OS-version/runtime combination; the current automated clean-room and
client jobs run on Linux.

## Filesystem boundary

Build Managed workspaces on a local POSIX filesystem. Correctness depends on advisory
locks, fsync, safe path inspection, and atomic rename. NFS and other network filesystems
are not claimed as supported workspace locations.

The committed public Repository is a closed `pool/ + dists/` tree and does not depend on
view-local hardlink identity. Keep both directories together. For publication, prefer a
configured target or an operator-controlled staged atomic switch over modifying a live
tree in place.

For a `filesystem` target, the `file:///...` endpoint directory must already exist and
resolve to one canonical real directory. SOW refuses a missing endpoint or a symlinked
alias. A fresh v0.2.0 local run has verified initial publication and idempotent replay.

## Publication Providers

| Provider | Implemented behavior | Current evidence boundary |
|---|---|---|
| `filesystem` | publish, verify, checkpoint, grace, conditional lifecycle maintenance | focused tests plus a fresh local CLI run |
| `r2` | S3-compatible publish; target GC records report-only candidates and never deletes objects | source and focused tests; no current real CLI/Provider end-to-end run |

A configured `public_endpoint` is part of target verification; it does not create a web
server, CDN, bucket policy, DNS record, or credentials. Validate those in the deployment
environment.

## Intentionally omitted metadata

- SQLite rpm-md, zchunk, and modulemd;
- source-package indexes;
- MD5/SHA1 DEB manifests;
- Plain-mode DEB `Release` and signatures.

## External tools

Metadata generation and parsing are in-process. RPM package signing needs `rpm` and a
working GPG environment. `agent://` metadata keys need `gpg` with `gpg-agent`; path,
`file://`, and `env://` metadata keys are signed in-process.

## Version

```console
sow 0.2.0 darwin/arm64 go1.26.5
```

OS, architecture, and Go toolchain reflect the binary being run. `sow/v3` and
`sow.cli/v1` are configuration/protocol identifiers.

## See also

- [Repository Layout](/docs/reference/layout/)
- [`sow publish`](/docs/command/publish/) and [`sow gc`](/docs/command/gc/)
- [Compatibility design](/docs/design/compatibility/)
