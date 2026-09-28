---
title: "SOW：Software Object Warehouse"
description: "SOW 0.5.0 从本地软件包生成 YUM 与 APT 索引。可直接创建平面仓库，也可托管软件包策略、签名、快照与增量发布。"
url: "/zh/"
weight: 1
type: home
cascade:
  # Scoped to the docs tree on purpose. An unscoped cascade also reaches the
  # taxonomy and term pages Hugo generates, and `type: docs` there sends them
  # to the docs list layout instead of OINK's taxonomy.html / term.html.
  - target:
      path: '/docs/**'
    type: docs
---
