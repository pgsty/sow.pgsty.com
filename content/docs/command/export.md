---
title: "sow export"
linkTitle: "export"
description: "Export one RPM architecture view as a standalone repository."
categories: [Command]
tags: [cli, rpm, dist]
url: "/docs/command/export/"
weight: 1800
icon: fa-solid fa-file-export
---

`sow export rpm-leaf` creates a standalone RPM repository for one Dist and architecture. It copies the packages into an external directory and rewrites metadata to use local `pool/...` paths.

## Synopsis

```text
sow export rpm-leaf DIST ARCH DIR [--hardlink] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

| Argument | Requirement |
|---|---|
| `DIST` | Canonical configured RPM Dist name |
| `ARCH` | `x86_64` or `aarch64` |
| `DIR` | Absent or empty destination outside Repository, private-state, and filesystem-target roots |

| Flag | Meaning | Default |
|---|---|---|
| `--hardlink` | Use hard links for read-only output on the same filesystem | copy files |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | selection rules |
| `--json` | Output JSON | false |

## Output

```console
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
exported RPM leaf el9/x86_64 generation=00000000000000000012 method=copy packages=84 to /srv/export/el9-x86_64
```

The destination contains:

- RPM metadata with local package paths;
- the required package subtree;
- an export manifest;
- `.sow-export.json` provenance.

The source Repository must be clean, have a completed Built Generation, and have no unfinished operation. The requested RPM view must belong to that Generation. The export is independent of the Workspace and does not protect source packages from GC.

If export fails, correct the reported cause and retry into a new or empty directory. The failed destination can contain partial files.

Managed RPM and `export rpm-leaf` use a fixed `0` repomd data timestamp and expose no
`--metadata-timestamp` option. They cannot directly take over the same EL7 repository ID
while clients retain a positive cached timestamp; changing the base URL alone does not help.
Use a new client repository ID or clear its metadata cache. To keep the old ID and cache,
continue with Plain `create` and an explicit publication time, following the
[migration guide](/docs/tutorial/yum-migration/) and re-signing repomd.

## Copy versus hard link

Copying is the default. Use `--hardlink` only for read-only output on the same filesystem. Editing a hard-linked package also changes the source package in SOW's pool.

## Exit behavior

| Code | Trigger |
|---|---|
| `0` | Standalone RPM leaf exported |
| `1` | Filesystem, copy, hard-link, or metadata-write failure |
| `2` | Invalid syntax, malformed Dist/architecture token, discovery, or implicit Repository ambiguity |
| `5` | Source Generation or Repository state is inconsistent |
| `6` | Explicit Repository is not configured, Dist is not RPM, view/signer is unavailable, or destination is unsafe/non-empty/overlapping |

## See also

- [Platforms & Integrations](/docs/reference/compatibility/) — client and tool compatibility
- [Repository Layout](/docs/reference/layout/) — source tree and export boundaries
- [`sow publish`](/docs/command/publish/) — managed delivery to configured targets
