---
title: "SOW v0.9.0"
linkTitle: "SOW v0.9.0"
date: 2026-11-27T13:30:00+08:00
lastmod: 2026-11-27
authors: [Vonng]
description: "Fault-tolerant flat create and prune with --strict, RPM v6 and native OPENPGP multi-signature verification, sow.yaml support, and direct max_cache_ttl grace."
categories: [Release]
tags: [release, plain, rpm, signing, gc]
weight: -70
url: "/blog/release/sow-v0.9.0/"
release_url: https://github.com/pgsty/sow/releases/tag/v0.9.0
---

{{< release-card >}}

SOW 0.9.0 makes flat `create` and `prune` resilient to bad packages by default, adds full RPM format v6 and native OPENPGP signature verification, accepts both `sow.yml` and `sow.yaml`, and aligns target GC grace periods directly with `max_cache_ttl`. The database stays at schema v13.

## Fault-tolerant flat repositories {#flat-fault-tolerance}

Plain `sow create` and `sow prune` now skip corrupt, unreadable, source (`src`/`nosrc`), and coordinate-conflicting packages (including Debian version-equivalent conflicts such as `1.0-1` vs `1.00-1`), as well as unmatched `--protect` names, with warnings so valid packages still publish. Pass `--strict` to fail before writing on any skipped package or conflict.

```bash
sow create /srv/flat                 # skip bad inputs with warnings
sow create /srv/flat --strict        # fail fast on any bad or conflicting input
sow prune /srv/flat --dry-run        # preview superseded RPMs safely
```

- **Per-format isolation:** If every candidate of one format fails, SOW preserves that format's previous index, history, and completion state while still publishing valid packages of the other format (including in fresh `--pigsty` directories).
- **Mixed-directory prune:** `sow prune` updates the RPM index, leaves the DEB index intact, and carries forward existing `repo_complete` digests for still-present DEBs without prematurely hashing newly arrived unindexed DEBs.
- **Structured warnings:** Human output prints warnings to `stderr`. Successful `--json` output includes `warnings` and `skipped` in the `stdout` envelope and leaves `stderr` empty.
- **Safe single-pass checks:** SOW retains file-identity, size, and modification-time checks across scan, publication, signed RPM installation, and deletion without repeating full decompression read-backs.

## RPM v6, package parsing, and signing {#rpm-v6-and-signing}

- **RPM format v6 and native OPENPGP signatures:** SOW supports RPM format v6 packages (lead major versions 3 through 6, `PAYLOADSHA256` without `PAYLOADSHA256ALGO`, and native `RPMSIGTAG_OPENPGP` tag `278` OpenPGP v4 and v6 signature arrays) across flat `create`, `prune`, `--sign-with`, and Managed `add`, `build`, and `check`, including dual- and multi-signed RPMs. When tag `278` is present, it is authoritative over legacy signature tags.
- **Real-world RPM and DEB compatibility:** RPM indexing accepts identical duplicate main-header tags (such as the duplicate `SOURCERPM` found in EL10 packages) while still rejecting conflicting main tags and duplicate signature-header tags. Binary `.deb` `control` files with legacy Latin-1 bytes (`>= 0x80`) are normalized to UTF-8, and `.asc` OpenPGP keyrings tolerate comment headers outside armor fences.
- **Broader signing keys and passfiles:** Metadata signing accepts ECDSA and DSA keys alongside RSA and EdDSA (Ed25519/Ed448). `--passfile`, `SOW_GPG_PASSFILE`, and `passfile` support regular files, symlinks (including Kubernetes Secret mounts), and named pipes (FIFOs with a 2-second deadline), strip an optional UTF-8 BOM and final LF/CRLF, and surface bounded helper `stderr` diagnostics on failure.

## Managed workspaces, publication, and CLI {#managed-and-publication}

- **Direct `max_cache_ttl` grace:** New target GC grace records use the configured `max_cache_ttl` directly instead of enforcing a hardcoded 30-day floor and 24-hour padding. Existing recorded `NotBefore` deadlines remain effective, and backward NTP clock steps keep the time-witness high-water mark.
- **Target ergonomics and safety:** `authoritative_workspace`, `single_writer`, and `exclusive_write_authority` default to `true` when omitted (explicit `false` remains rejected). R2 `region` defaults to `auto`, dotted bucket names and shorthand durations such as `24h` or `0` are accepted and normalized, and overlapping R2 targets on the same `(endpoint, bucket, prefix)` are rejected across region spellings such as `auto` vs `us-east-1`.
- **Hardened HTTP verification:** Public HTTP checks follow CDN redirects, block hop-by-hop HTTPS-to-HTTP downgrades, validate connected dial IPs against private loopback and link-local ranges, and refuse cross-origin redirects through an HTTP proxy. Harmless foreign files outside `pool/` and `dists/` at the target root are ignored.
- **Workspace config, SQLite, and recovery:** Workspaces accept either `sow.yml` or `sow.yaml` (preserving support for a legacy repository directory named `sow.yaml` beside `sow.yml`), and explicit `-C`/`--workdir` never falls back to `CWD` or `SOW_DIR`. SQLite resolves the physical database path before probing `-wal`/`-shm`/`-journal` sidecars and enforcing single-hardlink invariants, eliminating Darwin-specific C ABI code. Missing `.sow/workspace.lock` in a populated workspace requires explicit offline recovery, while `sow init` repairs missing per-repository locks under `workspace.lock`.
- **Managed ergonomics:** `sow check` reports `sow.yml` `limit`/`exclude` drift as `dirty` instead of an integrity error, verifies APT `by-hash` files by content digest when hard links are broken, and tolerates `.DS_Store` under `.sow/`. `sow rm --check` stays strictly read-only without touching `.sow/<repo>/stage`, `sow add -R` ignores unreadable non-package files, legacy schema v12 migration-required errors consistently exit `6`, and interrupted v0.7.1 local GC plans containing an empty `manifest` array now resume directly.
- **CLI and packaging:** Duplicate flags use last-wins semantics, boolean flags accept `=true`/`=false`, `--timeout 0s` is accepted, `sow log export FILE` resolves symlinked parent directories (such as macOS `/tmp`), and release archives and Linux packages ship the `sow` binary and `LICENSE` directly.

## Upgrade and downloads {#upgrade}

> [!WARNING]
> Review any publication target configured with `max_cache_ttl: 0s` before upgrading. New target GC grace records now follow `max_cache_ttl` without a 30-day floor, so superseded objects with `0s` TTL can become eligible at the next target GC. Previously recorded later `NotBefore` deadlines remain effective.

Workspaces on 0.5.0 through 0.8.0 stay on schema v13 and need no database migration. Stop workspace writers, back up the complete workspace with hard links preserved, install SOW 0.9.0, and run `sow build` and `sow check` for each repository. Interrupted 0.7.1 local GC plans with an empty `manifest` array now resume directly under 0.9.0 without needing the 0.7.1 binary first. See the [upgrade guide](/docs/start/install/#upgrade-to-090).

Linux and macOS archives, Linux RPM and DEB packages, and their checksums are on the [download page](/download/). See the [full changelog](https://github.com/pgsty/sow/compare/v0.8.0...v0.9.0).

{{< release-assets src="release/sow-v0.9.0-checksums.txt" group="auto" >}}{{< /release-assets >}}
