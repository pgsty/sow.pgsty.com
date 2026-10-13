---
title: "SOW v0.2.0"
linkTitle: "SOW v0.2.0"
date: 2026-08-08
authors: [Vonng]
description: "SOW v0.2.0 引入 Plain 与 Managed RPM/DEB 仓库、签名、发布、构建快照保留与 RPM Leaf 导出。"
categories: [Release]
tags: [release, managed, signing, publish, generation]
weight: 10
url: "/zh/blog/release/sow-docs-launch/"
---

SOW 0.2.0 引入了面向 RPM 与 DEB 仓库的 Plain 和 Managed 工作流。它以单个 Go 可执行文件，在 Linux 或 macOS 上构建静态软件包仓库。

本文记录 0.2.0 发布时的功能。当前安装与操作方法见[现行文档](/zh/docs/)。

<span id="两种工作模式"></span>

## 构建平面仓库

Plain 模式索引目录顶层的 RPM 与 DEB 文件：

```bash
sow create /srv/repo
```

RPM 生成 `repodata/`，DEB 生成 `Packages` 与 `Packages.gz`，混合目录同时生成两种索引。Plain 模式以目录内容作为状态，不需要工作区或数据库。

本版还加入 `--sign-with`，为未签名 RPM 软件包签名。使用 `--overwrite` 可替换已有 RPM 签名。Plain 模式不生成或签署 APT `Release` 文件。

<span id="生命周期控制"></span>

## 持续管理仓库

Managed 模式记录软件包成员，并构建具名 Dist：

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow check -r pigsty
```

每个 Repository 在 `pool/` 下保存一份软件包文件。Dist 的 RPM 或 APT 元数据位于 `dists/`。每次构建记录一个快照，供 SOW 比较变更并保留选定的仓库状态。

0.2.0 加入了以下功能：

- `sow/v3` 配置与软件包成员策略；
- RPM、APT 元数据签名，以及 RPM 软件包签名；
- `status`、`check`、`changes` 与操作日志；
- 可恢复的 filesystem 与 R2 发布；
- 构建快照保留与本地垃圾回收；
- 为需要独立 RPM 目录的工具提供 `rpm-leaf` 导出。

服务或发布完整 Repository 目录树，让元数据能访问共享包池。对已配置目标，`sow publish` 管理上传顺序与中断恢复。R2 清理只报告候选对象，不删除远端对象。

<span id="兼容性证据"></span>

## 发布测试与源码

本版加入 APT/DNF 与 S3 兼容集成测试，并通过标签触发 GoReleaser，构建 Linux/macOS 归档与 Linux RPM/DEB 软件包。历史代码与测试保留在 [v0.2.0 源码标签](https://github.com/pgsty/sow/tree/v0.2.0)。

当前版本见[下载页](/zh/download/)。当前客户端与存储测试范围见[平台与集成](/zh/docs/reference/compatibility/)。
