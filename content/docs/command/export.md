---
title: "sow export"
linkTitle: "export"
description: "Export one built RPM Dist architecture as a standalone compatibility repository."
url: "/docs/command/export/"
weight: 1800
icon: fa-solid fa-file-export
---

SOW 0.2.0 provides one export subcommand: `sow export rpm-leaf`. It creates an external, standalone
RPM repository whose repodata uses local `pool/...` hrefs.

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
| `--hardlink` | Use hard links for trusted, same-filesystem, read-only output | copy files |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | selection rules |
| `--json` | Emit the `sow.cli/v1` envelope | false |

The command accepts no `--dist`, jobs, timeout, or lock option.

## Output

```console
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
exported RPM leaf el9/x86_64 generation=00000000000000000012 method=copy packages=84 to /srv/export/el9-x86_64
```

The destination contains:

- rewritten RPM repodata with local payload hrefs;
- the required package subtree;
- an export manifest;
- `.sow-export.json` provenance.

The source must be a completed Built Generation. The export is a separate artifact: it is not
Desired Membership, a Built Generation, publication input, or a GC root.

## Copy versus hard link

Copying is the safe default. `--hardlink` is an explicit optimization for an output on the same
filesystem that consumers cannot mutate. A hard-linked payload shares an inode with SOW's pool; do
not use this mode for writable or untrusted destinations.

SOW rejects output that overlaps a configured filesystem publication root. This prevents an export
from being mistaken for, or modifying, a managed publication target.

## Exit behavior

| Code | Trigger |
|---|---|
| `0` | Standalone RPM leaf exported |
| `1` | Filesystem, copy, hard-link, or metadata-write failure |
| `2` | Invalid syntax, malformed Dist/architecture token, discovery, or implicit Repository ambiguity |
| `5` | Source Generation or Repository state is inconsistent |
| `6` | Explicit Repository is not configured, Dist is not RPM, view/signer is unavailable, or destination is unsafe/non-empty/overlapping |

## See also

- [Compatibility Design](/docs/design/compatibility/) — compatibility surfaces and non-goals
- [Repository Layout](/docs/reference/layout/) — source tree and export boundaries
- [`sow publish`](/docs/command/publish/) — managed delivery to configured targets
