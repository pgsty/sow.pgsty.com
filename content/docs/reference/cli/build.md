---
title: "sow build / status / check / changes"
linkTitle: "build / status / check / changes"
description: "Converge Desired state into a Built Generation, and the three commands that tell you where you stand."
url: "/docs/reference/cli/build/"
weight: 900
icon: fa-solid fa-hammer
---

One concept, one command. `status` is the cheap read, `check` is the full verification, `build` is
the only thing that changes the public tree, and `changes` is the physical file diff between
Generations. This page covers all four, because you almost always use them together.

## Synopsis

```text
sow status [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow build [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
sow check [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow changes [BASE_GENERATION] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

## The state model

Every Repository tracks two things: the **Desired Revision** in SQLite, and the **Built Generation**
that the `dists/` tree on disk corresponds to.

| State | Meaning | What clients see |
|---|---|---|
| `clean` | Desired matches Built | Every view current and complete |
| `dirty` | Desired is ahead — from `--skip` or a config change | The old Built view, still complete |
| `recovering` | An unfinished Operation exists; the next write command must recover first | The last completed protocol pointer |
| `error` | Automatic recovery cannot safely decide; needs a human | The last completed view, never overwritten |

Dirty never means a half-written index. Clients always follow a protocol pointer to a complete old
or complete new view.

## sow status

Cheap, read-only, no hashing. Reports Repository state, Desired Revision, Built Generation, dirty
Dists, pending payload count and bytes, the most recent Operation, and lock state.

```console
sow status
repository=pigsty status=clean ready_to_copy=true revision=11 generation=12 dirty_dists= pending=0/0 locked=false
```

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

`ready_to_copy` is the single field a sync script should read: it tells you whether `pool/ + dists/`
can be rsynced as-is right now.

**`status` returns `0` in every readable state** — clean, dirty, recovering and error alike — so
scripts can consume structured state instead of parsing an error. Only an unreadable or unparsable
state database produces a non-zero (integrity) exit. Use `sow check` when you want a hard gate.

```console
sow status -r demo --json
{"schema":"sow.cli/v1","command":"status","ok":true,"repository":"demo","operation":null,"result":{"repository":"demo","status":"dirty","ready_to_copy":false,"desired_revision":5,"built_generation":4,"dirty_dists":["el9"],"dirty_reasons":["dist el9 Desired and Built membership sets differ","one or more dists differ from their built projections"],"pending":{"count":1,"bytes":19776},"recent_operation":{"id":"3329269325810066022","kind":"add","state":"done_dirty","created_at":"2026-08-04T04:10:22.481991Z","updated_at":"2026-08-04T04:10:22.553516Z"},"repository_locked":false},"errors":[]}
```

`status` never recovers anything, and it never reports a stale-but-self-consistent Generation as
corruption.

## sow build

Takes the Repository write lock, recovers any unfinished Operation, then converges the current
Desired state into a new Built Generation.

```console
sow build -r pgsql -d el9
{"operation":"4262183287563704350","repository":"pgsql","dists":["el9"],"desired_revision":6,"built_generation":6,"noop":false,"dirty":false}
```

| Flag | Description | Default |
|---|---|---|
| `-j, --jobs N` | Parallel workers | logical CPU count |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Select a distribution; repeatable | all Dists |
| `-T, --timeout DUR` | Maximum lock wait; `0` waits indefinitely | `0` |
| `-N, --no-wait` | Fail immediately when the lock is held | false |
| `--json` | Emit the versioned JSON envelope | false |

Without `-d`, `build` converges every affected Dist of the Repository. With `-d`, only the selected
ones converge and the rest stay dirty.

Like `rm` and `show`, `build` prints structured JSON on stdout even without `--json`.

### No-op builds

If neither inputs nor renderer configuration changed, `build` does nothing and does not increment the
Generation:

```console
sow build
{"operation":"6295064788473690577","repository":"pigsty","dists":["el9","trixie"],"desired_revision":5,"built_generation":5,"noop":true,"dirty":false}
```

### Policy convergence is one-way

`build` re-executes the current policy, so editing `limit` or `exclude` in `sow.yml` and running
`build` is the supported way to apply it. Tightening a policy removes members. Loosening one does
*not* reconstruct historical members from leftover pool bytes — re-run `sow add`.

### Commit ordering

All metadata is staged on the same filesystem, verified and signed, then switched in. Protocol
pointers — RPM `repomd.xml`, APT `Release`/`InRelease` — are replaced last, and checksum-named
metadata plus APT by-hash guarantee that old and new clients never fetch a dangling reference.

One build Operation may cover several Dists. SOW does not promise that concurrent readers see all
Dists flip at the same instant; it promises that each protocol view is always self-consistent, and
that when the command returns every target belongs to the same Built Generation.

### Recovery

`build` is the one explicit forward-recovery entry point. It first tries to complete or roll back any
decidable non-terminal Operation. The `error` state is reserved for cases where journal, database and
file evidence contradict each other and the tool cannot safely choose — there `build` refuses to
overwrite, and you restore from backup before running `check`/`build` again. There is no
`repair --force` that could guess wrong.

### Metadata signing

Managed metadata signing comes only from `sow.yml`; there is no command-line override. An RPM
architecture view always gets `repodata/repomd.xml`, plus an ASCII-armored `repodata/repomd.xml.asc`
when `signing.rpm.metadata.key` is set. A DEB Dist always gets `Release`, plus a clearsigned
`InRelease` and a detached `Release.gpg` when `signing.deb.metadata.key` is set. Changing a key
reference or fingerprint makes the affected Dists dirty; the next `build` re-signs and produces a new
Generation.

## sow check

Full, read-only verification of the selected Repository and Dists, reported in eight layers.

```console
sow check
repository=pigsty status=clean ready_to_copy=true revision=5 generation=5
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=67
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=8
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=5
```

| Layer | What it verifies | `checked` counts |
|---|---|---|
| `config` | `sow.yml` parses and validates for this Repository | configuration objects |
| `state` | SQLite `quick_check`, foreign keys, and journal/recovery evidence | always 1 |
| `public-modes` | File and directory permissions across the served tree | inspected paths |
| `package-bytes` | SHA-256 of every pool and pending payload | package objects |
| `desired-membership` | Membership rows resolve to real objects under current policy | memberships |
| `index` | Rendered indexes match the membership they claim | Dists |
| `signature` | Every declared signature verifies | signatures |
| `generation-manifest` | The Built Generation manifest matches the files on disk | the Generation number |

| Flag | Description | Default |
|---|---|---|
| `-j, --jobs N` | Parallel workers | logical CPU count |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Select a distribution; repeatable | all Dists |
| `--json` | Emit the versioned JSON envelope | false |

`check` never repairs, never builds and never recovers an Operation.

### Dirty is a check failure

When the Repository is dirty, `check` verifies both the Desired state and the old Built Generation —
and then rules the tree not ready to copy, exiting `5`:

```console
sow check
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=67
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=7
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=5
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

Every layer passed. Exit `5` here means "the old tree is intact but it is not what you asked for" —
run `build`. That is exactly the gate you want in a release pipeline.

## sow changes

Prints the physical file changes between two Built Generations, as a delivery plan.

```console
sow changes
base=4 generation=5 dirty=false
add	payload	dists/el9/x86_64/pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm	19776	ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
add	payload	pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm	19776	ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
add	metadata	dists/el9/x86_64/repodata/5bc463cb00bec4d6185ea593a6fa8f180f24d3251b498f5bbeb14875581c33cc-primary.xml.gz	1460	5bc463cb00bec4d6185ea593a6fa8f180f24d3251b498f5bbeb14875581c33cc
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1514	05d3d5bf0f9236626b22a8ae9c92853277fff506f5773fbc33316ea12683cf0b
delete	delete	dists/el9/x86_64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz	0
```

Columns are `op`, `phase`, repository-relative path, size and SHA-256. `op` is `add`/`update`/`delete`;
`phase` is `payload`/`metadata`/`pointer`/`delete`. **Apply them in phase order** — payload first,
pointer last, deletions after everything else — and no client ever sees a dangling reference.

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `--json` | Emit the versioned JSON envelope | false |

### BASE_GENERATION

Without an argument, `changes` diffs the latest Built Generation against its predecessor.

`changes 0` produces the complete delivery manifest for the current Built Generation — every file
under `pool/` and `dists/`, excluding `sow.yml` and `.sow/`:

```console
sow changes 0
base=0 generation=2 dirty=false
add	payload	dists/el9/aarch64/pool/e/epel-release/epel-release-7-5.noarch.rpm	14524	d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab
add	payload	dists/el9/x86_64/pool/e/epel-release/epel-release-7-5.noarch.rpm	14524	d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab
add	payload	pool/e/epel-release/epel-release-7-5.noarch.rpm	14524	d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab
add	metadata	dists/el9/aarch64/repodata/fb3777fe0da404b2ac78b26566e1eec95a4fc90f04b322e52925fc9baebb2764-primary.xml.gz	797	fb3777fe0da404b2ac78b26566e1eec95a4fc90f04b322e52925fc9baebb2764
add	pointer	dists/el9/x86_64/repodata/repomd.xml	1511	16d334bc2b1c20c27aac9f3a353b97018a994e55ef45acc90fa50dcf5b8268a4
```

Out-of-range bases are rejected:

```console
sow changes 99
operation rejected: managed: operation rejected: base generation 99 is outside 0..2
```

A Repository that has never built anything prints an empty plan:

```console
sow changes -r empty
base=0 generation=0 dirty=false
```

### Repository scope only

`changes` is a Repository-level Generation output and rejects `-d`. Filter by repository-relative
path if you want one Dist:

```console
sow changes -d el9
usage error: --dist is not allowed for changes
```

### Dirty and recovering

A dirty Desired state does not enter `changes`. The output flags `dirty=true` and still ends at the
current Built Generation — private pending payloads are invisible here, because they are not part of
the deliverable tree yet:

```console
sow changes -r demo
base=3 generation=4 dirty=true
add	metadata	dists/el9/aarch64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz	140	0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f
```

When the Repository is `recovering` or `error`, `changes` refuses to emit a sync plan at all: pending
file actions must not be mistaken for a Generation.

## Examples

The standard bulk-import cycle:

```bash
sow add /srv/build/ -R -r pgsql -d el9 --skip
sow status -r pgsql
sow build -r pgsql -j 12
sow check -r pgsql
```

Gate a release on a fully verified tree:

```bash
sow check -r pgsql || { echo "not deliverable"; exit 1; }
rsync -a --delete /srv/repo/pgsql/ mirror:/srv/www/pgsql/
```

Hand an incremental plan to an external sync tool:

```bash
sow changes 41 -r pgsql --json > changes-41-current.json
```

Wait at most 30 seconds for another writer, then give up:

```bash
sow build -r pgsql -T 30s
```

## Exit codes

| Command | Code | Trigger |
|---|---|---|
| `status` | `0` | State readable — in `clean`, `dirty`, `recovering` and `error` alike |
| `status` | `2` | Workspace not found or ambiguous selection |
| `status` | `5` | State database unreadable or unparsable |
| `build` | `0` | Converged, or nothing to do |
| `build` | `1` | Renderer, signing or I/O failure |
| `build` | `2` | Usage error or ambiguous selection |
| `build` | `4` | Lock unavailable |
| `build` | `5` | Recovery could not safely complete, or the Repository is in `error` |
| `build` | `6` | Configuration rejects the current state, for example an architecture still in use was removed |
| `check` | `0` | All layers pass and the tree is ready to copy |
| `check` | `1` | I/O failure while verifying |
| `check` | `2` | Usage error or ambiguous selection |
| `check` | `5` | A layer failed, or the Repository is dirty and therefore not deliverable |
| `changes` | `0` | Plan printed, including an empty plan |
| `changes` | `2` | `-d` given, ambiguous selection, or Workspace not found |
| `changes` | `5` | Repository is `recovering` or `error` |
| `changes` | `6` | `BASE_GENERATION` outside the valid range |

## See also

- [Transactions & Recovery](/docs/feature/transactions/) — the journal, lock model and crash matrix
- [Observability & Audit](/docs/feature/audit/) — how these four fit with `sow log`
- [sow add](/docs/reference/cli/add/) and [sow rm](/docs/reference/cli/rm/) — where dirty comes from
- [Serve Repositories](/docs/tutorial/serving/) — using `ready_to_copy` and `changes` for delivery
- [Exit Codes](/docs/reference/exit-codes/) — why `check` on a dirty Repository exits `5`
