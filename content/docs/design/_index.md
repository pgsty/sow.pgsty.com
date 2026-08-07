---
title: "Design"
linkTitle: "Design"
description: "The architectural decisions behind SOW: ownership, repository layout, publication, compatibility, and version evolution."
url: "/docs/design/"
weight: 350
icon: fa-solid fa-compass-drafting
---

This section records the reasoning that should survive an implementation rewrite: where
SOW draws ownership boundaries, which invariants make a repository safe to copy and
publish, and why a compatibility choice was accepted or rejected.

{{% alert title="Version boundary" color="warning" %}}
The operational guides and CLI reference on this site describe the released **v0.2.0**
line. These design pages also document the implemented **0.3 development** architecture.
They label the boundary explicitly; a development design is not a release or compatibility
claim.
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
Why 0.3 keeps one canonical package path per Repository while rendering metadata-only
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
{{< doc-card title="Design Evolution" link="/docs/design/evolution/" >}}
How the V1 experiment, v0.2 C2 hardlink layout, and 0.3 single-payload layout relate —
including the decision that 0.3 deliberately reverses.
{{< /doc-card >}}
{{< /doc-cards >}}

## Authority and evidence

These pages are the maintained design authority. Historical PRDs, review transcripts,
ADRs, and dated acceptance reports are preserved in the source repository's sealed
archive. They remain evidence for the version and environment they name, but they do not
silently redefine the current product.

A claim progresses through distinct layers:

```text
design contract -> source implementation -> focused tests -> real client/provider evidence -> release
```

Passing an earlier layer never implies that a later one passed. The
[compatibility design](/docs/design/compatibility/) and each release note state the highest
verified layer explicitly.
