---
title: "Capability Overview"
linkTitle: "Capability Overview"
description: "The implemented v0.2.0 surface across repository generation, managed state, signing, publication, and compatibility."
url: "/docs/feature/overview/"
weight: 100
icon: fa-solid fa-table-list
---

SOW 0.2.0 is a local package repository manager delivered as one self-contained Go binary. It
generates repository metadata in-process and has no serving daemon.

## Execution paths

| Capability | Plain | Managed |
|---|---:|---:|
| RPM and DEB metadata | yes | yes |
| Mixed RPM + DEB operation | one directory | one Repository, separate Dists |
| Persistent membership and generations | no | yes |
| Architecture views | no | yes |
| `exclude` and version `limit` policy | no | yes |
| Metadata signing | no | RPM and DEB |
| RPM package signing | `--sign-with` | `never`, `fill`, `always` |
| Transaction journal and recovery | operation-local | Workspace, Repository, publication |
| Audit log and JSONL export | no | yes |
| Publication targets | no | filesystem and R2 |

Plain and Managed do not share state. `sow create` never discovers a Workspace; Managed
commands never adopt an arbitrary flat directory as state.

## Repository metadata

| Surface | RPM/YUM | DEB/APT |
|---|---|---|
| Package facts | RPM header | DEB control archive |
| Identity | NEVRA plus exact-byte SHA-256 | `name=version:arch` plus exact-byte SHA-256 |
| Indexes | `primary`, `filelists`, `other`, `repomd.xml` | `Packages`, `Packages.gz`, `Release` |
| Managed architecture names | `x86_64`, `aarch64` | `binary-amd64`, `binary-arm64` |
| Neutral architecture | `noarch` | `all` |
| Immutable index addressing | checksum-named rpm-md | `by-hash/SHA256` |
| Managed metadata signatures | `repomd.xml.asc` | `InRelease`, `Release.gpg` |

SOW intentionally does not generate SQLite rpm-md, zchunk, modulemd, or source-package
indexes. DEB metadata uses SHA-256 and does not emit MD5/SHA1 manifests.

## Managed lifecycle

Managed mode provides:

- strict `sow/v3` configuration and upward Workspace discovery;
- Repository isolation, one canonical package pool, and metadata-only views;
- Desired Membership, Built Generations, dirty-state detection, and physical changesets;
- bounded locks, durable operation journals, crash recovery, and fail-closed path checks;
- `status`, nine-layer `check`, package queries, and an exportable operation log;
- explicit Generation retention, local GC, and target-scoped publication/GC state;
- self-contained RPM leaf export for workflows that require local package hrefs.

## Signing and external programs

Metadata signing with path, `file://`, or `env://` private-key references is in-process.
An `agent://` metadata key uses `gpg`/`gpg-agent`. RPM package signing uses the environment's
`rpm` command and GPG setup because it rewrites package payloads. Metadata generation,
package parsing, SQLite state, and publication do not require external command-line tools.

## Publication

Configured targets bind one Repository to one provider prefix:

| Provider | v0.2.0 behavior |
|---|---|
| `filesystem` | publish and verify a Generation; conditional lifecycle deletion after recorded safety gates |
| `r2` | publish through the S3-compatible API; target GC is report-only and never deletes objects |

Publication is not an HTTP server. `public_endpoint` describes how SOW verifies the public
surface; the operator supplies the actual server, bucket, CDN, credentials, and access policy.

## Platforms and evidence

Release builds target Linux and macOS on `amd64` and `arm64`, with `CGO_ENABLED=0`.
Managed workspaces require local POSIX locking, fsync, and atomic rename semantics; network
filesystems are not claimed as supported build locations.

Client and provider claims are deliberately narrower than the metadata format surface.
See [Compatibility](/docs/reference/compatibility/) for the exact current CI and local
evidence, including what has not been tested end to end.

## Non-goals

- building packages;
- serving HTTP or operating a CDN;
- multi-writer or distributed coordination;
- cross-Repository payload deduplication;
- automatic R2 object deletion;
- module streams, source-package indexes, SQLite rpm-md, or zchunk;
- a web UI.

## Next

- [Plain Flat Repositories](/docs/feature/plain/)
- [Managed Workspaces](/docs/feature/managed/)
- [Signing Model](/docs/feature/signing/)
- [Publication & Recovery](/docs/design/publication/)
