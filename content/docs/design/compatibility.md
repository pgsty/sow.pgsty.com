---
title: "Compatibility Boundaries"
linkTitle: "Compatibility Boundaries"
description: "How SOW separates protocol correctness, client behavior, mirror tools, relocation, HTTP normalization, and storage-provider semantics."
url: "/docs/design/compatibility/"
weight: 500
icon: fa-solid fa-table-cells
---

"Compatible" is too broad to be a useful engineering claim. A package may install while a
mirror tool refuses the same metadata; a tree may work on POSIX disk while multiplying
objects after upload. SOW therefore treats compatibility as a set of independent gates.

## The layers

| Layer | Question | Required evidence |
|---|---|---|
| Format | Is the metadata valid rpm-md / Debian archive syntax? | parser and structural validation |
| Ordinary client | Can `apt`, `dnf`, or `yum` refresh, resolve, download, verify, and install? | real client run |
| Mirror tool | Can the named mirror tool materialize the repository safely? | that exact tool and version |
| Relocation | Does a whole-root copy remain byte-closed and consumable? | copy + manifest + client run |
| HTTP/proxy | Are relative URLs normalized inside the same prefix without traversal or double encoding? | target HTTP matrix |
| Storage | Do object identity, conditional operations, listing, caching, and deletion match the state machine? | real provider protocol test |

No row inherits PASS from another row or from an earlier Repository layout.

## The `reposync` lesson

The v0.2 design tested an RPM view whose metadata used `../../../pool/...`. On AlmaLinux
9.8, ordinary DNF operations passed: `makecache`, query, download, and install. Default
`dnf reposync` failed because it normalized the destination outside its per-repository
download root and rejected the write through its safe-path check.

v0.2 treated default `reposync` as mandatory, so it selected C2: view-local `pool/...`
hardlinks and metadata hrefs with no parent traversal. The resulting native and neutral
package matrix passed ordinary DNF and default `reposync`, even after a copy lost hardlink
identity.

That result remains valid evidence for v0.2. It does not prove that the 0.3 canonical
single-payload layout passes default `reposync`.

## The 0.3 contract

The 0.3 development design makes these choices explicit:

- APT and ordinary DNF against the complete Repository are required.
- Whole-root relocation is required.
- Default EL `reposync` against the canonical Repository is unsupported by design.
- A completed external RPM leaf export is the intended `reposync` fallback and needs its
  own positive real-client gate.
- DNF4/DNF5 options such as `--safe-write-path` may be documented as best effort only; they
  do not change the canonical layout.

## Filesystem compatibility

Canonical 0.3 correctness never depends on inode identity or hardlink count. A Repository
must keep working after a normal copy, tar extraction, or object-store upload. Hardlinks
are limited to private transaction state, small immutable APT by-hash aliases, and an
explicit trusted compatibility export.

Local builders still require POSIX locking and atomic rename semantics. NFS and other
network filesystems are not implicitly supported just because the published tree is static.

## HTTP and proxy boundary

Parent-relative RPM hrefs are resolved before retrieval. Each supported target must prove:

- `GET`, `HEAD`, Range, length, ETag, and cache behavior;
- the normalized request lands on the canonical `pool/...` object inside the same prefix;
- encoded dot segments, backslashes, double encoding, redirects, and prefix escape are
  rejected;
- public/private access control covers the complete Repository prefix, including `pool/`.

An edge rewrite or absolute deployment URL cannot be required for canonical correctness.

## Provider capability boundary

Publication support does not imply safe deletion support. A provider may pass streaming
upload, conditional put, listing, and public verification yet lack atomic conditional
delete. SOW records capabilities per provider and disables the state-machine branch that
cannot be proven.

In particular, the 0.3 R2 path is implemented and mock-verified for publication, while a
fresh authorized nonproduction R2 run remains a separate release-evidence gate and physical
remote deletion is disabled by design.

## Reading status words

| Status | Meaning |
|---|---|
| `DESIGNED` | written contract only |
| `IMPLEMENTED` | source path exists |
| `LOCALLY VERIFIED` | focused local/fault/mock checks passed |
| `LIVE VERIFIED` | named real client or provider passed on the named revision |
| `RELEASED` | packaged release includes the behavior and its required gates |
| `UNSUPPORTED` | intentionally outside the contract |
| `UNVERIFIED` | no current evidence; never a synonym for failure or PASS |

For the released v0.2 client matrix, use the operational
[Compatibility reference](/docs/reference/compatibility/). For 0.3, consult the release
notes when that line is published; this design page deliberately avoids upgrading local
implementation evidence into a release claim.
