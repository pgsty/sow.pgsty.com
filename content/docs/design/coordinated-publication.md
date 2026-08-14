---
title: "Coordinated Publication Proposal"
linkTitle: "Coordinated Publication"
description: "Proposed SOW v0.4.0 workflow for plan-driven, rclone-executed publication with deterministic Ctrl+C recovery."
url: "/docs/design/coordinated-publication/"
weight: 450
icon: fa-solid fa-cloud-arrow-up
---

> **Status: proposed for SOW v0.4.0.** This page is a product and implementation
> plan, not documentation of behavior available in SOW v0.3.x. Current commands
> remain documented in [`sow publish`](/docs/command/publish/).

## Executive decision

SOW v0.4.0 should coordinate publication rather than implement another bulk object-store
client:

- **SOW owns meaning:** the frozen Generation, exact change set, publication waves,
  protocol order, recovery state, and verification result.
- **rclone owns transport:** retries, parallel payload transfer, S3 multipart upload, and
  transfer-level integrity checks.
- **the serving layer owns cache behavior:** immutable payload may be cached; mutable
  repository metadata must not serve an older generation after commit.

The primary failure model is one operator pressing **Ctrl+C** during publication. The
design therefore optimizes for deterministic rerun and forward convergence, not for
distributed writers or a multi-key transaction that object storage cannot provide.

The public promise is deliberately precise:

> Publication is ordered, restartable, additive, and eventually converges to exactly one
> frozen Generation. It is not an atomic transaction across every object key.

## User stories

### Story 1: inspect exactly what will be published

As the repository maintainer, I want to see the target Generation and every publication
wave before SOW writes the remote, so an accidental build or unexpectedly large change is
visible before delivery.

```console
sow check --repo pgsql
sow publish prod --dry-run
```

The proposed dry run prints, without credentials:

- target name, repository, base checkpoint, and target Generation;
- plan SHA-256;
- object and byte counts for prepare and commit;
- every APT/RPM view in commit order;
- delete candidates, explicitly marked **not deleted**.

`--json` returns the same closed plan as machine-readable output. A dry run has no remote
side effects and creates no active attempt.

### Story 2: publish one verified Generation

As the maintainer, I want one command to publish the current Built Generation without
manually splitting rclone commands or remembering APT/RPM pointer order.

```console
sow publish prod
```

SOW freezes the current Built Generation, persists a plan, invokes rclone for the prepare
wave, commits views in deterministic order, verifies the result, and records an Applied
Checkpoint. A later run publishes only the next exact Generation delta. If the target is
already current, the command is a no-op.

The operator never runs `rclone sync` against this prefix. SOW may invoke `rclone copy`
and `rclone copyto`, but publication never deletes a remote object.

### Story 3: stop safely before public commit

As the maintainer, I want Ctrl+C during the long payload transfer to stop quickly without
damaging the currently published repository.

If Ctrl+C arrives during prepare, SOW cancels rclone and exits with a clear message:

```text
publication stopped before commit; rerun `sow publish prod` to continue,
or run `sow publish prod --abort` to abandon the attempt
```

Only add-only payload and immutable metadata can have reached the target at this point.
The old repository pointers remain valid. A rerun uses the same frozen plan and reuses
matching objects; `--abort` is legal because no commit intent exists.

### Story 4: stop during pointer commit

As the maintainer, I want SOW to avoid abandoning half of one APT/RPM view when I press
Ctrl+C during the short commit phase.

After durable commit intent, the first Ctrl+C does not start another view. If a view is
already being committed, SOW finishes that small ordered commit unit, records its
progress, then exits. A second Ctrl+C forces immediate termination if the operator really
needs it.

```text
interrupt received; finishing view dists/noble before stopping
publication has commit intent; rerun `sow publish prod` to roll forward
```

After commit intent, `--abort` is rejected. Rerunning the same command revalidates the
frozen plan and rewrites the incomplete view from the beginning before proceeding. This
also recovers from `kill -9`, a lost terminal, or a network failure between two pointer
writes.

### Story 5: audit the complete remote explicitly

As the maintainer, I want normal incremental publication to stay proportional to the
change, while retaining a deliberate full-integrity operation before migration or when I
suspect drift.

```console
sow audit prod
```

The proposed audit:

- enumerates the complete configured prefix;
- compares it with the Applied Checkpoint and Generation manifest;
- downloads and hashes content where the provider cannot return the required digest;
- checks the public commit pointers through `public_endpoint`;
- reports missing, changed, and unknown objects without deleting them.

`publish` verifies its changed closure and all affected final pointers. `audit` is the
expensive, complete proof. A first v0.4 publication over a prefix last managed by v0.3
requires a successful audit to establish the transport migration baseline.

### Story 6: operate Cloudflare R2 without cache surprises

As an R2 operator, I want a client that reads a new repository pointer to see the objects
that pointer names, rather than an older edge-cached copy.

Before production cutover, configure the serving domain so that:

- `<prefix>/pool/**` may use a long cache TTL;
- `<prefix>/dists/**` bypasses cache in the initial v0.4 contract;
- a legacy YUM layout outside `dists/`, if any, also bypasses
  `**/repodata/repomd.xml*`;
- 404 responses for mutable metadata paths are not retained across publication.

R2 API operations are strongly consistent, but a cached custom domain can continue to
serve an old overwritten object. SOW can verify the configured public endpoint, but it
does not create DNS, bucket policy, or Cloudflare Cache Rules.

## User workflow

### Configure once

The v0.4 proposal keeps the current target identity and credential model. `r2` remains
the provider; rclone becomes its default transfer engine rather than a new provider type.

```yaml
targets:
  prod:
    repository: pgsql
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: repo/pgsql
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/repo/pgsql/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

SOW resolves the existing credential reference and passes credentials to a temporary,
private rclone configuration or child-process environment. Secrets never appear in argv,
logs, dry-run output, or the public tree. Startup performs capability checks against a
tested rclone version range rather than merely accepting any executable named `rclone`.

### Routine operation

```console
sow add ./packages/*.rpm --repo pgsql --dist el9
sow build --repo pgsql
sow check --repo pgsql
sow publish prod --dry-run
sow publish prod
```

The workflow deliberately keeps `build` and `publish` separate. Unbuilt Desired changes
are not silently delivered.

### Recovery decision

```text
Was commit intent persisted?
├── no  -> rerun publish, or publish --abort
└── yes -> rerun publish; forward recovery is the only legal path
```

No `--resume` flag is needed. The target has at most one active attempt, so repeating the
original command is the resume operation.

## Publication protocol

### Plan

The `sow/publication-plan/v2` plan is target-scoped, deterministic, and side-effect
free. It binds:

- Repository and target identity;
- base checkpoint and frozen target Generation;
- target manifest digest and plan digest;
- every operation's path, size, SHA-256, and expected old digest for updates;
- prepare waves, ordered view commit units, and delete candidates.

While an attempt is active, normal SOW mutations remain blocked by the existing
Repository lock and active-publication fence. Recovery always reconstructs and compares
the same plan digest; after commit intent, a mismatch fails closed.

### Wave 1: immutable prepare

Payload and checksum-addressed metadata are copied first from an exact generated file
list. The conceptual command is:

```text
rclone copy <repository-root> <remote-prefix> \
  --files-from-raw <prepare-list> \
  --immutable --checksum --no-traverse
```

The concrete flags and minimum supported rclone version are established by integration
tests before release. The executor must preserve transfer integrity and must never turn a
prepare operation into deletion. If the destination already contains different bytes at
an immutable path, publication fails closed.

SOW v0.3 stores an explicit `sow-sha256` object metadata value on R2. A batched rclone
copy cannot be assumed to reproduce a different SHA-256 metadata value for every input
without a per-file mapper. v0.4 therefore adopts a transport-neutral checkpoint identity:

- the Generation manifest remains authoritative SHA-256 content identity;
- the checkpoint records size, opaque provider identity, transfer engine/version, and
  the successful transfer receipt without pretending that an ETag is SHA-256;
- recovery validates the changed closure with rclone's common checksum when available;
- `sow audit` downloads and hashes an object when the provider cannot return SHA-256.

This keeps rclone a transport rather than embedding SOW's state model in a metadata-mapper
subprocess. It requires a one-time v0.3-to-v0.4 audit and checkpoint migration; old
`sow-sha256` remains valid migration evidence but is never silently reinterpreted as a new
receipt. An object with only a size match is insufficient evidence for checkpoint
migration.

### Wave 2: ordered view commit

Commit intent is persisted before the first mutable name is overwritten. Each view owns
its stable aliases and pointers; views are committed serially.

```text
APT view:
  stable Packages/Sources aliases and compressed forms
  -> Release.gpg, when signed
  -> Release
  -> InRelease, when signed

RPM view:
  repomd.xml.asc, when signed
  -> repomd.xml
```

Every mutable file is transferred with a separate forced `rclone copyto
--no-check-dest --retries 1`, using bounded I/O timeouts. SOW checks the exit status and
reconciles target state before advancing. A resumed incomplete view is rewritten from its
first mutable operation. This is intentional idempotence, not a claim of multi-object
atomicity.

APT stable aliases belong inside their view's commit unit. Publishing every repository
alias globally before the first view pointer would enlarge the inconsistent window and
couple otherwise independent views.

### Wave 3: verify and checkpoint

Normal publication verifies:

- every object changed by the plan through provider evidence appropriate to that object;
- every affected final APT/RPM pointer through the public endpoint;
- each affected view's referenced closure and signatures;
- the final plan and target Generation identities.

It then records the Applied Checkpoint. It does not list and publicly download every
unchanged package on every run. Full-prefix proof belongs to `sow audit`.

### Deletion policy

`DeleteCandidates` remain plan evidence only. Neither `rclone sync` nor `rclone delete`
is part of publication. Remote physical deletion and lifecycle garbage collection are a
separate future design, after an observation period has demonstrated that the new
checkpoint and audit evidence is sufficient.

## State and signals

| Durable state | Ctrl+C behavior | Next legal action |
|---|---|---|
| plan not persisted | stop | start again |
| planned / preparing | cancel rclone immediately | rerun or `--abort` |
| commit intent, between views | stop before next view | rerun |
| commit intent, inside view | first signal finishes current view; second forces exit | rerun |
| all views committed, not checkpointed | stop or failure leaves recoverable evidence | rerun verification/checkpoint |
| Applied Checkpoint | complete | next publish or audit |

The command always prints the plan/attempt identity and the exact legal next command.
Machine-readable progress emits phase and view boundaries without exposing secrets or raw
rclone configuration.

## Verification and acceptance

The implementation is accepted only after the following matrix passes with both APT and
RPM views:

| Scenario | Required result |
|---|---|
| initial publish to empty prefix | package manager installs successfully |
| incremental package add/update | transfer is bounded to the plan; clients see new metadata |
| no-op publish | no object mutation and same checkpoint |
| Ctrl+C during prepare | old clients remain valid; rerun converges |
| failure before/after every mutable write | rerun rewrites the view and clients converge |
| failure after final pointer but before local receipt | reconciliation recognizes the installed bytes |
| immutable-path conflict | fail closed; never overwrite it |
| stale/missing public cache rule | public verification fails before checkpoint |
| v0.3 prefix migration | full audit succeeds before first v0.4 commit |
| full audit after publication | manifest, checkpoint, remote, and public pointers agree |

Test layers proceed in this order:

1. pure plan and pointer-order contract tests;
2. fake-rclone argv, exit-code, and signal tests;
3. real rclone against local filesystem remotes;
4. S3-compatible integration with fault injection;
5. Cloudflare R2 shadow prefix and real `apt`/`dnf` clients;
6. production cutover only after the shadow prefix passes repeated interruption tests.

## Delivery roadmap

| Milestone | Deliverable | Exit gate |
|---|---|---|
| M0 — protocol | ADR, plan schema, user-visible dry run | ordered APT/RPM contract tests |
| M1 — prepare | thin rclone runner and immutable file-list copy | initial/incremental/no-op and pre-commit interruption tests |
| M2 — commit | view-owned aliases, serial `copyto`, signal boundary | fault after every mutable write converges on rerun |
| M3 — evidence | incremental verification, `sow audit`, v0.3 migration | audit agrees with the former full verification path |
| M4 — provider | S3/R2 integration and cache deployment contract | real APT/DNF clients pass through a shadow domain |
| M5 — cutover | replace production whole-tree sync entry points | no managed repository publish path invokes `rclone sync` |

Expected scope is approximately 15–20 focused development days followed by an observation
period. Correctness gates, not the calendar, decide promotion from alpha to beta and GA.

## Explicit non-goals for v0.4.0

- multiple concurrent writers or distributed locking;
- a generic publication-executor plugin framework;
- parallel commit of independent views;
- remote object deletion or automatic garbage collection;
- automatic Cloudflare purge, DNS, or Cache Rule management;
- Worker-based indirection or generation-prefix switching;
- bucket-versioning transactions;
- immediate removal of the native R2 transport or existing inventory/grace records.

Keeping these out makes v0.4.0 one controlled change: retain SOW's publication semantics,
replace the bulk transfer mechanism, and make interruption recovery observable and usable.

## References

- [Current Publication & Recovery model](/docs/design/publication/)
- [Current `sow publish` command](/docs/command/publish/)
- [Cloudflare R2 consistency model](https://developers.cloudflare.com/r2/reference/consistency/)
- [Cloudflare R2 custom-domain caching](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/)
- [rclone copy](https://rclone.org/commands/rclone_copy/)
- [rclone global flags and metadata behavior](https://rclone.org/docs/)
