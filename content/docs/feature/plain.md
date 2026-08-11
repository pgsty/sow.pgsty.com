---
title: "Plain Flat Repositories"
linkTitle: "Plain Flat Repositories"
description: "The one-pass, overwrite-rebuild contract behind sow create, including deterministic output and the Pigsty completion marker."
url: "/docs/feature/plain/"
weight: 200
icon: fa-solid fa-folder-open
---

`sow create` takes a directory that already contains `.rpm` and `.deb` files and writes flat repository indexes beside them. Plain mode has no workspace, configuration file, database, desired state, or operation journal. The package directory is the authority; every index is a disposable projection of its current contents.

That distinction is intentional. Managed repositories retain state and recover transactions. Plain repositories are cheap to recreate: if a run fails or is interrupted, run the same command again and overwrite the derived metadata.

## Contract

Four rules define Plain mode:

1. **Packages are authoritative.** Default `create` does not modify package bytes. It replaces only `repodata/`, `Packages`, and `Packages.gz`; `--pigsty` and explicit RPM signing are the documented exceptions.
2. **One package-content pass.** On the normal unsigned path, every selected package is opened once, SHA-256 hashed once, and parsed during that same pass. Complete parsed RPM/DEB metadata is retained for rendering; render and validation do not reopen package payloads.
3. **One cheap final check.** Immediately before publication, SOW relists the top-level package set and compares `stat` facts with the scan snapshot. It does not compute a second package SHA-256.
4. **Failure means rebuild.** There is no Plain transaction journal, pre-image, roll-forward, or rollback. A failure may leave partially replaced derived metadata. The next `sow create` discards owned temporary residue and rebuilds from the package directory.

For identical input bytes, output remains deterministic and a repeat reports `noop=true`.

## The one-pass pipeline

`--jobs` defaults to the logical CPU count and controls the only package-content pass:

```text
lock directory
  -> list and sort top-level RPM/DEB candidates
  -> parallel open + SHA-256 + parse (once per package)
  -> resolve coordinates and Pigsty filtering
  -> render RPM/DEB metadata from retained parsed facts
  -> validate generated metadata only
  -> relist and compare package stat snapshots
  -> replace derived outputs; repo_complete last with --pigsty
```

Worker completion order never affects bytes: facts are consumed in canonical basename/index order. RPM XML is written from the parsed package object retained by the worker. DEB `Packages` paragraphs are written from the retained control paragraph and the SHA-256 already computed by that worker.

Output self-validation still reads generated XML, `repomd.xml`, `Packages`, and `Packages.gz`. Those files are small derived metadata; it does not read package bodies again.

### What the final stat check proves

The final check requires:

- the same sorted set of top-level regular `.rpm`/`.deb` basenames;
- the same file identity/inode;
- unchanged file type and mode;
- unchanged size and modification time.

If any fact differs, publication is rejected with integrity exit code `5`. This catches normal add, remove, replace, truncate, and rewrite races at directory-scan cost.

It is deliberately not cryptographic validation. An external writer that changes bytes in place while preserving inode, size, and mtime can evade it. Plain mode accepts that tradeoff because it targets one local cooperating writer and a rebuildable result. Use a Managed repository when hostile/concurrent mutation evidence or durable recovery is required.

## Scan and output rules

- Only regular files at the directory top level are considered; scanning never recurses and never follows symlinks.
- Only `.rpm` and `.deb` suffixes are selected.
- Package identity and architecture come from the RPM header or DEB control member, never the filename. RPM `src` and `nosrc` are rejected.
- Every valid version is indexed. Two different byte streams with the same logical coordinate are rejected.
- Default mode rejects a directory with no packages. `--pigsty` may converge an interrupted cleanup whose authoritative package set is now empty.

RPM input produces `repodata/`; DEB input produces `Packages` and `Packages.gz`:

```text
/srv/repo/
├── pev2-1.23.0-1.noarch.rpm
├── xray_26.2.6-1_amd64.deb
├── Packages
├── Packages.gz
└── repodata/
    ├── <sha256>-primary.xml.gz
    ├── <sha256>-filelists.xml.gz
    ├── <sha256>-other.xml.gz
    └── repomd.xml
```

Flat locations are relative: RPM uses the bare basename and DEB uses `./<basename>`. Public directories are mode `0755`; generated files and `repo_complete` are `0644`, independent of umask.

When one format disappears, SOW removes its known derived outputs. A rerun also replaces incomplete pairs such as a lone `Packages` left by an interruption, and removes SOW-shaped checksum RPM metadata no longer referenced by the new generation. Unknown files remain untouched.

## Determinism and no-op

`repomd.xml` always uses revision and timestamps `0`; gzip headers are fixed; ordering is canonical. A given package set therefore produces byte-identical metadata. Before publication SOW compares the staged metadata with live metadata. If package cleanup/signing is unnecessary and every output already matches, it removes the private stage without replacing public inodes and returns `noop=true`.

The JSON field `recovered` is always `false` because Plain create never performs journal recovery.

## Publication and interruption semantics

All metadata is generated and validated in a same-directory private stage before publication starts. Individual file replacements use same-filesystem rename, and RPM publishes checksum-named metadata before `repomd.xml`.

This is not a multi-file transaction. A process killed during publication may leave new RPM metadata with old DEB metadata, one member of the DEB pair, or extra old checksum-named RPM metadata. That state is not evidence to reconcile; it is disposable output. The next run renders the complete current projection and overwrites/removes the residue.

The implementation creates no durable journal or recovery trash. On startup it discards
SOW-owned residue in the reserved Plain staging namespace before starting a fresh scan.

## The `--pigsty` marker gate

`--pigsty` additionally removes parsed package facts matching its compatibility rules (DEB `i386` and Patroni 3.0.4) and writes `repo_complete` as `<sha256><two spaces><basename>`, sorted by basename. An RPM is not removed merely because its architecture is `i386/i486/i586/i686`.

Its publication order is:

```text
stage + validate
  -> final stat check
  -> withdraw old repo_complete
  -> install signed RPMs, if explicitly requested
  -> install RPM and DEB metadata
  -> delete matched packages
  -> write repo_complete last
```

A missing marker means “not complete”; consumers must not use the directory until the marker reappears. If a run stops after withdrawing the marker, rerun `sow create --pigsty`. The rerun scans the packages that now exist, overwrites metadata, finishes cleanup, and writes a fresh marker. No action log is required.

Default mode refuses to run while `repo_complete` exists, preventing an un-gated command from leaving a stale readiness claim.

## Explicit RPM signing

`--sign-with` authorizes package mutation and is a separate slow path. SOW signs private stage copies, validates the embedded signature and signature-neutral digest, reparses the resulting RPM, then installs the signed bytes before their metadata. These necessary signing/copy/verification reads are outside the unsigned one-pass guarantee. If signing is interrupted, rerun from the package directory; no signing transaction is replayed from a journal.

## Locking and scope

`sow create` locks the target directory and its stable parent for one run. `--timeout` and `--no-wait` control cooperative lock acquisition. The lock prevents another cooperating SOW process from writing concurrently; it does not turn arbitrary external package mutation into a supported workload.

Use Plain for a local, single-process flat-directory build that can be regenerated. Use [Managed Workspaces](/docs/feature/managed/) when desired state, audit history, atomic generation switching, or evidence-driven crash recovery is part of the requirement.

## Next

- [`sow create` reference](/docs/command/create/) — flags, output, and failure contract
- [Transactions & Recovery](/docs/feature/transactions/) — the Managed durability boundary
- [Quick Start](/docs/start/quickstart/) — build one in five minutes
