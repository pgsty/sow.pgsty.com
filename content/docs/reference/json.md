---
title: "JSON Output"
linkTitle: "JSON Output"
description: "The sow.cli/v1 envelope, its fields, and the result shape of every command."
url: "/docs/reference/json/"
weight: 600
icon: fa-solid fa-code
---

Every command that produces data accepts `--json`. The output is a single line on stdout
carrying a versioned envelope, so you can pipe it straight into `jq` without worrying
about which command produced it.

```bash
sow status --json
```

```json
{"schema":"sow.cli/v1","command":"status","ok":true,"repository":"pigsty","operation":null,
 "result":{"repository":"pigsty","status":"clean","ready_to_copy":true,"desired_revision":4,
 "built_generation":4,"dirty_dists":[],"dirty_reasons":[],"pending":{"count":0,"bytes":0},
 "recent_operation":{"id":"8632724976452398569","kind":"add","state":"done",
 "created_at":"2026-08-04T04:07:17.665377Z","updated_at":"2026-08-04T04:07:18.293848Z"},
 "repository_locked":false},"errors":[]}
```

(Line-wrapped here for readability; the real output is one line.)

## The envelope

| Field | Type | Meaning |
|---|---|---|
| `schema` | string | Always `sow.cli/v1`. Check it before parsing anything else. |
| `command` | string | The command as invoked, including the subcommand: `add`, `repo ls`, `config show`. |
| `ok` | bool | `true` when `errors` is empty. Equivalent to exit code `0`. |
| `repository` | string or null | The selected repository, or `null` for workspace-wide and plain-mode commands. |
| `operation` | string or null | The operation ID for write commands, `null` for read-only ones. |
| `result` | object or null | Command-specific payload, described below. |
| `errors` | array | Zero or more `{code, class, message}` objects. |

All seven fields are always present. `result` is `null` only when the command failed
before it could produce anything — an unknown flag, for example.

### errors

```json
"errors":[{"code":3,"class":"partial","message":"managed: batch partially succeeded"}]
```

| Field | Meaning |
|---|---|
| `code` | The process [exit code](/docs/reference/exit-codes/) — `1` through `6`. |
| `class` | `runtime`, `usage`, `partial`, `lock`, `integrity`, or `rejected`. |
| `message` | The same text written to stderr. |

Branch on `class`, not on message text. Messages carry paths and package names and will
change; the class will not.

{{% alert title="A nonzero exit still returns the result" color="info" %}}
When a batch partially succeeds, `ok` is `false` *and* `result` lists everything that was
committed. Never discard the payload because the exit code was nonzero — for `add`, that
is exactly where you learn which packages landed.
{{% /alert %}}

### Operation IDs are strings

```json
"operation":"8632724976452398569"
```

Operation IDs are 64-bit values serialized as decimal strings, because they routinely
exceed what an IEEE 754 double can represent exactly. In JavaScript, `JSON.parse` on a
bare number would silently corrupt them. Keep them as strings; `jq` handles them
correctly as-is.

### stdout and stderr

Results and the JSON envelope go to stdout. Warnings and error diagnostics go to stderr,
*in addition to* appearing in the `errors` array. So this works:

```bash
sow check --json 2>/dev/null | jq -e '.ok'
```

## Result shapes

### create

```bash
sow create /srv/offline --json
```

```json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,
 "result":{"dir":"/srv/offline","rpm":4,"deb":3,
 "kept":["blackbox_exporter-0.28.0-1.aarch64.rpm","blackbox_exporter-0.28.0-1.x86_64.rpm",
 "libpq5_18.2-1.pgdg12+1_amd64.deb","pev2-1.23.0-1.noarch.rpm"],
 "removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

| Field | Meaning |
|---|---|
| `dir` | The absolute directory that was indexed |
| `rpm`, `deb` | Package counts per format |
| `kept` | Filenames included in the indexes, sorted |
| `removed` | Packages deleted by `--pigsty` cleanup; empty otherwise |
| `marker` | Whether `repo_complete` was written |
| `marker_sha256` | Digest of the marker file; present only with `--pigsty` |
| `noop` | `true` when the indexes were already correct and nothing changed |
| `recovered` | `true` when this run completed an interrupted previous run |
| `signed` | Filenames re-signed; present only with `--sign-with` |

### init

```json
"result":{"workspace":"/srv/repo","config_created":true,
 "repositories_initialized":0,"dists_initialized":0,"existing":[]}
```

On a rerun over a workspace that already exists, the counters are `0` and `existing`
names what was found:

```json
"result":{"workspace":"/srv/repo","config_created":false,
 "repositories_initialized":0,"dists_initialized":0,"existing":["sow.yml"]}
```

### config check and config show

```json
"result":{"workspace":"/srv/repo","repositories":1,"dists":2}
```

`config show` returns the effective configuration itself, in the same shape as
[`sow.yml`](/docs/reference/config/) after normalization:

```json
"result":{"schema":"sow/v2","architectures":["x86_64","aarch64"],
 "repos":{"pigsty":{"protected":false,
 "signing":{"rpm":{"packages":{"mode":"never"}}},
 "dists":{"el9":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":0,"exclude":null},
          "trixie":{"format":"deb","architectures":["x86_64","aarch64"],"limit":0,"exclude":null}}}}}
```

With `--all`, signing entries additionally carry `key_fingerprint`. Private key material
and passphrases never appear.

### repo ls, repo new, repo show

`repo ls` returns an array; `repo new` and `repo show` return one object of the same
shape.

```json
"result":{"repositories":[{"name":"pigsty","path":"/srv/repo/pigsty","protected":false,
 "dists":2,"generation":4,"desired_revision":4,"status":"clean","packages":7,"memberships":7,
 "recent_operation":{"id":"8632724976452398569","kind":"add","state":"done",
  "created_at":"2026-08-04T04:07:17.665377Z","updated_at":"2026-08-04T04:07:18.293848Z"},
 "config":{"protected":false,"signing":{...},"dists":{...}}}]}
```

`packages` counts distinct package objects in the pool; `memberships` counts
distribution memberships, so a package in two distributions counts once and twice
respectively.

`repo rm` returns only the outcome:

```json
"result":{"name":"demo","noop":false,"removed":true}
```

### dist ls, dist new, dist show

```json
"result":{"dists":[{"name":"el9","format":"rpm",
 "architectures":[{"family":"x86_64","ecosystem_arch":"x86_64"},
                  {"family":"aarch64","ecosystem_arch":"aarch64"}],
 "desired_members":4,"built_members":4,"generation":3,"dirty":false,"status":"clean",
 "effective_config_sha256":"39913af601d10d4d4033b0c29e8d66df385f8a6eb22f45219773a7fc170d4243",
 "config":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":0,"exclude":null}}]}
```

Each architecture entry carries both names: `family` is the canonical form used in
configuration, `ecosystem_arch` is what appears in the published tree — identical for RPM,
`amd64`/`arm64` for DEB.

`desired_members` ahead of `built_members`, or `dirty: true`, means a `sow build` is
pending. `effective_config_sha256` is the digest of everything that feeds the renderer;
when it changes, the distribution becomes dirty.

`dist rm` mirrors `repo rm`: `{"name":"el9","noop":false,"removed":true}`.

### add

```json
"result":{"operation":"320653458389425222","repository":"demo",
 "desired_revision":2,"built_generation":2,"dirty":false,
 "accepted":1,"failed":0,"memberships_added":1,"memberships_removed":0,
 "items":[{"input":"/incoming/pev2-1.23.0-1.noarch.rpm","status":"accepted","format":"rpm",
 "coordinate":"pev2-0:1.23.0-1.noarch",
 "sha256":"d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229",
 "dists":{"el9":"accepted"}}]}
```

One `items` entry per input path, in stable order. `status` is the item's overall
outcome, and `dists` gives the per-distribution decision:

| `status` | Meaning |
|---|---|
| `accepted` | New package object, membership created |
| `reused` | The identical object already existed; may still add membership elsewhere |
| `excluded` | Kept out by policy — see `dists` for whether it was `excluded` or `limited` |
| `failed` | Not admitted; `error` carries the reason |

The per-distribution values are `accepted`, `excluded`, and `limited`. A package can be
accepted by one distribution and limited by another in the same command:

```json
"items":[{"input":".../libpq5_18.2-1.pgdg12+1_amd64.deb","status":"excluded","format":"deb",
 "coordinate":"libpq5=18.2-1.pgdg12+1:amd64","sha256":"310611d0...","dists":{"trixie":"limited"}}]
```

A failed item carries `error` instead of the package fields:

```json
{"input":"/incoming/broken-1.0-1.x86_64.rpm","status":"failed",
 "error":"invalid RPM package: parse RPM reader: unexpected EOF"}
```

`memberships_added` and `memberships_removed` count both sides, because `limit` can evict
older versions in the same operation that admits a new one.

### rm

```json
"result":{"operation":"3422380511083828695","repository":"pigsty",
 "desired_revision":5,"built_generation":5,"dirty":false,"check":false,
 "removed":[{"dist":"el9","sha256":"45171966...",
   "coordinate":"rpm:pgbouncer_fdw_18-0:1.4.0-1PGDG.rhel9.8.x86_64","name":"pgbouncer_fdw_18"}],
 "dists":["el9"],
 "changes":[{"op":"add","path":"dists/el9/x86_64/repodata/1a57aa2f...-filelists.xml.gz",
   "phase":"metadata","size":382,"sha256":"1a57aa2f..."},
  {"op":"update","path":"dists/el9/x86_64/repodata/repomd.xml","phase":"pointer",
   "size":1510,"sha256":"f28ffe14..."},
  {"op":"delete","path":"dists/el9/x86_64/repodata/0df96f0b...-primary.xml.gz","phase":"delete"}]}
```

`check` is `true` when the command ran with `-c/--check`, in which case nothing was
written and `changes` is a forecast. Note that `removed` lists membership removals only —
pool bytes are never deleted by `rm`.

### build

```json
"result":{"operation":"3701044631565986409","repository":"pigsty",
 "dists":["el9","trixie"],"desired_revision":5,"built_generation":5,
 "noop":true,"dirty":false}
```

`noop: true` means the desired state already matched the built tree, so no generation was
created. `dists` lists the distributions considered, not necessarily the ones rebuilt.

### status

```json
"result":{"repository":"pigsty","status":"clean","ready_to_copy":true,
 "desired_revision":4,"built_generation":4,"dirty_dists":[],"dirty_reasons":[],
 "pending":{"count":0,"bytes":0},
 "recent_operation":{"id":"8632724976452398569","kind":"add","state":"done",
  "created_at":"...","updated_at":"..."},
 "repository_locked":false}
```

`status` is one of `clean`, `dirty`, `recovering`, `error`. `ready_to_copy` is the field
to read in a deploy script — but remember `status` exits `0` in every state, so test the
field, not the exit code:

```bash
sow status --json | jq -e '.result.ready_to_copy' >/dev/null || exit 1
```

`pending` counts package bytes held privately after `add --skip`, not yet published.
`repository_locked` reports whether another process currently holds the write lock.

### check

```json
"result":{"repository":"pigsty","status":"clean","ready_to_copy":true,
 "built_generation":4,"desired_revision":4,
 "layers":[{"name":"config","ok":true,"checked":5,"issues":[]},
  {"name":"state","ok":true,"checked":1,"issues":[]},
  {"name":"public-modes","ok":true,"checked":72,"issues":[]},
  {"name":"package-bytes","ok":true,"checked":7,"issues":[]},
  {"name":"desired-membership","ok":true,"checked":7,"issues":[]},
  {"name":"index","ok":true,"checked":2,"issues":[]},
  {"name":"signature","ok":true,"checked":11,"issues":[]},
  {"name":"generation-manifest","ok":true,"checked":4,"issues":[]}]}
```

Eight layers, always in this order, each with a count of what it examined and any issues
found. A dirty repository reports every layer `ok: true` and still fails with exit `5`,
because the layers verify consistency while `ready_to_copy` reports currency:

```json
{...,"ok":false,"result":{"status":"dirty","ready_to_copy":false,...},
 "errors":[{"code":5,"class":"integrity",
  "message":"integrity or recovery error: managed: repository is not ready to copy: repository status is dirty"}]}
```

### changes

```json
"result":{"repository":"pigsty","base":4,"generation":5,"dirty":false,
 "changes":[{"op":"add","path":"dists/el9/x86_64/repodata/1a57aa2f...-filelists.xml.gz",
   "phase":"metadata","size":382,"sha256":"1a57aa2f..."},
  {"op":"update","path":"dists/el9/x86_64/repodata/repomd.xml","phase":"pointer",
   "size":1510,"sha256":"f28ffe14..."},
  {"op":"delete","path":"dists/el9/x86_64/repodata/0df96f0b...-primary.xml.gz","phase":"delete"}]}
```

| Field | Values |
|---|---|
| `op` | `add`, `update`, `delete` |
| `phase` | `payload`, `metadata`, `pointer`, `delete` |
| `path` | Always relative to the repository root, always `/`-separated |
| `size`, `sha256` | Present for `add` and `update`; omitted for `delete` |

Apply the phases in that order and no client ever sees a dangling reference: package
bytes first, then checksum-named metadata, then the protocol pointers (`repomd.xml`,
`Release`), and only then the deletion of superseded files.

`sow changes 0` yields the complete current tree as one `add` set — a full delivery
manifest.

### ls, show, where

`ls` returns an array of package objects; `show` returns exactly one under `package`.

```json
"result":{"repository":"pigsty","dists":["el9"],"dirty":false,
 "packages":[{"sha256":"d06d7f23...","format":"rpm","coordinate":"pev2-0:1.23.0-1.noarch",
 "architecture":"noarch","canonical_arch":"neutral",
 "pool_path":"pool/p/pev2/pev2-1.23.0-1.noarch.rpm","filename":"pev2-1.23.0-1.noarch.rpm",
 "size":316372,"name":"pev2","source":"pev2","version":"1.23.0","epoch":"0","release":"1",
 "kind":"main","payload_sha256":"0413d629...","signature_key":"E7935D8DB9BD8B20",
 "storage":"pool","created_revision":3,"dists":["el9"],"built_dists":["el9"]}]}
```

The fields worth knowing:

| Field | Meaning |
|---|---|
| `architecture` | As it appears in the package header: `x86_64`, `noarch`, `amd64`, `all` |
| `canonical_arch` | The family SOW groups by: `x86_64`, `aarch64`, or `neutral` |
| `payload_sha256` | RPM only — the signature-neutral digest used to recognize re-signed copies |
| `signature_key` | Key ID of the embedded signature, when the package carries one |
| `storage` | `pool` when published, `pending` when added with `--skip` |
| `dists` / `built_dists` | Desired membership versus what the last build published |

`dists` longer than `built_dists` is another way to see that a build is pending.

`where` searches the whole workspace and returns locations instead of full objects:

```json
"result":{"reference":"pev2","locations":[{"repository":"pigsty","dists":["el9"],
 "built_dists":["el9"],"sha256":"d06d7f23...","coordinate":"rpm:pev2-0:1.23.0-1.noarch"}]}
```

### log

`sow log` returns the operation ledger, newest first:

```json
"result":{"repository":"pigsty","operations":[{"id":"3701044631565986409","kind":"build",
 "state":"done",
 "payload_json":"{\"version\":2,\"repository\":\"pigsty\",\"kind\":\"build\",\"config_sha256\":\"37eb6dcf...\",\"skip\":false,\"noop\":true,\"dists\":[\"el9\",\"trixie\"],\"build_dists\":[],\"manifest_sha256\":\"125d7266...\"}",
 "result_json":"{\"dists\":2,\"dropped_pending\":[]}",
 "created_at":"2026-08-04T04:08:08.691678Z","updated_at":"2026-08-04T04:08:08.763019Z"}]}
```

`payload_json` and `result_json` are strings containing nested JSON, not objects. They are
stored verbatim so the audit record is byte-stable; parse them with a second pass:

```bash
sow log --json | jq -r '.result.operations[] | .payload_json | fromjson | .config_sha256'
```

Passing an operation ID returns the full detail — state transitions, packages,
memberships, and every file action:

```json
"result":{"repository":"pigsty","detail":{"operation":{...},"duration_ms":598,
 "events":[{"sequence":0,"state":"planned","detail_json":"{}","occurred_at":"..."},
  {"sequence":1,"state":"staged",...},{"sequence":2,"state":"applied",...},
  {"sequence":3,"state":"built",...},{"sequence":4,"state":"done",...}],
 "packages":[{"sequence":0,"input_path":"pgbouncer_fdw_18","package_sha256":"45171966...",
  "coordinate":"rpm:pgbouncer_fdw_18-0:1.4.0-1PGDG.rhel9.8.x86_64","disposition":"removed"}],
 "memberships":[{"sequence":0,"dist":"el9","package_sha256":"45171966...","action":"remove"}],
 "files":[{"sequence":0,"action":"add","phase":"metadata","path":"dists/el9/x86_64/repodata/1a57aa2f...-filelists.xml.gz","size":382,"sha256":"1a57aa2f..."}]}}
```

`sow log prune` returns what it removed:

```json
"result":{"operation":"7140280533435786353","repository":"demo",
 "before":"2026-01-01T00:00:00+08:00","pruned":0}
```

Note that `before` echoes the absolute timestamp a bare date resolved to in your local
timezone.

### log export is not an envelope

`sow log export` writes **JSON Lines** — one complete operation record per line, no
envelope, no `--json` flag. It is meant for archiving, not for scripting a single command:

```bash
sow log export - | head -1
sow log export operations.jsonl
```

It refuses to overwrite an existing file, and it refuses a target whose parent directory
is a symlink.

## A worked example

Fail a deploy unless the repository is both consistent and current, then list exactly what
to copy:

```bash
#!/usr/bin/env bash
set -euo pipefail

if ! sow check -r pigsty --json 2>/dev/null | jq -e '.ok' >/dev/null; then
  echo "repository is not deliverable" >&2
  exit 1
fi

# Full manifest of the current published tree, in delivery order.
sow changes 0 -r pigsty --json \
  | jq -r '.result.changes[] | [.phase, .op, .path] | @tsv'
```

## See also

- [Exit Codes](/docs/reference/exit-codes/) — the `code` and `class` values in `errors`
- [CLI Commands](/docs/reference/cli/) — which commands accept `--json`
- [Observability & Audit](/docs/feature/audit/) — what the operation ledger records
