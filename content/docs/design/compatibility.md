---
title: "Compatibility Boundaries"
linkTitle: "Compatibility Boundaries"
description: "Why SOW evaluates format, product CLI, clients, mirror tools, filesystems, HTTP, and Providers separately."
url: "/docs/design/compatibility/"
weight: 500
icon: fa-solid fa-table-cells
---

“Compatible” is not one state. SOW separates the following contracts:

| Contract | Required evidence |
|---|---|
| Metadata format | parser, renderer, and closure validation |
| Product CLI | production binary on a fresh Workspace |
| Package client | the named client refreshes, resolves, verifies as configured, downloads, and installs |
| Mirror tool | the named tool materializes a complete repository within its path rules |
| Workspace filesystem | locks, fsync, safe paths, and atomic rename on the named filesystem |
| Publication Provider | current CLI path against that Provider, including recovery and public verification |
| HTTP/CDN | actual URL normalization, access policy, cache behavior, and protocol entry points |

Evidence for one contract never promotes another.

## Canonical Repository versus mirror leaf

One Repository owns one canonical package pool. RPM views keep only metadata and use
parent-relative hrefs back to that pool. The layout is closed only when `pool/ + dists/`
are delivered together; it violates the default `dnf reposync` leaf-root safety rule.

SOW therefore declares two different artifacts:

- the canonical Repository, served and published as `pool/ + dists/`;
- an explicit `sow export rpm-leaf` artifact with a local `pool/` for downstream mirror
  workflows.

Success of either artifact does not prove the other. The export also remains outside
membership, Generation, retention, and publication state.

## Filesystem boundary

Workspace correctness depends on local POSIX semantics. The public tree does not depend on
package hardlinks between pool and views and can be copied as a complete root. Private
workspace state cannot be copied into the served prefix.

A safe deployment either uses `sow publish` or stages a complete verified tree and switches
an operator-owned parent reference atomically. An unordered, in-place sync of a live tree
does not inherit SOW's pointer ordering or recovery guarantees.

## Provider boundary

The parser accepts `filesystem` and `r2`, but configuration acceptance is only the first
gate. A Provider claim also needs upload, replay, recovery, public verification, and—if
deletion is allowed—conditional deletion evidence.

- Filesystem publication is implemented and locally exercised through the current CLI.
- R2 publication is implemented, but the active MinIO Integration job exercises a separate
  provider package. The current R2 CLI/Provider end-to-end gate is therefore still open.
- R2 target GC is report-only by design; it never sends object deletion.

## HTTP boundary

SOW publishes files and verifies the configured `public_endpoint`; it does not own the web
server, reverse proxy, CDN, DNS, authentication, or cache configuration. A deployment must
verify its own RPM/DEB entry points, package paths, signatures, range/length behavior, and
access policy over the complete prefix.

## Status language

| Term | Meaning |
|---|---|
| implemented | source path exists |
| focused-test verified | repository tests cover the named behavior |
| client verified | a named real client completed the named operation |
| Provider verified | the current CLI completed the named flow against that Provider |
| unsupported | deliberately outside the contract |
| unverified | no current evidence; neither PASS nor known failure |

The current status for each surface is in the
[Compatibility reference](/docs/reference/compatibility/).
