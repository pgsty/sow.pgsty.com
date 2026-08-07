---
title: "Transactions & Recovery"
linkTitle: "Transactions & Recovery"
description: "The three journals, the two-level lock model, the fixed commit order, and what happens when a write command is killed halfway through."
url: "/docs/feature/transactions/"
weight: 700
icon: fa-solid fa-shield-halved
---

Repository tools fail in one of two embarrassing ways: they leave an index that points at packages that no longer exist, or they corrupt their own database and require a rebuild from scratch. SOW is built to make both impossible, and this page explains the machinery that does it.

## The invariant

**A client following a protocol pointer always reads a complete old view or a complete new view. There is no third option, including after a power loss.**

Everything below exists to hold that line: metadata is fully staged and verified before anything public moves, the pointer swap is the commit decision, and every operation records enough durable evidence that the next command can finish it or undo it without guessing.

Note what this does *not* claim. `dirty` does not mean a half-written index — it means the Desired state is ahead of the Built generation while the old built view continues to serve correctly. And SOW does not promise that two different Dists flip generation at the same instant; it promises that each protocol view is self-consistent at every instant, and that when the command returns, all targets are on the same Built generation.

## Three journals

Different phases of a repository's life need different durability substrates, so there are three, each with a narrow scope:

| Journal | Location | Covers | Recovered by |
|---|---|---|---|
| Plain file journal | `.sow-plain-operation.json` in the target directory | one `sow create` run | the next `sow create` on that directory |
| Workspace file journal | `.sow/workspace-ops/active.json` | `init`, `repo new`, `repo rm` | the next workspace-lifecycle command |
| Repository operation journal | the repository's SQLite | `dist new/rm`, `add`, `rm`, `build`, `log prune` | the next write command on that repository |

The split is not arbitrary. Workspace lifecycle operations run when the target repository's database does not exist yet or is about to be deleted, so they cannot use it. Plain mode has no database at all by design. Everything else has a repository database available and uses it.

The **Plain journal** binds the parsed inputs, the complete ordered action plan, and a durable pre-image of every file it will replace — old hash, mode, UID, GID, and its location in a same-filesystem recovery trash. Details and the `--pigsty` ordering are in [Plain Flat Repositories](/docs/feature/plain/).

The **workspace journal** stores the operation kind, a random 64-hex id, the repository name, and both the old and new raw `sow.yml` bytes with their SHA-256. The workspace lock guarantees at most one active operation. The atomic rename of `sow.yml` is the commit decision: if the current config still hashes to the old value, the planned journal is cleaned up and rolled back; if it hashes to the new value, SOW idempotently finishes creating the repository shell or moves the removed objects into recovery. If it matches neither, SOW refuses to guess.

The **repository operation journal** commits a `planned` operation into SQLite *before* any public file side effect, then records each state transition. Its payload binds the repository, the config SHA-256, the exact selected Dist set, the exact `build_dists`, the `--skip` decision, and a manifest hash covering the new object facts, the complete Desired set, the per-Dist policy outcomes, the RPM public certificate snapshot, and the target generation.

This is not SQLite's WAL. WAL handles SQLite's own page transactions; it cannot atomically coordinate the pool, the staging area, and `dists/`. The application-level journal is what spans the database and the POSIX file actions.

## The operation lifecycle

```text
planned → staged → applied → built → done
                       └──────────────→ done_dirty
   any nonterminal → recovering → built / rolled_back
   pre-apply error → failed
```

| State | What is durable |
|---|---|
| `planned` | command, arguments, targets, and intended actions |
| `staged` | new packages and metadata written to a private staging area and verified |
| `applied` | Desired state and any private pending payload committed; the public tree may still be the old generation |
| `built` | the complete static generation has been switched in |
| `done` / `done_dirty` | terminal; kept as the audit record |

`sow log <OPERATION>` shows the transitions with timestamps:

```json
"events":[
  {"sequence":0,"state":"planned","occurred_at":"2026-08-04T04:06:32.907704Z"},
  {"sequence":1,"state":"staged","occurred_at":"2026-08-04T04:06:33.067824Z"},
  {"sequence":2,"state":"applied","occurred_at":"2026-08-04T04:06:33.253073Z"},
  {"sequence":3,"state":"built","occurred_at":"2026-08-04T04:06:34.074916Z"},
  {"sequence":4,"state":"done","occurred_at":"2026-08-04T04:06:34.077441Z"}
]
```

`done_dirty` is reachable only when you explicitly pass `--skip`. A default `add` that fails after `applied` returns an error, keeps the old built view serving, and leaves the operation recoverable — it does not quietly settle as dirty.

An operation that fails before `applied` becomes `failed`. This matters for a subtle case in the contract: `add` must record a `planned` operation before parsing packages, so a package with a disallowed architecture does produce an audit record. But apart from that terminal `failed` record, nothing is written — no package object, no membership, no pending bytes, no public tree change, no generation. You keep the audit trail without letting an invalid architecture reach any product projection.

## The lock model

Locks are POSIX advisory `flock` on the local machine. The product contract is single-writer, local POSIX, cooperative locking — network filesystems are neither detected nor supported.

| Lock | File | Held by |
|---|---|---|
| Workspace | `.sow/workspace.lock` | `init`, `repo new/rm`, `dist new/rm` |
| Repository | `.sow/repo-locks/<repo>.lock` | `add`, `rm`, `build`, `dist new/rm`, `log prune` |
| Plain directory | the target directory and its stable parent | `sow create` |

When both are needed, the order is fixed: workspace first, then repository, released in reverse. The repository lock's inode lives at a stable path and never moves with the private state directory, so removing a repository can withdraw the lock path while another process still holds an old descriptor, without a second writer forming on a new inode.

`sow create` locks the target directory *and* its stable parent. The parent lock is what stops another cooperating writer from replacing the directory by rename and then acquiring an independent lock on the substitute.

Read-only commands never take a write lock and do not accept lock flags. The ones that combine config, SQLite, and live metadata (`config check`, `repo ls/show`, `dist ls/show`) take shared locks for the duration of their snapshot. `status` is deliberately lighter: it probes the repository lock so it can report `recovering` or `locked` while a write is in flight, without blocking on it.

Two flags control waiting, on every command that takes a write lock:

| Flag | Behavior |
|---|---|
| `-T, --timeout DUR` | wait up to `DUR`; `0` (the default) waits forever |
| `-N, --no-wait` | try once and fail immediately if the lock is held |

Both failure paths exit `4`. Combining `--no-wait` with a non-zero `--timeout` is a usage error, exit `2`.

```console
$ sow add ./build/*.rpm -r pgsql -d el9 -N
lock unavailable
```

Use `-N` in cron jobs where a skipped run is better than a pile-up, and `-T 30s` in CI where a short queue is fine but a hang is not.

## The commit order

Every generation is written in the same four phases, and the order is what makes the invariant hold:

```text
payload  →  metadata  →  pointer  →  delete
```

1. **payload** — package bytes into `pool/` and the view aliases. Nothing references them yet.
2. **metadata** — checksum-named RPM metadata, `Packages`, `Packages.gz`, and by-hash index copies. Still nothing points at them.
3. **pointer** — the client entry points: `repomd.xml` (plus `.asc` if configured) for RPM; for Managed APT, `Release` (plus `InRelease` and `Release.gpg`) after every per-architecture direct and by-hash index is in place. **This is the commit.**
4. **delete** — expired metadata from generations that have aged out.

Read it forward: a package always exists before an index names it, and an index always exists before a pointer names it. Read it backward: nothing is deleted until a pointer that no longer references it is durable. There is no window in which a client can follow a live pointer to a missing file.

All of this happens through a staging area on the same filesystem as the target, verified at initialization by comparing `st_dev`. A different mount or device is an explicit failure, never a degraded copy. Files are written, fsynced, validated by SOW's own parser and closure validator, and only then moved in with atomic renames. Public files do not inherit your umask: `repodata/` is `0755`, index files and pointers are `0644`.

`sow changes` shows the same phases, which is why an external sync script can consume its output in order and never publish a broken intermediate state. See [Observability & Audit](/docs/feature/audit/).

## Crash recovery

**Every write command recovers before it does its own work.** There is no separate repair command and no daemon watching for stale state; recovery is a precondition of mutation. If a nonterminal operation exists, the next `add`, `rm`, `build`, `dist new/rm`, or `log prune` completes or rolls it back first, then proceeds.

Global recovery order is fixed: workspace lifecycle first under the workspace lock, then — if that was not a repository removal — repository operations in repository-name order under each stable repository lock. A workspace operation that has already passed the repository-removal commit decision takes precedence and forbids any nested repository recovery, since recovering state inside a repository that is being deleted would be meaningless.

Recovery is evidence-driven, not optimistic. Each phase has a defined rule:

| Phase reached | Recovery rule |
|---|---|
| `planned` | config still old → roll back the stage; otherwise conflicting evidence, exit `5` |
| `staged` | config still old → roll back; config already new → forward only |
| `applied` | the new config is atomically in place; this is the commit decision, so always forward |
| `built` | pointers and directories are durable; forward-commit the database rows |
| `done` | database, config, and tree agree; clean up staging, repeat recovery is a no-op |

This was validated by sending `SIGKILL` to `sow add` at many different moments. In every case `status` reported `recovering`, the next write command recovered that operation before executing its own, the final `check` passed all layers, and the public tree was never torn.

```console
$ sow status
repository=pigsty status=recovering ready_to_copy=false ...
```

`sow build` is the one explicit forward-recovery entry point: it attempts to complete or roll back any decidable nonterminal operation before converging. If you see `recovering`, running `sow build` is the normal response.

`error` is reserved for the case where the journal, database, and file evidence contradict each other and no automatic choice is safe. Build refuses to overwrite; the last completed view keeps serving; you restore from backup and then run `check` and `build`. There is deliberately no `repair --force`, because a repair that guesses wrong is worse than a repair that refuses.

## Fail-closed path safety

Managed paths are never assembled from user-supplied strings. Every create, rename, and delete follows the same sequence:

1. resolve the workspace root to an absolute real path;
2. reconstruct the target from a fixed relative fragment and verify the relative path contains no escape;
3. `Lstat` every existing controlled component and reject symlinks and unexpected file types;
4. delete only objects that were first atomically moved into `.sow/.../recovery` (or the Plain recovery trash);
5. before deleting, prove again that the recovery target sits inside the corresponding private state directory.

Names must match `[a-z0-9][a-z0-9._-]*`, and `.`, `..`, `.sow`, `pool`, `dists` and workspace-reserved names are rejected outright.

The same posture applies to file handles. The Plain journal is read through a no-follow, descriptor-bound handle, so a symlink cannot be substituted between the check and the open. SQLite is opened with `O_NOFOLLOW` and bound to a regular-file inode, re-verified by path after the connection is established; a database, WAL, shm, or rollback journal that is a symlink, a non-regular file, multiply hardlinked, or rebound during the open is rejected. `log export` refuses to overwrite an existing file and refuses a symlinked parent directory — which is why exporting into `/tmp` on macOS fails, since `/tmp` is a symlink there.

Journals are bounded by size: 64 MiB for Plain, 32 MiB for the workspace, 16 MiB for a repository operation payload, and 64 MiB each for the external mutation and base manifests. An oversized journal is never truncated and never degraded — it fails outside the commit window, so a writer can never produce an operation record that a recovery reader would be unable to read back.

None of this claims to defend against a malicious process running as the same user with unlimited privileges. It defends against the realistic failure modes: crashes, races between cooperating processes, and paths that changed shape between the check and the use.

## Next

- [Observability & Audit](/docs/feature/audit/) — reading the state these mechanisms maintain
- [Exit Codes](/docs/reference/exit-codes/) — what `4`, `5`, and `6` mean and when you see them
- [`build` / `status` / `check` / `changes` reference](/docs/reference/cli/build/)
