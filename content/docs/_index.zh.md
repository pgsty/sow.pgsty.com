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

SOW 是 [Pigsty](https://pigsty.cc) 出品的自包含软件仓库管理器:一个静态 Go 二进制,
在 Linux 与 macOS 上创建并维护 **APT(DEB)** 与 **YUM(RPM)** 软件仓库 ——
不需要 `createrepo_c`、`dpkg-scanpackages`、`reprepro`,也没有常驻服务。

它提供两条相互隔离的运行路径:

- **Plain 平面模式** —— `sow create` 把任意一个存放 `.rpm` / `.deb` 的目录就地变成
  可直接对外服务的平面仓库,输出确定性可复现。
- **Managed 托管模式** —— 工作区模型:Debian 风格包池、按架构渲染的发布视图、
  GPG 签名、成员策略、事务式构建与完整审计账本。

{{< doc-cards cols="2" >}}
{{< doc-card title="上手指南" link="/zh/docs/start/" >}}
安装 SOW,五分钟搭出第一个平面仓库,并建立核心概念的心智模型。
{{< /doc-card >}}
{{< doc-card title="教程" link="/zh/docs/tutorial/" >}}
端到端实战:YUM 与 APT 仓库、GPG 签名、Nginx 对外服务、从 createrepo_c / reprepro 迁移。
{{< /doc-card >}}
{{< doc-card title="功能" link="/zh/docs/feature/" >}}
SOW 的工作原理:Plain 与 Managed 双引擎、包池与架构视图、成员策略、签名模型、事务与审计。
{{< /doc-card >}}
{{< doc-card title="设计" link="/zh/docs/design/" >}}
架构与决策记录:所有权、0.3 单包体模型、发布、兼容性边界,以及从 v0.2 开始的设计演进。
{{< /doc-card >}}
{{< doc-card title="参考" link="/zh/docs/reference/" >}}
完整命令行参考、`sow.yml` 配置、包引用文法、退出码、仓库布局与兼容矩阵。
{{< /doc-card >}}
{{< /doc-cards >}}

## 从哪里开始

| 你想要…… | 阅读 |
|---|---|
| 立刻把仓库跑起来 | [快速上手](/zh/docs/start/quickstart/) |
| 先理解设计与心智模型 | [核心概念](/zh/docs/start/concepts/) |
| 搭建生产级 YUM / APT 仓库 | [教程](/zh/docs/tutorial/) |
| 理解架构决策与版本边界 | [设计](/zh/docs/design/) |
| 替换现有 createrepo_c / reprepro 流水线 | [迁移指南](/zh/docs/tutorial/migration/) |
| 查命令或配置字段 | [参考](/zh/docs/reference/) |
