---
title: "Tutorials"
linkTitle: "Tutorials"
description: "End-to-end walkthroughs that take a pile of packages all the way to a signed repository your clients can install from."
categories: [Tutorial]
tags: [yum, apt, signing, publish]
url: "/docs/tutorial/"
weight: 200
icon: fa-solid fa-graduation-cap
---

The tutorials cover new Managed workspaces and migration of existing Plain repositories.
Commands are intended to be run in order;
replace uppercase placeholders and package paths for your environment.

If you have not installed SOW yet, start with [Installation](/docs/start/install/) and
[Quick Start](/docs/start/quickstart/).

{{< cards >}}
{{< card title="Migrate an Existing YUM Repository" link="/docs/tutorial/yum-migration/" >}}
Replace a flat repository's metadata generator while preserving publication time, signatures,
and compatibility with clients that already have cached metadata.
{{< /card >}}
{{< card title="Build a YUM Repository" link="/docs/tutorial/yum-repo/" >}}
A managed RPM repository with per-architecture views, `noarch` projection, debuginfo filtering,
version limits, and a working `dnf` client configuration.
{{< /card >}}
{{< card title="Build an APT Repository" link="/docs/tutorial/apt-repo/" >}}
A managed DEB repository with a Debian-style pool, `by-hash` indexes, and a deb822 client
configuration.
{{< /card >}}
{{< card title="Sign Your Repository" link="/docs/tutorial/signing/" >}}
Generate a dedicated GPG key, sign repository metadata and RPM packages, and configure
clients to reject anything unsigned.
{{< /card >}}
{{< card title="Serve Repositories" link="/docs/tutorial/serving/" >}}
Serve a Repository with Nginx and publish a verified Generation to a configured filesystem
target without exposing private workspace state.
{{< /card >}}
{{< card title="Build the pigsty-infra Repository" link="/docs/tutorial/infra-repo/" >}}
Turn existing dual-architecture infra-pkg RPMs and DEBs into a real repository, then rehearse local
installation, rolling updates, Stable promotion, and monthly snapshots.
{{< /card >}}
{{< /cards >}}

## Which one first

| Your situation | Start here |
|---|---|
| You already maintain a flat RPM directory with createrepo_c | [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) |
| You ship RPMs to dnf clients | [Build a YUM Repository](/docs/tutorial/yum-repo/) |
| You ship DEBs for Debian or Ubuntu | [Build an APT Repository](/docs/tutorial/apt-repo/) |
| You need signed metadata or signed RPM payloads | [Sign Your Repository](/docs/tutorial/signing/) |
| The tree is built but nothing can reach it | [Serve Repositories](/docs/tutorial/serving/) |
| You want to turn a dual-architecture package pool into a maintained Infra repository | [Build the pigsty-infra Repository](/docs/tutorial/infra-repo/) |

The YUM and APT tutorials are independent fresh-workspace paths. A real Workspace may hold
both RPM and DEB Dists in one Repository when that ownership boundary suits your operation.

## Conventions used here

Shell blocks contain commands without a `$` prefix so you can copy a whole block at once.
Output appears in a separate block below the command, or as a comment when it is one line.
Where a command needs a value you must substitute, it appears in `UPPERCASE`.

Every tutorial includes verification. For Managed mode, `sow check` returning `0` confirms
that the selected Repository is complete and matches the recorded Generation. Plain mode
uses metadata and signature checks plus real client acceptance, as described in the
migration guide; `sow check` does not audit a flat directory.
