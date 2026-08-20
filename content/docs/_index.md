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
---

SOW is Pigsty's self-contained package repository manager. `sow create` turns the RPM and
DEB files in a directory into a usable flat repository. Managed workspaces add package
membership, policy, signing, immutable generations, audit history, and publication targets.

Press {{< kbd "Ctrl" "K" >}} (or {{< kbd "⌘" "K" >}} on macOS) to search this
site. Press {{< kbd "/" >}} outside an input to open command mode directly.

- [Get Started](/docs/start/) — Install SOW, create a flat repository, and build the first Managed workspace.
- [Tutorials](/docs/tutorial/) — Complete YUM, APT, signing, serving, and publication walkthroughs.
- [Features](/docs/feature/) — Plain and Managed execution, pool projections, policy, signing, transactions, and audit.
- [Design](/docs/design/) — Ownership, state, publication ordering, recovery, and evidence boundaries.
- [Commands](/docs/command/) — Syntax, selection rules, output, state transitions, and exit behavior for every command.
- [Reference](/docs/reference/) — Configuration, package references, layouts, JSON, exit codes, platforms, and integration coverage.
{.cards}

## Choose a path

| Goal | Start here |
|---|---|
| Index a package directory now | [Quick Start](/docs/start/quickstart/) |
| Maintain a curated long-lived repository | [First Workspace](/docs/start/workspace/) |
| Build a complete YUM or APT repository | [Tutorials](/docs/tutorial/) |
| Look up exact CLI behavior | [Commands](/docs/command/) |
| Check a field, path, or compatibility claim | [Reference](/docs/reference/) |
