---
title: "设计归档"
linkTitle: "设计归档"
description: "按日期归档 SOW 在所有权、仓库布局、发布、恢复与兼容性边界上的架构决策。"
categories: [Design]
tags: [managed, publish, transaction]
url: "/zh/blog/design/"
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

设计归档解释 SOW 为什么采纳某项契约、否决了哪些替代方案，以及结论实际达到了哪一层证据。
文章按 `date` 排列，记录设计理由首次形成可维护正文的日期；`lastmod` 记录后续编辑或与
实现对齐的日期。功能实际在哪个版本交付，仍以发布注记与源码 Tag 为准。

## 权威与证据

本专栏是持续维护的设计理由与决策历史权威来源。当前命令、配置与运维行为仍以
[SOW 文档](/zh/docs/)为准；历史版本的精确行为则绑定对应源码 Tag 与[发布注记](/zh/blog/release/)。

每项运维结论都应与它真正达到的证据层一致：

```text
设计 -> 实现 -> 聚焦测试 -> 真实客户端/Provider 实跑 -> 发布物
```

前一层通过，不代表后一层自动通过。[平台与集成](/zh/docs/reference/compatibility/)
记录自动化客户端、Provider 与文件系统覆盖；Release 制品属于独立交付门禁。
