---
title: "SOW v0.3.0"
linkTitle: "SOW v0.3.0"
date: 2026-08-10
authors: [Vonng]
description: "SOW v0.3.0 减少重复软件包读取与数据库查询，批量提交包文件，并增加构建进度事件。"
categories: [Release]
tags: [release, plain, managed, transaction]
weight: 5
url: "/zh/blog/release/sow-v0.3.0/"
draft: false
---

SOW 0.3.0 减少了重复包读取与数据库查询。Plain 生成只遍历一次包内容；Managed 构建缓存已解析的包数据，并批量提交新包池文件。本版还移除了已退役的运行时与发布代码。

<span id="plain一遍完成包体处理" data-td-print-local></span>

## Plain：每个软件包只读一次

默认不签名的 `sow create` 流程对每个 RPM 或 DEB 只做一次哈希与解析，`--jobs` 控制并行任务数。SOW 根据解析结果生成元数据，写入索引前再次检查软件包集合与文件属性是否变化。

Plain 构建中断后，从软件包目录重新运行即可。0.3 移除了 Plain 的操作日志、回滚副本与重复包哈希；Managed 恢复机制不变。

Pigsty 预处理现在保留包头架构为 `i386`、`i486`、`i586` 或 `i686` 的 RPM。它们继续进入仓库元数据与 `repo_complete` 校验清单。DEB `i386` 与精确匹配 Patroni 3.0.4 的过滤规则保持不变。

<span id="managed扩展规模不放松完整性" data-td-print-local></span>

## Managed：减少查询与包读取

成员表增加了按软件包 SHA-256 的反向索引。SOW 通过一次有序查询读取期望成员与已构建成员，替代逐对象查询。项目基准中，列出含 5,000 个对象的 Dist 从约 4.1 秒降至 33 毫秒；50,000 个对象可在一秒内完成。

Schema v10 新增可重建的包数据缓存，以软件包 SHA-256 为键。导入时校验并解析新包，保存生成元数据所需的信息。构建时批量读取缓存；条目缺失或损坏时，从已校验的包文件重建。

包池不变时，重复构建通过设备号、inode、大小、修改时间与状态变更时间识别未变化文件。指纹变化时，执行完整 SHA-256 检查。`sow check` 仍会读取并校验完整包内容。

RPM 元数据与 DEB 架构索引使用受 `--jobs` 限制的并行任务。构建快照清单与变更记录改为批量写入。

<span id="有界提交与可观察构建" data-td-print-local></span>

## 批量提交与构建进度

Managed 构建将软件包分批移入公共包池，每批最多 512 个对象或 1 GiB。SOW 先持久保存目标目录，再移除 pending 名称。批次中断时，无论包位于 pending、包池还是两处，恢复流程都能处理。

Pending 文件在私有 `0700` 目录中使用最终的 `0644` 权限。构建不再全程为每个 pending 包持有文件描述符，减少了大型仓库的资源占用。

长时间构建会为渲染、包文件提交、Dist 发布、规范化与完成阶段记录 `build_progress` 事件。使用 `sow log` 查看进度。

<span id="收敛发布与运行时边界" data-td-print-local></span>

## 统一仓库实现

本版移除了已退役的 V1 CLI 与运行时、云与 CDN 发布代码、Edge Worker、已完成的迁移程序及其旧测试。当前 CLI 使用统一的仓库实现。

R2 发布保留 SOW 所需的存储操作：list、HEAD、GET 与条件 PUT。远端垃圾回收只报告候选对象，不执行删除。

<span id="正确性与发布质量" data-td-print-local></span>

## 其他变更

- 本地垃圾回收可处理大小写不敏感文件系统中记录的唯一包池路径别名，删除前检查包路径、大小与摘要。
- 归档包含 `LICENSE`。RPM 与 DEB 分别把 Apache-2.0 协议安装到 `/usr/share/licenses/sow/LICENSE` 与 `/usr/share/doc/sow/copyright`。
- CI 覆盖格式化、模块一致性、静态分析、死代码检查、测试、竞态检测、源码交付与软件包构建。
- 集成测试覆盖混合 RPM/DEB 流程、Ubuntu 22.04 上未签名 Plain APT 安装、AlmaLinux 8/9 与 `pgsty/el10` 的 DNF 签名切换，以及固定 MinIO 版本上的 S3 条件操作。

<span id="获取发布版本" data-td-print-local></span>

## 获取 0.3.0

在 [v0.3.0 GitHub Release](https://github.com/pgsty/sow/releases/tag/v0.3.0) 下载该版本的 Linux/macOS 归档、Linux RPM/DEB 软件包与 `SHA256SUMS`。安装后执行 `sow version`。该源码标签要求 Go 1.26.5 或更新版本。

现在首次安装请使用[当前下载页](/zh/download/)。当前行为见 [Plain 模式](/zh/docs/feature/plain/)、[Managed 工作区](/zh/docs/feature/managed/)与[平台与集成](/zh/docs/reference/compatibility/)。
