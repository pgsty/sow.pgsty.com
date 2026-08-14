---
title: "Design"
linkTitle: "Design"
description: "The durable decisions behind SOW: ownership, state, publication ordering, recovery, and evidence."
url: "/docs/design/"
weight: 350
icon: fa-solid fa-compass-drafting
---

This section records SOW's ownership boundaries and the invariants that make a repository
safe to build, copy, publish, recover, and collect.

{{< doc-cards cols="2" >}}
{{< doc-card title="Design Principles" link="/docs/design/principles/" >}}
The small set of invariants that decide what SOW owns, what can be rebuilt, and what must
fail closed.
{{< /doc-card >}}
{{< doc-card title="System Model" link="/docs/design/model/" >}}
Workspace, Repository, Dist, Package Object, Membership, Generation, and publication
target — and why each has a separate owner.
{{< /doc-card >}}
{{< doc-card title="Publication & Recovery" link="/docs/design/publication/" >}}
Pointer-last publication, commit intent, forward recovery, retained generations, and
evidence-gated garbage collection.
{{< /doc-card >}}
{{< doc-card title="Coordinated Publication Proposal" link="/docs/design/coordinated-publication/" >}}
The proposed v0.4.0 user workflow and implementation plan for SOW-orchestrated,
rclone-executed publication and deterministic interruption recovery.
{{< /doc-card >}}
{{< /doc-cards >}}

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
