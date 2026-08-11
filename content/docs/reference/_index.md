---
title: "Reference"
linkTitle: "Reference"
description: "Configuration schema, package references, on-disk layout, exit codes, JSON output, platforms, and integrations."
url: "/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

This section is the stable contract for configuration fields, package references, paths,
exit codes, JSON, platforms, and integrations. CLI syntax and state transitions live in
[Commands](/docs/command/); use [Get Started](/docs/start/) for the operating model.

Output examples show shape; identifiers, paths, hashes, timestamps, and counts vary by
workspace. The built-in `sow help` remains the exact syntax authority.

{{< doc-cards cols="2" >}}
{{< doc-card title="sow.yml Reference" link="/docs/reference/config/" >}}
The complete configuration schema: workspace, repository, distribution, membership
policy, signing, and publication targets.
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
The seven exit codes and what each one means.
{{< /doc-card >}}
{{< doc-card title="JSON Output" link="/docs/reference/json/" >}}
The `sow.cli/v1` envelope, the meaning of each top-level field, and result shapes for the
primary command families.
{{< /doc-card >}}
{{< doc-card title="Platforms & Integrations" link="/docs/reference/compatibility/" >}}
Release targets, filesystem requirements, repository-client checks, publication Providers,
and the exact scope of each automated integration.
{{< /doc-card >}}
{{< /doc-cards >}}

## Conventions

Command examples are written without a `$` prompt so you can copy a whole block. Output
blocks are representative; variable values and long structures may be shortened where
marked. The built-in `sow help` remains the exact syntax authority shipped with a binary.

Placeholders in syntax blocks are uppercase (`NAME`, `DIR`, `PACKAGE`); literal text is
lowercase. Square brackets mark optional arguments, `...` marks a repeatable one, and a
vertical bar separates alternatives — the same convention `sow help` uses.
