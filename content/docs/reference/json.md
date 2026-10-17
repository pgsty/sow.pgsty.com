---
title: "JSON Output"
linkTitle: "JSON Output"
description: "Look up JSON response fields, package and operation IDs, errors, and command results."
categories: [Reference]
tags: [cli, output, json]
url: "/docs/reference/json/"
weight: 600
icon: fa-solid fa-code
---

<span id="stdout-and-stderr" data-td-print-local></span>

Use `--json` on data commands to read one newline-terminated JSON document from stdout.
Diagnostics go to stderr. `log export` is the exception: it writes JSON Lines and does
not accept `--json`.

```bash
sow status -r demo --json | jq '.result.status'
```

<span id="the-envelope" data-td-print-local></span>

## Envelope

Every JSON response has these seven fields:

| Field | Type | Meaning |
|---|---|---|
| `schema` | string | `sow.cli/v1` |
| `command` | string | Command name, including subcommand, such as `repo ls` |
| `ok` | boolean | Command succeeded; `false` when errors are present |
| `repository` | string or null | Selected repository, when attached to the response |
| `operation` | string or null | Command-specific operation or publication identity |
| `result` | object or null | Command data, including useful partial or diagnostic results on failure |
| `errors` | array | Error objects with `code`, `class`, and `message` |

Example of a successful configuration check:

```json
{
  "schema": "sow.cli/v1",
  "command": "config check",
  "ok": true,
  "repository": null,
  "operation": null,
  "result": {"workspace": "/srv/repo", "repositories": 1, "dists": 2},
  "errors": []
}
```

The actual output occupies one line. Paths and counts depend on the workspace.
A failure before meaningful work usually has `result: null`. A failed `check` and a
partially successful `add` can still return useful results. Preserve them when `ok` is false.

A maintenance error after a database commit can also return committed results.
Inspect the result, `status`, and the operation log before retrying. A nonzero exit does not mean that the transaction rolled back.

### Errors

```json
{"code":3,"class":"partial","message":"managed: batch partially succeeded"}
```

Branch on `code` or `class`, not message text. Classes are `runtime`, `usage`, `discovery`,
`config`, `partial`, `lock`, `integrity`, `rejected`, and `interrupted`.
See [Exit codes](/docs/reference/exit-codes/) for the mapping and next steps.

<span id="operation-ids-are-strings" data-td-print-local></span>
<span id="generation-ids-are-fixed-width-strings" data-td-print-local></span>

### Identities

Keep operation and generation IDs as strings. Operation IDs can exceed JavaScript's exact
integer range. Generation IDs are 20-digit, zero-padded decimal strings:

```json
{"operation":"8632724976452398569","built_generation":"00000000000000000004"}
```

This applies to `generation`, `built_generation`, `base_generation`, and generation-valued
`base` fields. Desired revisions and counts remain JSON numbers.

The top-level `operation` field is set as follows:

| Command | Value |
|---|---|
| `add`, `rm` without preview, `build`, local `gc` | Journal ID, if allocated |
| `publish`, `publish --abort` | Publication attempt ID, if available |
| `log ID` | Requested operation ID |
| Other commands | `null`; `log prune` puts its ID in `result.operation` |

A null operation does not mean the command is read-only. `where` keeps the top-level
repository null and places repository names inside its locations.

<span id="result-shapes" data-td-print-local></span>
<span id="create" data-td-print-local></span>

## Plain `create`

| Result field | Meaning |
|---|---|
| `dir` | Absolute indexed directory |
| `rpm`, `deb` | Indexed package counts |
| `kept` | Sorted included filenames |
| `removed` | Files removed by `--pigsty` |
| `marker` | Whether the completion marker was produced |
| `marker_sha256` | Marker digest, present with the marker |
| `noop` | No public changes were needed |
| `recovered` | Always `false`; Plain mode has no journal recovery |
| `signed`, `signer` | Signed filenames and signer identity, when available |

<span id="init" data-td-print-local></span>
<span id="config-check-and-config-show" data-td-print-local></span>

## Initialization and configuration

| Command | Result |
|---|---|
| `init` | `workspace`, `config_created`, `repositories_initialized`, `dists_initialized`, `existing` |
| `config check` | `workspace`, `repositories`, `dists` |
| `config show` | Effective configuration: `schema`, `architectures`, `repos`, and `targets` when present |

Resolved signing settings can contain public fingerprints and certificate snapshot
hashes. Fingerprint and hash arrays are independently sorted and must not be paired by
index. See [Configuration](/docs/reference/config/#key-references).

<span id="repo-ls-repo-new-repo-show" data-td-print-local></span>
<span id="dist-ls-dist-new-dist-show" data-td-print-local></span>

## Repositories and Dists

`repo ls` returns `result.repositories[]`. `repo new` and `repo show` return one repository
object directly. Common fields are `name`, `path`, `protected`, `dists`, `generation`,
`desired_revision`, `status`, `packages`, `memberships`, and `config`.
`dirty_reasons` and `recent_operation` appear when available. An operation summary has
`id`, `kind`, `state`, `created_at`, and `updated_at`, plus optional `error_class`.
The same summary shape appears in `status.pending_operation` and `status.recent_operation`.

`packages` counts stored package objects; `memberships` counts Desired Dist memberships.
One object in two Dists counts as one package and two memberships.

`dist ls` returns `result.dists[]`. `dist new` and `dist show` return one Dist object:
`name`, `format`, `architectures`, `desired_members`, `built_members`, `generation`, `dirty`,
`status`, `effective_config_sha256`, and `config`, with optional `dirty_reasons`.

Each architecture entry has `family` and `ecosystem_arch`. DEB uses canonical family
`x86_64` with ecosystem name `amd64`, for example.

`repo rm` and `dist rm` return `name`, `removed`, and `noop`.
`repo migrate` returns `repository`, `repository_id`, `from_layout`, `to_layout`,
`schema_from`, `schema_to`, `phase`, `generation`, `grace_not_before`, `legacy_aliases`, and
`complete`, plus optional `warnings`. `grace_not_before` is null when no grace deadline applies.
Migration-abort warnings identify retained temporary stages or incomplete cleanup.
Once repository selection succeeds, a migration failure keeps that repository in the response.
See [`repo migrate`](/docs/command/repo/#sow-repo-migrate) for phase meanings.

<span id="add" data-td-print-local></span>
<span id="rm" data-td-print-local></span>
<span id="build" data-td-print-local></span>

## `add`, `rm`, and `build`

All three report repository state after the operation: `repository`, `desired_revision`,
`built_generation`, and `dirty`.

`add` also returns `operation`, `accepted`, `failed`, `memberships_added`,
`memberships_removed`, and `items[]`. Each item has `input` and `status`. It also has
`format`, `coordinate`, `sha256`, a per-Dist `dists` map, and `error` when those values are available.

| Item status | Meaning |
|---|---|
| `accepted` | New package accepted into membership |
| `reused` | Existing package object reused; membership can still change |
| `excluded` | No selected Dist accepted the package because of policy |
| `failed` | Input failed; inspect `error` |

Per-Dist outcomes are `accepted`, `excluded`, or `limited`. A package can have different
outcomes in different Dists. Membership removal counts can increase when `limit` removes
older versions.

`rm` returns optional `operation`, `removed[]`, selected `dists`, `changes[]`, and `check`.
Each `removed` record has `dist`, `sha256`, `coordinate`, and `name`.
A preview has `check: true`; only `prediction_complete: true` confirms a complete predicted
file list. Pool bytes are not removed by `rm`.

`build` returns `operation`, considered `dists`, and `noop`. A no-op creates no new generation.

<span id="status" data-td-print-local></span>
<span id="check" data-td-print-local></span>

## `status` and `check`

`status` returns `status`, `ready_to_copy`, `desired_revision`, `built_generation`,
`dirty_dists`, `dirty_reasons`, `pending`, and `repository_locked`.
Optional fields include `pending_operation`, `recent_operation`, and `lock_holder`.

`status` is `clean`, `dirty`, `recovering`, or `error`. `pending` contains `count` and `bytes`.
A successful status query can return any repository state. `ok: true` means the query
succeeded. Before publication or copying, run `check` for a complete validation.

`check` returns `repository`, `status`, `ready_to_copy`, `built_generation`,
`desired_revision`, and `layers[]`. Each layer has `name`, `ok`, `checked`, and `issues`.

Normal layers are `config`, `state`, `public-modes`, `retained`, `package-bytes`,
`desired-membership`, `index`, `signature`, and `generation-manifest`.
An active layout transition instead reports the first three and `layout-transition`.
A dirty repository can pass individual consistency layers and still fail readiness with
exit `5`.

## `changes`

The result has `repository`, `base`, `generation`, `dirty`, and `changes[]`.
Each change contains:

| Field | Values |
|---|---|
| `op` | `add`, `update`, `delete` |
| `phase` | `payload`, `metadata`, `pointer`, `delete` |
| `path` | Slash-separated path relative to the repository root |
| `size`, `sha256` | Present for added/updated files; omitted for deletions |

No base compares with the previous built generation. Base `0` lists the complete current
tree. A numbered base compares that recorded generation with the current one.
This is a local file difference; use `publish` and target `gc` for remote changes.

<span id="ls-show-where" data-td-print-local></span>

## Package queries

| Command | Result fields |
|---|---|
| `ls` | `repository`, selected `dists`, `dirty`, `packages[]` |
| `show` | `repository`, `package` |
| `where` | `reference`, `locations[]` |

Package objects include `sha256`, `format`, `coordinate`, `architecture`, `canonical_arch`,
`pool_path`, `filename`, `size`, `name`, `source`, `version`, `kind`, `storage`,
`created_revision`, `dists`, and `built_dists`. Optional fields include `epoch`, `release`,
RPM `payload_sha256` and `signature_key`, and `warning`.

`architecture` is native (`noarch`, `amd64`, etc.); `canonical_arch` is `x86_64`, `aarch64`,
or `neutral`. `storage` is `pool` or `pending`; it does not describe remote publication.
`dists` records Desired membership; `built_dists` records the last built membership.
Package-object `coordinate` omits the format prefix; prepend `format + ":"` to form a
CLI coordinate reference. `where` location coordinates already include the prefix. Each location has `repository`,
`dists`, `built_dists`, `sha256`, and `coordinate`.

<span id="publish-retain-gc-export" data-td-print-local></span>

## Publication and maintenance

| Command | Main result fields |
|---|---|
| `publish` | `repository`, `target`, `provider`, `generation`, optional `attempt`/`checkpoint`, `phase`, `objects`, `noop` |
| `publish --abort` | `repository`, `target`, `provider`, `attempt`, `phase`, `objects` |
| `retain add/rm` | `repository`, `record`, `record_identity`, `path` |
| `retain ls` | `repository`, `generations[]` |
| Local `gc` | Optional `operation`, `repository`, `base_generation`, `generation`, `objects`, `bytes`, `noop` |
| Target `gc` | `repository`, `target`, `provider`, `phase`, `reports`, `candidates`, `deleted_objects`, `deleted_bytes`, `retained_objects`, `pending_grace`, `completed_attempts`, `noop` |
| `export rpm-leaf` | `repository`, `repository_id`, `generation`, `dist`, `arch`, `directory`, `method`, `signed`, `signer_identity`, `packages`, `files`, `manifest_sha256` |

`publish --rebind` has the normal publish shape. R2 target GC reports candidates without
deleting remote objects.

<span id="log" data-td-print-local></span>
<span id="log-export-is-not-an-envelope" data-td-print-local></span>

## Operation logs

`log` returns `repository` and `operations[]`, newest first. `log ID` returns `repository`
and `detail`, with `operation`, `duration_ms`, `events`, `packages`, `memberships`, and `files`.

| Detail array | Record fields |
|---|---|
| `events` | `sequence`, `state`, `detail_json`, `occurred_at` |
| `packages` | `sequence`, `input_path`, `disposition`; optional `package_sha256`, `coordinate`, `error_class`, `message`, `dists` |
| `memberships` | `sequence`, `dist`, `package_sha256`, `action` |
| `files` | `sequence`, `action`, `phase`, `path`; optional `size`, `sha256` |

`payload_json`, `result_json`, and event `detail_json` are strings containing JSON.
New metadata-building operations include `publication_time` in `payload_json`. Older journals and layout migrations can omit it.
Parse these JSON strings separately when needed:

```bash
sow log -r demo --json \
  | jq '.result.operations[] | .payload_json | fromjson'
```

`log prune` returns `operation`, `repository`, `before`, `pruned`, and
`compaction_deferred`. A date-only argument is resolved in the machine's local timezone;
`before` contains the resolved timestamp.

`log export` writes one complete operation record per line, without the envelope:

```bash
sow log export operations.jsonl -r demo
sow log export - -r demo
```

A file target must be new and its immediate parent must be a real directory, not a symlink.

<span id="a-worked-example" data-td-print-local></span>

## Use a validation result in a script

```bash
#!/usr/bin/env bash
set -euo pipefail
sow check -r demo --json | jq -e '.ok' >/dev/null
sow changes 0 -r demo --json \
  | jq -r '.result.changes[] | [.phase, .op, .path] | @tsv'
```

This checks the local repository and prints its current file manifest. To publish it,
run `sow publish TARGET` for the configured target.

<span id="see-also" data-td-print-local></span>
