---
title: "Design Records"
linkTitle: "Design"
description: "Why SOW uses its current repository layout and publication workflow, and how the design changed."
categories: [Design]
tags: [managed, publish, transaction]
url: "/blog/design/"
aliases:
  - "/docs/design/"
weight: 10
icon: fa-solid fa-compass-drafting
sidebar_expanded: true
blog_index: list
images: [/images/blog/sow-design.webp]
featured_image: wash
cascade:
  images: [/images/blog/sow-design.webp]
  featured_image: wash
---

Design records explain the choices behind SOW's repository layout, state model, and
publication workflow. Article dates record when a decision was documented; modification
dates record later revisions.

Start with these current design explanations:

- [System model](/blog/design/model/): packages, Dists, Generations, and targets.
- [One package tree](/blog/design/single-payload/): why views share a Pool.
- [Publication and recovery](/blog/design/publication/): upload order, checkpoints, and cleanup.
- [Design principles](/blog/design/principles/): state ownership and coordination.

<span id="authority-and-evidence"></span>

The historical series follows the v0.1 program, its design decisions and tests, the v0.2
reset, and later releases. It links to dated source snapshots. Use [SOW Docs](/docs/) for
current commands and [release notes](/blog/release/) for version-specific changes.
