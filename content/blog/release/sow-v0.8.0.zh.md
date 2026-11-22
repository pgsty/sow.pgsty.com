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

`sow gc TARGET` 默认生成候选报告。需要删除时，可以在查看报告后加上 `--delete`，也可以直接执行。删除前，SOW 会重新检查仍受保护的发布记录、缓存宽限期，以及每个对象的大小、SHA-256 元数据和 ETag。随后确认存储端已无此对象、公开 URL 返回 HTTP 404 或 410，再写入绑定因果发布纪元的删除回执。

```bash
sow gc prod --json
sow gc prod --delete --json
```

每个目标前缀只应由一个工作区写入。删除中断时，重新执行带 `--delete` 的命令；未加 `--delete` 运行会拒绝未完成的条件删除报告。如果软件包在旧报告生成后重新发布，SOW 会按这次发布重新计算保护期，重复发布相同字节保持幂等。详见[目标 GC](/zh/docs/command/gc/#target-gc)。

## 签名与软件包格式 {#signing}

- 外部口令文件、密钥和受信任密钥环可以使用符号链接，包括 Kubernetes Secret 挂载。链接解析的每一跳都必须位于工作区之外。平面仓库的 `create` 以仓库根目录为边界。临时 RPM 口令文件在删除前先以零字节覆写；设置 `GNUPGHOME` 时自动传给 `rpmsign`。
- `create --sign-with` 对签名后的 RPM 包进行 OpenPGP 密码学验证。新的 Managed RPM 元数据发布（`repomd.xml.asc`）与 APT 元数据同样强制要求 SHA-256 及以上摘要算法；RPM 与 APT 解析也更严格地检查签名结构与软件包头。
- DEB 控制归档支持未压缩的 tar，以及 gzip、bzip2、xz 和 zstd。本版移除 `control.tar.lzma` 解压支持以及不再维护的 `kjk/lzma`、`pault.ag/go/debian/deb` 依赖；使用 `control.tar.lzma` 的二进制 DEB 需要先重新打包，再导入仓库。

## 发布、恢复与 CLI {#recovery}

- R2 列出的不可变 `pool/` 对象与已知记录的路径、大小和 ETag 一致时，复用原有 SHA-256。文件系统目标在同一会话中复用已验证散列，并在条件删除后清理空的 `pool/` 和 `dists/` 父目录。
- 本地 GC 分批处理大量待回收对象，并自动重放中断的 `retain-remove-*` 墓碑（`sow check` 会报告未完成的移除阶段）。SQLite 批量更新仓库成员和发布记录，重建的写连接保持 WAL 持久化与 `BEGIN IMMEDIATE` 事务。
- 平面仓库的 `create` 和 `prune` 在绑定目标后即释放父目录锁，相邻目录可并行工作。`create` 拒绝在 Managed `.sow` 工作区内部或未加 `--pigsty` 时覆盖中断的 `.sow-prune-repo-complete` 标记。托管仓库统一 `dist new`、`dist rm` 与 `repo migrate` 的 `workspace.lock` -> `repo.lock` 加锁顺序。
- 冻结的 `sow/v2` 工作区支持只读检查命令（`config check`、`repo ls`、`repo show`、`dist ls`、`dist show`）。`log prune --json` 填充顶层 `operation`，`where -r NAME --json` 填充顶层 `repository`；目录中只有 `sow.yaml` 而缺少 `sow.yml` 时，工作区发现会给出明确提示。

## 工具链与依赖 {#dependencies}

源码构建要求 **Go 1.27.4 或更新版本**。CI 新增 macOS 契约测试与已签名的 Managed APT/DNF 容器测试，S3 兼容发布测试更新至 Silo `20261112`。

| 组件 | 0.7.1 | 0.8.0 |
|---|---|---|
| Go | 1.27.4 | 1.27.4 |
| AWS SDK S3 | 1.114.10 | 1.116.0 |
| modernc/sqlite | 1.62.0 | 1.63.0 |
| modernc/libc | 1.81.0 | 1.82.12 |
| klauspost/compress | 1.20.4 | 1.20.5 |
| golang.org/x/crypto | 0.58.0 | 0.59.0 |
| pault.ag/go/debian | 0.21.3 | 0.21.4 |
| GoReleaser | 2.20.1 | 2.20.3 |
{.wide .expand}

## 升级与下载 {#upgrade}

先停止工作区写入，备份整个工作区并保留硬链接。**如果 0.7.1 的本地 GC 曾中断，先用 0.7.1 的二进制执行 `sow gc -r REPOSITORY -C WORKSPACE` 完成恢复。** 旧计划中的 `manifest` 可能是空数组，需要旧版读取。随后安装 0.8.0，对各仓库运行 `sow build` 和 `sow check`。从 0.5.0 至 0.7.1 升级均无需迁移数据库。详见[升级指南](/zh/docs/start/install/#upgrade-to-080)。

Linux 和 macOS 归档、Linux RPM 与 DEB 安装包及校验值见[下载页](/zh/download/)。[完整变更记录](https://github.com/pgsty/sow/compare/v0.7.1...v0.8.0)。

{{< release-assets src="release/sow-v0.8.0-checksums.txt" group="auto" >}}{{< /release-assets >}}
