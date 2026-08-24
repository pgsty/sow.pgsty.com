---
title: "Design"
linkTitle: "Design"
description: "The durable decisions behind SOW: ownership, state, publication ordering, recovery, and evidence."
categories: [Design]
tags: [managed, publish, transaction]
url: "/docs/design/"
weight: 350
icon: fa-solid fa-compass-drafting
---

This section records SOW's ownership boundaries and the invariants that make a repository
safe to build, copy, publish, recover, and collect.

{{< cards >}}
{{< card title="Design Principles" link="/docs/design/principles/" >}}
The small set of invariants that decide what SOW owns, what can be rebuilt, and what must
fail closed.
{{< /card >}}
{{< card title="System Model" link="/docs/design/model/" >}}
Workspace, Repository, Dist, Package Object, Membership, Generation, and publication
target — and why each has a separate owner.
{{< /card >}}
{{< card title="Publication & Recovery" link="/docs/design/publication/" >}}
Pointer-last publication, commit intent, forward recovery, retained generations, and
evidence-gated garbage collection.
{{< /card >}}
{{< card title="Coordinated Publication Decision" link="/docs/design/coordinated-publication/" >}}
Why v0.4.0 kept SOW's native providers, which hardening shipped, and which earlier rclone
proposal surfaces are not product commands.
{{< /card >}}
{{< /cards >}}

The canonical one-payload layout is documented with the mechanism in
[Pool & Metadata Views](/docs/feature/views/). Platform and integration requirements live
in [Platforms & Integrations](/docs/reference/compatibility/).

## Authority and evidence

Each operational claim should match the evidence layer it has actually reached:

```text
design -> implementation -> focused tests -> real client/provider run -> release artifact
```

Passing one layer does not imply the next. The [platform and integration reference](/docs/reference/compatibility/)
records the automated client, Provider, and filesystem coverage; release artifacts are a
separate delivery gate.
