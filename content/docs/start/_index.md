---
title: "Getting Started"
linkTitle: "Getting Started"
description: "Install SOW, publish a working repository in five minutes, and learn the model behind it."
url: "/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW is one static binary that builds APT and YUM repositories. You do not install a
server, you do not install `createrepo_c` or `reprepro`, and you do not configure a
daemon. You drop the binary on a machine, point it at some packages, and copy the
result to any static web server.

There are two ways to use it, and they never touch each other. `sow create` takes a
plain directory of `.rpm` and `.deb` files and writes repository indexes next to them —
that is all it does, and it is the fastest way to get something servable. The managed
workspace is the other path: a package pool, named distributions, per-architecture
views, membership policy, GPG signing, and an audit trail for every change. Start with
the first, move to the second when you need to curate what goes in.

Read these four pages in order and you will have both paths working, with a clear idea
of which one your situation calls for.

{{< doc-cards cols="2" >}}
{{< doc-card title="Installation" link="/docs/start/install/" >}}
Download a prebuilt binary or build from source. Covers the supported platform matrix
and the two commands that need external tools.
{{< /doc-card >}}
{{< doc-card title="Quick Start" link="/docs/start/quickstart/" >}}
Five minutes: turn a directory of packages into a flat repository, serve it over HTTP,
and install from it with `dnf` or `apt`.
{{< /doc-card >}}
{{< doc-card title="First Workspace" link="/docs/start/workspace/" >}}
Ten minutes: create a workspace, add a repository with an RPM and a DEB distribution,
add packages, and inspect the pool and the published tree.
{{< /doc-card >}}
{{< doc-card title="Core Concepts" link="/docs/start/concepts/" >}}
The mental model: Workspace, Repository, Dist, Architecture View, and the difference
between Desired Membership and a Built Generation.
{{< /doc-card >}}
{{< /doc-cards >}}

## What you need

A Linux or macOS machine on `amd64` or `arm64`, and enough free space for the packages
you plan to publish. Nothing else — SOW parses RPM headers and Debian control files
itself and writes the indexes in-process.

Two operations do shell out to the environment: signing RPM package payloads, and
signing repository metadata with a key held by `gpg-agent`. Both are optional and both
are covered in [Installation](/docs/start/install/).

## Where to go next

| If you want to… | Read |
|---|---|
| Publish a directory of packages right now | [Quick Start](/docs/start/quickstart/) |
| Curate a long-lived repository | [First Workspace](/docs/start/workspace/) |
| Understand pools, views, and generations | [Core Concepts](/docs/start/concepts/) |
| Build a production YUM or APT repository | [Tutorials](/docs/tutorial/) |
| Look up a flag, field, or exit code | [Reference](/docs/reference/) |
