---
title: "SOW: Software Object Warehouse"
description: "Store once. Serve everywhere. SOW is a self-contained APT / YUM package repository manager from Pigsty."
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
