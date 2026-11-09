---
title: "Reference"
linkTitle: "Reference"
description: "Look up configuration, package references, file paths, command results, and troubleshooting steps."
categories: [Reference]
tags: [config, cli]
url: "/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

Use these pages to look up configuration fields, package references, file paths, and
script interfaces. For command syntax, see [Commands](/docs/command/) or run
`sow help COMMAND`.

- [**Configuration** — Fields, defaults, validation rules, signing references, and publication targets in `sow.yml`.](/docs/reference/config/)
- [**Package references** — Select packages by digest, coordinate, filename, or name, and resolve ambiguous matches.](/docs/reference/package-ref/)
- [**Repository layout** — Locate package files, indexes, private state, and publication output.](/docs/reference/layout/)
- [**Exit codes** — Interpret command results and choose the next action in scripts.](/docs/reference/exit-codes/)
- [**JSON output** — Read the `sow.cli/v1` response and command result fields.](/docs/reference/json/)
- [**Platforms and integrations** — Check supported systems, filesystems, client formats, and integration coverage.](/docs/reference/compatibility/)
- [**Troubleshooting** — Find the next step for configuration, build, signing, and publication errors.](/docs/reference/troubleshooting/)
{.cards}

<span id="conventions" data-td-print-local></span>

## Example conventions

Command blocks omit the shell prompt so you can copy them. Uppercase words such as `NAME`
and `DIR` in syntax descriptions are placeholders. Square brackets mean optional arguments;
`...` means repeatable arguments; `|` separates alternatives.

Output paths, IDs, hashes, timestamps, and counts depend on the workspace. Keep operation
and generation IDs as strings; see [JSON output](/docs/reference/json/).
