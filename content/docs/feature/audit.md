---
title: "Observability & Audit"
linkTitle: "Observability & Audit"
description: "One question per command: status for cheap state, check for a full proof, changes for a delivery plan, log for the operation ledger — plus how generation retention works."
url: "/docs/feature/audit/"
weight: 800
icon: fa-solid fa-magnifying-glass-chart
---

Four read-only commands answer four different questions, and each one refuses to do the others' job. That separation is deliberate: a cheap status check that occasionally hashes the whole repository is useless in a loop, and a full verification that silently repairs things is useless as evidence.

| Command | Question | Cost | Writes |
|---|---|---|---|
| `status` | What state is this repository in right now? | cheap, no hashing | never |
| `check` | Can I prove this tree is correct and shippable? | full verification | never |
| `changes` | Which files do I need to copy to bring a mirror up to date? | reads the generation manifest | never |
| `log` | What happened, when, and to which packages? | reads the ledger | `prune` only |

## `status` — cheap state

```console
$ sow status
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4 dirty_dists= pending=0/0 locked=false
```

`status` never hashes the repository, never recovers an operation, and never builds. It reports the repository state, the Desired revision, the Built generation, which Dists are dirty, how many pending payload objects exist and how many bytes they occupy, whether a lock is held, and the most recent operation.

There are four states:

| State | Meaning | What clients see |
|---|---|---|
| `clean` | Desired and Built agree | every view complete and current |
| `dirty` | Desired is ahead, usually from `--skip` or a config change | the old Built view, still complete |
| `recovering` | a nonterminal operation exists; the next write command must recover it | the last completed protocol pointer |
| `error` | automatic recovery cannot safely decide; human intervention needed | the last completed view, never overwritten |

After an `add --skip`, the difference is visible immediately:

```console
$ sow add pkg/vray-5.44.1-1.x86_64.rpm -r pigsty -d el9 --skip
add repository=pigsty operation=1723106391526629874 accepted=1 failed=0 memberships=+1/-0 revision=5 generation=4 dirty=true

$ sow status
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4 dirty_dists=el9 pending=1/18787411 locked=false
```

The revision moved to 5, the generation stayed at 4, `el9` is dirty, and one pending object of 18.7 MB is durably stored in the private pending store. The public `pool/` and `dists/` are byte-for-byte unchanged.

**`status` exits `0` in all four states**, as long as the state database is readable. That is intentional — scripts should read the structured state rather than infer it from an exit code, and a `recovering` repository is a fact to act on, not a command failure. Only an unreadable or unparseable state returns an integrity error. The `ready_to_copy` field is the plain answer to "can I ship this"; if you want a strict gate that fails the build, use `sow check`.

## `check` — a full proof

`check` verifies the selected Repository or Dists across eight layers, in order, and writes nothing:

```console
$ sow check
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=66
package-bytes	ok=true	checked=5
desired-membership	ok=true	checked=5
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=4
```

| Layer | What it proves |
|---|---|
| `config` | `sow.yml` parses, and matches the live Dists, architectures, and signing availability |
| `state` | SQLite schema, migration ledger, and relational integrity |
| `public-modes` | every public file and directory carries the expected permissions |
| `package-bytes` | every pool and pending object hashes to its recorded SHA-256 |
| `desired-membership` | memberships, coordinates, and architecture aliases are consistent |
| `index` | rendered metadata matches the membership set, and every reference resolves |
| `signature` | package signatures and declared metadata signatures verify |
| `generation-manifest` | the built generation manifest matches the actual tree on disk |

`check` does not repair, does not build, and does not recover operations. When the repository is dirty it verifies **both** the Desired state and the old Built generation — and then still refuses to call the result shippable:

```console
$ sow check; echo "rc=$?"
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4
config	ok=true	checked=5
…
generation-manifest	ok=true	checked=4
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
rc=5
```

Every layer passed and the exit code is still `5`. That is the correct reading: nothing is broken, but what is on disk is not what you asked for, so it is not ready to copy. This is the command to put in a release pipeline — `status` tells you what is going on, `check` decides whether you ship.

On a 16-package workspace all eight layers complete in about 0.12 s. `-j/--jobs N` parallelizes the hashing.

## `changes` — the delivery plan

```console
$ sow changes
base=4 generation=5 dirty=false
add	payload	dists/el9/x86_64/pool/v/vray/vray-5.44.1-1.x86_64.rpm	18787411	4bb5c796…
add	payload	pool/v/vray/vray-5.44.1-1.x86_64.rpm	18787411	4bb5c796…
add	metadata	dists/el9/x86_64/repodata/75fdd4f3…-primary.xml.gz	1089	75fdd4f3…
add	metadata	dists/el9/x86_64/repodata/a8de7a88…-filelists.xml.gz	512	a8de7a88…
add	metadata	dists/el9/x86_64/repodata/6f97bb31…-other.xml.gz	355	6f97bb31…
update	pointer	dists/el9/aarch64/repodata/repomd.xml	1510	60596dfb…
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1512	944d47f0…
delete	delete	dists/el9/x86_64/repodata/0df96f0b…-primary.xml.gz	0
delete	delete	dists/el9/x86_64/repodata/8402c28c…-filelists.xml.gz	0
delete	delete	dists/el9/x86_64/repodata/c16c7739…-other.xml.gz	0
…
```

Each row is an operation (`add`, `update`, `delete`), a phase, a repository-relative path, a size, and a SHA-256. The **phase order is the same one `build` uses on local disk**: `payload → metadata → pointer → delete`. Consume the plan in that order on the far side and the mirror is never inconsistent — packages land before the indexes that name them, indexes land before the pointers that name them, and nothing is deleted until a pointer that no longer references it has been published.

The base argument selects the comparison point:

- **No argument** — the most recent Built generation versus its predecessor. This is the incremental sync plan.
- **`changes N`** — the net change from generation `N` to the current one. Useful when a mirror is several generations behind; you get one net plan, not a replay.
- **`changes 0`** — the complete delivery manifest of the current generation: every file under `pool/` and `dists/`, excluding `sow.yml` and `.sow/`. This is what a fresh mirror needs.

Three constraints keep the output honest. A dirty Desired state never enters `changes` — the output warns that the repository is dirty and still ends at the current Built generation, because the plan describes the physical tree, not your intentions. A `recovering` or `error` repository refuses to emit a plan at all, so an undecided file action is never mistaken for a generation. And `changes` operates at repository scope and does not accept `-d`; if you need one Dist, filter the output by path.

SOW does not know about remote endpoints, does not hold credentials, and does not invoke any transfer tool. `--json` gives you a stable structure to drive `rclone`, `rsync`, or your own script from:

```json
{
  "base": 41,
  "generation": 43,
  "dirty": false,
  "changes": [
    {"op": "add", "path": "pool/p/pkg/pkg.rpm", "phase": "payload", "size": 123, "sha256": "…"}
  ]
}
```

## Generation retention

Every real physical change produces a new monotonic generation. Metadata is checksum-named, and **the previous generation's metadata files stay on disk for exactly one more generation**.

Here is a view directory at generation 5, holding two generations of metadata:

```console
$ ls -1 dists/el9/x86_64/repodata/
1e73e26d…-primary.xml.gz        # generation 3
31b640e0…-filelists.xml.gz      # generation 3
58f05bff…-other.xml.gz          # generation 3
6f97bb31…-other.xml.gz          # generation 5, current
75fdd4f3…-primary.xml.gz        # generation 5, current
a8de7a88…-filelists.xml.gz      # generation 5, current
repomd.xml

$ grep -o 'href="[^"]*"' dists/el9/x86_64/repodata/repomd.xml
href="repodata/75fdd4f3…-primary.xml.gz"
href="repodata/a8de7a88…-filelists.xml.gz"
href="repodata/6f97bb31…-other.xml.gz"
```

`repomd.xml` references only the current generation. The older trio is unreferenced but still fetchable — which is exactly the point. A client that downloaded `repomd.xml` seconds before the build can still fetch the metadata that file promised, instead of getting a 404 mid-transaction. The APT side gets the same property from by-hash entries.

Files that age out of the window appear in the `delete` phase of the next `changes`, as the generation-1 entries do in the transcript above. Once you have applied that plan to a mirror, both sides are back in step.

## `log` — the operation ledger

Every write command leaves a durable record. `sow log` shows the most recent 50, newest first; `sow log OPERATION` expands one:

```json
{"id":"2299498205178002745","kind":"add","state":"done",
 "payload_json":"{\"version\":2,\"repository\":\"pigsty\",\"kind\":\"add\",
   \"config_sha256\":\"37eb6dcf…\",\"skip\":false,\"dists\":[\"el9\"],
   \"build_dists\":[\"el9\"],\"manifest_sha256\":\"73933eb6…\"}",
 "result_json":"{\"accepted\":3,\"dropped_pending\":[],\"failed\":0}",
 "created_at":"2026-08-04T04:06:32.907704Z","updated_at":"2026-08-04T04:06:34.077441Z"}
```

The single-operation view adds the state transitions with timestamps, the per-package dispositions with their per-Dist outcomes, the membership additions and removals, and the complete file changeset with phases. Because the payload records `config_sha256` and `manifest_sha256`, you can prove which configuration and which intended result an operation was executed against — not just that it ran.

`-d` filters to operations that touched a given Dist.

### Exporting

```bash
sow log export pgsql-ops.jsonl -r pgsql
sow log export - -r pgsql | jq -c 'select(.operation.kind == "add")'
```

`export` writes eligible terminal operations as JSONL, one object per line, in a stable order. Omitting the filename or passing `-` writes to stdout. It refuses to overwrite an existing file and refuses a symlinked parent directory — which is why exporting into `/tmp` on macOS fails, since `/tmp` is a symlink there. Write to an explicit path you control.

### Pruning

```console
$ sow log prune 2026-01-01 -r pgsql
{"operation":"2594304813413153341","repository":"pigsty","before":"2026-01-01T00:00:00+08:00","pruned":1}
```

`BEFORE` is an ISO-8601 date or an RFC 3339 timestamp; a bare date is interpreted as local midnight and echoed back as an absolute time, so there is no ambiguity about what was pruned.

Prune deletes only terminal audit records that nothing else needs. It never removes a nonterminal operation, a record required for recovery, current package or membership state, a Built generation, or a changeset. It is a repository-level operation and does not accept `-d`, because pruning half of an operation would produce a record that cannot be interpreted. It runs under its own durable journal, so a crash mid-prune is recovered by the next write command like any other operation.

## Putting it together

A release pipeline usually reads:

```bash
sow build -r pgsql -j 12          # converge
sow check -r pgsql                # gate: non-zero means do not ship
sow changes 41 -r pgsql --json > plan.json
```

`status` for a dashboard, `check` for the gate, `changes` for the transport, `log` for the postmortem.

## Next

- [`build` / `status` / `check` / `changes` reference](/docs/reference/cli/build/)
- [`sow log` reference](/docs/reference/cli/log/)
- [JSON Output](/docs/reference/json/) — the `sow.cli/v1` envelope and per-command result shapes
- [Transactions & Recovery](/docs/feature/transactions/) — what produces the states these commands report
