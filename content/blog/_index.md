---
title: SOW Blog
linkTitle: Blog
description: Release notes and project news
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

Release notes, design notes, and project news for SOW — the self-contained APT / YUM
package repository manager by Pigsty.
