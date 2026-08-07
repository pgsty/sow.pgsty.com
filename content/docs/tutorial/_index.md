---
title: "Tutorials"
linkTitle: "Tutorials"
description: "End-to-end walkthroughs that take a pile of packages all the way to a signed repository your clients can install from."
url: "/docs/tutorial/"
weight: 200
icon: fa-solid fa-graduation-cap
---

Each tutorial here is a complete journey: you start with nothing, run every command in order,
and finish with something a real `dnf` or `apt` client can use. Commands are copy-pasteable and
every output block is a real transcript.

If you have not installed SOW yet, start with [Installation](/docs/start/install/) and
[Quick Start](/docs/start/quickstart/) — those get you to a working flat repository in five
minutes. The tutorials below pick up from there and build the production shape.

{{< doc-cards cols="2" >}}
{{< doc-card title="Build a YUM Repository" link="/docs/tutorial/yum-repo/" >}}
A managed RPM repository with per-architecture views, `noarch` projection, debuginfo filtering,
version limits, and a working `dnf` client configuration.
{{< /doc-card >}}
{{< doc-card title="Build an APT Repository" link="/docs/tutorial/apt-repo/" >}}
A managed DEB repository with a Debian-style pool, `by-hash` indexes, and both deb822 and
legacy `sources.list` client configurations.
{{< /doc-card >}}
{{< doc-card title="Sign Your Repository" link="/docs/tutorial/signing/" >}}
Generate a dedicated GPG key, sign repository metadata and RPM packages, and configure
clients to reject anything unsigned.
{{< /doc-card >}}
{{< doc-card title="Serve Repositories" link="/docs/tutorial/serving/" >}}
Publish the tree over HTTP with Nginx, preview it locally, and copy it to an air-gapped host
without losing hardlink deduplication.
{{< /doc-card >}}
{{< doc-card title="Migrate from createrepo_c / reprepro" link="/docs/tutorial/migration/" >}}
Take over an existing repository in place, move a reprepro archive into a workspace, and see
exactly what changes and what does not.
{{< /doc-card >}}
{{< /doc-cards >}}

## Which one first

| Your situation | Start here |
|---|---|
| You ship RPMs for EL8 / EL9 / EL10 | [Build a YUM Repository](/docs/tutorial/yum-repo/) |
| You ship DEBs for Debian or Ubuntu | [Build an APT Repository](/docs/tutorial/apt-repo/) |
| You have a repository and clients complain it is unsigned | [Sign Your Repository](/docs/tutorial/signing/) |
| The tree is built but nothing can reach it | [Serve Repositories](/docs/tutorial/serving/) |
| You have a `createrepo_c` cron job or a reprepro database | [Migration](/docs/tutorial/migration/) |

The YUM and APT tutorials share one workspace and are written to be followed in sequence — the
APT tutorial adds a second Dist to the repository the YUM tutorial creates. You can also follow
either one standalone; each states its own prerequisites.

## Conventions used here

Shell blocks contain commands without a `$` prefix so you can copy a whole block at once.
Output appears in a separate block below the command, or as a comment when it is one line.
Where a command needs a value you must substitute, it appears in `UPPERCASE`.

Every tutorial ends with a verification step. If verification fails, do not continue — the next
step assumes the tree is in the state the previous one produced. `sow check` is the gate that
tells you the truth: exit code `0` means the tree is complete and ready to copy, exit code `5`
means it is not.
