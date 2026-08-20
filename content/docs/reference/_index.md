---
title: "Reference"
linkTitle: "Reference"
description: "Configuration schema, package references, on-disk layout, exit codes, JSON output, and compatibility evidence."
url: "/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

This section covers stable data and interface contracts: "what fields may appear in
`sow.yml`", "what does exit code 5 mean", and "which file lands where" — precisely,
without a narrative around it. Command syntax and behavior live in the separate
[Command manual](/docs/command/). If you are trying to learn
how SOW works, start with [Getting Started](/docs/start/) or [Features](/docs/feature/)
instead; those pages explain the model, and link back here for the details.

Syntax and configuration rules on these pages are checked against the v0.2.0 binary and
its strict parser. Output examples illustrate shape; identifiers, paths, hashes, and
counts vary with the workspace.

{{< cards >}}
{{< card title="sow.yml Reference" link="/docs/reference/config/" >}}
The complete configuration schema: workspace, repository, distribution, membership
policy, signing, and publication targets.
{{< /card >}}
{{< card title="Package References" link="/docs/reference/package-ref/" >}}
The five ways to name a package on the command line, how ambiguity is resolved, and
which forms `rm`, `show`, and `where` accept.
{{< /card >}}
{{< card title="Repository Layout" link="/docs/reference/layout/" >}}
Every path SOW creates in plain and managed mode, the pool grouping rule, name
constraints, and which directories must never be exposed over HTTP.
{{< /card >}}
{{< card title="Exit Codes" link="/docs/reference/exit-codes/" >}}
The seven exit codes and what each one means.
{{< /card >}}
{{< card title="JSON Output" link="/docs/reference/json/" >}}
The `sow.cli/v1` envelope, the meaning of each top-level field, and result shapes for the
primary command families.
{{< /card >}}
{{< card title="Compatibility" link="/docs/reference/compatibility/" >}}
The exact current build, client, Provider, and filesystem evidence, including what is not
yet established.
{{< /card >}}
{{< /cards >}}

## Conventions used on these pages

Command examples are written without a `$` prompt so you can copy a whole block. Output
blocks are representative of v0.2.0; identifiers, timestamps, hashes, counts, and paths
vary, and long structures may be shortened where marked. The built-in `sow help` remains
the exact syntax authority shipped with the binary.

Placeholders in syntax blocks are uppercase (`NAME`, `DIR`, `PACKAGE`); literal text is
lowercase. Square brackets mark optional arguments, `...` marks a repeatable one, and a
vertical bar separates alternatives — the same convention `sow help` uses.
