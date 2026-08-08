---
title: "上手指南"
linkTitle: "上手指南"
description: "安装 SOW，创建软件仓库，并理解 v0.2.0 的使用模型。"
url: "/zh/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW 是一个用于 RPM/YUM 与 DEB/APT 仓库的自包含二进制。它负责生成静态文件，HTTP
服务器或对象存储负责向客户端提供这些文件。

先选一条运行路径。`sow create` 在普通目录中为软件包就地生成平面索引；Managed 命令
操作工作区，提供包池、具名 Dist、架构视图、策略、签名、Generation、审计与发布目标。
两条路径不共享状态。

下面四页分别介绍安装、两条运行路径和共同的心智模型。

{{< doc-cards cols="2" >}}
{{< doc-card title="安装" link="/zh/docs/start/install/" >}}
下载预编译二进制或从源码构建，说明 Release 构建目标以及会使用外部工具的可选能力。
{{< /doc-card >}}
{{< doc-card title="快速上手" link="/zh/docs/start/quickstart/" >}}
把一个装包的目录变成平面仓库，用 HTTP 暴露出去，再用 `dnf` / `apt` 装包。
{{< /doc-card >}}
{{< doc-card title="第一个工作区" link="/zh/docs/start/workspace/" >}}
创建工作区，建一个含 RPM 与 DEB 两种 Dist 的仓库，添加软件包，查看包池与发布树。
{{< /doc-card >}}
{{< doc-card title="核心概念" link="/zh/docs/start/concepts/" >}}
心智模型:Workspace、Repository、Dist、架构视图,以及期望成员集与已构建代的区别。
{{< /doc-card >}}
{{< /doc-cards >}}

## 你需要什么

一台 Linux 或 macOS 机器（`amd64` 或 `arm64`）、Managed 工作区所需的本地 POSIX
文件系统，以及容纳包体和 staging 的磁盘空间。

元数据生成在进程内完成。可选的 RPM 包签名需要 `rpm`；`agent://` 元数据 key 需要
`gpg` 与 `gpg-agent`。详见[安装](/zh/docs/start/install/)。

## 接下来读什么

| 你想要…… | 阅读 |
|---|---|
| 索引一个装包的目录 | [快速上手](/zh/docs/start/quickstart/) |
| 长期维护一个精选仓库 | [第一个工作区](/zh/docs/start/workspace/) |
| 搞懂包池、视图与代际 | [核心概念](/zh/docs/start/concepts/) |
| 搭建 Managed YUM / APT 仓库 | [教程](/zh/docs/tutorial/) |
| 查某个参数、字段或退出码 | [参考](/zh/docs/reference/) |
