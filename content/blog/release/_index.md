---
title: Release Notes
linkTitle: Release
description: Changes and upgrade instructions for each SOW release.
url: "/blog/release/"
weight: 20
icon: fa-solid fa-tag
sidebar_expanded: true
categories: [Release]
tags: [release]
images: [/images/blog/sow-release.webp]
featured_image: wash
cascade:
  # The purpose-made release banner, not the generic social card: it is the
  # image the index cards crop to 16:9 and the one every release note carries.
  images: [/images/blog/sow-release.webp]
  # OINK 1.5.1 renders it behind the article header at a tenth of its opacity,
  # masked out before the text starts -- a post takes a colour from its subject
  # without spending any contrast on it.
  featured_image: wash
---

Read the changes and upgrade steps for each SOW release, with the newest version first.

[SOW 0.9.0](/blog/release/sow-v0.9.0/) makes flat `create` and `prune` fault-tolerant by default with a `--strict` opt-in, adds RPM format v6 and native OPENPGP multi-signature verification, accepts both `sow.yml` and `sow.yaml`, supports ECDSA/DSA metadata keys and FIFO passfiles, and aligns target GC grace directly with `max_cache_ttl`. Workspaces on 0.5.0 through 0.8.0 keep schema v13; review any target with `max_cache_ttl: 0s` before upgrading. See the [0.9.0 upgrade guide](/docs/start/install/#upgrade-to-090).

[SOW 0.8.0](/blog/release/sow-v0.8.0/) adds opt-in R2 conditional deletion (`sow gc TARGET --delete`), allows external secret and keyring symlinks outside the workspace, drops `.deb` `control.tar.lzma` support, hardens DEB/RPM verification, and accelerates large-repository publication and GC. Workspaces on 0.5.0 through 0.7.1 keep schema v13; complete any interrupted 0.7.1 local GC before upgrading. See the [0.8.0 upgrade guide](/docs/start/install/#upgrade-to-080).

[SOW 0.7.1](/blog/release/sow-v0.7.1/) upgrades to Go 1.27.4, refreshes dependencies, and fixes recovery, input validation, and S3/R2 handling. Workspaces on 0.5.0 through 0.7.0 need no schema migration. See the [0.7.1 upgrade guide](/docs/start/install/#upgrade-to-071).

[SOW 0.7.0](/blog/release/sow-v0.7.0/) adds flat RPM pruning and password-file signing, fixes migration and recovery defects, and updates dependencies. Workspaces on 0.5.0 through 0.6.1 need no schema migration. See the [0.7.0 upgrade guide](/docs/start/install/#upgrade-to-070).

[SOW 0.6.1](/blog/release/sow-v0.6.1/) updates Go to 1.27.3, refreshes dependencies, and improves invalid-input diagnostics.
Workspaces already on 0.5.0 or 0.6.0 need no schema migration. See the [upgrade guide](/docs/start/install/#upgrade-to-061).
