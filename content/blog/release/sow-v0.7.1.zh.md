---
title: "SOW v0.7.1"
linkTitle: "SOW v0.7.1"
date: 2026-11-11T22:00:00+08:00
lastmod: 2026-11-11
authors: [Vonng]
description: "SOW 0.7.1 升级到 Go 1.27.4，更新依赖，并修复恢复、软件包校验和 S3/R2 处理。"
categories: [Release]
tags: [release, recovery, rpm, s3]
weight: -50
url: "/zh/blog/release/sow-v0.7.1/"
release_url: https://github.com/pgsty/sow/releases/tag/v0.7.1
---

{{< release-card >}}

SOW 0.7.1 更新 Go 工具链与依赖，并修复恢复、软件包校验、RPM 导出和 S3/R2 处理中的问题。

可从 [GitHub](https://github.com/pgsty/sow/releases/tag/v0.7.1) 或[下载页](/zh/download/)获取本版本。

本说明覆盖 **0.7.0** 以来的变化。数据库 schema **v13**、配置 schema **sow/v3**、CLI 与公开仓库布局保持兼容。**0.5.0 至 0.7.0** 的工作区无需迁移数据库。

## 恢复与仓库状态 {#recovery}

- 修复未启用有效签名时，旧版 `dist.new` 和 `dist.init` 操作中断后的恢复。
- 将无法证明可安全清理的 C2 迁移暂存文件完整保留到 `.sow/<repo>/abandoned/`，并报告路径。空暂存目录会被移除，重复恢复安全，本地 GC 可继续执行。删除前请检查报告路径中的文件。
- 在删除批次之间重新打开目录游标，避免 macOS APFS 与 BSD 文件系统上的清理遗漏。
- 将多语句 SQLite 读取放入同一个只读事务。大型 Dist 成员查询分批执行，避免超过 SQLite 参数上限。
- 规范化旧仓库中带小数秒的时间记录，并拒绝超出 `1..9999` 的年份。

## 软件包校验与 RPM 导出 {#packages}

- Plain `create`、`prune` 的全部路径及 Managed 入库一致拒绝 RPM v6。
- 限制 DEB control 归档与 APT/RPM 元数据流的解压大小，包括过大的 PAX 头部。
- 识别 Linux `renameat2` 不受支持时的错误，并保留跨平台回退实现。
- 无关的 filesystem 发布目标未挂载时，仍可执行 `export rpm-leaf`；实际物理路径重叠仍会被拒绝。
- 导出元数据签名使用所选 Dist 已记录的构建发布时间，后续其他 Dist 的构建不再改变该时间。导出 `repomd.xml` 的 data 时间戳仍为 `0`。
- `sow add` 同时接收显式文件和其父目录时，允许重复输入同一软件包。

## S3 与 R2 {#s3-r2}

新版 AWS SDK 会重试不带响应体的 HTTP 429。重试耗尽后，SOW 保留 HTTP 错误分类。

SOW 还能从组合错误中提取 HTTP 状态码。中止 multipart 上传时返回 HTTP 404，表示上传已被移除。列表与 multipart 操作的错误 XML 响应也增加了大小限制。

## 工具链与依赖 {#dependencies}

源码构建要求 **Go 1.27.4 或更新版本**。发布准备期间，已逐一核对全部 35 个显式依赖的最新可用版本。

| 组件 | 0.7.0 | 0.7.1 |
|---|---|---|
| Go | 1.27.3 | 1.27.4 |
| AWS SDK core / S3 | 1.47.8 / 1.114.9 | 1.48.0 / 1.114.10 |
| Smithy | 1.28.8 | 1.28.9 |
| klauspost/compress | 1.20.3 | 1.20.4 |
| modernc/libc | 1.80.1 | 1.81.0 |
| golang.org/x/sys | 0.49.0 | 0.50.0 |
| GoReleaser | 2.20.0 | 2.20.1 |
{.wide .expand}

同时更新 AWS 内部模块、pprof、`x/mod`、`x/sync` 和 modernc 编译器依赖，保留本地 RPM 解析器安全补丁。第三方许可声明已与新版本构建同步。

## 升级 {#upgrade}

停止工作区写入，以保留硬链接的方式备份完整工作区。安装 0.7.1，再对每个配置中的仓库执行构建与检查：

```bash
sow version
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

没有变化时，构建为 no-op。0.3 或 0.4 工作区仍需先执行 `sow repo migrate REPOSITORY`。Plain 仓库无需迁移数据库。

SOW 0.6.1 及更早版本无法读取包含 `passfile` 的配置，降级前须移除这些字段。RPM v6 仍不受支持。

本版本提供四个 Linux/macOS 归档、两个 RPM、两个 DEB，以及 `SHA256SUMS`。详见[升级指南](/zh/docs/start/install/#upgrade-to-071)和[完整变更](https://github.com/pgsty/sow/compare/v0.7.0...v0.7.1)。

{{< release-assets src="release/sow-v0.7.1-checksums.txt" group="auto" >}}{{< /release-assets >}}
