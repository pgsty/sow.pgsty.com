---
title: "Get Started"
linkTitle: "Get Started"
description: "Install SOW, create a flat repository, and learn the Managed workspace model."
categories: [Start]
tags: [install, plain, managed]
url: "/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW turns RPM and DEB files into static YUM and APT repositories. Install SOW, then choose how to manage your packages:

- **Plain mode:** run `sow create DIR` to build indexes for the packages in a directory.
- **Managed mode:** create a workspace to group packages into Dists, limit versions, sign metadata, and publish updates.

- [Installation](/docs/start/install/) — Install a release archive, Linux package, or source build.
- [Quick Start](/docs/start/quickstart/) — Build a flat repository and use it from a local client.
- [First Workspace](/docs/start/workspace/) — Create RPM and DEB Dists, add packages, and check the result.
- [Core Concepts](/docs/start/concepts/) — Learn how workspaces, repositories, Dists, and generations fit together.
{.cards}

Serve the generated files through a static HTTP server or object storage. See [Installation](/docs/start/install/#storage-and-optional-tools) for storage and signing requirements.
