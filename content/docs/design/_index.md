---
title: "Design"
linkTitle: "Design"
description: "The architectural decisions behind SOW 0.2.0: ownership, layout, publication, recovery, and compatibility."
url: "/docs/design/"
weight: 350
icon: fa-solid fa-compass-drafting
---

This section records the reasoning that should survive an implementation rewrite: where
SOW draws ownership boundaries, which invariants make a repository safe to copy and
publish, and why a compatibility choice was accepted or rejected.

{{% alert title="Current release" color="primary" %}}
All maintained pages describe **SOW v0.2.0**. The configuration schema is `sow/v3`;
wire identifiers such as `sow.cli/v1` are protocol identifiers, not product versions.
{{% /alert %}}

{{< doc-cards cols="2" >}}
{{< doc-card title="Design Principles" link="/docs/design/principles/" >}}
The small set of invariants that decide what SOW owns, what can be rebuilt, and what must
fail closed.
{{< /doc-card >}}
{{< doc-card title="System Model" link="/docs/design/model/" >}}
Workspace, Repository, Dist, Package Object, Membership, Generation, and publication
target — and why each has a separate owner.
{{< /doc-card >}}
{{< doc-card title="Single-Payload Layout" link="/docs/design/single-payload/" >}}
Why one canonical package path per Repository feeds metadata-only
APT and RPM views.
{{< /doc-card >}}
{{< doc-card title="Publication & Recovery" link="/docs/design/publication/" >}}
Pointer-last publication, commit intent, forward recovery, retained generations, and
evidence-gated garbage collection.
{{< /doc-card >}}
{{< doc-card title="Compatibility Boundaries" link="/docs/design/compatibility/" >}}
Separate protocol, client, mirror-tool, filesystem, HTTP, and object-storage compatibility
instead of hiding them behind one green check mark.
{{< /doc-card >}}
{{< /doc-cards >}}

## Authority and evidence

These pages describe the current contract. A claim should name the evidence layer it has
actually reached:

```text
design -> implementation -> focused tests -> real client/provider run -> release artifact
```

Passing one layer does not imply the next. The [compatibility reference](/docs/reference/compatibility/)
states the current evidence without upgrading adjacent tests into product claims.
