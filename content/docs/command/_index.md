---
title: "Commands"
linkTitle: "Commands"
description: "Complete SOW CLI syntax, options, behavior, output, and exit codes."
url: "/docs/command/"
aliases:
  - "/docs/reference/cli/"
  - "/docs/reference/cli/query/"
  - "/docs/reference/cli/build/"
  - "/docs/reference/cli/publication/"
weight: 450
icon: fa-solid fa-terminal
---

Each top-level command has its own page. Command groups
such as `config`, `repo`, `dist`, `retain`, `export`, and `log` document their subcommands together.

The built-in `sow help` output is the syntax authority. These pages add selection rules, state
transitions, output contracts, failure behavior, and practical examples.

## Command index

`sow create` is the Plain-mode repository command and operates directly on a directory. `sow init`
bootstraps Managed mode and may create `sow.yml`; the remaining stateful commands discover an
existing Workspace. `help` and `version` are utility commands and need neither mode.

| Command | Mode | Purpose |
|---|---|---|
| [`sow create [DIR]`](/docs/command/create/) | Plain | Generate a flat RPM/DEB repository in place |
| [`sow init [DIR]`](/docs/command/init/) | Managed | Initialize a Workspace and converge declared Repositories/Dists |
| [`sow config check\|show`](/docs/command/config/) | Managed | Validate or print the effective configuration |
| [`sow repo ls\|new\|show\|migrate\|rm`](/docs/command/repo/) | Managed | Manage Repositories; `migrate` is specialized maintenance |
| [`sow dist ls\|new\|show\|rm`](/docs/command/dist/) | Managed | Manage Dists |
| [`sow add PATH...`](/docs/command/add/) | Managed | Add packages to Desired Membership |
| [`sow rm PACKAGE...`](/docs/command/rm/) | Managed | Remove packages from Desired Membership |
| [`sow ls`](/docs/command/ls/) | Managed | List Desired and Built Membership |
| [`sow show PACKAGE`](/docs/command/show/) | Managed | Inspect one Package Object |
| [`sow where PACKAGE`](/docs/command/where/) | Managed | Locate a Package Object across the Workspace |
| [`sow status`](/docs/command/status/) | Managed | Read Repository state without deep verification |
| [`sow build`](/docs/command/build/) | Managed | Converge Desired state into a Built Generation |
| [`sow check`](/docs/command/check/) | Managed | Verify configuration, state, bytes, views, signatures, and manifest |
| [`sow changes [BASE_GENERATION]`](/docs/command/changes/) | Managed | Diff Built Generations as a file delivery plan |
| [`sow publish TARGET`](/docs/command/publish/) | Managed | Publish a verified Generation to a configured target |
| [`sow retain add\|ls\|rm`](/docs/command/retain/) | Managed | Manage explicit retained-Generation roots |
| [`sow gc [TARGET]`](/docs/command/gc/) | Managed | Collect unreachable local payloads or maintain a publication target |
| [`sow export rpm-leaf`](/docs/command/export/) | Managed | Build a standalone RPM compatibility leaf |
| [`sow log [OPERATION]`](/docs/command/log/) | Managed | Read, export, and prune the Operation audit ledger |

## Global syntax

```text
sow [OPTIONS] COMMAND [ARGS]
```

Running `sow` with no arguments prints the command list and exits `0`. Use `sow help COMMAND` or
`sow help COMMAND SUBCOMMAND` for built-in usage. `sow version` and `sow --version` print the binary
identity.

There is no global `--format`, `--yes`, `--dry-run`, `-q`, `-v`, or `--config`. Unknown flags are
usage errors.

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

Other commands deliberately differ:

- `build`, `check`, and `status` default to all Dists when `-d` is absent;
- `show` searches the whole selected Repository unless `-d` narrows it;
- `where` searches all matching Dists across the Workspace unless `-r`/`-d` narrow it;
- `changes` is Repository-wide and rejects `-d`.

## Locking

Write commands other than `init` accept `-T/--timeout DUR` and `-N/--no-wait`. `init` takes the
Workspace lock and waits without a CLI timeout override. Other locks are Repository-scoped except
for `repo new` and `repo rm`, which also use the Workspace lock. `--timeout 0` waits indefinitely;
a positive timeout uses Go duration syntax such as `500ms`, `30s`, or `5m`. `--no-wait` fails
immediately. A positive timeout and `--no-wait` are mutually exclusive. Lock acquisition failure
exits `4`.

Read-only commands take no write lock. `status` still reports whether a writer holds the Repository
lock.

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

Some commands print command-specific structured JSON without `--json` when a compact representation
would lose useful detail. The individual command page states that behavior; `--json` always selects
the standard envelope.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success or idempotent no-op |
| `1` | Runtime I/O, parser, renderer, signing, or transport error |
| `2` | Usage, Workspace discovery, or configuration error |
| `3` | Partial batch success |
| `4` | Write lock unavailable |
| `5` | Integrity/recovery failure, or `check` ruling the tree not deliverable |
| `6` | Expected rejection: conflict, protected object, no match, or incompatible architecture |

See [Exit Codes](/docs/reference/exit-codes/) for command-specific triggers.
