---
title: "Commands"
linkTitle: "Commands"
description: "SOW command syntax, options, selection rules, and exit codes."
categories: [Command]
tags: [cli]
url: "/docs/command/"
aliases:
  - "/docs/reference/cli/"
  - "/docs/reference/cli/query/"
  - "/docs/reference/cli/build/"
  - "/docs/reference/cli/publication/"
weight: 450
icon: fa-solid fa-terminal
search_keywords: [cli, command reference, sow help, options, subcommands]
search_boost: 1.5
---

Use these pages for command syntax, selection rules, results, and examples. Run `sow help COMMAND` or `sow help COMMAND SUBCOMMAND` to check the options in your installed version.

## Command index

`sow create` builds a flat repository directly in a directory. To manage packages in a Workspace, start with `sow init`. All other Managed commands use an existing Workspace. `help` and `version` can run anywhere.

| Command | Mode | Purpose |
|---|---|---|
| [`sow create [DIR]`](/docs/command/create/) | Plain | Generate a flat RPM/DEB repository in place |
| [`sow init [DIR]`](/docs/command/init/) | Managed | Initialize a Workspace and create declared Repositories/Dists |
| [`sow config check\|show`](/docs/command/config/) | Managed | Validate or print the effective configuration |
| [`sow repo ls\|new\|show\|migrate\|rm`](/docs/command/repo/) | Managed | Create, inspect, upgrade, or remove Repositories |
| [`sow dist ls\|new\|show\|rm`](/docs/command/dist/) | Managed | Manage Dists |
| [`sow add PATH...`](/docs/command/add/) | Managed | Add packages and rebuild indexes |
| [`sow rm PACKAGE...`](/docs/command/rm/) | Managed | Remove packages and rebuild indexes |
| [`sow ls`](/docs/command/ls/) | Managed | List Desired packages with their Built locations |
| [`sow show PACKAGE`](/docs/command/show/) | Managed | Inspect one package |
| [`sow where PACKAGE`](/docs/command/where/) | Managed | Find a package across the Workspace |
| [`sow status`](/docs/command/status/) | Managed | Show Repository state and pending changes |
| [`sow build`](/docs/command/build/) | Managed | Build a Generation from Desired state |
| [`sow check`](/docs/command/check/) | Managed | Verify a Repository before delivery |
| [`sow changes [BASE_GENERATION]`](/docs/command/changes/) | Managed | Compare files in two Built Generations |
| [`sow publish TARGET`](/docs/command/publish/) | Managed | Publish a verified Generation to a configured target |
| [`sow retain add\|ls\|rm`](/docs/command/retain/) | Managed | Protect a Generation’s package files from local GC |
| [`sow gc [TARGET]`](/docs/command/gc/) | Managed | Reclaim unused local packages or maintain a publication target |
| [`sow export rpm-leaf`](/docs/command/export/) | Managed | Export a standalone RPM repository |
| [`sow log [OPERATION]`](/docs/command/log/) | Managed | Read, export, and prune operation records |

## Global syntax

```text
sow [OPTIONS] COMMAND [ARGS]
```

Running `sow` with no arguments prints the command list and exits `0`. Use `sow help COMMAND` or
`sow help COMMAND SUBCOMMAND` for built-in usage. `sow version` and `sow --version` print version and build information.

Options apply only to the commands that list them. Use `--` before a positional argument that starts with `-`. Unknown or repeated single-value options return exit code `2`.

## Workspace discovery

Managed commands find the nearest ancestor containing `sow.yml`:

1. Start at `-C/--workdir DIR`, when supplied; otherwise start at the current directory.
2. Search upward and stop at the first `sow.yml`.
3. If that search finds nothing, repeat from `SOW_DIR` when set. An explicit `-C` suppresses the
   current-directory candidate, but not the `SOW_DIR` fallback.
4. If no Workspace is found, exit `2`.

`--workdir` changes only the discovery start directory. It does not change the process working
directory, so relative positional paths still resolve against the actual current directory.

`sow create` never performs Workspace discovery.

## Repository selection

Commands that require one Repository select it in this order:

1. explicit `-r/--repo NAME`;
2. the Repository containing the discovery start directory;
3. the only Repository in the Workspace;
4. otherwise fail with exit `2` and list the candidates.

`repo new` and `repo rm` take `NAME` positionally and do not accept `-r`. `sow where` searches all
Repositories by default; `-r` narrows its scope. Publication targets select their configured
Repository, so `publish TARGET` and `gc TARGET` do not accept an additional Repository selection.

## Dist selection

`add`, `rm`, and `ls` require a concrete Dist set and select it in this order:

1. repeated `-d/--dist NAME` values;
2. the Dist containing the discovery start directory;
3. the only Dist in the selected Repository;
4. otherwise fail with exit `2` and list the candidates.

Other commands use these defaults:

- `build`, `check`, and `status` default to all Dists when `-d` is absent;
- `show` searches the whole selected Repository unless `-d` narrows it;
- `where` searches all matching Dists across the Workspace unless `-r`/`-d` narrow it;
- `changes` is Repository-wide and rejects `-d`.

## Locking

`create` locks its target directory. Managed mutations coordinate through Workspace and Repository locks. `init` waits for its locks without a CLI timeout option.

Other write commands accept `-T/--timeout DUR` and `-N/--no-wait`. The default `--timeout 0` waits indefinitely. Positive durations use `ms`, `s`, `m`, or `h`, for example `500ms`, `30s`, or `5m`. `--no-wait` fails immediately if a lock is held. It cannot be combined with a positive timeout. Lock acquisition failure returns `4`.

Most read-only Managed commands use shared locks and wait for a conflicting writer. They do not accept lock wait options. `status` normally probes the Repository lock so you can inspect an active writer. Cancel a waiting command with Ctrl-C.

## Parallelism

`-j/--jobs N` is available only where SOW parses packages, hashes bytes, renders indexes, or verifies
state: `create`, `add`, `rm`, `build`, `check`, and `repo migrate`. It defaults to the logical CPU
count and must be at least `1`.

## JSON output

Commands with `--json` emit one versioned envelope on stdout; diagnostics remain on stderr:

```json
{
  "schema": "sow.cli/v1",
  "command": "add",
  "ok": true,
  "repository": "demo",
  "operation": "1430722512865805553",
  "result": {},
  "errors": []
}
```

`ok` is false for every non-zero exit. A partial batch still returns its committed and failed items.
See [JSON Output](/docs/reference/json/) for complete result shapes.

Use text output for interactive work and `--json` for scripts. `config show` prints YAML by default. `log export` is the exception: it writes JSONL directly and does not accept `--json`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success or idempotent no-op |
| `1` | Runtime I/O, parser, renderer, signing, or transport error |
| `2` | Usage, Workspace discovery, or configuration error |
| `3` | Partial batch success |
| `4` | Write lock unavailable |
| `5` | Integrity/recovery failure, or `check` ruling the tree not deliverable |
| `6` | Rejected operation: conflict, protected object, no match, or incompatible architecture |
| `130` | Command interrupted by SIGINT or SIGTERM |

See [Exit Codes](/docs/reference/exit-codes/) for command-specific triggers.
