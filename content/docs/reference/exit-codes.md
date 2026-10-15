---
title: "Exit Codes"
linkTitle: "Exit Codes"
description: "Exit codes 0–6 and interruption code 130, with meanings and examples."
categories: [Reference]
tags: [cli, output]
url: "/docs/reference/exit-codes/"
weight: 500
icon: fa-solid fa-triangle-exclamation
---

<span id="1--runtime-error" data-td-print-local></span>
<span id="2--usage-discovery-or-configuration" data-td-print-local></span>
<span id="6--expected-rejection" data-td-print-local></span>

Use exit codes in scripts and read the diagnostic for the specific cause.
SOW uses the same code meanings across commands.

| Code | Meaning | Next step |
|---|---|---|
| `0` | Success or no-op | Read the result; no-op commands may report `noop: true` |
| `1` | Runtime I/O, package parsing, rendering, or other unclassified error | Correct the reported input or environment problem, then retry |
| `2` | Invalid command, workspace discovery, or configuration | Check `sow help COMMAND`, selection flags, and `sow config check` |
| `3` | Partial success | Inspect the result to identify committed work and failed items |
| `4` | Write lock unavailable | Retry later or use a longer `--timeout` |
| `5` | Integrity/recovery error, or repository not ready for delivery | Inspect `status` and `check`; build a dirty repository or recover the recorded operation |
| `6` | Rejected operation | Correct the conflict, package reference, architecture, signing setting, or protection setting named in the error |
| `130` | Command interrupted by SIGINT or SIGTERM | Follow the recovery procedure for the interrupted operation |

<span id="0--success-or-no-op" data-td-print-local></span>
<span id="5--integrity-recovery-or-not-deliverable" data-td-print-local></span>

## Success does not always mean ready

`status` returns `0` when it can report state, including `dirty`, `recovering`, or `error`.
Its `ready_to_copy` field is a state summary, not a full byte check. Use `check` before
delivery:

```bash
sow build -r demo
sow check -r demo
```

A dirty repository can have consistent old indexes and still fail `check` with code `5`,
because Desired state has not been built. Run `build` and check again.
If the diagnostic reports corrupted bytes or conflicting recovery evidence, inspect that
failure before retrying. See [Troubleshooting](/docs/reference/troubleshooting/).

<span id="3--partial-success" data-td-print-local></span>
<span id="using-them-in-scripts" data-td-print-local></span>

## Partial success

For `add`, code `3` means at least one input was accepted or reused and at least one
failed. The JSON result retains per-input outcomes. Exclusion by policy is not a failed
input. `init` can also return `3` after creating some declared objects and failing on a
later one.

Capture both output and status before deciding whether to continue:

```bash
#!/usr/bin/env bash
set -uo pipefail

sow add ./incoming/ -r demo -d el9 --json > add-result.json
rc=$?
case "$rc" in
  0) ;;
  3) jq '.result.items[] | select(.status == "failed")' add-result.json
     exit 3 ;;
  4) echo 'Repository is busy; retry later.' >&2
     exit 4 ;;
  *) exit "$rc" ;;
esac

sow check -r demo || exit $?
sow publish mirror
```

`mirror` must be a configured target for `demo`. The script stops on partial success so
you can inspect failed inputs before publishing.

<span id="130--interrupted" data-td-print-local></span>
<span id="4--lock-unavailable" data-td-print-local></span>

## Lock waits and interruption

`-T 0` waits for a write lock without a time limit and is the default. `-T 30s` waits up
to 30 seconds. `-N` tries once. Lock contention returns `4`; `-N` combined with a nonzero
`-T` returns `2`.

Read-only commands do not accept these flags. Some take shared locks for a consistent
snapshot; `status` reports repository writer-lock activity without waiting for that writer.

Ctrl-C or SIGTERM returns `130` when SOW handles the interruption. An internal timeout,
such as an upload progress timeout, keeps its normal error class. Interruption does not
undo work that already committed. Inspect the state and follow
[Transactions and recovery](/docs/feature/transactions/) to resume the operation.

## JSON errors

With `--json`, stdout contains the result envelope and stderr contains diagnostics.
The `errors` array uses these classes:

| Code | JSON `class` |
|---|---|
| `1` | `runtime` |
| `2` | `usage`, `discovery`, or `config` |
| `3` | `partial` |
| `4` | `lock` |
| `5` | `integrity` |
| `6` | `rejected` |
| `130` | `interrupted` |

Branch on the code or class, not message text. Plain `create` prints its domain error to
stderr; its JSON message can include an extra CLI category prefix. Diagnostic and partial
results remain available when `ok` is `false`.

See [JSON output](/docs/reference/json/) and
[Transactions and recovery](/docs/feature/transactions/).

<span id="see-also" data-td-print-local></span>
