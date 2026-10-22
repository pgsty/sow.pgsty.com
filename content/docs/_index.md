---
title: "SOW Docs"
linkTitle: "Docs"
description: "Create and manage RPM/YUM and DEB/APT repositories with one self-contained binary."
url: "/docs/"
weight: 1
type: docs
icon: fa-solid fa-book
sidebar_expanded: true
sidebar_root_for: self
sidebar_root_link_self: true
search_keywords: [sow, documentation, package repository, rpm, yum, deb, apt]
search_boost: 1.5
cascade:
  search_boost: 1.15
  sidebar_expanded: true
---

SOW creates RPM/YUM and DEB/APT software repositories. Run `sow create DIR` to index
packages in a directory. Use a Managed workspace when you need to organize packages into
Dists, limit versions, sign metadata, or publish updates.

These docs cover **SOW 0.6.1**. See the [release notes](/blog/release/sow-v0.6.1/) for
version changes and the [upgrade guide](/docs/start/install/#upgrade-to-061)
for an existing Managed workspace.

- [Get Started](/docs/start/) — Install SOW, create a flat repository, and build the first Managed workspace.
- [Tutorials](/docs/tutorial/) — Complete YUM, APT, signing, serving, and publication walkthroughs.
- [Features](/docs/feature/) — How package storage, filtering, signing, and recovery work.
- [Design Records](/blog/design/) — The reasons behind the architecture and its history.
- [Commands](/docs/command/) — Options, examples, output, and exit codes for every command.
- [Reference](/docs/reference/) — Configuration fields, package names, directory layouts, and compatibility.
{.cards}

## Choose a path

| Goal | Start here |
|---|---|
| Index a package directory now | [Quick Start](/docs/start/quickstart/) |
| Replace an existing createrepo_c workflow | [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) |
| Maintain a curated long-lived repository | [First Workspace](/docs/start/workspace/) |
| Build a complete YUM or APT repository | [Tutorials](/docs/tutorial/) |
| Look up exact CLI behavior | [Commands](/docs/command/) |
| Resolve an error or interrupted command | [Troubleshooting](/docs/reference/troubleshooting/) |
| Check a field, path, or compatibility claim | [Reference](/docs/reference/) |
| Understand an architecture decision | [Design Records](/blog/design/) |
