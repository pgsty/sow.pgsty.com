---
title: "Features"
linkTitle: "Features"
description: "Plain and Managed repository generation, package pools, policy, signing, transactions, publication, and audit."
categories: [Feature]
tags: [plain, managed, policy, signing]
url: "/docs/feature/"
aliases:
  - "/docs/feature/overview/"
weight: 300
icon: fa-solid fa-cubes
---

SOW has two isolated execution paths. Plain mode is a stateless rebuild of one directory;
Managed mode records package membership and immutable repository generations in a workspace.
Neither path silently adopts state from the other.

## Capability matrix

| Capability | Plain | Managed |
|---|---:|---:|
| RPM and DEB metadata | yes | yes |
| Mixed RPM + DEB operation | one directory | one Repository, separate Dists |
| Persistent membership and generations | no | yes |
| Per-architecture views and neutral packages | no | yes |
| `exclude` and version `limit` policy | no | yes |
| Metadata signing | no | RPM and DEB |
| RPM package signing | `--sign-with` | `never`, `fill`, `always` |
| Transaction journal and recovery | rerun `create` | workspace, Repository, publication |
| Queryable operation log and JSONL export | no | yes |
| Publication targets | no | filesystem and R2 |

SOW parses packages and renders metadata in-process. It does not invoke
`createrepo_c`, `dpkg-scanpackages`, `reprepro`, or `modifyrepo_c`. RPM package signing
is the exception: it needs the host `rpm` command and GPG environment because it rewrites
package payloads.

## Repository formats

| Surface | RPM/YUM | DEB/APT |
|---|---|---|
| Package facts | RPM header | DEB control archive |
| Identity | NEVRA + exact-byte SHA-256 | `name=version:arch` + exact-byte SHA-256 |
| Indexes | `primary`, `filelists`, `other`, `repomd.xml` | `Packages`, `Packages.gz`, `Release` |
| Neutral architecture | `noarch` | `all` |
| Immutable index paths | checksum-named rpm-md | `by-hash/SHA256` |
| Managed metadata signatures | `repomd.xml.asc` | `InRelease`, `Release.gpg` |

SOW intentionally omits SQLite rpm-md, zchunk, modulemd, source-package indexes, and
MD5/SHA1 DEB manifests. It builds repository files; it does not run an HTTP server or CDN.

## Read by question

| Question | Page |
|---|---|
| What does `sow create` write and replace? | [Plain Flat Repositories](/docs/feature/plain/) |
| How do workspaces, repositories, Dists, and private state relate? | [Managed Workspaces](/docs/feature/managed/) |
| How does one pool feed many metadata-only views? | [Pool & Metadata Views](/docs/feature/views/) |
| Why was a package excluded or limited? | [Membership Policy](/docs/feature/policy/) |
| Which key signs which object? | [Signing Model](/docs/feature/signing/) |
| What happens after interruption? | [Transactions & Recovery](/docs/feature/transactions/) |
| How do I inspect, verify, and audit a repository? | [Observability & Audit](/docs/feature/audit/) |

For release targets, filesystem requirements, clients, and Providers, use
[Platforms & Integrations](/docs/reference/compatibility/).
