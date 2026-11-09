---
title: "Tutorials"
linkTitle: "Tutorials"
description: "Build, sign, serve, and update RPM and DEB repositories."
categories: [Tutorial]
tags: [yum, apt, signing, publish]
url: "/docs/tutorial/"
weight: 200
icon: fa-solid fa-graduation-cap
---

These tutorials cover repository creation, signing, publication, and updates. Start with [Installation](/docs/start/install/) if you have not installed SOW.

<span id="which-one-first" data-td-print-local></span>

- [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) — Replace the metadata generator for a flat RPM repository and prune superseded RPMs while preserving publication timestamps, signatures, and client caches.
- [Build a YUM Repository](/docs/tutorial/yum-repo/) — Create RPM architecture views, filter packages, set version limits, and configure DNF.
- [Build an APT Repository](/docs/tutorial/apt-repo/) — Create a DEB pool with by-hash indexes and configure an APT client.
- [Sign Your Repository](/docs/tutorial/signing/) — Sign metadata and RPM packages, then configure clients to verify signatures.
- [Serve Repositories](/docs/tutorial/serving/) — Publish to a filesystem target and serve it with Nginx.
- [Build the pigsty-infra Repository](/docs/tutorial/infra-repo/) — Use both package formats and architectures, test installation, and maintain rolling channels, stable releases, and monthly snapshots.
{.cards}

<span id="conventions-used-here" data-td-print-local></span>

## Follow the examples

Run commands in order. Replace uppercase placeholders and `/path/to/` inputs with your values. Examples under `/srv` require a writable directory; you can substitute a path under your home directory.

The YUM and APT tutorials each start with a new workspace. To combine them, create the second Dist in the existing `pigsty` Repository and keep both Dist definitions in `sow.yml`.

Each tutorial shows how to check its result. For a command error or interrupted operation,
see [Troubleshooting](/docs/reference/troubleshooting/).
