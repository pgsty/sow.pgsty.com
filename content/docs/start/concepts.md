---
title: "Core Concepts"
linkTitle: "Core Concepts"
description: "The model behind SOW: two modes, four layers, and the split between what you asked for and what is published."
url: "/docs/start/concepts/"
weight: 400
icon: fa-solid fa-diagram-project
---

Once you have run [the quick start](/docs/start/quickstart/) and
[built a workspace](/docs/start/workspace/), a handful of ideas explain everything else
SOW does. This page covers them: the two modes and how to choose, the four layers of the
managed model, and the distinction between what you asked for and what is currently
published.

## Two ways to build a repository

SOW has two engines that never touch each other. Plain mode does not read `sow.yml`, does
not perform workspace discovery, and does not create a database. Managed mode never treats
a plain directory as a repository. Picking one is the first decision you make.

| | Plain mode | Managed mode |
|---|---|---|
| Entry point | `sow create DIR` | `sow init`, `repo`, `dist`, `add`, `rm`, `build` |
| Layout | packages and indexes in one flat directory | `pool/` for bytes, `dists/` for published views |
| Persistent state | none — the directory *is* the state | `sow.yml`, per-repository SQLite, operation journal |
| What you control | which files sit in the directory | which packages are members of which Dist |
| Formats | RPM and DEB in the same directory | one format per Dist |
| Architectures | one flat index, no split | one view per architecture |
| APT `by-hash` | no | yes |
| Signing | RPM package payloads, via `--sign-with` | RPM and DEB metadata, plus an RPM payload policy |
| Membership policy | none | `exclude` patterns and `limit` version caps |
| Audit trail | none | operation ledger with JSONL export |
| Cost of an update | rescan the whole directory | rebuild only the affected Dists |
| Closest classic tool | `createrepo_c` + `dpkg-scanpackages` | `reprepro` |

Choose plain mode when the directory already holds exactly what you want to publish: a
build output, a directory pulled down from an upstream mirror, an offline bundle burned to
a disk. It is one command
with nothing to maintain.

Choose managed mode when you need to decide *which* packages belong in the repository —
several distributions in one tree, per-architecture views, "keep only the two newest
versions", signed metadata, or a record of who changed what and when.

## The managed hierarchy

Four layers, each owning something specific:

```text
Workspace                     /srv/sow
│  sow.yml   what this workspace contains — the single source of truth
│  .sow/     locks, per-repository SQLite, operation journal (never served)
│
└── Repository                /srv/sow/pigsty
    │  owns one pool, one database, one lock
    │  no package sharing with sibling repositories
    │
    ├── pool/                 immutable package bytes, one copy per object
    │
    └── Dist                  /srv/sow/pigsty/dists/el9
        │  a named membership set in exactly one format (rpm or deb)
        │
        ├── Architecture View  dists/el9/x86_64/    x86_64 members + noarch
        └── Architecture View  dists/el9/aarch64/   aarch64 members + noarch
```

A **Workspace** is a discovery and configuration boundary, nothing more. It owns exactly
two things at its root: `sow.yml` and `.sow/`. Commands find it by searching upward from
the current directory.

A **Repository** is a directory directly under the workspace root, and it is the unit of
isolation. Its pool, database, lock, and recovery state are all its own. Two repositories
never deduplicate packages against each other, which is what makes removing one safe.

A **Dist** is a named set of packages in exactly one format. The name is a plain label —
`el9`, `trixie`, `staging` — with no built-in lifecycle or promotion machinery attached.
It is what your users see in a URL.

An **Architecture View** is a rendering of a Dist, not a separate membership set. Adding a
package to `el9` adds it once; build decides which views it appears in. RPM views use the
canonical family names `x86_64` and `aarch64`; DEB views use the ecosystem names
`binary-amd64` and `binary-arm64`. When you write `amd64` or `arm64` in configuration or on
the command line, SOW normalizes it to `x86_64` or `aarch64` at the parsing boundary and
reports the canonical name from then on.

`noarch` and `all` packages are a **neutral** projection, not a third architecture. A
`noarch` RPM has one object and one membership, and build projects it into every applicable
view — which is why `pev2` shows up under both `x86_64/` and `aarch64/`.

## One copy of the bytes

Package payloads live once, in the repository's `pool/`, grouped Debian-style by first
letter and source package. Architecture views reference those bytes with hardlinks rather
than copies, so a `noarch` package present in two views has a link count of three and still
occupies disk space once.

This is why a repository's `pool/` and `dists/` must sit on the same filesystem. If
hardlinks are unavailable or the target is on another device, SOW fails rather than
silently copying. A plain `cp -r` or `rsync` that does not preserve hardlinks still yields
a working repository — you just lose the deduplication.

Because views hold real files, package locations inside `repodata` are relative paths like
`pool/p/pev2/…` with no `..` escaping the view root. That detail is what lets
`dnf reposync` mirror a SOW repository correctly.

Objects are identified by the SHA-256 of their exact bytes. Their logical **coordinate** —
NEVRA for RPM, `name=version:arch` for DEB — comes from the RPM header or the Debian
control file, never from the filename. A renamed package is indexed as whatever it actually
is. Two packages claiming the same coordinate with different content are rejected, not
silently merged.

## Desired versus Built

This is the central idea of managed mode. Two states, tracked separately:

**Desired Membership** is what you asked for. `add` and `rm` maintain it, and it advances a
counter called `revision`. It is a logical set — package X belongs to Dist Y — with no files
involved.

**Built Generation** is what is currently published under `pool/` and `dists/`. `build`
produces it, and it advances a monotonic counter called `generation`.

```text
sow add / sow rm  ────▶   Desired Membership     revision 5
                                  │
                              sow build
                                  │
                                  ▼
                          Built Generation       generation 5
                                  │
                                  ▼
                          pool/ + dists/         ready to copy
```

When Desired is ahead of Built, the Dist is **dirty**. By default `add` and `rm` build
before returning, so you rarely see a dirty repository. Pass `--skip` when you want to
stage several changes and build once:

```bash
sow add pkg/asciinema-3.2.1-1.x86_64.rpm -r pigsty -d el9 --skip
```

```console
add repository=pigsty operation=4281492977639306333 accepted=1 failed=0 memberships=+1/-0 revision=5 generation=4 dirty=true
item input="pkg/asciinema-3.2.1-1.x86_64.rpm" status=accepted format=rpm coordinate="asciinema-0:3.2.1-1.x86_64" sha256:11f56fbd54f23ce1b8d8866c67a91e0819bac3fa22d2ace681b411ac0fe26703 dists=el9:accepted
```

Revision moved to 5, generation stayed at 4, and the published tree is byte-for-byte
unchanged — the new package sits in private pending storage where no client can see it:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4 dirty_dists=el9 pending=1/4429718 locked=false
```

`ready_to_copy=false` is the signal that matters. A dirty repository is not damaged — the
old Built Generation on disk is complete and perfectly serveable — it just does not reflect
your latest intent yet. `sow check` treats that as not deliverable and exits `5`:

```console
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

Converge when you are ready:

```bash
sow build -d el9
```

```console
{"operation":"1543183855804634265","repository":"pigsty","dists":["el9"],"desired_revision":5,"built_generation":5,"noop":false,"dirty":false}
```

```bash
sow status
```

```console
repository=pigsty status=clean ready_to_copy=true revision=5 generation=5 dirty_dists= pending=0/0 locked=false
```

A Dist also goes dirty when its *inputs* change, not only its members. Adding an
architecture, changing an `exclude` rule or a `limit`, or switching signing keys all change
what the renderer would produce, so SOW marks the Dist dirty and waits for an explicit
`build`. Nothing rebuilds behind your back.

## Generations and what changed

Every build that actually changes files produces a new generation. Generations are
monotonic, and SOW keeps the previous generation's metadata files on disk alongside the
current ones — a client that started downloading a moment ago can finish. `repomd.xml` and
`Release` only ever point at the current generation.

`sow changes` reports the physical difference between any base generation and the current
one, which is exactly the file list you would need to sync:

```bash
sow changes 4
```

```console
base=4 generation=5 dirty=false
add	payload	dists/el9/x86_64/pool/a/asciinema/asciinema-3.2.1-1.x86_64.rpm	4429718	11f56fbd54f23ce1b8d8866c67a91e0819bac3fa22d2ace681b411ac0fe26703
add	payload	pool/a/asciinema/asciinema-3.2.1-1.x86_64.rpm	4429718	11f56fbd54f23ce1b8d8866c67a91e0819bac3fa22d2ace681b411ac0fe26703
add	metadata	dists/el9/x86_64/repodata/26435ad6857a58369efe0b5ddfb955c1023c0af7d2a2cde9501b877c41728d58-filelists.xml.gz	795	26435ad6857a58369efe0b5ddfb955c1023c0af7d2a2cde9501b877c41728d58
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1514	ce90e820933f3daab456904a4531b54466ef28c50fbc87b1a6863d8bb42c3ff6
delete	delete	dists/el9/x86_64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz	0	
```

*(excerpt — the full listing covers both architecture views)*

The four phases in the second column are an ordering, and it is the same order SOW itself
uses when writing: `payload` first, then `metadata`, then `pointer`, then `delete`. Publish
the bytes before anything references them, swap the entry point once everything it points
at exists, and only then remove what is no longer referenced. A mirror that applies the
plan in that order is never internally inconsistent, even halfway through.

`sow changes 0` gives the complete current tree as one big add set — useful for seeding a
fresh mirror.

## Fail-closed

SOW refuses rather than guesses. If it cannot tell which repository you meant, it says so
instead of picking one. If a package is truncated or its header contradicts its content,
the whole batch is rejected and the repository stays clean. If recorded state and the files
on disk disagree, that is an integrity error, not something to repair silently.

Every write operation records its intent in a durable journal before touching anything
public, so an interrupted command leaves a recoverable state rather than a half-written
tree. The next write command finishes or unwinds the interrupted operation before doing its
own work. A published tree is never torn.

Exit codes carry that distinction, so scripts can branch on it:

| Code | Meaning |
|---|---|
| `0` | Success, or nothing to do |
| `1` | Runtime I/O, parser, or renderer error |
| `2` | Usage, discovery, or configuration error |
| `3` | Partial success — some valid work was committed |
| `4` | Lock unavailable |
| `5` | Integrity or recovery error, or not deliverable (includes dirty) |
| `6` | Expected rejection — conflict, protected, no match, incompatible architecture |

Full details in [Exit Codes](/docs/reference/exit-codes/).

## Where to go deeper

- [Plain Flat Repositories](/docs/feature/plain/) — what `sow create` guarantees, and how determinism is achieved.
- [Managed Workspaces](/docs/feature/managed/) — the three-layer model, fixed layout, and discovery rules.
- [Pool & Architecture Views](/docs/feature/views/) — hardlink projection and reposync compatibility.
- [Membership Policy](/docs/feature/policy/) — `exclude` and `limit` semantics in detail.
- [Signing Model](/docs/feature/signing/) — the two independent trust chains.
- [Transactions & Recovery](/docs/feature/transactions/) — journals, locks, and crash behavior.
- [Observability & Audit](/docs/feature/audit/) — `status`, `check`, `changes`, and the operation log.
