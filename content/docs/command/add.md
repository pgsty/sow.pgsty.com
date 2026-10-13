---
title: "sow add"
linkTitle: "add"
description: "Import packages, apply membership policy, and build local indexes."
categories: [Command]
tags: [cli, managed, policy]
url: "/docs/command/add/"
aliases: ["/docs/reference/cli/add/"]
weight: 600
icon: fa-solid fa-plus
---

`sow add` imports packages into the selected Dists and builds their local indexes. It reads package format and architecture from the package headers, then applies each Dist's policy. Use `--skip` to import several batches before one build. To update a remote target, run [`sow publish`](/docs/command/publish/) after the build.

## Synopsis

```text
sow add PATH... [-R|--recursive] [--skip] [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

## Options

| Flag | Description | Default |
|---|---|---|
| `-R, --recursive` | Descend into subdirectories of a `PATH` directory | off (top level only) |
| `--skip` | Update Desired state only; do not build | off |
| `-j, --jobs N` | Parallel workers for parsing, hashing and rendering | logical CPU count |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Select a distribution; repeatable | selection rules |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Output JSON | false |

## Inputs and targets

`PATH` can be a file or a directory. A directory is scanned top level only unless you pass `-R`.

Select one Repository and one or more Dists. Use `-r` and `-d`, or the [directory-based defaults](/docs/command/). In a mixed RPM/DEB batch, each package goes only to Dists of its format. A package with no compatible target fails.

Choose Dists that match the package’s intended distribution. SOW checks package format and architecture; it does not test operating-system or dependency compatibility.

```console
sow add /srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=8677129233475584643 accepted=2 failed=0 memberships=+2/-0 revision=3 generation=3 dirty=false
item input="/srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm" status=accepted format=rpm coordinate="centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead dists=el9:accepted
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=accepted format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

The summary reports the Operation ID, item counts, and membership changes. It also shows the Desired Revision, Built Generation, and dirty state. Each input then has one `item` line, in stable order.

## Item statuses

Each `item` line carries an overall `status` plus a per-Dist verdict in `dists=`.

| Status | Meaning |
|---|---|
| `accepted` | New Package Object created and at least one Membership added |
| `reused` | The content already exists in this Repository; only Membership references may change |
| `excluded` | Policy removed it from every target Dist — see the `dists=` field for `excluded` vs `limited` |
| `failed` | The package was rejected; the `error=` field says why |

`reused` is content idempotence: adding the same file twice never creates a second object or a
duplicate Membership. A repeated `add` also builds the selected Dist by default. If it is already
current, the Generation stays unchanged. If an earlier `--skip` or configuration change left it dirty, SOW completes the build and may advance the Generation:

```console
sow add /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=656950149626836753 accepted=1 failed=0 memberships=+0/-0 revision=4 generation=4 dirty=false
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=reused format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

The same object added to a second Dist is also `reused` — the pool keeps one copy and gains a second
Membership. Use `--skip` again to postpone the build.

## Package architecture {#architecture-is-read-never-guessed}

`add` reads format and native architecture from the package header, then checks the Workspace permit
list. An unsupported architecture or one outside the configured list rejects that package:

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
item input="/srv/pkg/centos-release-3.1-1.i386.rpm" status=failed error="managed: operation rejected: unknown rpm package architecture \"i386\"; supported rpm package architectures are [x86_64, aarch64, noarch] (canonical families [x86_64, aarch64, neutral]); use a supported package or update only supported architecture families in sow.yml"
```

RPM `noarch` and DEB `all` are architecture-neutral. They create one Package Object and one
Membership, and render into every effective architecture view of the target Dist. Only the selected Dists receive them.

## Policy: exclude and limit

After merging into the target Memberships, SOW re-evaluates `exclude` and then `limit` over the
complete Dist candidate set. A package removed by policy is reported, not treated as a parse failure.

```console
sow add /srv/pkg/debs -r pgsql -d trixielim
add repository=pgsql operation=4142220455201181493 accepted=3 failed=0 memberships=+3/-0 revision=6 generation=6 dirty=false
item input="/srv/pkg/debs/libpq5-dbgsym_18.3-1_amd64.deb" status=excluded format=deb coordinate="libpq5-dbgsym=18.3-1:amd64" sha256:cf491b9d9b218fa49ad2b41b4740d62cd972e1b515bf33677c2c3ead75acc60a dists=trixielim:excluded
item input="/srv/pkg/debs/libpq5_18.2-1_amd64.deb" status=excluded format=deb coordinate="libpq5=18.2-1:amd64" sha256:fa84dc641b7c686be2f9b512311ad0b74eac03e2afc9eff7e9af75b82b68ff41 dists=trixielim:limited
item input="/srv/pkg/debs/libpq5_18.3-1_amd64.deb" status=reused format=deb coordinate="libpq5=18.3-1:amd64" sha256:491992c502113627d44d0d66a2b189cdaa8accff293ebaf84fe10ccbc9da574c dists=trixielim:accepted
item input="/srv/pkg/debs/libpq5_18.3-1_arm64.deb" status=reused format=deb coordinate="libpq5=18.3-1:arm64" sha256:3a2f7ef7cddfa3dc06280ef59eda1dab9724d57499931ee80758b11531c1f40c dists=trixielim:accepted
item input="/srv/pkg/debs/pg-sample_1.17-1_all.deb" status=reused format=deb coordinate="pg-sample=1.17-1:all" sha256:f23581c5164a143e5e902232589adf1d30b73ba3857a692a11da607f246aacc3 dists=trixielim:accepted
```

Here `trixielim` has `exclude: [{kind: [dbgsym]}]` and `limit: 1`. The dbgsym package was excluded by
rule; `libpq5 18.2-1` lost to `18.3-1` under the version limit and is reported as `limited`. Both
appear as `excluded` in the top-level status, and the `dists=` field distinguishes them.

Limit groups by `(binary name, canonical architecture)`, so `18.3-1:amd64` and `18.3-1:arm64` both
survive a `limit: 1`. A package can be accepted by one Dist and skipped by another in the same run.

To restore a package after relaxing `exclude` or `limit`, run `sow add` again. Policy applies to Desired membership, not every file left in `pool/`.

## Partial batches

Valid, conflict-free packages are committed even when siblings fail. Failed inputs stay where they
are, each with its own error, and the command exits `3`:

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm /srv/pkg/centos-release-6-0.el6.centos.5.x86_64.rpm -r pigsty -d el9
add repository=pigsty operation=4623871845694427260 accepted=1 failed=1 memberships=+1/-0 revision=5 generation=5 dirty=false
item input="/srv/pkg/centos-release-3.1-1.i386.rpm" status=failed error="managed: operation rejected: unknown rpm package architecture \"i386\"; ..."
item input="/srv/pkg/centos-release-6-0.el6.centos.5.x86_64.rpm" status=accepted format=rpm coordinate="centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16 dists=el9:accepted
managed: batch partially succeeded
```

If *every input fails*, the operation exits `6`; Desired memberships and public content
remain unchanged. Human output includes each failed input and its reason, and JSON includes
them in `result.items`:

```bash
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
```

Policy-excluded inputs are not input failures; an entirely excluded batch can succeed even
when the Dist was empty. If you interrupt the command with SIGINT or SIGTERM, it returns `130`. Rerun it with the original input files; recovery preserves committed membership changes.

For changed package content, use a new version and filename. A previously published pool path remains reserved after local GC. A path conflict rejects that input; other valid inputs can still succeed.

Keep filename capitalization consistent when adding the same package again. Paths that differ only by case conflict. On a case-insensitive filesystem, source-package directory names must also be distinct; see [Workspace filesystem](/docs/reference/compatibility/#workspace-filesystem).

## --skip

`--skip` commits Desired membership and leaves `pool/`, `dists/`, and the Built Generation unchanged. New package files stay in private pending storage until a build needs them. The Repository is dirty when the resulting Desired state differs from Built state; reusing an unchanged member can leave it clean.

```console
sow add /srv/pkg/tree -R --skip -r pgsql -d trixie
add repository=pgsql operation=8405631664133415270 accepted=6 failed=0 memberships=+4/-0 revision=4 generation=3 dirty=true
```

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

`pending=4/2326` is four objects totalling 2326 bytes waiting in the private store. They never appear
in [`sow changes`](/docs/command/changes/) — only a successful build promotes them into the
deliverable tree.

Use `--skip` for bulk imports, then build once:

```bash
sow add /srv/build/ -R -r pgsql -d el9 --skip
sow status -r pgsql
sow build -r pgsql -j 12
sow check -r pgsql
```

## Processing order

SOW inspects the packages and signs new RPMs when configured. It applies `exclude` and `limit`, records the resulting membership, then builds unless `--skip` is set.

Input files remain unchanged. Signing uses private copies.

## RPM signing modes

Managed RPM package signing is configured in `sow.yml` under `signing.rpm.packages.mode`; there is no
command-line override.

| Mode | Behavior |
|---|---|
| `never` | Keep the input bytes exactly |
| `fill` | Sign when unsigned or when the signature is not trusted; keep bytes when a `trusted_keys` signature verifies. Default when a key is configured |
| `always` | Ensure the final package is validly signed by the configured key; re-sign a stage copy otherwise |

Without a configured key only `never` is available.

Repeated imports reuse identical package content. They can also reuse an RPM whose only difference is its signature, if the stored package satisfies the current signing policy. A changed payload or an incompatible stored signature causes a coordinate conflict. See [Signing Model](/docs/feature/signing/) for the matching rules.

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Inputs processed, including policy-excluded inputs; build completed or skipped |
| `1` | Runtime I/O, parser, renderer or signing failure |
| `2` | Usage error, Workspace not found, or ambiguous Repository/Dist selection |
| `3` | Partial batch — at least one item committed and at least one failed |
| `4` | Repository lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error, including a build that failed after `applied` |
| `6` | Every input failed, or selection/signing/state preconditions reject the operation |

## See also

- [sow rm](/docs/command/rm/) — the inverse operation
- [sow build](/docs/command/build/) — build after `--skip`
- [Membership Policy](/docs/feature/policy/) — `exclude` rules and `limit` semantics in full
- [Signing Model](/docs/feature/signing/) — the two trust chains and key references
- [Package References](/docs/reference/package-ref/) — the coordinate grammar printed on each item line
