---
title: "SOW v0.6.1"
linkTitle: "SOW v0.6.1"
date: 2026-10-22T20:30:00+08:00
lastmod: 2026-10-22
authors: [Vonng]
description: "SOW 0.6.1 升级到 Go 1.27.3，更新依赖并修复无效输入的错误信息，工作区格式保持兼容。"
categories: [Release]
tags: [release, maintenance, dependencies]
weight: -30
url: "/zh/blog/release/sow-v0.6.1/"
---

SOW 0.6.1 是一次维护更新，升级依赖并改善错误信息。
命令接口、数据库 **schema v13**、配置 **sow/v3** 与公开仓库布局保持不变。
已使用 0.5.0 或 0.6.0 的工作区无需迁移数据库。

软件包与归档见[下载页](/zh/download/)，校验和来自
[v0.6.1 发布页](https://github.com/pgsty/sow/releases/tag/v0.6.1)。

## 工具链与依赖

源码构建现在要求 **Go 1.27.3 或更新版本**。所有发布二进制均使用 Go 1.27.3 构建。
本版更新了加密、S3 访问、压缩、SQLite 与 Debian 包解析等依赖。

| 依赖 | 版本 |
|---|---|
| ProtonMail go-crypto | 1.5.2 |
| AWS SDK for Go / S3 | 1.47.3 / 1.114.4 |
| klauspost/compress | 1.20.3 |
| modernc SQLite / libc | 1.61.0 / 1.79.0 |
| pault.ag/go/debian | 0.21.1 |
| go.yaml.in/yaml/v3 | 3.0.5 |
| golang.org/x/crypto / x/sys | 0.58.0 / 0.49.0 |

YAML 解析切换到 YAML 官方团队维护的模块，现有 `sow.yml` 配置格式不变。
RPM 解析器继续保留已有的本地安全补丁。
第三方许可清单已更新，随每个归档与 Linux 软件包分发。

## 维护修复

- 修复无效路径与 OpenPGP armor 类型的错误信息，不再出现 `%!w(<nil>)`。
  涉及日志导出、RPM 元数据生成、签名校验与工作区检查。
  原来被拒绝的无效输入仍然会被拒绝。
- CI 快照包直接从 Makefile 读取版本，避免遗漏硬编码版本号。
  同步更新发布工具与 GitHub Actions，包括 GoReleaser 2.18.3、deadcode 0.52.0 和 govulncheck 1.9.0。

## 升级

更换可执行文件前，停止工作区写入任务并备份完整工作区。
安装 0.6.1 后，对每个仓库执行构建与检查：

```bash
sow version
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

把 `REPOSITORY` 换成 `sow.yml` 中的仓库名。没有变化的仓库会报告空操作，保留原构建快照编号与时间戳。
安装命令以及从 0.3、0.4 迁移的步骤，见[安装指南](/zh/docs/start/install/#升级到-061)。

发布验证覆盖包测试、竞态检查、APT/DNF 客户端、S3 兼容传输，以及 50,000 包的 RPM 元数据生成。
升级与回退检查使用已发布的 0.6.0 二进制创建 RPM/DEB 工作区，由 0.6.1 操作后，再用 0.6.0 重新打开。

## 漏洞扫描结果

源码分析与保留符号的对照构建均未发现受影响的符号或导入包。
[GO-2026-5932](https://pkg.go.dev/vuln/GO-2026-5932) 涉及未使用的旧 `golang.org/x/crypto/openpgp` 包。
SOW 使用维护中的 ProtonMail 分支；四个发布目标的导入图均不包含该旧包。

发布二进制移除了符号表。对这类二进制，`govulncheck -mode=binary` 会退回模块级判断并报告此提示，
因此其二进制扫描结果与源码扫描不同。

发布附件包含 Linux 与 macOS 的 `amd64`、`arm64` 归档，两个 RPM、两个 DEB，以及 `SHA256SUMS`。
源码变化见[完整差异](https://github.com/pgsty/sow/compare/v0.6.0...v0.6.1)。
