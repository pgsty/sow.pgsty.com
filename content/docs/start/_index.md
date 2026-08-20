---
title: "Get Started"
linkTitle: "Get Started"
description: "Install SOW, create a flat repository, and learn the Managed workspace model."
url: "/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW builds static RPM/YUM and DEB/APT repositories; it is not an HTTP daemon. Choose one
of two isolated paths:

- **Plain:** `sow create` rebuilds indexes beside the packages in an ordinary directory.
- **Managed:** a workspace tracks package membership, Dists, architecture views, policy,
  signing, generations, audit history, and publication targets.

- [Installation](/docs/start/install/) — Choose a release archive, RPM/DEB package, or source build; verify the installed binary.
- [Quick Start](/docs/start/quickstart/) — Create and serve a flat repository from a directory of packages.
- [First Workspace](/docs/start/workspace/) — Initialize Managed mode, create RPM and DEB Dists, add packages, build, and check.
- [Core Concepts](/docs/start/concepts/) — Workspace, Repository, Dist, Package Object, Desired Membership, and Built Generation.
{.cards}

Managed workspaces require a local POSIX filesystem with advisory locks, fsync, and atomic
rename semantics. Metadata generation is in-process; optional RPM package signing needs
`rpm`, while an `agent://` metadata key needs `gpg` and `gpg-agent`.
