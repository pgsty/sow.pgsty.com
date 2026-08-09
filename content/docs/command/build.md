---
title: "sow build"
linkTitle: "build"
description: "Converge Desired Membership and renderer configuration into a complete Built Generation."
url: "/docs/command/build/"
weight: 1200
icon: fa-solid fa-hammer
---

`sow build` is the explicit Desired-to-Built convergence command. It acquires the Repository write
lock, recovers any decidable unfinished Operation, renders and verifies a complete Generation, then
switches protocol pointers last.

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
| `--json` | Wrap the result in the `sow.cli/v1` envelope | false |

Without `-d`, SOW converges every affected Dist in the selected Repository. With `-d`, only those
Dists converge; unselected changes remain dirty.

## Result

The command-specific result is JSON even without `--json`:

```console
sow build -r pgsql -d el9
{"operation":"4262183287563704350","repository":"pgsql","dists":["el9"],"desired_revision":6,"built_generation":"00000000000000000006","noop":false,"dirty":false}
```

Adding `--json` wraps it in the standard envelope.

## No-op builds

When membership, relevant policy, renderer settings, and signing configuration already match the
Built Generation, `build` is an idempotent no-op and does not increment the Generation:

```console
sow build
{"operation":"6295064788473690577","repository":"pigsty","dists":["el9","trixie"],"desired_revision":5,"built_generation":"00000000000000000005","noop":true,"dirty":false}
```

## Policy convergence

`build` re-evaluates the current `exclude` and `limit` policy. Tightening policy may remove Desired
Membership. Loosening policy does not reconstruct historical members from leftover pool bytes; run
[`sow add`](/docs/command/add/) again for packages you want to restore.

## Commit and recovery

SOW stages new metadata on the same filesystem, verifies it, then switches mutable protocol pointers
last. RPM checksum-named metadata and APT by-hash keep old and new readers self-consistent.

One Operation may cover several Dists. Each Dist always exposes a complete view; when `build`
returns, every included Dist belongs to the same Built Generation.

Before starting new work, `build` attempts forward recovery or safe rollback of a non-terminal
Operation. If journal, database, and filesystem evidence contradict each other, the Repository enters
`error` and `build` refuses to guess. There is no force-repair flag.

## Metadata signing

Managed metadata signing is configured only in `sow.yml`; there is no command-line key override.
Changing a configured key reference or fingerprint makes affected Dists dirty, and the next build
re-signs their metadata.

- RPM: always writes `repodata/repomd.xml`; writes `repomd.xml.asc` when configured.
- DEB: always writes `Release`; writes `InRelease` and `Release.gpg` when configured.

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Converged successfully or nothing to do |
| `1` | Renderer, signing, or filesystem failure |
| `2` | Usage error, Workspace not found, or implicit Repository selection is ambiguous |
| `4` | Repository write lock unavailable |
| `5` | Recovery cannot complete safely, or Repository is in `error` |
| `6` | Explicit scope is not configured, or current configuration rejects existing state |

## See also

- [`sow status`](/docs/command/status/) — determine whether convergence is needed
- [`sow check`](/docs/command/check/) — verify the resulting tree
- [`sow changes`](/docs/command/changes/) — inspect the resulting file delta
- [Transactions & Recovery](/docs/feature/transactions/) — full commit protocol
