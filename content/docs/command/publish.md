---
title: "sow publish"
linkTitle: "publish"
description: "Publish a Built Generation to a filesystem or R2 target."
categories: [Command]
tags: [cli, publish, object-storage, filesystem]
url: "/docs/command/publish/"
weight: 1500
icon: fa-solid fa-cloud-arrow-up
---

`sow publish` copies the current Built Generation to a target in the `targets:` section of `sow.yml`. The target selects the Repository and storage provider. Build first when the target must include the latest Desired changes.

## Synopsis

```text
sow publish TARGET [--abort | --rebind] [-C|--workdir DIR] [-T|--timeout DUR | -N|--no-wait] [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `--abort` | Abandon an interrupted publication before its commit phase | false |
| `--rebind` | Confirm and record permitted target name/public endpoint/cache-TTL changes | false |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-T, --timeout DUR` | Maximum Repository-lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

`TARGET` must name a configured `filesystem` or `r2` publication target. `--abort` and
`--rebind` are mutually exclusive.

## Before publication {#safety-boundaries}

Run `build` first to include the latest package and policy changes. A dirty Repository can still publish its previous completed Built Generation.

Configure the target's web server or bucket access so that `public_endpoint` serves the published files. Then run `sow publish TARGET`.

## Publication protocol

SOW verifies the local files against the completed Generation manifest, then publishes in this order:

1. package files;
2. metadata with content-specific URLs;
3. client entry points, such as `repomd.xml` and `Release`;
4. public visibility checks and a saved publication checkpoint.

SOW records progress so the same command can resume an interrupted publication. When the target already contains the current Generation, repeating the command changes nothing.

```console
sow publish local
published demo generation=00000000000000000005 to local (filesystem): phase=grace objects=14
sow publish local
publication demo generation=00000000000000000005 to local is already current (noop)
```

## Rebind mutable target settings

The first publication records the Repository and target binding. After changing the target name, public endpoint, or cache TTL, use `--rebind` to record the updated settings and continue publication:

```bash
sow publish prod --rebind
```

If you renamed the target in `targets:`, use its new name.

| May change | Immutable; configure a new target |
|---|---|
| target name | Repository identity |
| `public_endpoint` | provider, storage `endpoint`, or region |
| `max_cache_ttl` | bucket or `prefix` |

Complete pending target maintenance before changing `max_cache_ttl`. For a filesystem target, also complete pending deletion before changing `public_endpoint`. To publish to a new target for the first time, use `sow publish TARGET` without `--rebind`.

## Abort and recovery

After an interruption, rerun `sow publish TARGET` to resume the publication.

To abandon the attempt, use `sow publish TARGET --abort` before it reaches `commit_intent`. SOW checks the objects already uploaded and records the abandonment. It leaves remote files in place. Once the attempt reaches `commit_intent`, rerun the ordinary publish command to finish it.

A published package URL identifies fixed content. Use a new package version and filename for changed content. If existing remote files differ from the recorded attempt, follow the reported conflict diagnosis; see [Troubleshooting](/docs/reference/troubleshooting/).

## Public visibility checks

Before recording a checkpoint, SOW verifies that the published files can be read through `public_endpoint`. HTTP(S) verification uses ordinary GET requests. Stale or missing content is retried up to `max_cache_ttl`.

Filesystem targets support `file://` or HTTP(S) public endpoints. R2 targets require HTTP(S). Each R2 publication lists the target prefix and checks each object with HEAD. An update performs this inventory check twice.
SOW uses up to eight concurrent HEAD requests per page. This limit is internal; `publish` has no `--jobs` option.
Upload retries do not reset the idle timeout unless data transfer makes progress. Keep old objects on R2: target GC reports them without deleting them, and later publication checks the prefix against the recorded inventory.

## Removing a published view

While a target remains configured, its published entry points must remain available locally. These include Dists, RPM architecture views, and signing companion files.

To retire that target, stop publishing to it, remove its entry from `targets:` in `sow.yml`, and run `sow config check`. You can then remove the local view. This leaves the old remote files and publication history intact. To publish the reduced repository, configure a new target with a different storage prefix and update clients to use it.

## Exit behavior

| Code | Trigger |
|---|---|
| `0` | Publication completed or target was already current |
| `1` | Filesystem, provider, network, verification, or binding conflict (including required rebind) |
| `2` | Usage, Workspace discovery, or invalid `sow.yml` error |
| `4` | Repository write lock unavailable |
| `5` | Local or publication recovery evidence is inconsistent, or source is not deliverable |
| `6` | Target is missing/unsafe, or another safety precondition rejects publish/abort/rebind |

## See also

- [`sow status`](/docs/command/status/) and [`sow check`](/docs/command/check/) — decide whether the Built Generation is the one you intend to deliver
- [`sow gc`](/docs/command/gc/) — reclaim unused target files
- [`sow.yml` targets](/docs/reference/config/#publication-targets) — provider configuration
- [Publication Model](/blog/design/publication/) — phases, receipts, recovery, and cache grace
