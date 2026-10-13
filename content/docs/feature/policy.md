---
title: "Membership Policy"
linkTitle: "Membership Policy"
description: "Configure exclusions and version limits, read policy results, and restore removed members."
categories: [Feature]
tags: [policy, managed]
url: "/docs/feature/policy/"
weight: 500
icon: fa-solid fa-filter
---

<span id="the-two-rules-and-their-order"></span>

Use Dist policy to exclude unwanted packages and limit the number of versions in indexes.
Set `exclude` and `limit` in `sow.yml`:

```yaml
dists:
  el9:
    format: rpm
    limit: 2
    exclude:
      - kind: [debuginfo, debugsource, llvmjit]
```

SOW applies `exclude` first, then `limit`. `add`, `rm`, and `build` apply policy to the
complete candidate membership of each selected Dist. Edit the policy, run
`sow config check`, then run `sow build` to apply it to existing members.

<span id="exclude"></span>

## Exclude packages

Each rule contains one or more fields. All fields in a rule must match. Any pattern
within a field can match. A package is excluded when any rule matches.

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

This excludes the listed package kinds on every architecture. It also excludes `aarch64`
packages whose names start with `test-` or end with `-experimental`.

| Field | Package value |
|---|---|
| `name` | Binary package name |
| `source` | Normalized source package name |
| `arch` | `x86_64`, `aarch64`, or `neutral` |
| `kind` | Classification in the table below |
| `format` | `rpm` or `deb` |

Patterns are case-sensitive exact strings or shell globs: `*`, `?`, and `[...]`.
Regular expressions, version comparisons, and negation are not supported. Empty rules,
empty or untrimmed patterns, duplicate patterns within a field, and invalid globs are errors.

SOW derives `kind` from the binary package name:

| Format | Name suffix | `kind` |
|---|---|---|
| RPM | `-debuginfo` | `debuginfo` |
| RPM | `-debugsource` | `debugsource` |
| RPM | `-llvmjit` | `llvmjit` |
| DEB | `-dbgsym` | `dbgsym` |
| DEB | `-dbg` | `dbg` |
| Either | No matching suffix | `main` |

Use `sow show PACKAGE --json` to inspect the computed kind. Pattern values are not checked
against this table: `kind: [debug]` is valid YAML but matches no package kind.

<span id="limit"></span>

## Limit versions

`limit` groups packages by binary name and canonical architecture family. Neutral
packages (`noarch` or `all`) form their own group.

| Value | Result |
|---|---|
| `0` | Keep all versions; this is the default |
| Positive `N` | Keep the newest `N` versions in each group |
| Negative value | Configuration error |

RPM versions use epoch-version-release ordering. DEB versions use Debian version ordering.
Versions are not sorted as plain strings.

With `limit: 2`, adding version 3 to a Dist that contains versions 1 and 2 removes version 1
from membership in the same operation. An `x86_64` package and a `noarch` package count in
separate groups, even when they share a binary name.

<span id="policy-runs-over-the-full-candidate-set"></span>

## Read policy results

An input excluded from every selected Dist has item status `excluded`. Its per-Dist result
is `excluded` for an exclusion rule or `limited` for the version cap. Policy exclusion
does not count as a failed input and does not make the command fail.

A package can be accepted by one Dist and excluded by another. If no Dist accepts a new
package, SOW does not store an unreferenced package object for it.

<span id="loosening-a-policy-never-resurrects-anything"></span>

## Restore a removed version

Relaxing policy does not restore previous members. Raising `limit`, removing an exclusion,
or deleting the newest version only changes the rules for current and future candidates.
To restore a version, add its package file again:

```bash
sow add ./archive/example-1.0-1.x86_64.rpm -r demo -d el9
```

Policy removes membership, not package bytes. A package can remain in the pool because a
built or retained generation still needs it. Use [`sow gc`](/docs/command/gc/) to reclaim
unreferenced objects. Use `sow gc TARGET` for a published target.

<span id="previewing-a-decision"></span>

## Preview removal

```bash
sow rm example -r demo -d el9 --check
```

The preview reports membership removals and predicted file changes without changing repository state.
Check `prediction_complete` in JSON before treating the file list as complete.
`--check` cannot be combined with `--skip`, `--timeout`, or `--no-wait`.

See [Configuration](/docs/reference/config/) for the full schema and
[`sow add`](/docs/command/add/) for input results.

<span id="next"></span>
