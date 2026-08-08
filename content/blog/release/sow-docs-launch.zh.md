---
title: "SOW v0.2.0"
linkTitle: "SOW v0.2.0"
date: 2026-08-08
author: "冯若航"
description: "SOW v0.2.0 提供 Plain 与 Managed RPM/DEB 仓库、可验证 Generation、签名、发布、保留、GC 与 RPM Leaf 导出。"
categories: [发布]
tags: [发布, sow]
weight: 10
url: "/zh/blog/release/sow-docs-launch/"
---

SOW 0.2.0 是 [Pigsty](https://pigsty.cc) 出品的自包含 RPM/DEB 仓库管理器，Release
资产以单个 Go 可执行文件覆盖 Linux 与 macOS 构建目标。

## 两种工作模式

**Plain 模式**给目录顶层已有的 RPM 与 DEB 文件就地生成索引：

```bash
sow create /srv/repo
```

它写入 `repodata/`、`Packages` 与 `Packages.gz`。Plain 模式没有 Workspace、状态数据库、
Generation，也不生成或签署 DEB `Release`。

**Managed 模式**负责包成员关系与完整生命周期：

```bash
mkdir -p /srv/sow && cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow check -r pigsty
```

每个接纳的包体只在 `pool/` 下保存一次；RPM 与 APT 客户端视图位于 `dists/`，并以不可变
Generation 落成。

## 生命周期控制

Managed 仓库提供：

- 严格的 `sow/v3` 配置与显式成员策略；
- RPM 元数据、APT 元数据与可选 RPM 包体签名；
- 低成本 `status` 与作为发布门禁的九层 `check`；
- 可恢复的 filesystem 与 R2 发布尝试；
- 显式保留 Generation 与基于可达性的本地 GC；
- 面向拒绝 rpm-md 父级相对路径的消费者的独立 `rpm-leaf` 导出。

规范 Managed 树必须作为完整仓库交付。已配置目标使用 `sow publish`；其他传输方式应先把
整根复制到离线 staging，再原子切换。不要逐文件更新在线仓库。

## 兼容性证据

当前测试套件证明：两种格式都能由现行 CLI 在干净环境构建；Ubuntu 22.04 能消费 Plain APT
仓库；AlmaLinux 8/9/10 探针覆盖 RPM 分离签名行为；另有独立 S3 兼容 Provider Fixture。
这些探针本身不能证明完整的现行 Managed DNF/APT 或 R2 CLI 端到端验收。

确切声明边界见[兼容性](/zh/docs/reference/compatibility/)，全新安装入口见
[快速上手](/zh/docs/start/quickstart/)。
