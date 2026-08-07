---
title: "sow add"
linkTitle: "sow add"
description: "Add packages to Desired Membership, apply policy, and rebuild the affected indexes."
url: "/docs/reference/cli/add/"
weight: 600
icon: fa-solid fa-plus
---

`sow add` is the main write path. It parses the packages you point at, derives their format and
architecture from the package headers, applies the Dist's membership policy, and — unless you pass
`--skip` — rebuilds every affected index before it returns. When the command exits `0`, clients can
already see the new packages.

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
| `--json` | Emit the versioned JSON envelope | false |

## Inputs and targets

`PATH` can be a file or a directory. A directory is scanned top level only unless you pass `-R`.

You must end up with exactly one Repository and at least one target Dist — see the
[selection rules](/docs/reference/cli/). Mixed RPM/DEB batches are fine: each package is only
considered for target Dists of its own format. A package with no compatible target fails.

SOW never infers the target from a manifest, a directory name, or the host OS.

```console
sow add /srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=8677129233475584643 accepted=2 failed=0 memberships=+2/-0 revision=3 generation=3 dirty=false
item input="/srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm" status=accepted format=rpm coordinate="centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead dists=el9:accepted
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=accepted format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

The summary line reports the Operation ID, per-item counts, the membership delta, the new Desired
Revision, the Built Generation and whether the Repository is left dirty. Then one `item` line per
input, in stable order.

## Item statuses

Each `item` line carries an overall `status` plus a per-Dist verdict in `dists=`.

| Status | Meaning |
|---|---|
| `accepted` | New Package Object created and at least one Membership added |
| `reused` | The content already exists in this Repository; only Membership references may change |
| `excluded` | Policy removed it from every target Dist — see the `dists=` field for `excluded` vs `limited` |
| `failed` | The package was rejected; the `error=` field says why |

`reused` is what idempotence looks like. Adding the same file twice does not create a second object
and does not bump the Generation:

```console
sow add /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=656950149626836753 accepted=1 failed=0 memberships=+0/-0 revision=4 generation=4 dirty=false
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=reused format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

The same object added to a second Dist is also `reused` — the pool keeps one copy and gains a second
Membership.

## Architecture is read, never guessed

`add` reads format and native architecture from the package header, then checks the Workspace permit
list. An architecture outside the list fails the package and tells you exactly what to edit:

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
item input="/srv/pkg/centos-release-3.1-1.i386.rpm" status=failed error="managed: operation rejected: unknown rpm package architecture \"i386\"; supported rpm package architectures are [x86_64, aarch64, noarch] (canonical families [x86_64, aarch64, neutral]); use a supported package or update only supported architecture families in sow.yml"
```

It does not create a directory and does not modify `sow.yml`.

RPM `noarch` and DEB `all` are architecture-neutral. They create one Package Object and one
Membership, and render into every effective architecture view of the target Dist. They do not
spread to Dists you did not select with `-d`.

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

Limit groups by `(binary name, native architecture)`, so `18.3-1:amd64` and `18.3-1:arm64` both
survive a `limit: 1`. A package can be accepted by one Dist and skipped by another in the same run.

{{% alert title="Policy removals do not come back" color="warning" %}}
`exclude` and `limit` remove real Desired Memberships. Relaxing the policy later does not resurrect
them — leftover bytes in `pool/` are not a candidate set. Re-run `sow add`.
{{% /alert %}}

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

If *nothing* is accepted, the whole operation is rejected with exit `6` and the Repository is
unchanged:

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
operation rejected: managed: operation rejected: no input package was accepted
```

There is no rejected/quarantine directory.

## --skip

`--skip` stops after the Desired state is committed. The public `pool/` and `dists/` bytes do not
change, the Built Generation stays where it was, and the Repository becomes dirty. New package bytes
are durably held in a private pending store until the next build publishes them.

```console
sow add /srv/pkg/tree -R --skip -r pgsql -d trixie
add repository=pgsql operation=8405631664133415270 accepted=6 failed=0 memberships=+4/-0 revision=4 generation=3 dirty=true
```

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

`pending=4/2326` is four objects totalling 2326 bytes waiting in the private store. They never appear
in [`sow changes`](/docs/reference/cli/build/) — only a successful build promotes them into the
deliverable tree.

Use `--skip` for bulk imports, then converge once:

```bash
sow add /srv/build/ -R -r pgsql -d el9 --skip
sow status -r pgsql
sow build -r pgsql -j 12
sow check -r pgsql
```

## Processing order

For the record, one `add` executes in this order:

1. Take the Repository write lock and recover any unfinished Operation.
2. Commit a `planned` Operation in SQLite.
3. Parse inputs read-only; compute logical coordinates and input SHA-256 (plus, for RPM, the
   signature-neutral payload digest).
4. Check the architecture permit list and look up existing coordinates.
5. For genuinely new coordinates only, run optional RPM signing on a stage copy and compute the final
   SHA-256, then verify content and path uniqueness.
6. Merge target Memberships, then apply `exclude` and `limit` over the complete Dist set.
7. Commit the Desired state; new bytes go to the private pending content store.
8. Unless `--skip`, publish still-needed pending objects into `pool/` and render indexes — each Dist
   is built at most once per command.

Input files are never modified, moved or deleted, in any mode.

## RPM signing modes

Managed RPM package signing is configured in `sow.yml` under `signing.rpm.packages.mode`; there is no
command-line override.

| Mode | Behavior |
|---|---|
| `never` | Keep the input bytes exactly |
| `fill` | Sign when unsigned or when the signature is not trusted; keep bytes when a `trusted_keys` signature verifies. Default when a key is configured |
| `always` | Ensure the final package is validly signed by the configured key; re-sign a stage copy otherwise |

Without a configured key only `never` is available.

Because a signature embeds non-deterministic fields, SOW cannot re-sign and then compare final
hashes. Retry idempotence works on the coordinate instead: identical input bytes are reused
directly; an identical RPM signature-neutral digest is reused when the existing object satisfies the
current policy. A different payload digest, or an existing object that no longer satisfies the
policy, is a hard conflict — `add` will not silently re-sign a coordinate in place.

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Every input accepted or reused; indexes rebuilt (or skipped with `--skip`) |
| `1` | Runtime I/O, parser, renderer or signing failure |
| `2` | Usage error, Workspace not found, or ambiguous Repository/Dist selection |
| `3` | Partial batch — at least one item committed and at least one failed |
| `4` | Repository lock held and `--no-wait` given or `--timeout` expired |
| `5` | Integrity or recovery error, including a build that failed after `applied` |
| `6` | Nothing accepted — unsupported architecture, no compatible target Dist, or a coordinate conflict |

## See also

- [sow rm](/docs/reference/cli/rm/) — the inverse operation
- [sow build](/docs/reference/cli/build/) — converging after `--skip`
- [Membership Policy](/docs/feature/policy/) — `exclude` rules and `limit` semantics in full
- [Signing Model](/docs/feature/signing/) — the two trust chains and key references
- [Package References](/docs/reference/package-ref/) — the coordinate grammar printed on each item line
