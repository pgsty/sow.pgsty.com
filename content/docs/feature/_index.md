---
title: "Features"
linkTitle: "Features"
description: "Choose a repository mode, then add package policies, signing, publication, and audit."
categories: [Feature]
tags: [plain, managed, policy, signing]
url: "/docs/feature/"
aliases:
  - "/docs/feature/overview/"
weight: 300
icon: fa-solid fa-cubes
---

SOW creates repository indexes in two modes. Choose Plain for a directory you can rebuild.
Choose Managed for ongoing package updates, policy, signing, and publication.

<span id="capability-matrix" data-td-print-local></span>

## Capabilities

| Capability | Plain | Managed |
|---|---|---|
| RPM and DEB indexes | One directory, either or both formats | One repository, separate Dists |
| Stored membership and generations | — | Yes |
| Per-architecture views | — | Yes, including neutral packages |
| Package exclusions | Fixed cleanup with `--pigsty` | Configurable per Dist |
| Version limits | — | Configurable per Dist |
| Metadata signing | — | RPM and DEB |
| RPM package signing | `--sign-with` | `never`, `fill`, `always` |
| Recovery after interruption | Rerun `create` | Recorded operations and publication attempts |
| Operation log and JSONL export | — | Yes |
| Publication targets | — | Filesystem and R2 |

SOW parses packages and generates indexes itself. It does not require `createrepo_c`,
`dpkg-scanpackages`, or `reprepro`. RPM package signing uses the host `rpm` and GPG
environment. Metadata signing uses `gpg` when a key reference resolves to a GPG key identifier.

<span id="repository-formats" data-td-print-local></span>

## Generated formats

| Format | Plain | Managed additions |
|---|---|---|
| RPM | `primary`, `filelists`, `other` XML and `repomd.xml` | Architecture views; optional `repomd.xml.asc` |
| DEB | `Packages`, `Packages.gz` | `Release`, by-hash indexes; optional `InRelease` and `Release.gpg` |

RPM XML is gzip-compressed. SOW does not generate SQLite rpm-md, zchunk, modulemd, or
source-package indexes. Use your HTTP server or object-storage service to serve the
output. See [Platforms and integrations](/docs/reference/compatibility/) for client details.

<span id="read-by-question" data-td-print-local></span>

## Learn a feature

| Task | Read |
|---|---|
| Generate indexes beside existing packages | [Plain repositories](/docs/feature/plain/) |
| Manage repeated package updates | [Managed workspaces](/docs/feature/managed/) |
| Share package bytes across Dist views | [Pool and views](/docs/feature/views/) |
| Exclude packages or keep recent versions | [Membership policy](/docs/feature/policy/) |
| Sign packages and indexes | [Signing](/docs/feature/signing/) |
| Continue after an interruption | [Transactions and recovery](/docs/feature/transactions/) |
| Inspect state, validate output, and read history | [Observability and audit](/docs/feature/audit/) |
