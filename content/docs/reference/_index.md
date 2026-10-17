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

{{< cards >}}
{{< card title="Configuration" link="/docs/reference/config/" >}}
Fields, defaults, validation rules, signing references, and publication targets in `sow.yml`.
{{< /card >}}
{{< card title="Package references" link="/docs/reference/package-ref/" >}}
Select packages by digest, coordinate, filename, or name. Resolve ambiguous matches.
{{< /card >}}
{{< card title="Repository layout" link="/docs/reference/layout/" >}}
Locate package files, indexes, private state, and publication output.
{{< /card >}}
{{< card title="Exit codes" link="/docs/reference/exit-codes/" >}}
Interpret command results and choose the next action in scripts.
{{< /card >}}
{{< card title="JSON output" link="/docs/reference/json/" >}}
Read the `sow.cli/v1` response and command result fields.
{{< /card >}}
{{< card title="Platforms and integrations" link="/docs/reference/compatibility/" >}}
Check supported systems, filesystems, client formats, and integration coverage.
{{< /card >}}
{{< card title="Troubleshooting" link="/docs/reference/troubleshooting/" >}}
Find the next step for configuration, build, signing, and publication errors.
{{< /card >}}
{{< /cards >}}

<span id="conventions" data-td-print-local></span>

## Example conventions

Command blocks omit the shell prompt so you can copy them. Uppercase words such as `NAME`
and `DIR` in syntax descriptions are placeholders. Square brackets mean optional arguments;
`...` means repeatable arguments; `|` separates alternatives.

Output paths, IDs, hashes, timestamps, and counts depend on the workspace. Keep operation
and generation IDs as strings; see [JSON output](/docs/reference/json/).
