---
title: "Platforms & Integrations"
linkTitle: "Platforms"
description: "Supported platforms, filesystem requirements, repository formats, clients, and integration coverage."
categories: [Reference]
tags: [rpm, deb, yum, apt, object-storage]
url: "/docs/reference/compatibility/"
aliases:
  - "/docs/design/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

SOW builds RPM and DEB repository files on Linux and macOS. Choose a supported local
filesystem for the workspace, then configure HTTP or storage access for clients.

<span id="release-targets" data-td-print-local></span>

## Platforms

| Operating system | `amd64` | `arm64` | Release formats |
|---|---:|---:|---|
| Linux | Yes | Yes | Archive, RPM, DEB |
| macOS | Yes | Yes | Archive |
| Windows | No | No | — |
{.matrix}

Release binaries use `CGO_ENABLED=0` and need no language runtime. Source builds require
Go 1.27.4 or later. Archives include the `sow` binary and the Apache-2.0 `LICENSE`;
Linux packages install `/usr/bin/sow` and the Apache-2.0 license.
Run `sow version` to inspect the binary version, platform, and build toolchain.

## Workspace filesystem

Use a local POSIX filesystem with advisory locks, `fsync`, and atomic same-filesystem
rename. Network filesystems such as NFS are not supported workspace locations.
On macOS, use APFS; SOW rejects builds when required atomic directory exchange is unavailable.

Keep the workspace's public tree and private staging on the same filesystem.
Serve only `<workspace>/<repo>/`. You can copy that complete `pool/ + dists/` tree to
other storage without the private database or journal.

SOW rejects full pool paths that differ only in case. On case-insensitive filesystems,
SOW also rejects source-directory case aliases. A repository created on a case-sensitive
volume can contain source directories that a case-insensitive destination cannot represent;
filesystem publication checks this before starting. See [Layout](/docs/reference/layout/).

<span id="repository-client-contract" data-td-print-local></span>

## Repository formats and clients

| Output | Client entry point | Package locations |
|---|---|---|
| Plain RPM | `repodata/repomd.xml` | Beside `repodata/` |
| Plain DEB | `Packages` or `Packages.gz` | Beside the indexes; flat APT source |
| Managed RPM | `dists/<dist>/<arch>/repodata/repomd.xml` | Relative paths back to root `pool/` |
| Managed DEB | `dists/<dist>/Release` or signed `InRelease` | Root-relative `pool/` paths |
{.wide .expand}

Managed APT uses component `main` and SHA-256 by-hash indexes. Metadata signing produces
RPM `repomd.xml.asc` or APT `InRelease` and `Release.gpg`.

For binary DEBs, SOW reads `control.tar` uncompressed or compressed with gzip, bzip2, xz, or zstd, and normalizes legacy Latin-1 bytes (`>= 0x80`) in binary `control` files to UTF-8. Rebuild packages that use `control.tar.lzma` with a supported control archive (dropped in 0.8.0) before importing them.

### Publication times

New Managed operations record one publication time when they build metadata, except `sow repo migrate`.
APT `Release` dates, RPM `repomd.xml` data timestamps, and metadata signatures use that time.
RPM `revision` remains the Generation number.

Recovery reuses the recorded time. Older journals without a recorded publication time retain their previous timestamp behavior.
No-op operations leave publication times unchanged.

### XML and SQLite RPM metadata

SOW generates gzip-compressed `primary`, `filelists`, and `other` XML. It does not generate
SQLite `primary_db`, `filelists_db`, or `other_db`. These are distinct metadata formats;
a tool that only accepts `primary_db` needs an XML input path or a separate conversion.

Missing `primary_db` does not by itself prevent YUM from reading the repository. YUM's
upstream loader falls back to XML and creates its local cache when a suitable SQLite
index is unavailable. See the [YUM metadata loader](https://github.com/rpm-software-management/yum/blob/master/yum/yumRepo.py).
SOW's generated XML uses gzip, so zstd support is a separate question when comparing
other repositories or tools.

SOW does not generate zchunk, modulemd, or source-package indexes. If your clients need
module profiles or `dnf module install`, keep a tool that provides module metadata.
For ordinary RPM installation from modular packages, apply the appropriate client
`module_hotfixes` policy; see the [migration guide](/docs/tutorial/yum-migration/).

### `dnf reposync`

Default `dnf reposync` confines downloads to one repository directory, so it rejects the
parent-relative package locations in a canonical Managed RPM view. This follows its
[documented safe-write path](https://dnf-plugins-core.readthedocs.io/en/latest/reposync.html).
Use [`sow export rpm-leaf`](/docs/command/export/) to generate a self-contained directory
for that workflow.

<span id="migrating-an-existing-plain-yum-repository" data-td-print-local></span>

### Existing EL7 caches

EL7 YUM compares metadata data timestamps with its cached repository. Plain
`create --metadata-timestamp SECONDS` and `prune --metadata-timestamp SECONDS` let you
preserve and advance an existing publication time. The default is `0`.

Exported RPM leaves and RPM metadata generated during `sow repo migrate` use timestamp `0`, with no timestamp override.
Later Managed builds use their recorded publication time.
For these outputs, use a new repository ID if the existing ID has cached a positive timestamp.
Alternatively, clear that ID's metadata cache. Changing the base URL alone is insufficient.
To retain the old ID and cache, follow the timestamp procedure with Plain mode in
[YUM migration](/docs/tutorial/yum-migration/).

### RPM formats and signatures {#rpm-signatures}

SOW supports RPM format v4 and RPM format v6 (lead major versions 3 through 6, `PAYLOADSHA256` without `PAYLOADSHA256ALGO`, and native `RPMSIGTAG_OPENPGP` tag `278` OpenPGP v4 and v6 signature arrays) across Plain `create` / `prune` and Managed `add` / `build` / `check`, including dual- and multi-signed RPMs. SOW also verifies RSA, DSA, ECDSA, and EdDSA (Ed25519) OpenPGP packets in RPM header signature tag `267` (`RPMSIGTAG_DSA`) and legacy PGP tags; when tag `278` is present it is authoritative. RPM indexing accepts identical duplicate main-header tags (such as EL10 duplicate `SOURCERPM`) while rejecting conflicting main tags and duplicate signature-header tags. Metadata signing supports RSA, EdDSA (Ed25519/Ed448), ECDSA, and DSA keys; see [Signing](/docs/feature/signing/).

## Publication providers

| Provider | Publication | Target GC |
|---|---|---|
| `filesystem` | Writes below an existing canonical `file://` endpoint | Conditional deletion after cache grace, followed by public-absence verification |
| `r2` | Writes through S3-compatible storage operations | Reports candidates by default. `gc TARGET --delete` rechecks eligible objects, deletes them and verifies absence |
{.wide .expand}

Both publish the complete repository under the configured prefix. Configure the HTTP
service, DNS, credentials, access policy, and cache behavior for that storage.
`public_endpoint` tells SOW where to verify public content; it does not create the service.
R2 public endpoints must use HTTP(S). Filesystem targets also accept `file://` verification.

<span id="automated-integration-matrix" data-td-print-local></span>
<span id="deployment-gate" data-td-print-local></span>

## Automated coverage

The source tree contains these integration checks:

| Check | Environment | Scope |
|---|---|---|
| Core contract tests | Linux and macOS CI | Repository manager, recovery, signing, and patched RPM parser unit and contract suites |
| CLI clean-room workflow | Linux CI | Shipping binary, mixed Plain output, Managed initialization, RPM/DEB Dists, queries, build, and check |
| Plain APT client | Ubuntu 22.04 | Update, discovery, download, and installation from an explicitly trusted unsigned source |
| Signed Managed clients | Ubuntu 22.04 and AlmaLinux 9 | APT and DNF verify signed repository metadata and install a package |
| RPM signing and detached-signature transitions | AlmaLinux 8, 9, and 10 | Protected-key signing with a password file and DNF behavior while the detached signature changes |
| S3-compatible publication | Pinned PGSTY Silo container | Object transport, Managed GC deletion, republishing identical bytes, and a subsequent no-op publish |
| Release packaging | Linux CI | Four archives, two RPMs, two DEBs, checksums, package paths, and license files |
{.wide .expand}

Verify conditional multipart completion against the hosted R2 endpoint used in your deployment.

Before switching clients, run `sow check`, publish to the intended target, then use the
actual client configuration to refresh indexes and install a package. See
[Serving](/docs/tutorial/serving/) for client setup.
