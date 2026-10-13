---
title: "Transactions & Recovery"
linkTitle: "Transactions & Recovery"
description: "Recover interrupted Managed operations and understand local build order and lock behavior."
categories: [Feature]
tags: [transaction, generation, audit]
url: "/docs/feature/transactions/"
weight: 700
icon: fa-solid fa-shield-halved
---

<span id="the-invariant"></span>

Managed mode records changes before it applies them. After an interruption, SOW uses
these records to finish or roll back the operation. The recovery command depends on the
operation that stopped.

<span id="crash-recovery"></span>

## Recover an interrupted operation

Start with the recorded state:

```bash
sow status -r demo
sow log -r demo
```

| State | Next step |
|---|---|
| `clean` | Run `sow check` before delivery |
| `dirty` | Run `sow build` to apply pending membership or configuration changes |
| `recovering` | Use the recovery command for the interrupted operation, listed below |
| `error` | Inspect the reported file or operation in the diagnostic and log |

| Interrupted operation | Recovery command |
|---|---|
| `add`, `rm`, Dist change, or build | `sow build -r demo` |
| `init`, `repo new`, or `repo rm` | Rerun the corresponding lifecycle command |
| Publication | `sow publish TARGET` |
| Plain index generation | Rerun `sow create` with the original options |

First correct any reported input, configuration, or storage error. Keep the workspace
configuration, database, and private state together during recovery. After a local recovery,
run `sow check -r demo`. See [Troubleshooting](/docs/reference/troubleshooting/) for common errors
and [`publish`](/docs/command/publish/) for publication recovery.

<span id="two-durable-journals"></span>
<span id="the-operation-lifecycle"></span>

## What SOW records

| Record | Location | Purpose |
|---|---|---|
| Workspace lifecycle journal | `.sow/workspace-ops/active.json` | Coordinates configuration with repository creation or removal |
| Repository operation journal | `.sow/<repo>.db` | Records local membership changes, builds, and maintenance |
| Publication state | `.sow/<repo>.db` | Records target bindings, frozen publication plans, and progress |

Workspace lifecycle recovery compares the current `sow.yml` digest with the journal's old
and new configurations. The configuration replacement decides whether to roll back or
finish that lifecycle change. A digest matching neither is an integrity error.

Repository mutations record their own state transitions:

```text
planned → staged → applied → built → done
                       └────────────→ done_dirty
```

| State | Meaning |
|---|---|
| `planned` | The operation and its intended scope are recorded |
| `staged` | Inputs have been prepared for the next stage |
| `applied` | Desired state has committed; the previous public generation can still be active |
| `built` | The generated public tree has been installed |
| `done` | The operation is complete |
| `done_dirty` | Desired state has committed and a build remains pending |

Other terminal outcomes include `rolled_back` and `failed`. Read transitions and timestamps
with `sow log OPERATION -r demo`.

`--skip` normally ends at `done_dirty`. A recognized signing-policy change, configuration
change before a build plan is frozen, or supported contract upgrade can also leave a
committed operation dirty. The log records the reason. Correct the configuration if
needed, then run `build` again.

<span id="the-commit-order"></span>

## Local build order

SOW stages and validates output on the same filesystem, then applies it in this order:

```text
package bytes → metadata → client pointers → obsolete metadata cleanup
```

1. Put package bytes in the canonical `pool/` path.
2. Install checksum-named RPM metadata and APT direct and by-hash indexes.
3. Install RPM `repomd.xml` and configured signatures, or APT `Release`, `InRelease`, and
   `Release.gpg` as applicable.
4. Remove obsolete metadata after the replacement is durable.

The build keeps the immediately preceding RPM immutable metadata and APT by-hash objects
available for readers of the previous pointer. Explicit generation retention is separate;
see [`retain`](/docs/command/retain/).

A dirty repository still serves its last built generation. A multi-Dist operation can
switch views at different times. Remote HTTP requests and caches also have their own
lifetimes; use `sow publish` for live target updates. `sow changes` lists local file
changes and does not perform publication or target cleanup.

<span id="the-lock-model"></span>

## Locks and waiting

SOW uses advisory locks to coordinate its processes. Workspace lifecycle uses
`.sow/workspace.lock`; repository writes use `.sow/repo-locks/<repo>.lock`.
When both are required, the workspace lock comes first.

Read commands that need a consistent snapshot use shared locks. `status` probes the
repository writer lock so it can report activity without waiting for that writer.
Plain `create` locks its directory and parent.

| Option | Behavior |
|---|---|
| `-T 30s` | Wait up to 30 seconds for a write lock |
| `-T 0` | Wait until the lock is available; default |
| `-N` | Try once; exit immediately if the lock is held |

A failed lock attempt exits `4`. Combining `-N` with a nonzero `-T` exits `2`.
Use only the lock options accepted by the command; read-only commands do not accept them.

<span id="fail-closed-path-safety"></span>

## Filesystem requirements

Use a local POSIX filesystem with advisory locks, `fsync`, and atomic rename. On macOS,
use APFS. Keep public files and private staging on the same filesystem. SOW rejects symlinked
control paths, unexpected file types, and path escapes. It checks file identity before
replacing or removing controlled objects. Network filesystems are not supported workspace
locations.

Repository and Dist names use `[a-z0-9][a-z0-9._-]*`; reserved names are listed in
[Repository layout](/docs/reference/layout/). For script responses to interruption, lock
contention, or integrity errors, see [Exit codes](/docs/reference/exit-codes/).

<span id="next"></span>
