---
title: "SOW Documentation"
linkTitle: "Documentation"
description: "Create and manage APT / YUM package repositories with a single self-contained binary."
url: "/docs/"
weight: 1
type: docs
icon: fa-solid fa-book
sidebar_expanded: true
---

SOW 0.2.0 is a self-contained package repository manager built by
[Pigsty](https://pigsty.io). One Go executable creates RPM/YUM and DEB/APT repository
metadata; no repository daemon or metadata toolchain is required.

It operates in two isolated modes:

- **Plain mode** — `sow create` indexes the top-level RPM and DEB files in one directory,
  in place.
- **Managed mode** — a workspace with Debian-style package pools, per-architecture views,
  signing, membership policy, transactional generations, auditing, and publication targets.

{{< doc-cards cols="2" >}}
{{< doc-card title="Getting Started" link="/docs/start/" >}}
Install SOW, build your first flat repository in five minutes, and learn the core concepts.
{{< /doc-card >}}
{{< doc-card title="Tutorials" link="/docs/tutorial/" >}}
End-to-end walkthroughs: YUM and APT repositories, GPG signing, serving with Nginx, and
publishing a verified public tree.
{{< /doc-card >}}
{{< doc-card title="Features" link="/docs/feature/" >}}
How SOW works: the Plain and Managed engines, package pools and architecture views,
membership policy, signing, transactions, and auditing.
{{< /doc-card >}}
{{< doc-card title="Design" link="/docs/design/" >}}
Architecture and decision records: ownership, the v0.2.0 single-payload model,
publication, recovery, and compatibility boundaries.
{{< /doc-card >}}
{{< doc-card title="Command" link="/docs/command/" >}}
One page per top-level command: syntax, options, behavior, output, and exit codes.
{{< /doc-card >}}
{{< doc-card title="Reference" link="/docs/reference/" >}}
`sow.yml` schema, package reference grammar, exit codes, JSON contracts, repository
layouts, and compatibility evidence.
{{< /doc-card >}}
{{< /doc-cards >}}

## Where to begin

| If you want to… | Read |
|---|---|
| Get a repository online right now | [Quick Start](/docs/start/quickstart/) |
| Understand the mental model first | [Core Concepts](/docs/start/concepts/) |
| Build a Managed YUM / APT repository | [Tutorials](/docs/tutorial/) |
| Understand the ownership and publication model | [Design](/docs/design/) |
| Look up command syntax and behavior | [Command](/docs/command/) |
| Look up a config field or data contract | [Reference](/docs/reference/) |
