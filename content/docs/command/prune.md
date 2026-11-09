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

`sow prune` keeps the highest RPM Epoch/Version/Release for each package name and architecture, rebuilds the flat index, then removes older versions. This command requires SOW 0.7.0 or later.

## Synopsis

```text
sow prune DIR [--dry-run] [--protect NAME]... [-j N] [--metadata-timestamp SECONDS] [-T DUR | -N] [--json]
```

`DIR` is required. Only top-level regular binary RPM files are scanned. Subdirectories are not scanned, and the command does not discover a Workspace or read `sow.yml`.

## Preview and prune

Run this on a local publication source. Clients using cached old indexes may still need older RPMs; account for that in the publication workflow.

```bash
sow prune /srv/candidate --dry-run
sow prune /srv/candidate --protect age_18 --protect age_18-llvmjit
```

`--dry-run` performs validation and reports candidates without changing files. Use the same protection options for the preview and the actual run.

`--protect NAME` keeps every version of that exact package name across architectures. It is repeatable and does not accept patterns. Every supplied name must match a package; a typo returns exit code `2` before changes. Equal EVRs in one name/architecture group are rejected, including protected groups.

## Options

| Option | Behavior |
|---|---|
| `--dry-run` | Preview validated removal candidates without writes |
| `--protect NAME` | Keep all versions of an exact package name; repeatable |
| `-j, --jobs N` | Package inspection workers; defaults to CPU count |
| `--metadata-timestamp SECONDS` | Index publication time in Unix seconds; defaults to `0`, as for `create` |
| `-T, --timeout DUR` | Limit the wait for the directory lock |
| `-N, --no-wait` | Fail immediately if the directory lock is busy |
| `--json` | Return the standard JSON envelope |

`--timeout` and `--no-wait` are mutually exclusive. Prune does not sign packages or repository metadata and does not accept `--pigsty`.

## Integrity and recovery

The replacement RPM for each removed version must pass its embedded digest checks. SOW binds those checks and the indexed bytes to a stable file identity, including change time. It checks the replacement before each deletion and again before completion. A detected change stops further deletion, including an in-place rewrite with restored size and modification time.

The filtered index is published before package deletion. If an error occurs after publication or some deletions, the result reports what changed and returns partial-result exit code `7`; interruption returns `130`. Already removed packages are not restored. Resolve the reported problem, then rerun the same command.

An existing `repo_complete` marker is withdrawn during changes and refreshed only after successful completion. Its pending state survives interruption. Prune creates no marker when none existed and does not apply `create --pigsty` package exclusion rules.

JSON result fields include `kept`, `candidates` (each old path and its replacement), `removed`, `index_updated`, `dry_run`, and `noop`.

## Supported repositories

Prune rejects managed workspaces, DEB packages or indexes, package symlinks, source RPMs, RPM v6 packages, and repositories with `repodata/repomd.xml.asc`. It also rejects an existing `repomd.xml` that registers independent metadata SOW does not generate, such as groups, updateinfo, modules, or an unknown type. Alternate package-index encodings such as SQLite and zchunk are allowed.

See [`sow create`](/docs/command/create/) for the explicit procedure to rebuild a candidate without additional metadata and for metadata timestamp behavior.
