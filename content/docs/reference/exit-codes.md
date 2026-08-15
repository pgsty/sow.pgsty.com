---
title: "Exit Codes"
linkTitle: "Exit Codes"
description: "The seven exit codes, what each means, and a command that reproduces it."
url: "/docs/reference/exit-codes/"
weight: 500
icon: fa-solid fa-triangle-exclamation
---

Every `sow` command exits with one of seven codes. They are stable, they are the same for
every command, and they are meant to be branched on in scripts — the distinction between
"this failed" and "this was correctly refused" is the whole point of having more than one
nonzero code.

| Code | Meaning |
|---|---|
| `0` | Complete success, or an idempotent no-op |
| `1` | Runtime I/O, parser, renderer, or unknown internal error |
| `2` | Usage, workspace discovery, or configuration error |
| `3` | Partial success: at least one item committed, at least one failed |
| `4` | Write lock unavailable — held and `--no-wait`, or the timeout expired |
| `5` | Integrity or recovery error, or `check` judged the result not deliverable |
| `6` | Expected rejection: conflict, protected, no match, incompatible architecture |

Human-readable results go to stdout; warnings and diagnostics go to stderr. Each code has
a stable message prefix on stderr, and a matching `class` in
[JSON output](/docs/reference/json/):

| Code | stderr prefix | JSON `class` |
|---|---|---|
| `1` | varies by subsystem | `runtime` |
| `2` | `usage error:` / `workspace discovery error:` / `configuration error:` | `usage` |
| `3` | `... batch partially succeeded` | `partial` |
| `4` | `lock unavailable:` | `lock` |
| `5` | `integrity or recovery error:` | `integrity` |
| `6` | `operation rejected:` | `rejected` |

`sow create` is the exception to the prefix column: being outside the managed layer, it
prints its raw domain error on stderr (`plain: scan …`, `plain: marker gate …`) without the
`operation rejected:` prefix. The prefix is still present in its JSON `errors[].message`.

---

## 0 — Success or no-op

The command did what you asked, or found there was nothing to do. Both are success:
re-running `sow create` over an unchanged directory, or `sow build` on a clean repository,
exits `0` and says so.

```bash
sow create /srv/offline --json
```

```console
{"schema":"sow.cli/v1","command":"create","ok":true,...,"result":{"dir":"/srv/offline","rpm":4,"deb":3,"kept":[...],"removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

The `"noop":true` is how you tell a no-op from real work; the exit code does not
distinguish them.

`sow status` is a deliberate special case. As long as the state database is readable it
exits `0` in every repository state — `clean`, `dirty`, `recovering`, and `error` alike —
so a script can read the structured state instead of decoding an exit code. Use
`sow check` when you want a gate.

## 1 — Runtime error

Something went wrong at the I/O, parsing, or rendering layer: a directory that cannot be
written, a disk that filled up, a package that cannot be read. These are environment
problems, not usage problems.

```bash
chmod 500 /srv/readonly
sow create /srv/readonly
```

```console
plain: create stage /srv/readonly: mkdir /srv/readonly/.sow-plain-stage-1457115008: permission denied
```

The staging directory is created up front precisely so this fails before anything is
published. A repository that already had valid indexes still has them.

## 2 — Usage, discovery, or configuration

You asked for something the CLI cannot act on: an unknown flag, an ambiguous target, no
workspace, or a `sow.yml` that does not parse. Nothing was attempted.

An unknown option:

```bash
sow status --nope
```

```console
usage error: unknown option "--nope"
```

Mutually exclusive options:

```bash
sow build -N -T 5s
```

```console
usage error: --no-wait and non-zero --timeout are mutually exclusive
```

An ambiguous target — the repository has two distributions and the command needs one:

```bash
sow ls
```

```console
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

No workspace anywhere above the current directory — the message names where it searched and
how to fix it:

```console
workspace discovery error: managed: workspace discovery or configuration error: workspace not found (searched cwd="/home/vonng"); run sow init or set --workdir/SOW_DIR
```

A start directory that is not a real directory — a symlink, for instance, which is what
`/tmp` is on macOS — is refused before the search even begins:

```console
workspace discovery error: managed: workspace discovery or configuration error: discover workspace from cwd "/tmp": start is not a directory
```

A malformed configuration file — note that the offending line is named:

```bash
sow config check
```

```console
configuration error: load config "/srv/repo/sow.yml": parse sow.yml: yaml: unmarshal errors:
  line 3: field repositories not found in type config.Config
```

Every syntax and schema error in [`sow.yml`](/docs/reference/config/) lands here.

## 3 — Partial success

A batch where some items were committed and some failed. This code exists so you never
have to guess whether a failed `sow add` left the repository untouched: with `3`, the
valid packages *are* in, and the failed ones are named.

```bash
sow add ./incoming/ -d el9
```

```console
add repository=pigsty operation=9162553676349401125 accepted=1 failed=1 memberships=+1/-0 revision=6 generation=6 dirty=false
item input="/incoming/broken-1.0-1.x86_64.rpm" status=failed error="invalid RPM package: parse RPM reader: unexpected EOF"
item input="/incoming/pgbouncer_fdw_18-1.4.0-1PGDG.rhel9.8.x86_64.rpm" status=reused format=rpm coordinate="pgbouncer_fdw_18-0:1.4.0-1PGDG.rhel9.8.x86_64" sha256:45171966... dists=el9:accepted
managed: batch partially succeeded
```

The failed input file is left exactly where it was. With `--json`, the committed items are
still listed in full — a nonzero exit never truncates the result:

```console
{..., "ok":false, "result":{"accepted":1,"failed":1,"items":[...]}, "errors":[{"code":3,"class":"partial","message":"managed: batch partially succeeded"}]}
```

`sow init` uses the same code when it commits some declared repositories or distributions
and then fails on a later one.

## 4 — Lock unavailable

Another process holds the write lock. SOW is single-writer by design, so this is a normal,
expected outcome — retry, or wait longer.

With `--no-wait`, the failure is immediate:

```bash
sow build -N
```

```console
lock unavailable: managed: lock unavailable
```

With a timeout, it fails after exactly that long:

```bash
time sow build -T 2s
```

```console
lock unavailable: managed: lock unavailable

real	0m2.016s
```

`-T 0` — the default — waits indefinitely. Read-only commands never take a write lock and
never return `4`; `sow status` even reports the contention as a field:

```console
repository=pigsty status=clean ready_to_copy=false revision=7 generation=7 dirty_dists= pending=0/0 locked=true
```

## 5 — Integrity, recovery, or not deliverable

Two different situations share this code, and both mean "do not ship this tree yet".

The common one is `sow check` on a repository whose desired state is ahead of what was
built — after `sow add --skip`, or after a policy or signing change. Every layer passes;
the repository is simply not converged:

```bash
sow rm 'rpm:pev2-0:1.23.0-1.noarch' -d el9 --skip
sow check
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=7 generation=6
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=69
package-bytes	ok=true	checked=7
desired-membership	ok=true	checked=6
index	ok=true	checked=2
signature	ok=true	checked=11
generation-manifest	ok=true	checked=6
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

The fix is `sow build`. This is the code a deploy script should gate on — it is the
difference between "the tree on disk is complete and current" and "the tree on disk is
complete but stale".

The rarer situation is genuine integrity failure: a state database, journal, and file tree
that contradict each other in a way SOW cannot safely resolve on its own. It refuses to
overwrite anything, and you restore from backup rather than forcing a repair. There is no
`--force` here on purpose.

## 6 — Expected rejection

The command was well-formed, the environment was fine, and SOW decided the answer is no.
These are policy and safety decisions, not failures.

A protected repository:

```bash
sow repo rm pigsty -f
```

```console
operation rejected: managed: operation rejected: repository "pigsty" is protected
```

A reference that matches nothing:

```bash
sow rm nosuchpkg -d el9
```

```console
operation rejected: managed: operation rejected: package reference not found: package reference "nosuchpkg" matches no Desired Membership
```

An ambiguous bare name, with the candidates listed so you can pick one:

```bash
sow show libpq5 -d trixie
```

```console
operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1.pgdg12+1:amd64 sha256:310611d0..., deb:libpq5=18.3-1.pgdg12+1:amd64 sha256:4b526223..., deb:libpq5=18.3-1.pgdg12+1:arm64 sha256:cadeb929...
```

An architecture the workspace does not allow. Note that the per-item message names the
detected value and tells you where to change it:

```bash
sow add ./centos-release-6-0.el6.centos.5.i686.rpm -d el9 --json
```

```console
"items":[{"input":".../centos-release-6-0.el6.centos.5.i686.rpm","status":"failed",
 "error":"managed: operation rejected: unknown rpm package architecture \"i686\"; supported rpm package architectures are [x86_64, aarch64, noarch] (canonical families [x86_64, aarch64, neutral]); use a supported package or update only supported architecture families in sow.yml"}]
```

A directory with nothing to index:

```bash
sow create /srv/empty
```

```console
plain: scan /srv/empty: no supported top-level regular RPM or DEB packages
```

A `--pigsty` completion marker guarding an existing build:

```bash
sow create /www/pigsty
```

```console
plain: marker gate /www/pigsty/repo_complete: repo_complete exists; use --pigsty or remove it explicitly before rebuilding
```

A signing key reference that parses but does not resolve — syntax errors are `2`,
resolution failures are `6`:

```console
operation rejected: ... deb metadata key: key reference does not resolve to a bounded regular file
operation rejected: ... deb metadata key: environment key reference SOW_METADATA_KEY is unset
```

## Using them in scripts

The codes are designed so a deploy pipeline can branch without parsing text:

```bash
#!/usr/bin/env bash
set -uo pipefail

sow add /incoming/*.rpm -r pigsty -d el9
case $? in
  0) ;;                                        # everything landed
  3) echo "some packages rejected, continuing with what landed" >&2 ;;
  4) echo "another writer holds the lock, retry later" >&2; exit 75 ;;
  *) echo "add failed" >&2; exit 1 ;;
esac

# Gate publication on a complete, current tree.
if ! sow check -r pigsty; then
  echo "repository not ready to publish" >&2
  exit 1
fi

sow publish mirror
```

Here `mirror` is a configured publication target for `pigsty`.

Two habits worth keeping: treat `4` as retryable rather than fatal, and never treat `6` as
a crash — it usually means your input, not SOW, needs to change.

## See also

- [JSON Output](/docs/reference/json/) — the `errors` array and its `class` field
- [`sow check`](/docs/command/check/) — the ordered verification layers behind code `5`
- [Transactions & Recovery](/docs/feature/transactions/) — what `recovering` and `error` mean
