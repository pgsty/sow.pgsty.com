---
title: "Reference"
linkTitle: "Reference"
description: "Command syntax, configuration schema, on-disk layout, exit codes, JSON output, and the tested compatibility matrix."
url: "/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

This section is the lookup half of the documentation. It answers "what exactly does this
flag do", "what fields may appear in `sow.yml`", "what does exit code 5 mean", and "which
file lands where" — precisely, without a narrative around it. If you are trying to learn
how SOW works, start with [Getting Started](/docs/start/) or [Features](/docs/feature/)
instead; those pages explain the model, and link back here for the details.

Everything on these pages is derived from the shipping binary. Command output is
transcribed from real runs of `sow 0.2.0-dev`, and configuration rules match the strict
parser, not an aspirational schema.

{{< doc-cards cols="2" >}}
{{< doc-card title="CLI Commands" link="/docs/reference/cli/" >}}
Every command, its arguments, the global options they accept, and the discovery and
selection rules that decide which repository and distribution they act on.
{{< /doc-card >}}
{{< doc-card title="sow.yml Reference" link="/docs/reference/config/" >}}
The complete configuration schema: workspace, repository, distribution, membership
policy, and the signing tree — including key reference syntax and validation rules.
{{< /doc-card >}}
{{< doc-card title="Package References" link="/docs/reference/package-ref/" >}}
The five ways to name a package on the command line, how ambiguity is resolved, and
which forms `rm`, `show`, and `where` accept.
{{< /doc-card >}}
{{< doc-card title="Repository Layout" link="/docs/reference/layout/" >}}
Every path SOW creates in plain and managed mode, the pool grouping rule, name
constraints, and which directories must never be exposed over HTTP.
{{< /doc-card >}}
{{< doc-card title="Exit Codes" link="/docs/reference/exit-codes/" >}}
The seven exit codes, what each one means, and a reproducible command that triggers it.
{{< /doc-card >}}
{{< doc-card title="JSON Output" link="/docs/reference/json/" >}}
The `sow.cli/v1` envelope, the meaning of each top-level field, and the result shape of
every command that produces data.
{{< /doc-card >}}
{{< doc-card title="Compatibility" link="/docs/reference/compatibility/" >}}
Which package managers were tested against SOW-built repositories, which platforms the
binary runs on, and the filesystem constraints you must respect.
{{< /doc-card >}}
{{< /doc-cards >}}

## Conventions used on these pages

Command examples are written without a `$` prompt so you can copy a whole block. When a
transcript shows both input and output, the command line comes first and the output
follows directly, exactly as the binary printed it. Where output was shortened to keep a
page readable, it says so.

Placeholders in syntax blocks are uppercase (`NAME`, `DIR`, `PACKAGE`); literal text is
lowercase. Square brackets mark optional arguments, `...` marks a repeatable one, and a
vertical bar separates alternatives — the same convention `sow help` uses.
