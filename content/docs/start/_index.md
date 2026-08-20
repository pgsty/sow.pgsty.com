---
title: "Getting Started"
linkTitle: "Getting Started"
description: "Install SOW, create a repository, and learn the v0.2.0 operating model."
url: "/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW is one self-contained binary for RPM/YUM and DEB/APT repositories. It builds static files;
an HTTP server or object-storage endpoint serves them.

Choose one execution path. `sow create` writes flat indexes beside packages in a normal
directory. Managed commands operate on a workspace with a package pool, named Dists,
architecture views, policy, signing, generations, audit, and publication targets. The
two paths do not share state.

The pages below cover installation, each execution path, and the model behind them.

{{< cards >}}
{{< card title="Installation" link="/docs/start/install/" >}}
Download a prebuilt binary or build from source. Covers the release build targets and
optional features that use external tools.
{{< /card >}}
{{< card title="Quick Start" link="/docs/start/quickstart/" >}}
Turn a directory of packages into a flat repository, serve it over HTTP,
and install from it with `dnf` or `apt`.
{{< /card >}}
{{< card title="First Workspace" link="/docs/start/workspace/" >}}
Create a workspace, add a repository with an RPM and a DEB distribution,
add packages, and inspect the pool and the published tree.
{{< /card >}}
{{< card title="Core Concepts" link="/docs/start/concepts/" >}}
The mental model: Workspace, Repository, Dist, Architecture View, and the difference
between Desired Membership and a Built Generation.
{{< /card >}}
{{< /cards >}}

## What you need

A Linux or macOS machine on `amd64` or `arm64`, a local POSIX filesystem for managed
workspaces, and enough space for package payloads and staging.

Metadata generation is in-process. Optional RPM package signing needs `rpm`; an
`agent://` metadata key needs `gpg` and `gpg-agent`. See [Installation](/docs/start/install/).

## Where to go next

| If you want to… | Read |
|---|---|
| Index a directory of packages | [Quick Start](/docs/start/quickstart/) |
| Curate a long-lived repository | [First Workspace](/docs/start/workspace/) |
| Understand pools, views, and generations | [Core Concepts](/docs/start/concepts/) |
| Build a Managed YUM or APT repository | [Tutorials](/docs/tutorial/) |
| Look up a flag, field, or exit code | [Reference](/docs/reference/) |
