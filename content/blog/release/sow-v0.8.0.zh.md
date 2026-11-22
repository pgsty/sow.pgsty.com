---
title: "SOW v0.8.0"
linkTitle: "SOW v0.8.0"
date: 2026-11-23T00:35:20+08:00
lastmod: 2026-11-23
authors: [Vonng]
description: "按需回收 R2 上的过期对象，使用挂载的密钥与口令文件签名，并减少大型 RPM、DEB 仓库发布和回收时的读取。"
categories: [Release]
tags: [release, r2, gc, signing, recovery]
weight: -60
url: "/zh/blog/release/sow-v0.8.0/"
release_url: https://github.com/pgsty/sow/releases/tag/v0.8.0
---

{{< release-card >}}

SOW 0.8.0 支持按需回收 R2 上的过期对象，也能直接使用挂载的密钥与口令文件签名。大型托管仓库发布时可以减少存储请求，本地垃圾回收可以分批处理积压的软件包。数据库继续使用 schema v13。

## 回收 R2 对象 {#r2-gc}

`sow gc TARGET` 默认生成候选报告。需要删除时，可以在查看报告后加上 `--delete`，也可以直接执行。删除前，SOW 会重新检查仍受保护的发布记录、缓存宽限期，以及每个对象的大小、SHA-256 元数据和 ETag。随后确认存储端已无此对象、公开 URL 返回 HTTP 404，再记录删除回执。

```bash
sow gc prod --json
sow gc prod --delete --json
```

每个目标前缀只应由一个工作区写入。删除中断时，重新执行带 `--delete` 的命令。如果软件包在旧报告生成后重新发布，SOW 会按这次发布重新计算保护期。详见[目标 GC](/zh/docs/command/gc/#target-gc)。

## 签名与软件包格式 {#signing}

- 外部口令文件、密钥和受信任密钥环可以使用符号链接，包括 Kubernetes Secret 挂载。链接解析的每一跳都必须位于工作区之外。平面仓库的 `create` 以仓库根目录为边界。
- `create --sign-with` 对签名后的 RPM 包进行 OpenPGP 验证。RPM 与 APT 元数据解析也会更严格地检查签名结构和软件包头。
- DEB 控制归档支持未压缩的 tar，以及 gzip、bzip2、xz 和 zstd。使用 `control.tar.lzma` 的二进制 DEB 需要先重新打包，再导入仓库。

## 发布与恢复 {#recovery}

- R2 列出的不可变对象与已知记录的路径、大小和 ETag 一致时，可以复用原有 SHA-256。文件系统目标可以在一次发布过程中复用已经验证的散列。
- 本地 GC 分批处理大量待回收对象。SQLite 批量更新仓库成员和发布记录，写连接重建后也会恢复 WAL 设置。
- 平面仓库的 `create` 和 `prune` 可以在相邻目录并行工作。托管仓库修复了删除仓库中途退出后恢复操作的加锁顺序。

## 升级与下载 {#upgrade}

先停止工作区写入，备份整个工作区并保留硬链接。**如果 0.7.1 的本地 GC 曾中断，先用 0.7.1 的二进制执行 `sow gc -r REPOSITORY -C WORKSPACE` 完成恢复。** 旧计划中的 `manifest` 可能是空数组，需要旧版读取。随后安装 0.8.0，对各仓库运行 `sow build` 和 `sow check`。从 0.5.0 至 0.7.1 升级均无需迁移数据库。详见[升级指南](/zh/docs/start/install/#upgrade-to-080)。

源码构建使用 Go 1.27.4。本版将 S3 SDK 升至 v1.116.0、SQLite 驱动升至 v1.63.0、`x/crypto` 升至 v0.59.0，打包使用 GoReleaser v2.20.3。Linux 和 macOS 归档、Linux RPM 与 DEB 安装包及校验值见[下载页](/zh/download/)。[完整变更记录](https://github.com/pgsty/sow/compare/v0.7.1...v0.8.0)。

{{< release-assets src="release/sow-v0.8.0-checksums.txt" group="auto" >}}{{< /release-assets >}}
