---
title: "Publish, Retain, GC, and Export"
linkTitle: "Publish & Lifecycle"
description: "Command reference for publication targets, retained Generations, conservative garbage collection, and RPM leaf exports."
url: "/docs/reference/cli/publication/"
weight: 950
icon: fa-solid fa-cloud-arrow-up
---

These commands cover the v0.2.0 delivery lifecycle. `publish`, target GC, and target
selection use the `targets:` map in `sow.yml`; local retention and GC operate on a selected
Repository. `export rpm-leaf` creates a separate compatibility artifact.

## sow publish

```text
sow publish TARGET [--abort] [-C DIR] [-T DUR | -N] [--json]
```

Publishes the current verified Generation of the Repository bound to `TARGET`. SOW plans
and applies immutable payloads first, checksum-addressed metadata second, mutable pointers
last, then verifies and records a checkpoint. Repeating an already-current publication is
an idempotent no-op.

```bash
sow publish prod
```

`--abort` is available only before durable commit intent. It reconciles exact objects that
may already have been created, retains that evidence, and abandons the attempt without
copying or deleting remote objects. After commit intent, recovery is forward-only: rerun
the normal publish command.

`publish` selects its Repository from the target and therefore does not accept `--repo` or
`--dist`.

## sow retain

```text
sow retain add GENERATION [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow retain ls             [-C DIR] [-r NAME] [--json]
sow retain rm GENERATION  [-C DIR] [-r NAME] [-T DUR | -N] [--json]
```

`retain add` verifies and freezes a Generation manifest and its metadata under private
state so its payloads remain explicit GC roots. `retain ls` is read-only. `retain rm`
removes that explicit root; it does not itself delete package bytes. Generation arguments
must be decimal integers greater than zero.

## sow gc

```text
sow gc          [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow gc TARGET   [-C DIR]           [-T DUR | -N] [--json]
```

Without a target, GC deletes only local pool objects unreachable from the current
Generation and all retained, migration, recovery, and publication roots. It journals the
operation and advances the repository Generation when bytes are removed.

With `TARGET`, GC maintains publication state:

| Provider | Behavior |
|---|---|
| `filesystem` | conditionally deletes eligible objects only after cache grace and recorded storage/public absence checks |
| `r2` | records an exact report-only candidate set; never sends object deletion |

A target selects its Repository, so `sow gc TARGET -r NAME` is a usage error.

## sow export rpm-leaf

```text
sow export rpm-leaf DIST ARCH DIR [--hardlink] [-C DIR] [-r NAME] [--json]
```

Exports one built RPM Dist architecture as a standalone repository with local `pool/...`
hrefs. `ARCH` must be `x86_64` or `aarch64`. Copying is the default. `--hardlink` is an
opt-in same-filesystem optimization for a trusted read-only export.

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

The directory includes rewritten repodata, its package tree, a manifest, and
`.sow-export.json`. An export is not a Membership, Generation, publication input, or GC
root, and SOW rejects an output that overlaps a configured filesystem publication root.

## Common flags

| Flag | Meaning |
|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory |
| `-r, --repo NAME` | Select a Repository where supported |
| `-T, --timeout DUR` | Maximum write-lock wait; `0` waits indefinitely |
| `-N, --no-wait` | Fail immediately when the write lock is held |
| `--json` | Emit the `sow.cli/v1` envelope |

## See also

- [`sow.yml` Targets](/docs/reference/config/#publication-targets)
- [Publication Model](/docs/design/publication/)
- [Repository Layout](/docs/reference/layout/)
