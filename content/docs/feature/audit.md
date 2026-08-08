---
title: "Observability & Audit"
linkTitle: "Observability & Audit"
description: "Use status, check, changes, retention, and the operation log without confusing state with proof."
url: "/docs/feature/audit/"
weight: 800
icon: fa-solid fa-magnifying-glass-chart
---

Each read surface answers a different question.

| Command | Question | Writes? |
|---|---|---:|
| `status` | What state is the Repository in? | no |
| `check` | Does the selected Repository satisfy the complete delivery contract? | no |
| `changes` | What physical files differ between Built Generations? | no |
| `log` | Which operations and dispositions were recorded? | no |
| `retain ls` | Which Generations are explicit local GC roots? | no |

## `status`: cheap state

```bash
sow status -r local
```

It reports the Desired revision, Built Generation, dirty Dists, pending payload counts,
lock state, and `ready_to_copy`. It does not hash the public tree, recover an operation, or
build.

| Repository state | Meaning |
|---|---|
| `clean` | Desired and Built agree |
| `dirty` | Desired changed; the public tree is still the previous Built Generation |
| `recovering` | a durable nonterminal operation exists |
| `error` | durable evidence conflicts and automatic recovery cannot choose safely |

Use `status` to diagnose. Do not use it as a substitute for `check`.

## `check`: delivery proof

```bash
sow check -r local
```

The v0.2.0 checker reports nine ordered layers:

| Layer | Verifies |
|---|---|
| `config` | strict configuration and effective Dist inputs |
| `retained` | explicit retained Generation records and frozen metadata |
| `state` | SQLite schema and relational state |
| `public-modes` | expected public file and directory modes |
| `package-bytes` | pool/pending objects against recorded SHA-256 |
| `desired-membership` | package identity, membership, and architecture consistency |
| `index` | rendered metadata and reference closure |
| `signature` | declared metadata and RPM package trust requirements |
| `generation-manifest` | recorded Built manifest against the public tree |

`check` writes and repairs nothing. A dirty or recovering Repository is not deliverable
even if its last committed tree remains readable. Put `check` in the release pipeline and
stop on any nonzero exit.

## `changes`: Generation difference

```bash
sow changes -r local
sow changes 0 -r local
sow changes 42 -r local --json
```

- no base argument compares the current Built Generation with its predecessor;
- base `0` describes the complete current public tree;
- base `N` gives the net difference from recorded Generation `N` to current Built.

Rows include operation, phase, Repository-relative path, size, and SHA-256. Phases use the
same vocabulary as local construction: payload, metadata, pointer, delete.

`changes` is a manifest/difference surface. It does not contact a destination, persist a
remote checkpoint, enforce cache grace, or recover an interrupted transfer. Use
`sow publish TARGET` for a configured live target. For an offline copy, stage a complete
tree, verify it, and switch it into service atomically.

## Generation retention and GC

```bash
sow retain add 42 -r local
sow retain ls -r local
sow retain rm 42 -r local
sow gc -r local
```

`retain add` verifies and freezes a Generation's metadata and reference sets; it does not
copy another package tree. The retained record is an explicit GC root. `retain rm` removes
that root but deletes no package bytes itself.

Local `sow gc` deletes only payloads proven unreachable from the current state, explicit
retentions, active recovery/publication state, and other recorded roots. Target GC is a
separate operation: `sow gc TARGET` uses that Provider's safety model.

During ordinary builds, SOW carries forward the immediately preceding RPM immutable
metadata and APT by-hash objects so a reader of the previous pointer can finish. This
bounded protocol window is separate from explicit `retain`.

## Operation log

```bash
sow log -r local
sow log OPERATION -r local
sow log export operations.jsonl -r local
sow log prune 2026-01-01 -r local
```

The ledger records operation kind/state, timestamps, configuration/manifest identities,
package dispositions, membership changes, and physical changes where applicable.

`log export` writes stable JSONL, refuses to overwrite an existing file, and validates its
output path. `log prune` accepts a date or RFC 3339 timestamp and removes only eligible
terminal audit records; it does not remove current state, recovery evidence, or Generation
manifests still required elsewhere.

## Operational pattern

```bash
sow build -r local
sow check -r local
sow publish public
```

Use `status` for monitoring, `check` for the gate, `publish` for target mutation, and `log`
for later evidence.

## See also

- [Build and check commands](/docs/reference/cli/build/)
- [Log commands](/docs/reference/cli/log/)
- [Publication lifecycle](/docs/reference/cli/publication/)
