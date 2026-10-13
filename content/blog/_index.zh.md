---
title: SOW 博客
linkTitle: 博客
description: 发布说明、设计决策与项目动态
url: "/zh/blog/"
weight: 40
type: blog
sidebar_root_for: self
sidebar_root_link_self: true
images: [/images/blog/sow.webp]
featured_image: wash

outputs:
  - HTML
  - RSS
  - print
cascade:
  type: blog
  outputs:
    - HTML
    - print
  images: [/images/blog/sow.webp]
  featured_image: wash
  # OINK 0.6 page-end share bar, scoped to the blog. Every entry is a plain
  # intent link carrying only this page's permalink and title -- no SDK, no
  # iframe, no third-party script, no share counts -- plus a local copy button.
  share: [x, linkedin, reddit, hackernews, telegram, weibo, email, copy]
  # An article says how long it takes to read; documentation pages do not.
  reading_time: true
  params:
    sidebar_menu_foldable: false
    sidebar_menu_compact: false
    sidebar_expand_levels: 3
icon: fa-solid fa-blog
---

SOW 的发布说明、设计决策与项目动态。SOW 是 Pigsty 出品的 APT 与 YUM 软件仓库管理器。
