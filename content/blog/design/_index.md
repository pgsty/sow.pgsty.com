---
title: "Design Records"
linkTitle: "Design"
description: "Dated architecture decisions behind SOW's ownership, repository layout, publication, recovery, and compatibility boundaries."
categories: [Design]
tags: [managed, publish, transaction]
url: "/blog/design/"
aliases:
  - "/docs/design/"
weight: 10
icon: fa-solid fa-compass-drafting
sidebar_expanded: true
blog_index: list
cascade:
  images: [/images/blog/sow-blog.webp]
  featured_image: wash
---

Design records explain why SOW adopted a contract, what it rejected, and which evidence
boundary applies. They are ordered by `date`, which records when the rationale first took
its maintained form; `lastmod` records later editorial or implementation-alignment
updates. Release notes and source tags remain authoritative for when behavior actually
shipped.

## Authority and evidence

This column is the maintained authority for design rationale and decision history. Current
commands, configuration, and operator behavior remain in [SOW Docs](/docs/); exact behavior
of a historical release remains attached to that release's source tag and
[release note](/blog/release/).

Each operational claim should match the evidence layer it has actually reached:

```text
design -> implementation -> focused tests -> real client/provider run -> release artifact
```

Passing one layer does not imply the next. The [platform and integration reference](/docs/reference/compatibility/)
records the automated client, Provider, and filesystem coverage; release artifacts are a
separate delivery gate.
