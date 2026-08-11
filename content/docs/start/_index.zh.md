---
title: "上手"
linkTitle: "上手"
description: "安装 SOW、创建平面仓库，并理解 Managed 工作区模型。"
url: "/zh/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW 生成 RPM/YUM 与 DEB/APT 静态仓库，本身不是 HTTP 守护进程。先选择一条相互隔离的
运行路径：

- **Plain：** `sow create` 在普通目录中为现有软件包重建索引。
- **Managed：** 工作区持续记录成员关系、Dist、架构视图、策略、签名、Generation、
  审计历史与发布目标。

{{< doc-cards cols="2" >}}
{{< doc-card title="安装" link="/zh/docs/start/install/" >}}
选择 Release 归档、RPM/DEB 安装包或源码构建，并校验二进制。
{{< /doc-card >}}
{{< doc-card title="快速上手" link="/zh/docs/start/quickstart/" >}}
从一个软件包目录创建平面仓库，并通过 HTTP 提供服务。
{{< /doc-card >}}
{{< doc-card title="第一个工作区" link="/zh/docs/start/workspace/" >}}
初始化 Managed 模式，创建 RPM/DEB Dist，添加软件包，然后构建并校验。
{{< /doc-card >}}
{{< doc-card title="核心概念" link="/zh/docs/start/concepts/" >}}
Workspace、Repository、Dist、Package Object、Desired Membership 与 Built Generation。
{{< /doc-card >}}
{{< /doc-cards >}}

Managed 工作区需要具备建议锁、fsync 与原子 rename 语义的本地 POSIX 文件系统。元数据
在进程内生成；可选的 RPM 包签名需要 `rpm`，`agent://` 元数据密钥需要 `gpg` 与
`gpg-agent`。
