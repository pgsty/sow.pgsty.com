---
title: "sow build"
linkTitle: "build"
description: "Build local indexes from Desired membership and current configuration."
categories: [Command]
tags: [cli, managed, generation]
url: "/docs/command/build/"
weight: 1200
icon: fa-solid fa-hammer
---

`sow build` updates local indexes to match Desired membership and current configuration. Run it after `add --skip`, `rm --skip`, or a policy change. It recovers unfinished local Repository operations before starting the next build.

## Synopsis

```text
sow build [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-j, --jobs N` | Parallel workers; must be at least `1` | logical CPU count |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a Repository | [selection rules](/docs/command/#repository-selection) |
| `-d, --dist NAME` | Build named Dists; repeatable | all affected Dists |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

Without `-d`, SOW builds every affected Dist in the selected Repository. With `-d`, only those
Dists are built; unselected changes remain dirty.

## Result

Without `--json`, `build` prints one human-readable summary:

```console
sow build -r demo -d el9
built repository=demo operation=2769214987359113555 dists=el9 revision=4 generation=00000000000000000005 dirty=false
```

Use `--json` to read the result in a script.

## No-op builds

When membership, relevant policy, renderer settings, and signing configuration already match the
Built Generation, `build` is an idempotent no-op and does not increment the Generation:

```console
sow build -r demo -d el9
build repository=demo dists=el9 already current (noop) revision=4 generation=00000000000000000005 dirty=false
```

## Apply policy changes {#policy-convergence}

`build` re-evaluates the current `exclude` and `limit` policy. Tightening policy may remove Desired
Membership. Loosening policy does not reconstruct historical members from leftover pool bytes; run
[`sow add`](/docs/command/add/) again for packages you want to restore.

## Commit and recovery

SOW moves required pending packages into `pool/`, writes the indexes, then updates client entry points such as `repomd.xml` and `Release`. One build can include several Dists. They share the resulting Generation; unselected dirty Dists still need a build.

If a build stops, rerun it. SOW uses the operation journal to finish or roll back the unfinished work. If the journal, database, and files disagree, the command reports an integrity error. Use `sow check` and `sow log` to identify the affected state.

## Publication time

Each new build records one UTC publication time, with whole-second precision.
APT `Release` dates, RPM data timestamps, and metadata signatures use this time across the affected Dists.
Recovery reuses it; a no-op build leaves it unchanged.

The chosen time cannot precede the recorded time of an existing build or the selected key's activation time.
A key that is not yet usable causes an error. Keep the host clock correct.

Older journals and `repo migrate` keep their previous timestamp behavior.
An `rm --check` preview chooses its own time, so its predicted hashes and sizes can differ from execution.
See [Publication times](/docs/reference/compatibility/#publication-times).

## Progress events

Long builds append structured `build_progress` records to the Operation log. Each event
contains `phase`, `completed`, `total`, and `jobs`. Current phases are:

- `rendering`;
- `promoting_payload`;
- `publishing_dists`;
- `normalizing_public_tree`;
- `finalizing`.

Inspect the events with [`sow log OPERATION`](/docs/command/log/#one-operation-in-detail).

## Metadata signing

Configure metadata signing in `sow.yml`.
Changing a configured key reference or fingerprint makes affected Dists dirty, and the next build
re-signs their metadata.

- RPM: always writes `repodata/repomd.xml`; writes `repomd.xml.asc` when configured.
- DEB: always writes `Release`; writes `InRelease` and `Release.gpg` when configured.

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Build completed or nothing to do |
| `1` | Renderer, signing, or filesystem failure |
| `2` | Usage error, Workspace not found, or implicit Repository selection is ambiguous |
| `4` | Repository write lock unavailable |
| `5` | Recovery cannot complete safely, or Repository is in `error` |
| `6` | Explicit scope is not configured, or current configuration rejects existing state |

## See also

- [`sow status`](/docs/command/status/) — determine whether a build is needed
- [`sow check`](/docs/command/check/) — verify the resulting tree
- [`sow changes`](/docs/command/changes/) — inspect the resulting file delta
- [Transactions & Recovery](/docs/feature/transactions/) — full commit protocol
