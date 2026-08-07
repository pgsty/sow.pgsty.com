---
title: "Managed Workspaces"
linkTitle: "Managed Workspaces"
description: "The Workspace to Repository to Dist model, the fixed on-disk layout, how sow.yml drives everything, and the discovery and selection rules."
url: "/docs/feature/managed/"
weight: 300
icon: fa-solid fa-sitemap
---

Managed mode is what you use when the same repository will be updated for months: packages arrive in batches, policy decides what stays, and you need to prove afterwards what changed and when. This page explains the three-tier model, the layout it produces, and how commands figure out which repository and which Dist you meant.

## The three tiers

```text
Workspace                          discovery and configuration boundary
└── Repository                     ownership boundary: pool, dists, SQLite, lock, generations
    └── Dist                       a named membership set in exactly one format
        └── Architecture View      a rendered projection — not a membership
```

Each tier has one job, and the boundaries are strict:

**Workspace** owns exactly two things: the root `sow.yml` and the `.sow/` state directory. Nothing else at the workspace root belongs to SOW. It is the unit of discovery — commands find a workspace by walking up from a starting directory — and it is where the architecture permit list lives.

**Repository** is fixed at `<workspace>/<name>`. You cannot point it somewhere else; there is no `path` option. A Repository owns its `pool/`, its `dists/`, its own SQLite database, its own lock, and its own recovery state. It is the boundary for transactions, generations, and changesets. Two Repositories never deduplicate against each other — the same package added to both is stored twice, on purpose, so that removing one Repository can never damage the other.

**Dist** is an ordinary named set of memberships in exactly one format, `rpm` or `deb`. The name is an opaque string to SOW. `el9`, `trixie`, `el9-beta`, `customer-acme` — none of these create a state machine, a promotion workflow, or a snapshot. If you want a beta channel, make a Dist called `el9-beta`; the meaning lives in your head and your `.repo` files, not in SOW.

**Architecture View** is what `build` renders. It creates no second membership. A `noarch` RPM has exactly one package object and exactly one membership, and gets projected into every applicable view. See [Pool & Architecture Views](/docs/feature/views/).

One Repository can hold an RPM Dist and a DEB Dist at the same time, sharing one `pool/`.

## The layout

Managed paths are never assembled from user input. They are derived from the resolved real workspace root, a validated name, and a fixed relative fragment — which is why symlink substitution and path escape have no surface to attack.

```text
<workspace>/
├── sow.yml                       # the only configuration file
├── .sow/                         # private state; never serve this
│   ├── workspace.lock
│   ├── workspace-ops/            # workspace lifecycle journal
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db                 # one SQLite per repository
│   └── <repo>/
│       ├── stage/                # staging on the same filesystem
│       ├── recovery/             # atomic-move target for deletions
│       └── pending/              # durable payload for --skip
└── <repo>/                       # the servable tree
    ├── pool/                     # immutable package bytes
    └── dists/
        └── <dist>/               # architecture views rendered here
```

A real workspace after two `dist new` and two `add` commands:

```console
$ find .sow | sort
.sow
.sow/pigsty
.sow/pigsty.db
.sow/pigsty.db-shm
.sow/pigsty.db-wal
.sow/pigsty/pending
.sow/pigsty/recovery
.sow/pigsty/stage
.sow/repo-locks
.sow/repo-locks/pigsty.lock
.sow/workspace-ops
.sow/workspace.lock
```

Everything under `<repo>/` is the delivery tree — that is what you rsync or serve. Everything under `.sow/` is private and must not be exposed; the [serving guide](/docs/tutorial/serving/) shows how to deny it in nginx.

Names must match `[a-z0-9][a-z0-9._-]*`, and `.`, `..`, `.sow`, `pool`, `dists` and workspace-reserved names are rejected outright.

## `sow.yml` drives everything

There is one configuration file, parsed with a strict decoder. Unknown fields do not get ignored — they fail. So do duplicate normalized architectures, illegal names or formats, a Dist architecture that is not a subset of the workspace permit list, an invalid glob or category, and an incomplete signing block.

```yaml
schema: sow/v2
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
```

`config show --all` expands every default and normalized alias so you can see what SOW actually decided:

```console
$ sow config show --all
schema: sow/v2
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    protected: false
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
      trixie:
        format: deb
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

Architecture aliases are normalized once, at the parse boundary: `amd64 → x86_64`, `arm64 → aarch64`. Output is always the canonical family. The ecosystem names come back only in the rendered DEB view directory names (`binary-amd64`, `binary-arm64`).

`config check` is not a YAML linter. It opens each initialized Repository's SQLite and compares the candidate configuration against the live Dists, architectures, memberships, built state, and signing availability. Removing an architecture family that memberships or built state still reference is an expected rejection (exit `6`); corrupt database or protocol evidence is an integrity error (exit `5`). Every write command runs the same preflight before it journals anything, so `config check` tells you in advance whether the next `add` would be refused.

```console
$ sow config check
configuration valid: /data/ws repositories=1 dists=2
```

The full schema is in the [`sow.yml` reference](/docs/reference/config/).

## Discovery: which workspace?

Managed commands look for the nearest ancestor `sow.yml`, in this order:

1. If `-C/--workdir DIR` is given, search upward from `DIR` only. If nothing is found there, the command fails — it does not fall back to the current directory.
2. Otherwise search upward from the current directory.
3. If that finds nothing, search upward from `$SOW_DIR`.
4. Still nothing: fail, with a hint about `sow init`, `--workdir`, and `SOW_DIR`.

The first `sow.yml` found wins; SOW does not keep climbing past it looking for a better one.

`--workdir` is not `chdir`. It changes only where discovery starts. A relative `PATH` argument in `sow add` is still resolved against your real current directory, which is what you want when you run `sow add ./build/*.rpm -C /srv/ws`.

`sow create` does not participate in any of this.

## Selection: which repository, which Dist?

Repository selection, in order:

1. Explicit `-r/--repo NAME`.
2. The command's starting directory is inside `<workspace>/<repo>/`.
3. The workspace has exactly one Repository.
4. Otherwise fail and list the candidates.

Dist selection, in order:

1. One or more explicit `-d/--dist NAME` (repeatable).
2. The starting directory is inside `<workspace>/<repo>/dists/<dist>/`.
3. The selected Repository has exactly one Dist.
4. Otherwise fail and list the candidates.

The important asymmetry: `build`, `check`, and `status` default to **all** Dists of the selected Repository when `-d` is absent, because operating on everything is the safe reading of "no filter". `add`, `rm`, and `ls` require a definite Dist set, because guessing where a package should land is not safe:

```console
$ sow ls
workspace discovery error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

That is exit `2`. Every inference happens only after path type and symlink validation.

## `init` converges, it does not reset

`sow init` is idempotent by design, and its rules are an architectural invariant rather than a convenience:

- **No `sow.yml`:** create one with `schema: sow/v2` and `architectures: [x86_64, aarch64]`, plus `.sow/`. No Repository is created automatically.
- **Valid config already present:** in stable name order, fill in whatever is not initialized yet — a missing Repository shell, a missing SQLite, an entire missing Dist. A newly created Dist immediately gets all empty views for its effective architectures.
- **Valid database state or a valid protocol pointer already present:** verify only. Never overwrite, never zero a generation, never rewrite bytes.
- **An architecture was added to the config after a Dist was already initialized:** `init` does not render the new view and does not advance the generation. The Dist stays dirty and waits for an explicit `build`. Removing a family that memberships or built state still use is a failure.

```console
$ sow init .
initialized /data/ws: config_created=false repositories_initialized=0 dists_initialized=0
```

The point of the third and fourth rules is that `init` must be safe to run on a repository holding real content. It converges toward the declared configuration; it never uses "not initialized yet" as an excuse to rebuild something that already works.

Objects are processed in stable order. If an early config, Repository, or Dist commits durably and a later object then fails, the committed count is preserved, the human output reports what did commit, `--json` keeps the structured result, and the command exits `3` (partial success). If nothing had committed yet, it exits with the original error class instead.

## Empty is a valid, consumable state

A Dist created by `dist new` is immediately usable by a client before you add a single package. An RPM Dist gets valid empty `repodata` per architecture family; a DEB Dist gets `Packages`, `Packages.gz`, by-hash entries, and a `Release`. If the Repository has a metadata key configured, the empty Dist is signed too.

This matters more than it sounds. It means "point the client at it now, fill it later" works, and it means removing the last package from a Dist leaves a valid signed empty index rather than a broken one.

## Protected repositories

```yaml
repos:
  pigsty:
    protected: true
```

`protected: true` refuses `repo rm` even with `-f`, and returns exit `6`. It does not restrict anything else: `add`, `rm`, `build`, and normal Dist maintenance all work. To actually delete the Repository you must edit `sow.yml`, pass `config check`, and only then remove it — which is precisely the friction the flag exists to create.

## Next

- [Pool & Architecture Views](/docs/feature/views/) — what `build` actually writes
- [Membership Policy](/docs/feature/policy/) — how `exclude` and `limit` decide what stays
- [First Workspace](/docs/start/workspace/) — a ten-minute hands-on version of this page
- [`sow.yml` reference](/docs/reference/config/) — the complete schema
