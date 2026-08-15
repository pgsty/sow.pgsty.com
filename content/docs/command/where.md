---
title: "sow where"
linkTitle: "where"
description: "Locate one Package Object across Repositories and Dists in a Workspace."
url: "/docs/command/where/"
weight: 1000
icon: fa-solid fa-location-dot
---

`sow where` answers which Dists in the Workspace still carry one Package Object. It is read-only,
searches every Repository by default, and takes no write lock.

## Synopsis

```text
sow where PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| Flag | Meaning | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Restrict the search to one Repository | all Repositories |
| `-d, --dist NAME` | Restrict the search to named Dists; repeatable | all Dists |
| `--json` | Emit the `sow.cli/v1` envelope | false |

## Reference resolution

`PACKAGE` uses the same grammar as [`sow show`](/docs/command/show/): SHA-256 identity, canonical
RPM/DEB coordinate, full filename, or bare name.

Resolution happens across the complete selected scope. A bare name must identify one Package Object;
different objects with the same binary name are ambiguous even when they live in different
Repositories. Use `-r`/`-d`, or supply an exact coordinate or SHA-256.

## Output

Without `--json`, `where` prints a command-specific JSON object:

```console
sow where epel-release
{"reference":"epel-release","locations":[{"repository":"pigsty","dists":["el9"],"built_dists":["el9"],"sha256":"d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab","coordinate":"rpm:epel-release-0:7-5.noarch"}]}
```

Each location reports both Desired `dists` and current `built_dists`. This makes the command useful
for answering whether a removed or superseded build is still client-visible anywhere.

With `--json`, the same object appears under `result`. A missing reference is an expected rejection,
not an empty success:

```console
sow where nosuchpkg
operation rejected: managed: operation rejected: package reference "nosuchpkg" was not found in the selected Workspace scope
```

## Example

List every location still serving an exact build:

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
