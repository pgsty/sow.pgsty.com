---
title: "sow changes"
linkTitle: "changes"
description: "Diff Built Generations as a deterministic Repository-relative file delivery plan."
categories: [Command]
tags: [cli, publish, generation]
url: "/docs/command/changes/"
weight: 1400
icon: fa-solid fa-code-compare
---

`sow changes` compares Built Generations. It reports physical Repository-relative file changes; it
does not show unbuilt Desired changes and is not a remote transaction protocol.

## Synopsis

```text
sow changes [BASE_GENERATION] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `--json` | Emit the `sow.cli/v1` envelope | false |

The command is Repository-wide and rejects `-d/--dist`.

## Output

```console
sow changes
base=4 generation=5 dirty=false
add	payload	pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm	19776	ffd9e7bd...
add	metadata	dists/el9/x86_64/repodata/5bc463cb...-primary.xml.gz	1460	5bc463cb...
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1514	05d3d5bf...
delete	delete	dists/el9/x86_64/repodata/0df96f0b...-primary.xml.gz	0	
```

Columns are operation, phase, Repository-relative path, size, and SHA-256.

| Field | Values |
|---|---|
| operation | `add`, `update`, `delete` |
| phase | `payload`, `metadata`, `pointer`, `delete` |

Phases describe how SOW constructed the local Generation. Do not replay individual rows into a live
remote tree. Use [`sow publish`](/docs/command/publish/), or stage and atomically switch a complete
copy.

## Base Generation

Without an argument, SOW compares the current Built Generation with its predecessor.

`BASE_GENERATION` is a decimal integer in the inclusive range `0..current`. Base `0` produces the
complete delivery manifest for the current Generation, excluding private `sow.yml` and `.sow/`.
Using the current Generation as base produces an empty plan. A Repository never built also yields an
empty `0 -> 0` plan.

```console
sow changes 99
operation rejected: managed: operation rejected: base generation 99 is outside 0..2
```

## Dirty and recovery states

When Desired state is dirty, the header says `dirty=true`, but the plan still ends at the current
Built Generation. Private pending payloads are excluded because they are not deliverable yet.

When the Repository is `recovering` or `error`, `changes` refuses to emit a plan: pending file
actions must not be mistaken for a completed Generation.

## Examples

Produce a complete manifest:

```bash
sow changes 0 -r pgsql --json > pgsql-current.json
```

Filter one Dist by path after producing the Repository-level plan:

```bash
sow changes -r pgsql --json |
  jq '.result.changes[] | select(.path | startswith("dists/el9/"))'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Plan printed, including an empty plan |
| `1` | Runtime I/O failure |
| `2` | Usage error, `-d` supplied, Workspace not found, or implicit Repository selection is ambiguous |
| `5` | Repository is `recovering` or `error`, or state evidence is inconsistent |
| `6` | Explicit Repository is not configured, or Base Generation is outside the valid range |

## See also

- [`sow build`](/docs/command/build/) — create the next Generation
- [`sow publish`](/docs/command/publish/) — apply the supported publication protocol
- [`sow log`](/docs/command/log/) — semantic Operations and their file actions
- [Repository Layout](/docs/reference/layout/) — public and private path boundaries
