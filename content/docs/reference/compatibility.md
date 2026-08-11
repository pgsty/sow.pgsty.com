---
title: "Platforms & Integrations"
linkTitle: "Platforms"
description: "Release targets, filesystem requirements, repository clients, publication Providers, and automated integration coverage."
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

Release binaries use `CGO_ENABLED=0` and require no language runtime. The project builds
with Go 1.26.5. Archives include `README.md`, `CHANGELOG.md`, and the Apache-2.0 `LICENSE`;
Linux packages install the same license with the binary. Use [`sow version`](/docs/command/)
to print the product version, target OS/architecture, and build toolchain.

## Workspace filesystem

Managed workspaces belong on a local POSIX filesystem. Correctness depends on advisory
locks, `fsync`, descriptor-bound path checks, and atomic same-filesystem rename. NFS and
other network filesystems are not supported workspace locations.

The public `<workspace>/<repo>/` tree is different: it is a closed `pool/ + dists/`
namespace designed for whole-root copying and publication. It does not depend on SQLite,
private journals, or view-local hard-link identity. Keep the complete Repository together
and never expose `.sow/`.

SOW rejects symlinked control paths, unsafe regular files, overlapping filesystem targets,
and case-folded pool-path collisions. This keeps one Repository portable between
case-sensitive Linux filesystems and the default case-insensitive macOS setup.

## Automated integration matrix

| Surface | Environment | Verified behavior |
|---|---|---|
| Production CLI clean room | Linux CI | Builds the shipping binary; creates mixed Plain RPM/DEB metadata; initializes `sow/v3`; creates RPM and DEB Dists; adds fixtures; runs query, build, check, changes, config, and log commands |
| Plain APT client | Ubuntu 22.04 container | Serves `sow create` output over HTTP; runs `apt-get update`, package discovery, exact-version selection, download, and install with an explicitly trusted unsigned source |
| RPM detached-signature transition | AlmaLinux 8, 9, and 10 containers | Runs real DNF clients against serial `repomd.xml` / `repomd.xml.asc` transition states and pins which combinations succeed or fail |
| S3-compatible transport | Pinned MinIO container | Exercises bucket listing, HEAD, GET, create-only PUT, compare-and-swap PUT, replay, object metadata, and prefix confinement |
| Release packaging | Linux CI | Builds four archives, two RPMs, two DEBs, and `SHA256SUMS`; checks package paths, Apache-2.0 metadata, and packaged license bytes |

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

## Publication Providers

| Provider | Contract |
|---|---|
| `filesystem` | Publishes beneath a pre-existing safe `file://` endpoint. Target GC performs exact conditional deletion only after cache grace and storage/public absence evidence. |
| `r2` | Publishes through the S3-compatible storage transport. Target GC writes exact report-only candidate records and never deletes remote objects. |

Both Providers publish the same complete `pool/ + dists/` namespace beneath the configured
prefix. `public_endpoint` is part of target verification; SOW does not create an HTTP
server, DNS record, bucket policy, CDN, or credentials. Validate those deployment-owned
surfaces on a nonproduction prefix before enabling production publication.

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
[Publication & Recovery](/docs/design/publication/) for the corresponding contracts.
