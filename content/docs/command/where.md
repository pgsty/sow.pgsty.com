---
title: "sow where"
linkTitle: "where"
description: "Find a package across the Workspace."
categories: [Command]
tags: [cli, managed]
url: "/docs/command/where/"
weight: 1000
icon: fa-solid fa-location-dot
---

`sow where` finds the Desired membership locations of one package across a Workspace. It searches all Repositories by default. Use `-r` or `-d` to limit the search.

## Synopsis

```text
sow where PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Restrict the search to one Repository | all Repositories |
| `-d, --dist NAME` | Restrict the search to named Dists; repeatable | all Dists |
| `--json` | Output JSON | false |

## Reference resolution

`PACKAGE` uses the same grammar as [`sow show`](/docs/command/show/): SHA-256 identity, canonical
RPM/DEB coordinate, full filename, or bare name.

The reference must identify one package: the same format, coordinate, and SHA-256. That package can exist in several Repositories. If different packages match, use `-r` or `-d` to narrow the search, or supply an exact coordinate or SHA-256.

## Output

Without `--json`, `where` prints a summary followed by one line per location:

```console
sow where 'rpm:centos-release-0:6-0.el6.centos.5.x86_64'
reference="rpm:centos-release-0:6-0.el6.centos.5.x86_64" locations=1
repository=demo coordinate="rpm:centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16 dists=el9 built_dists=el9
```

Each location reports Desired `dists` and current `built_dists` across its Repository. Candidate lookup uses Desired membership. A package removed from every selected Dist is no longer found, even if a previous Built index still contains it. Use `sow show PACKAGE -r NAME` without `-d` to inspect such a stored object.

With `--json`, the locations appear in `result.locations`. If no package matches, the command returns an error:

```console
sow where nosuchpkg
operation rejected: managed: operation rejected: package reference "nosuchpkg" was not found in the selected Workspace scope
```

## Example

List the Dists that include this package in Desired state:

```bash
sow where 'rpm:patroni-0:3.0.4-1.noarch' --json |
  jq -r '.result.locations[] | "\(.repository)/\(.dists | join(","))"'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | One resolved Package Object and its locations printed |
| `1` | Runtime I/O failure |
| `2` | Usage error or Workspace not found |
| `5` | A Repository state database is unreadable or inconsistent |
| `6` | Explicit Repository/Dist is not configured, or the reference matched nothing/was ambiguous |

## See also

- [`sow show`](/docs/command/show/) — inspect the resolved Package Object
- [`sow ls`](/docs/command/ls/) — list one Dist set
- [Package References](/docs/reference/package-ref/) — exact grammar and ambiguity rules
