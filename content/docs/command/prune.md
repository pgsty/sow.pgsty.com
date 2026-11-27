---
title: "sow prune"
linkTitle: "prune"
description: "Keep the latest RPM versions in a flat repository."
categories: [Command]
tags: [cli, plain, rpm]
url: "/docs/command/prune/"
weight: 110
icon: fa-solid fa-scissors
---

`sow prune` keeps the highest RPM Epoch/Version/Release for each package name and architecture, rebuilds the flat index, then removes older versions. EVR comparison follows RPM rules, including caret (`^`) snapshot versions such as `2.0^20250611 < 2.0.1`. This command requires SOW 0.7.0 or later.

## Synopsis

```text
sow prune DIR [--dry-run] [--strict] [--protect NAME]... [-j N] [--metadata-timestamp SECONDS] [-T DUR | -N] [--json]
```

`DIR` is required. SOW scans top-level regular binary RPM files (both RPM v4 and v6). It does not scan subdirectories, discover a Workspace, or read `sow.yml`. In a mixed RPM and DEB directory, `prune` updates the RPM index, preserves the DEB index, and carries forward existing `repo_complete` digests for still-present DEBs without hashing newly arrived unindexed DEBs.

## Preview and prune

Run this command on a local publication source. Clients using cached old indexes may still need older RPMs; account for that in the publication workflow.

```bash
sow prune /srv/candidate --dry-run
sow prune /srv/candidate --protect age_18 --protect age_18-llvmjit
```

`--dry-run` validates packages and reports candidates without changing files. Use the same protection options for the preview and the actual run.

`--protect NAME` keeps every version of that exact package name across architectures. It is repeatable and does not accept patterns. By default, corrupt packages, unmatched `--protect` names, and equal-version conflicts (retaining the whole name/architecture group) are reported as warnings and skipped safely; an all-skipped RPM scan preserves the previous `repodata/` and completion marker. Pass `--strict` to fail before publication on any corrupt package, unmatched `--protect` name, or equal-version conflict.

## Options

| Option | Behavior |
|---|---|
| `--dry-run` | Preview validated removal candidates without writes |
| `--strict` | Fail non-zero on corrupt packages, unmatched `--protect` names, or equal-version conflicts |
| `--protect NAME` | Keep all versions of an exact package name; repeatable |
| `-j, --jobs N` | Package inspection workers; defaults to CPU count |
| `--metadata-timestamp SECONDS` | Index publication time in Unix seconds; defaults to `0`, as for `create` |
| `-T, --timeout DUR` | Limit the wait for the directory lock |
| `-N, --no-wait` | Fail immediately if the directory lock is busy |
| `--json` | Return the standard JSON envelope |
{.wide .expand}

`--timeout` and `--no-wait` are mutually exclusive. Prune does not sign packages or repository metadata and does not accept `--pigsty` or `--passfile`.

## Integrity and recovery

The replacement RPM for each removed version must pass its embedded digest and signature header checks, including RPM v6 native `RPMSIGTAG_OPENPGP` tag 278 and RSA, DSA, ECDSA, and EdDSA packets in header signature tag 267 (`RPMSIGTAG_DSA`). SOW binds those checks and the indexed bytes to a stable file identity, including change time and link count. It checks the replacement before each deletion and again before completion: if only `ctime` or `nlink` changed (such as from an external hard link), SOW re-verifies the file's SHA-256 digest on the bound descriptor, so benign hard links succeed while an in-place rewrite with restored size and modification time still stops further deletion.

SOW locks only the target directory after binding (releasing the parent lock immediately), so sibling flat directories can run concurrently. SOW publishes the filtered index before deleting packages. If an error occurs after index publication or after some deletions, the result reports what changed and returns partial-result exit code `3`; interruption returns `130`. SOW does not restore already removed packages. Resolve the reported problem, then rerun the same command.

SOW withdraws an existing `repo_complete` marker during changes (tracking it via `.sow-prune-repo-complete`) and refreshes it only after completion, preserving existing marker digests for DEB files still present. That pending state survives interruption. Prune creates no marker when none existed and does not apply `create --pigsty` package exclusion rules.

JSON result fields include `dir`, `dry_run`, `kept`, `candidates` (each old `path` and its `latest` replacement), `removed`, optional `skipped` and `warnings`, `index_updated`, `marker`, and `noop`. Human output writes warnings to stderr; successful `--json` output includes them in stdout and leaves stderr empty.

## Supported repositories

Prune rejects managed workspaces and repositories with `repodata/repomd.xml.asc` on live runs. It also rejects an existing `repomd.xml` that registers independent metadata SOW does not generate, such as groups, updateinfo, modules, or an unknown type. Prune allows alternate package-index encodings such as SQLite and zchunk, supports both RPM v4 and v6 packages, and safely preserves DEB indexes in mixed directories.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Prune succeeded, or `--dry-run` / `noop` completed |
| `1` | Nonexistent or unreadable directory, filesystem, package parsing, digest verification, or metadata rendering error |
| `2` | Invalid flags, missing `DIR` argument, or (under `--strict`) unmatched `--protect` package name |
| `3` | Partial completion: failure after publishing the filtered index or removing at least one RPM |
| `4` | Directory lock is held by another process |
| `6` | Unsupported repository state (Managed workspace, signed `repomd.xml`, foreign metadata, or under `--strict`: skipped packages or equal EVRs) |
| `130` | Interrupted by SIGINT or SIGTERM |
{.wide .expand}

## See also

- [`sow create`](/docs/command/create/) for rebuilding a candidate without additional metadata and for metadata timestamp rules
- [Plain Mode](/docs/feature/plain/) for flat repository behavior
- [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) for replacing `createrepo_c` and pruning flat RPM directories
