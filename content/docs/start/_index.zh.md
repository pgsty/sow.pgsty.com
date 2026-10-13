---
title: "上手"
linkTitle: "上手"
description: "安装 SOW、创建平面仓库，并理解 Managed 工作区模型。"
categories: [Start]
tags: [install, plain, managed]
url: "/zh/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW 为 RPM 与 DEB 软件包生成 YUM 与 APT 静态仓库。安装 SOW 后，按需要选择管理方式：

- **Plain 模式：** 执行 `sow create DIR`，为目录中的软件包生成索引。
- **Managed 模式：** 创建工作区，按 Dist 组织软件包、限制版本数、签署元数据并发布更新。

- [安装](/zh/docs/start/install/) — 安装发布归档、Linux 软件包，或从源码构建。
- [快速上手](/zh/docs/start/quickstart/) — 创建平面仓库，并用本机客户端访问。
- [第一个工作区](/zh/docs/start/workspace/) — 创建 RPM 与 DEB Dist，添加软件包并检查结果。
- [核心概念](/zh/docs/start/concepts/) — 理解工作区、仓库、Dist 与构建快照的关系。
{.cards}

通过静态 HTTP 服务器或对象存储提供生成的文件。存储与签名要求见[安装说明](/zh/docs/start/install/#存储与可选工具)。
