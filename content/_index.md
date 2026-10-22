---
title: "SOW: Software Object Warehouse"
description: "SOW 0.6.1 builds YUM and APT indexes from local packages. Start with a flat repository, or manage package policy, signing, snapshots, and incremental publication."
url: "/"
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
