---
title: "Troubleshooting"
linkTitle: "Troubleshooting"
description: "Find the next command for migration, pending builds, interrupted publication, locks, and integrity errors."
url: "/docs/reference/troubleshooting/"
categories: [Reference]
tags: [cli, recovery, troubleshooting]
weight: 80
icon: fa-solid fa-wrench
---

Start with the error message and the [exit code](/docs/reference/exit-codes/).
For Managed commands, specify the workspace and Repository so you inspect the intended state:

```bash
sow version
sow status -C /srv/sow -r pgsql
sow log -C /srv/sow -r pgsql
```

Replace `/srv/sow`, `pgsql`, and the target name `prod` below with your configuration.

## The database needs migration

SOW 0.6.1 uses schema v13, as do 0.5.0 and 0.6.0. An upgrade from either version needs no schema migration.
For a 0.3 or 0.4 workspace, stop writers and back up the complete workspace. Then run:

```bash
sow repo migrate pgsql -C /srv/sow
sow build -C /srv/sow -r pgsql
sow check -C /srv/sow -r pgsql
```

Repeat this for each Repository. Compatible read-only commands can still inspect an older
schema, but they do not migrate it. See [Upgrade](/docs/start/install/#upgrade-to-061).

## Status shows pending changes

`add --skip`, `rm --skip`, and configuration edits can leave Desired state ahead of Built
state. Apply the pending changes, then check the result:

```bash
sow build -C /srv/sow -r pgsql
sow check -C /srv/sow -r pgsql
```

A local build updates local indexes. To update a configured remote target, also run
`sow publish prod -C /srv/sow`. See [`sow status`](/docs/command/status/) for the state fields.

## A command was interrupted

For Plain mode, resolve the reported input or filesystem issue, then rerun the original
`sow create` command with the same Pigsty, timestamp, and signing options.

For an interrupted `add`, `rm`, Dist change, or build, inspect `sow log` and fix the
reported cause. Run `sow build` for that Repository to complete recovery. Committed Desired
changes remain part of the pending build. For interrupted `init`, `repo new`, or `repo rm`
operations, rerun the corresponding lifecycle command to recover the workspace journal.

For an interrupted publication, restore access to its storage and public endpoint, then
rerun the same target:

```bash
sow publish prod -C /srv/sow
```

SOW resumes the saved attempt. To abandon an attempt before commit intent, use
`sow publish prod --abort -C /srv/sow`. After commit intent, rerun publication to finish it.
See [Publication recovery](/docs/command/publish/).

## Errors after a committed change

Database commit and later maintenance are separate steps. A checkpoint or cleanup error can occur after package membership or a build has committed.
SOW keeps the committed result in command output. It does not report those items as rolled back.

Read the result and `sow status`, then inspect the recorded operation with `sow log`.
Resume the command named in the diagnostic. Keep original input files until you have confirmed the result.

## Target configuration changed

Compare `sow.yml` with the target named in the error. If you intentionally changed its name,
`public_endpoint`, or `max_cache_ttl`, accept the change with:

```bash
sow publish prod --rebind -C /srv/sow
```

A change to the Repository, provider, storage endpoint, region, bucket, or prefix requires
a new target. Complete pending target maintenance before changing its TTL. See
[Target bindings](/docs/command/publish/).

## A command waits for a lock

Another process is using the workspace or Repository. Let that command finish, or stop it
through its normal process controls. Retry your command afterward.

For write commands that support lock options, use `--no-wait` to return immediately when
the lock is busy, or `--timeout 30s` to bound the wait. These options do not apply to `init`
or read commands. Shared-lock reads wait until the writer finishes or you cancel the
command; `status` normally reports the lock state without waiting. Keep the lock files in place: SOW uses their stable paths to coordinate processes.
See [Global options](/docs/command/).

## A package, signature, or path fails validation

Use the named file and the check stage to narrow the cause:

| Error | Action |
|---|---|
| Same Pool path, different bytes | Compare the input with the existing package. Give different content a new package version and file name. Moving it to another input directory does not change its Pool URL. |
| File name differs only by case | Use the already recorded spelling. Case aliases cannot create another Pool URL. |
| Missing or altered Pool file | Restore the original bytes from a matching backup, then rerun `sow check`. |
| Signing key unavailable | Check the configured key, secret-key access, GPG agent, and current key validity. Retry the build after correcting them. |
| RPM does not match the trust policy | Check the package signature and configured public keys. See [Signing](/docs/tutorial/signing/). |
| Public URL returns old content | Check the HTTP root, URL prefix, cache, and `max_cache_ttl`, then retry publication. |

`sow check` reports integrity errors; it does not rewrite damaged data. Keep the reported
path and operation ID when investigating. The [layout reference](/docs/reference/layout/)
explains which files belong to the package Pool, generated indexes, and private state.
