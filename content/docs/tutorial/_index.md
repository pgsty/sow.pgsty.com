---
title: "Tutorials"
linkTitle: "Tutorials"
description: "End-to-end walkthroughs that take a pile of packages all the way to a signed repository your clients can install from."
url: "/docs/tutorial/"
weight: 200
icon: fa-solid fa-graduation-cap
---

Each tutorial starts from a new v0.2.0 workspace. Commands are intended to be run in order;
replace uppercase placeholders and package paths for your environment.

If you have not installed SOW yet, start with [Installation](/docs/start/install/) and
[Quick Start](/docs/start/quickstart/). The tutorials below cover the managed repository path.

{{< cards >}}
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
{{< /cards >}}

## Which one first

| Your situation | Start here |
|---|---|
| You ship RPMs to dnf clients | [Build a YUM Repository](/docs/tutorial/yum-repo/) |
| You ship DEBs for Debian or Ubuntu | [Build an APT Repository](/docs/tutorial/apt-repo/) |
| You need signed metadata or signed RPM payloads | [Sign Your Repository](/docs/tutorial/signing/) |
| The tree is built but nothing can reach it | [Serve Repositories](/docs/tutorial/serving/) |

The YUM and APT tutorials are independent fresh-workspace paths. A real Workspace may hold
both RPM and DEB Dists in one Repository when that ownership boundary suits your operation.

## Conventions used here

Shell blocks contain commands without a `$` prefix so you can copy a whole block at once.
Output appears in a separate block below the command, or as a comment when it is one line.
Where a command needs a value you must substitute, it appears in `UPPERCASE`.

Every tutorial ends with a verification step. `sow check` returning `0` proves the selected
Repository is complete and matches the recorded Generation. A nonzero result is not a release
artifact.
