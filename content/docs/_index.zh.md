---
title: "SOW 文档"
linkTitle: "文档"
description: "用一个自包含二进制创建并管理 APT / YUM 软件仓库。"
url: "/zh/docs/"
weight: 1
type: docs
icon: fa-solid fa-book
sidebar_expanded: true
---

SOW 0.2.0 是 [Pigsty](https://pigsty.cc) 出品的自包含软件仓库管理器。一个 Go
二进制即可生成 RPM/YUM 与 DEB/APT 仓库元数据，不需要仓库守护进程或额外元数据工具链。

它提供两条相互隔离的运行路径:

- **Plain 平面模式** —— `sow create` 就地索引目录顶层的 RPM 与 DEB 文件。
- **Managed 托管模式** —— 工作区模型:Debian 风格包池、按架构渲染的发布视图、
  签名、成员策略、事务式 Generation、审计与发布目标。

{{< doc-cards cols="2" >}}
{{< doc-card title="上手指南" link="/zh/docs/start/" >}}
安装 SOW,五分钟搭出第一个平面仓库,并建立核心概念的心智模型。
{{< /doc-card >}}
{{< doc-card title="教程" link="/zh/docs/tutorial/" >}}
端到端实战:YUM 与 APT 仓库、GPG 签名、Nginx 对外服务与已校验公共树发布。
{{< /doc-card >}}
{{< doc-card title="功能" link="/zh/docs/feature/" >}}
SOW 的工作原理:Plain 与 Managed 双引擎、包池与架构视图、成员策略、签名模型、事务与审计。
{{< /doc-card >}}
{{< doc-card title="设计" link="/zh/docs/design/" >}}
架构与决策记录:所有权、单包体模型、发布、恢复与兼容性边界。
{{< /doc-card >}}
{{< doc-card title="命令手册" link="/zh/docs/command/" >}}
每条顶层命令单独成页：语法、参数、行为、输出与退出码。
{{< /doc-card >}}
{{< doc-card title="参考" link="/zh/docs/reference/" >}}
`sow.yml` Schema、包引用文法、退出码、JSON 契约、仓库布局与兼容性证据。
{{< /doc-card >}}
{{< /doc-cards >}}

## 从哪里开始

| 你想要…… | 阅读 |
|---|---|
| 立刻把仓库跑起来 | [快速上手](/zh/docs/start/quickstart/) |
| 先理解设计与心智模型 | [核心概念](/zh/docs/start/concepts/) |
| 搭建 Managed YUM / APT 仓库 | [教程](/zh/docs/tutorial/) |
| 理解所有权与发布模型 | [设计](/zh/docs/design/) |
| 查命令语法与行为 | [命令手册](/zh/docs/command/) |
| 查配置字段或数据契约 | [参考](/zh/docs/reference/) |
