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

[SOW 0.7.0](/blog/release/sow-v0.7.0/) adds flat RPM pruning and password-file signing, fixes migration and recovery defects, and updates dependencies. It is currently in draft preparation; public downloads remain at 0.6.1. Workspaces on 0.5.0 through 0.6.1 need no schema migration. See the [0.7.0 upgrade guide](/docs/start/install/#upgrade-to-070).

[SOW 0.6.1](/blog/release/sow-v0.6.1/) updates Go to 1.27.3, refreshes dependencies, and improves invalid-input diagnostics.
Workspaces already on 0.5.0 or 0.6.0 need no schema migration. See the [upgrade guide](/docs/start/install/#upgrade-to-061).
