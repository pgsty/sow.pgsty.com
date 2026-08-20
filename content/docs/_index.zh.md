---
title: "SOW 文档"
linkTitle: "文档"
description: "用一个自包含二进制创建并管理 RPM/YUM 与 DEB/APT 软件仓库。"
url: "/zh/docs/"
weight: 1
type: docs
icon: fa-solid fa-book
sidebar_expanded: true
sidebar_root_for: self
sidebar_root_link_self: true
search_keywords: [SOW 文档, 软件仓库, RPM, YUM, DEB, APT]
search_boost: 1.5
cascade:
  search_boost: 1.15
---

SOW 是 Pigsty 出品的自包含软件仓库管理器。`sow create` 能把目录中的 RPM 与 DEB
文件直接变成可用平面仓库；Managed 工作区则进一步提供成员关系、筛选策略、签名、不可变
Generation、审计历史与发布目标。

按 {{< kbd "Ctrl" "K" >}}（macOS 上也可用 {{< kbd "⌘" "K" >}}）搜索本站；
焦点不在输入框时按 {{< kbd "/" >}}，可直接打开命令模式。

- [上手](/zh/docs/start/) — 安装 SOW、创建平面仓库，并构建第一个 Managed 工作区。
- [教程](/zh/docs/tutorial/) — 完整的 YUM、APT、签名、对外服务与发布实战。
- [功能](/zh/docs/feature/) — Plain/Managed 运行路径、包池投影、策略、签名、事务与审计。
- [设计](/zh/docs/design/) — 所有权、状态、发布顺序、恢复与证据边界。
- [命令](/zh/docs/command/) — 每条命令的语法、选择规则、输出、状态变化与退出行为。
- [参考](/zh/docs/reference/) — 配置、包引用、目录布局、JSON、退出码、平台与集成覆盖。
{.cards}

## 选择路径

| 目标 | 从这里开始 |
|---|---|
| 立即索引一个软件包目录 | [快速上手](/zh/docs/start/quickstart/) |
| 长期维护精选仓库 | [第一个工作区](/zh/docs/start/workspace/) |
| 搭建完整 YUM 或 APT 仓库 | [教程](/zh/docs/tutorial/) |
| 查询精确 CLI 行为 | [命令](/zh/docs/command/) |
| 核对字段、路径或兼容性结论 | [参考](/zh/docs/reference/) |
