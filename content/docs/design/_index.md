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

{{% alert title="Current release" color="primary" %}}
All maintained user, reference, and design pages describe **SOW v0.2.0**. The
single-payload layout, publication targets, retention, garbage collection, migration, and
RPM compatibility export are part of that line. Wire identifiers such as `sow.cli/v1` and
configuration schema `sow/v3` are versioned independently from the product release.
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
Why v0.2.0 keeps one canonical package path per Repository while rendering metadata-only
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
How the v0.1.0 experiment, the unreleased C2 prototype, and the current v0.2.0
single-payload layout relate.
{{< /doc-card >}}
{{< /doc-cards >}}

## Authority and evidence

These pages are the maintained design authority. Historical PRDs, review transcripts,
ADRs, and dated acceptance reports remain available through Git history and version tags.
They remain evidence for the revision and environment they name, but they do not silently
redefine the current product.

A claim progresses through distinct layers:

```text
design contract -> source implementation -> focused tests -> real client/provider evidence -> release
```

Passing an earlier layer never implies that a later one passed. The
[compatibility design](/docs/design/compatibility/) and each release note state the highest
verified layer explicitly.
