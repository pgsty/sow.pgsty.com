---
title: "Platforms & Integrations"
linkTitle: "Platforms"
description: "Release targets, filesystem requirements, repository clients, publication Providers, and automated integration coverage."
categories: [Reference]
tags: [rpm, deb, yum, apt, object-storage]
url: "/docs/reference/compatibility/"
aliases:
  - "/docs/design/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

This page defines the environments SOW ships for, the storage semantics it requires, and
the exact scope of its automated integrations. Repository generation happens inside the
SOW binary; a real package manager remains the final check for a deployed repository.

## Release targets

| Operating system | `amd64` | `arm64` | Artifact |
|---|---:|---:|---|
| Linux | yes | yes | archive, RPM, DEB |
| macOS | yes | yes | archive |
| Windows | no | no | not supported |

Release binaries use `CGO_ENABLED=0` and require no language runtime. The source module requires
Go 1.27.1 or newer. Archives include `README.md`, `CHANGELOG.md`, the Apache-2.0 `LICENSE`,
and `THIRD_PARTY_NOTICES`. Linux packages include the same license and third-party notices
with the binary. Use [`sow version`](/docs/command/)
to print the product version, target OS/architecture, and build toolchain.

## Workspace filesystem

Managed workspaces belong on a local POSIX filesystem. Correctness depends on advisory
locks, `fsync`, descriptor-bound path checks, and atomic same-filesystem rename. NFS and
other network filesystems are not supported workspace locations. On macOS, use APFS:
HFS+ lacks atomic directory exchange, and SOW rejects the build.

The public `<workspace>/<repo>/` tree is different: it is a closed `pool/ + dists/`
namespace designed for whole-root copying and publication. It does not depend on SQLite,
private journals, or view-local hard-link identity. Keep the complete Repository together
and never expose `.sow/`.

SOW rejects symlinked control paths, unsafe regular files, overlapping filesystem targets,
and a new pool path that collides case-insensitively with an existing or published path,
including identical bytes added under a file name that differs only by case (add the file
under its original name). On a case-insensitive workspace filesystem, such as the macOS
default, SOW also rejects a new package whose source directory differs only by case from an
existing package's (for example `CaseDemo` and `casedemo`), and `publish` to a filesystem
target on a case-insensitive volume refuses such aliases before creating an attempt. On
case-sensitive filesystems (Linux) those source directories stay distinct, so a Repository
that contains both cannot be moved to a case-insensitive filesystem.

## Automated integration matrix

| Surface | Environment | Verified behavior |
|---|---|---|
| Production CLI clean room | Linux CI | Builds the shipping binary; creates mixed Plain RPM/DEB metadata; initializes `sow/v3`; creates RPM and DEB Dists; adds fixtures; runs query, build, check, changes, config, and log commands |
| Plain APT client | Ubuntu 22.04 container | Serves `sow create` output over HTTP; runs `apt-get update`, package discovery, exact-version selection, download, and install with an explicitly trusted unsigned source |
| RPM detached-signature transition | AlmaLinux 8, 9, and 10 containers | Runs real DNF clients against serial `repomd.xml` / `repomd.xml.asc` transition states and pins which combinations succeed or fail |
| S3-compatible transport | Pinned MinIO container | Exercises bucket listing, HEAD, GET, single-part create-only/CAS PUT, replay, and object SHA-256 metadata; retries and prefix confinement are covered by local protocol tests |
| Release packaging | Linux CI | Builds four archives, two RPMs, two DEBs, and `SHA256SUMS`; checks package paths, Apache-2.0 metadata, and packaged license bytes |

The current MinIO integration does not validate conditional multipart completion. Multipart
request/protocol tests are separate; they do not establish compatibility with hosted R2.
Verify real R2 multipart behavior separately before treating that path as accepted.

The DNF signature-transition probe is a protocol test, not a complete Managed RPM install.
The APT job covers an unsigned Plain repository, not Managed metadata signing. Run the
exact dnf/APT version, repository URL, access policy, and signing policy used by your
deployment before promoting it.

## Repository client contract

Plain RPM repositories expose `repodata/` beside package files. Plain DEB repositories
expose `Packages` and `Packages.gz` beside package files. They can be consumed through
`file://` or HTTP after the client trust policy is configured.

Managed clients consume the complete Repository root:

- APT indexes live below `dists/<dist>/main/binary-<arch>/` and refer to the root `pool/`.
  `Release` advertises SHA-256 by-hash indexes; configured signing adds `InRelease` and
  `Release.gpg`.
- RPM metadata lives below `dists/<dist>/<arch>/repodata/` and uses relative locations
  that point back to the root `pool/`. Serve the whole Repository, not one architecture
  directory.

Default `dnf reposync` rejects the canonical Managed RPM parent-relative package paths.
For that workflow, generate a self-contained copy with
[`sow export rpm-leaf`](/docs/command/export/). The export has local package paths and a
completion manifest; it is not a second canonical Repository.

Managed RPM and `export rpm-leaf` use a fixed `0` repomd data timestamp and expose no
`--metadata-timestamp` option. They cannot directly take over the same EL7 repository ID
while clients retain a positive cached timestamp; changing the base URL alone does not help.
Use a new client repository ID or clear its metadata cache. To keep the old ID and cache,
continue with Plain `create` and an explicit publication time, following the
[migration guide](/docs/tutorial/yum-migration/) and re-signing repomd.

## Migrating an existing Plain YUM repository

Plain emits the primary, filelists, and other XML streams. It does not generate legacy
SQLite metadata or module streams. Ordinary RPMs can be served with an appropriate
`module_hotfixes=1` policy; module profiles and `dnf module install` require a different workflow.

EL7 YUM compares the largest `repomd.xml` data timestamp with its cached copy. SOW 0.5.0
adds `create --metadata-timestamp SECONDS`, but its default is still `0`.
An existing online repository needs a timestamp at least as large as its historical
maximum; actual updates should advance it. Updating revision or file mtime is insufficient.
The caller maintains this history and signs `repomd.xml` separately. Test with the same
repository URL and ID, retaining the old cache and the intended GPG checks. Follow the
[migration guide](/docs/tutorial/yum-migration/) for the complete procedure.

RPM dependency projection follows modern createrepo_c semantics for `%pretrans` and
`%posttrans` requirements. The 0.5 regression tests strengthen that contract without changing
the parser. Older createrepo_c versions can emit different dependency rows or `pre="1"`
attributes; compare dependency meaning and real client behavior rather than raw row counts.
See [upstream PR #427](https://github.com/rpm-software-management/createrepo_c/pull/427).

RPM format v6 signatures are not supported in 0.5.0. The new signature tag can be treated
as unsigned, so package signing or verification may reject such a package. Use RPM format v4
packages for signing workflows; do not interpret this limitation as a promise to preserve
or verify an RPM format v6 signature.

## Publication Providers

| Provider | Contract |
|---|---|
| `filesystem` | Publishes beneath a pre-existing safe `file://` endpoint. Target GC performs exact conditional deletion only after cache grace and storage/public absence evidence. |
| `r2` | Publishes through the S3-compatible storage transport. Target GC writes exact report-only candidate records and never deletes remote objects. |

Both Providers publish the same complete `pool/ + dists/` namespace beneath the configured
prefix. `public_endpoint` is part of target verification; SOW does not create an HTTP
server, DNS record, bucket policy, CDN, or credentials. Validate those deployment-owned
surfaces on a nonproduction prefix before enabling production publication.

Filesystem and R2 HTTP(S) endpoints share the same canonical-GET content verifier. Filesystem
targets may also use descriptor-bound `file://` verification. R2 public endpoints must be HTTP(S).
Target name, `public_endpoint`, and `max_cache_ttl` may be changed only through explicit
[`publish --rebind`](/docs/command/publish/#rebind-mutable-target-settings); storage identity and
prefix are immutable.

## Deployment gate

Before delivery, require a clean deep check and inspect the physical change plan:

```bash
sow check -r REPOSITORY
sow changes 0 -r REPOSITORY
```

After publication, fetch the actual `repomd.xml` or `Release` URL and run the target package
manager. A local build, a Provider write, HTTP reachability, and a client install are
separate checks.

See [Repository Layout](/docs/reference/layout/), [Signing](/docs/feature/signing/), and
[Publication & Recovery](/blog/design/publication/) for the corresponding contracts.
