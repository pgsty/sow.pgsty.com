---
title: "Membership Policy"
linkTitle: "Membership Policy"
description: "How exclude and limit decide which packages stay in a Dist: rule fields, glob matching, version ordering, and why loosening a policy never resurrects a removed member."
url: "/docs/feature/policy/"
weight: 500
icon: fa-solid fa-filter
---

Policy is the answer to "I dumped a build directory into this Dist and I do not want the debuginfo packages, and I only want the latest version of each package." Two rules do that work, they run in a fixed order, and they run over the whole candidate set — not just the packages you happened to add this time.

## The two rules and their order

```text
candidate set  →  exclude  →  limit  →  Desired Membership
```

`exclude` drops packages that match a rule. `limit` then caps how many versions survive per package name and architecture. The order is fixed and never configurable, because the reverse order would let an excluded package consume a version slot on its way out.

Both rules are enforced on every `add`, every `rm`, and every `build`. That last one matters: editing `limit` or `exclude` in `sow.yml` marks the affected Dists dirty, and the next `build` re-applies the new policy to the existing membership. You do not have to re-add anything to make a tightened policy take effect.

```yaml
dists:
  el9:
    format: rpm
    limit: 1
    exclude:
      - kind: [debuginfo, debugsource, llvmjit]
```

## `exclude`

`exclude` is a list of rules. Within one rule, fields are combined with **AND**. Within one field, multiple patterns are combined with **OR**. Rules are combined with **OR** — any rule matching excludes the package. Field order and rule order never change the result.

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

That reads as: drop every debug-ish package regardless of architecture, *and* drop `aarch64` packages whose name starts with `test-` or ends with `-experimental`.

Five fields are allowed:

| Field | Matches against |
|---|---|
| `name` | the binary package name |
| `source` | the normalized source name |
| `arch` | `x86_64`, `aarch64`, or `neutral` |
| `kind` | the fixed enumeration below |
| `format` | `rpm` or `deb` |

Patterns are case-sensitive exact strings or shell globs (`*`, `?`, `[]`). There is no regex, no version comparison, no negation, and no expression language. Unknown fields, empty rules, and invalid globs fail at `config check` rather than silently matching nothing.

`kind` is derived from the binary name, most specific suffix winning:

| Format | Name suffix | `kind` |
|---|---|---|
| RPM | `-debuginfo` | `debuginfo` |
| RPM | `-debugsource` | `debugsource` |
| RPM | `-llvmjit` | `llvmjit` |
| DEB | `-dbgsym` | `dbgsym` |
| DEB | `-dbg` | `dbg` |
| any | none of the above | `main` |

Classification comes from the package itself. It never depends on which directory the file came from or which host you are running on, so the same input always classifies the same way. `sow show --json` exposes the computed `kind`.

An excluded package is reported, not treated as a parse error, and it is not stored:

```console
$ sow add pkg/blackbox_exporter-0.28.0-1.x86_64.rpm pkg/pev2-1.23.0-1.noarch.rpm -r demo -d el9
add repository=demo operation=7877233225745514469 accepted=1 failed=0 memberships=+1/-0 revision=3 generation=3 dirty=false
item input="pkg/blackbox_exporter-0.28.0-1.x86_64.rpm" status=excluded format=rpm coordinate="blackbox_exporter-0:0.28.0-1.x86_64" sha256:5759c643… dists=el9:excluded
item input="pkg/pev2-1.23.0-1.noarch.rpm" status=accepted format=rpm coordinate="pev2-0:1.23.0-1.noarch" sha256:d06d7f23… dists=el9:accepted
```

The command exits `0`. Nothing was wrong with the excluded package — it just does not belong in this Dist. If a package is accepted by no Dist at all, no ownerless pool object is written for it.

## `limit`

`limit` groups memberships by `(binary name, native architecture)` and keeps the newest N:

- `0` — keep every version. This is the default.
- positive `N` — keep the N newest by native version ordering.
- negative — a configuration error.

Two details decide most real questions.

**The grouping key includes architecture.** `limit: 1` does not mean "one version of this package in this Dist"; it means "one version per name and native architecture". So `pg_sample-1.13` for `x86_64` and `pg_sample-1.17` for `noarch` both survive in a `limit: 1` Dist, because they are in different groups. Neutral (`noarch`/`all`) counts once as its own native architecture even though it renders into multiple views.

**Ordering is native to the format.** RPM uses EVR comparison — epoch, version, release, with the standard rpm segment rules. DEB uses Debian version comparison, where the version string already carries the epoch and revision. SOW does not invent a version scheme or compare strings lexically.

Here is `limit: 1` deciding between two Debian versions of the same package and architecture:

```console
$ sow add pkg/libpq5_18.4-1.bookworm_amd64.deb pkg/libpq5_18.4-1.trixie_amd64.deb -r demo -d trixielim
add repository=demo operation=2402398619981505515 accepted=1 failed=0 memberships=+1/-0 revision=4 generation=4 dirty=false
item input="pkg/libpq5_18.4-1.bookworm_amd64.deb" status=excluded format=deb coordinate="libpq5=3:18.4-1.bookworm:amd64" sha256:be8a2863… dists=trixielim:limited
item input="pkg/libpq5_18.4-1.trixie_amd64.deb" status=accepted format=deb coordinate="libpq5=3:18.4-1.trixie:amd64" sha256:0a7df397… dists=trixielim:accepted
```

Note the two levels of reporting: the item's overall `status` is `excluded` (it did not become a member anywhere), while the per-Dist outcome is `limited` — telling you it lost on version, not on an `exclude` rule. When you have several Dists selected, each one reports its own outcome, so a package can be `accepted` in one and `limited` in another in a single command.

`limit` removing an older membership and adding the newer one happens inside the same operation, so the ledger shows one atomic decision rather than a delete followed by an unrelated insert.

## Policy runs over the full candidate set

A common misreading is that `add` applies policy only to the packages on the command line. It does not. After merging your input into the target memberships, SOW evaluates `exclude` and then `limit` over the **complete** membership set of each selected Dist.

The practical consequence: adding version 3 to a `limit: 2` Dist that already holds versions 1 and 2 removes version 1 in the same operation. You cannot smuggle a package past the version cap by adding it separately, and you never end up with N+1 members because the cap was only checked against the delta.

## Loosening a policy never resurrects anything

This is the semantics people most often expect to work the other way, so it is worth showing directly. Continuing from the `limit: 1` example above, remove the version that won:

```console
$ sow rm 'deb:libpq5=3:18.4-1.trixie:amd64' -r demo -d trixielim
$ sow ls -d trixielim
repository=demo dists=trixielim dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
```

The Dist is empty. The bookworm build did not come back, even though its bytes are still sitting in the pool, and even though there is now a free slot under `limit: 1`.

The reason is that `exclude` and `limit` remove **actual Desired Memberships**. SOW does not maintain a shadow list of "candidates that policy suppressed but might return later". Pool bytes are storage, not a candidate set. Raising a limit or relaxing an `exclude` therefore gives you room for future additions; it does not reach back into history and guess which of the packages you once had should reappear.

To get it back, add it again — explicitly:

```console
$ sow add pkg/libpq5_18.4-1.bookworm_amd64.deb -r demo -d trixielim
add repository=demo operation=590501245267266669 accepted=1 failed=0 memberships=+1/-0 revision=6 generation=6 dirty=false
item input="pkg/libpq5_18.4-1.bookworm_amd64.deb" status=accepted format=deb coordinate="libpq5=3:18.4-1.bookworm:amd64" sha256:be8a2863… dists=trixielim:accepted
```

Convergence is one-directional and it is stated as an invariant: **tightening policy can remove members; loosening policy never restores them.** That asymmetry is what makes `build` safe to run at any time. If it were symmetric, editing `sow.yml` could silently republish a package you deliberately withdrew — which is exactly the failure you do not want in a security update.

> [!WARNING] Withdrawing a package for real
> `sow rm` removes membership, not pool bytes. The package disappears from every index, so
> clients can no longer resolve it through the repository. Run `sow gc` only after the
> payload becomes unreachable from every safety root, including current and retained
> Generations, recovery state, publication attempts, and active maintenance operations.
> For published targets, use `sow gc TARGET`; filesystem deletion is conditional and R2 is
> report-only. Do not manually delete canonical pool files behind SOW's state.

## Previewing a decision

`sow rm -c` computes the removals, the policy consequences, and the file changes a build would produce, and writes nothing:

```bash
sow rm patroni -r pgsql -d el9 -c
```

`-c/--check` takes no write lock and is mutually exclusive with `--skip`. Passing `--timeout` or `--no-wait` alongside it is a usage error, so that nobody mistakes a preview for something that waits on a write transaction.

## Next

- [`sow.yml` reference](/docs/reference/config/) — the complete policy schema
- [`sow add` reference](/docs/command/add/) — per-item statuses and the partial-success exit code
- [Pool & Architecture Views](/docs/feature/views/) — where the surviving members get rendered
- [`sow retain`](/docs/command/retain/) and [`sow gc`](/docs/command/gc/) — payload lifecycle controls
