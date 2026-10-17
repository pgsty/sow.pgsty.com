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
  sidebar_expanded: true
---

SOW 创建 RPM/YUM 与 DEB/APT 软件仓库。执行 `sow create DIR`，即可为目录中的包生成索引。
需要按 Dist 组织软件包、限制版本数、签署元数据或发布更新时，使用 Managed 工作区。

本文档对应 **SOW 0.6.0**。版本变化见[发布注记](/zh/blog/release/sow-v0.6.0/)，
已有 Managed 工作区请参考[升级说明](/zh/docs/start/install/#升级到-060)。

- [上手](/zh/docs/start/) — 安装 SOW、创建平面仓库，并构建第一个 Managed 工作区。
- [教程](/zh/docs/tutorial/) — 完整的 YUM、APT、签名、对外服务与发布实战。
- [功能](/zh/docs/feature/) — 软件包存储、筛选、签名与恢复的工作方式。
- [设计归档](/zh/blog/design/) — 架构设计的原因与演变历史。
- [命令](/zh/docs/command/) — 每条命令的参数、示例、输出与退出码。
- [参考](/zh/docs/reference/) — 配置字段、包名称、目录布局与兼容性。
{.cards}

## 选择路径

| 目标 | 从这里开始 |
|---|---|
| 立即索引一个软件包目录 | [快速上手](/zh/docs/start/quickstart/) |
| 替换已有 createrepo_c 工作流 | [迁移现有 YUM 仓库](/zh/docs/tutorial/yum-migration/) |
| 长期维护精选仓库 | [第一个工作区](/zh/docs/start/workspace/) |
| 搭建完整 YUM 或 APT 仓库 | [教程](/zh/docs/tutorial/) |
| 查询精确 CLI 行为 | [命令](/zh/docs/command/) |
| 处理错误或中断操作 | [故障处理](/zh/docs/reference/troubleshooting/) |
| 核对字段、路径或兼容性结论 | [参考](/zh/docs/reference/) |
| 理解一项架构决策 | [设计归档](/zh/blog/design/) |
