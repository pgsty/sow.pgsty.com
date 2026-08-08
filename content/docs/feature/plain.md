---
title: "Plain Flat Repositories"
linkTitle: "Plain Flat Repositories"
description: "How sow create turns a directory of packages into a flat repository: scanning, staging, atomic replacement, deterministic output, and the Pigsty compatibility operation."
url: "/docs/feature/plain/"
weight: 200
icon: fa-solid fa-folder-open
---

`sow create` takes a directory that already contains `.rpm` and `.deb` files and writes an index over them, in place. That is the whole job. This page explains what it reads, what it writes, what it promises never to touch, and how it survives being killed halfway through.

## The invariants

Three rules hold for every `sow create` run, and everything else follows from them:

1. **SOW only replaces index paths it owns.** Your packages, your `README`, your leftover files from another tool — untouched. The one exception is `--pigsty`, which is an explicit request to delete specific packages.
2. **Same input, same bytes.** Timestamps and compression parameters are fixed and sort order is stable, so re-running over an unchanged directory produces a byte-identical index and reports `noop=true`.
3. **The commit is all-or-nothing per format pointer.** Metadata is fully generated and validated in a staging area on the same filesystem, and only then swapped in with atomic renames. If anything fails before the swap, the previous index keeps serving.

Plain mode has no workspace, no configuration file, and no database. It does not read `sow.yml` even if one exists in a parent directory, and it never performs workspace discovery.

## What it scans

```bash
sow create /srv/repo
```

- Only regular files at the **top level** of the directory. No recursion, ever — there is no `-R` for `create`.
- Only `.rpm` and `.deb` extensions. Symbolic links are not followed.
- Package facts come from the RPM header or the DEB `control` member, never from the filename. A binary RPM renamed to `*.src.rpm` is still indexed by its real architecture; a header that says `src` or `nosrc` is rejected.
- Architectures are read from the packages. Plain mode has no architecture parameter and no permit list — whatever is in the directory goes into the index.
- All valid versions are indexed. If two files claim the same logical coordinate but have different content, that is a hard failure, not a silent pick.

## What it writes

```console
$ sow create
created /srv/repo: rpm=2 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

RPMs present produce `repodata/`:

```text
/srv/repo/
├── pev2-1.23.0-1.noarch.rpm       # yours, untouched
├── xray-26.2.6-1.x86_64.rpm       # yours, untouched
├── xray_26.2.6-1_amd64.deb        # yours, untouched
├── Packages                       # SOW-owned
├── Packages.gz                    # SOW-owned
└── repodata/                      # SOW-owned
    ├── <sha256>-primary.xml.gz
    ├── <sha256>-filelists.xml.gz
    ├── <sha256>-other.xml.gz
    └── repomd.xml
```

Flat metadata references packages in the same directory, so the paths remain relative whether
the directory is exposed as a `file://` source or an HTTP document root:

```xml
<location href="pev2-1.23.0-1.noarch.rpm"/>
```

```text
Filename: ./xray_26.2.6-1_amd64.deb
```

The DEB side emits `Packages` plus a `Packages.gz` whose decompressed content is identical to the plain file. Only `SHA256` is written — no `MD5sum`, no `SHA1` — and fields that the package does not declare (such as `Section`) are omitted rather than emitted empty.

Public files do not inherit your umask. `repodata/` is always mode `0755`; `repomd.xml`, the checksum-named metadata, `Packages`, `Packages.gz`, and the marker are always `0644`. A repository built by a user with a restrictive umask is still readable by your web server.

## Deterministic output

`repomd.xml` carries `<revision>0</revision>` and `<timestamp>0</timestamp>` for every entry:

```xml
<revision>0</revision>
<data type="primary">
  <checksum type="sha256">c834c5e79f...</checksum>
  <open-checksum type="sha256">a80cb3cf91...</open-checksum>
  <location href="repodata/c834c5e79f...-primary.xml.gz"/>
  <timestamp>0</timestamp>
```

This is deliberate. Wall-clock timestamps would make every rebuild produce different bytes, which defeats content-addressed caching, breaks reproducible-build comparisons, and makes it impossible to tell a real change from a no-op. With time removed, a second run over the same directory is a genuine no-op:

```console
$ sow create --json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,
 "result":{"dir":"/srv/repo","rpm":2,"deb":1,
 "kept":["pev2-1.23.0-1.noarch.rpm","xray-26.2.6-1.x86_64.rpm","xray_26.2.6-1_amd64.deb"],
 "removed":[],"marker":false,"noop":false,"recovered":false},"errors":[]}
```

Run it again and the only field that changes is `"noop":true`. The files on disk are identical byte for byte.

## Mixed directories are one operation

A directory holding both formats is handled by a single command and a single transaction:

```console
$ sow create
created /srv/repo: rpm=2 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

Both renderers stage and validate before either one commits. If the DEB side fails to parse, the RPM index is not swapped in either, and the command exits non-zero. You do not get a mixed result where `repodata/` is fresh and `Packages` is stale.

One caveat that is honest rather than reassuring: POSIX cannot rename two files at the same instant. A concurrent reader that fetches `repomd.xml` and `Packages` during the swap window may observe one new and one old. Each protocol view is internally consistent at all times; cross-protocol simultaneity is not promised in default mode. If you need a gate, use `--pigsty` and treat `repo_complete` as the readiness signal.

## The `--pigsty` operation

`--pigsty` is a single, indivisible compatibility switch used by [Pigsty](https://pigsty.io) offline builds. It bundles three behaviors that only make sense together:

1. **Drop 32-bit x86 packages.** RPM `i386`/`i486`/`i586`/`i686`, DEB `i386` — identified from parsed package facts, not from filename globs.
2. **Drop Patroni 3.0.4.** Binary package name exactly `patroni` and upstream version exactly `3.0.4`. RPM compares `VERSION` ignoring epoch and release; DEB strips epoch and Debian revision first. `3.0.4+foo` is not a match.
3. **Write `repo_complete`.** After every index succeeds, a manifest of the remaining top-level packages is written as `<sha256><two spaces><basename>`, sorted by basename.

The ordering is what makes this safe, and it is fixed:

```text
scan / parse / hash
  → stage and validate both formats (and optional RPM signatures)
  → persist journal
  → withdraw the old marker
  → replace signed RPM bodies from their staged bytes
  → install immutable RPM metadata
  → atomically replace repomd.xml
  → atomically replace Packages and Packages.gz
  → rename each removed package into the recovery trash
  → atomically write the new marker
  → fsync
  → delete trash and journal
```

Read that in order and two properties fall out. The new index is published *before* any package is moved away, so it never references a file that has already been deleted. And the old marker is withdrawn *before* the index changes, so a consumer gated on `repo_complete` never sees a marker that outlives its own package list.

In default mode (no `--pigsty`), a pre-existing `repo_complete` is a hard error before anything is written. SOW will not leave behind a marker that claims completion for content it just replaced — you either opt into the atomic operation or move the marker away yourself.

## Signing RPMs in place

```bash
sow create /srv/repo --sign-with 6D5C5A26C36B1F73 --overwrite
```

`-S/--sign-with KEY` is the explicit authorization to modify package bodies. `KEY` is a GPG key ID or fingerprint of exactly 16, 40, or 64 hexadecimal characters; an `0x` prefix is not accepted. SOW normalizes it to uppercase and passes it to `rpm --addsign` in your environment as the `_gpg_name` macro. The private key, passphrase, GPG home, and pinentry all belong to the environment; SOW never receives, stores, or echoes a secret.

- Without `--overwrite`, only RPMs that have no parseable embedded OpenPGP signature are signed. Anything already signed keeps its bytes.
- `--overwrite` requires `--sign-with` and switches to `rpm --resign` over every retained RPM.
- Signing happens on a private staged copy on the same filesystem. Each result is re-parsed to confirm the embedded signature exists, the signature-neutral digest and NEVRA are unchanged, and the final full-byte SHA-256 is what goes into the metadata.
- Duplicate identical inputs are signed once and the same final bytes are reused.
- The journal is persisted only after every signature and every index has verified. Package replacement is ordered before the metadata pointer swap, and each replacement records both the original and the new SHA-256.
- A DEB-only directory, a missing `rpm` binary, an unavailable key or agent, or a failed verification all fail before anything public changes.

Details and exit codes are in the [`sow create` reference](/docs/reference/cli/create/); a walkthrough is in [Sign Your Repository](/docs/tutorial/signing/).

## Crash recovery

Plain mode keeps a durable journal at `.sow-plain-operation.json` in the target directory for the duration of an operation. It records the parsed inputs (by basename, coordinate, and hash), the complete ordered list of file actions, and for every replacement a durable pre-image: the old file's hash, mode, UID, GID, and its location in a recovery trash on the same filesystem. Staging area, trash, pre-images, and journal are all on the same device as the target, so every step is a rename, never a cross-device copy.

Two different failures get two different treatments.

An **ordinary error** after the journal is durable rolls the same plan forward if the complete new state is already durable: SOW verifies and fsyncs every public target, marks the journal complete, and returns success. If the new state cannot be completed, it walks the actions in reverse using the durable pre-images to restore the complete old state, verifies it, cleans up, and returns the error. If the rollback itself fails, the journal and evidence are kept and the operation is locked closed as an error — SOW will not pretend the old state was restored.

A **process kill** does not run any of that. The next `sow create` over the same directory reads the journal, re-parses the inputs, checks the hashes against the recorded evidence, and idempotently forward-completes. Recovery for a signing operation requires exactly the same `--sign-with`/`--overwrite` authorization; it will not silently replay with weaker arguments. Contradictory evidence — a changed input, a missing pre-image, an escaped path, a symlink substituted for a regular file — returns integrity error `5` rather than guessing.

This is validated by injecting process termination after the journal lands, after the old marker is withdrawn, after each metadata pointer swap, after each package rename, and on both sides of the new marker. Every rerun lands on either the complete old state or the complete new state; the trash never loses a package, and the completion marker never disagrees with the package list.

The journal is read through a no-follow, descriptor-bound handle with a 64 MiB ceiling, so a symlink cannot be swapped in between the check and the open.

## Locking

`sow create` takes a write lock on the target directory, and also on its stable parent, so that another cooperating writer cannot replace the directory by rename and acquire an independent lock on the substitute. The lock covers one complete create-or-recover round. `-T/--timeout` and `-N/--no-wait` behave the same as everywhere else — see [Transactions & Recovery](/docs/feature/transactions/).

## Next

- [`sow create` reference](/docs/reference/cli/create/) — every flag, exit code, and failure mode
- [Quick Start](/docs/start/quickstart/) — build one in five minutes
- [Managed Workspaces](/docs/feature/managed/) — when a flat directory is no longer enough
