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

SOW is a self-contained package repository manager built by [Pigsty](https://pigsty.io).
It ships as one static Go binary that creates and maintains **APT (DEB)** and **YUM (RPM)**
repositories on Linux and macOS — no `createrepo_c`, no `dpkg-scanpackages`, no `reprepro`,
no daemon.

It operates in two isolated modes:

- **Plain mode** — `sow create` turns any directory of `.rpm` / `.deb` files into a flat,
  servable repository, deterministically and in place.
- **Managed mode** — a workspace with Debian-style package pools, per-architecture views,
  GPG signing, membership policies, transactional builds, and a full audit trail.

{{< doc-cards cols="2" >}}
{{< doc-card title="Getting Started" link="/docs/start/" >}}
Install SOW, build your first flat repository in five minutes, and learn the core concepts.
{{< /doc-card >}}
{{< doc-card title="Tutorials" link="/docs/tutorial/" >}}
End-to-end walkthroughs: YUM and APT repositories, GPG signing, serving with Nginx, and
migrating from createrepo_c or reprepro.
{{< /doc-card >}}
{{< doc-card title="Features" link="/docs/feature/" >}}
How SOW works: the Plain and Managed engines, package pools and architecture views,
membership policy, signing, transactions, and auditing.
{{< /doc-card >}}
{{< doc-card title="Design" link="/docs/design/" >}}
Architecture and decision records: ownership, the v0.2.0 single-payload model,
publication, compatibility boundaries, and the evolution from v0.1.0.
{{< /doc-card >}}
{{< doc-card title="Reference" link="/docs/reference/" >}}
Complete CLI reference, `sow.yml` configuration, package reference grammar, exit codes,
repository layouts, and the compatibility matrix.
{{< /doc-card >}}
{{< /doc-cards >}}

## Where to begin

| If you want to… | Read |
|---|---|
| Get a repository online right now | [Quick Start](/docs/start/quickstart/) |
| Understand the mental model first | [Core Concepts](/docs/start/concepts/) |
| Build a production YUM / APT repository | [Tutorials](/docs/tutorial/) |
| Understand architectural decisions and version boundaries | [Design](/docs/design/) |
| Replace an existing createrepo_c / reprepro pipeline | [Migration guide](/docs/tutorial/migration/) |
| Look up a command or config field | [Reference](/docs/reference/) |
