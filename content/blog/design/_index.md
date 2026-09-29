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
images: [/images/blog/sow-design.webp]
featured_image: wash
cascade:
  images: [/images/blog/sow-design.webp]
  featured_image: wash
---

Design records explain why SOW adopted a contract, what it rejected, and which evidence
boundary applies. They are ordered by `date`, which records when the rationale first took
its maintained form; `lastmod` records later editorial or implementation-alignment
updates. Release notes and source tags remain authoritative for when behavior actually
shipped.

The Design History records distill the original v0.1 program, its 44 surviving ADR files,
112 dated evidence reports, and the v0.2 reset into a small maintained narrative. Raw
planning prompts, reviews, and transcripts stay available through immutable source tags
and commits; they are primary sources, not a second documentation hierarchy.

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
