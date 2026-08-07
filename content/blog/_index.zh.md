---
title: SOW 博客
linkTitle: 博客
description: 发布注记与项目动态
weight: 40
type: blog
sidebar_root_for: self
sidebar_root_link_self: true

outputs:
  - HTML
  - RSS
  - print
cascade:
  type: blog
  outputs:
    - HTML
    - print
  params:
    ui:
      sidebar_menu_foldable: false
      sidebar_menu_compact: false
      ul_show: 3
icon: fa-solid fa-blog
---

SOW 的发布注记、设计札记与项目动态 —— Pigsty 出品的自包含 APT / YUM 软件仓库管理器。
