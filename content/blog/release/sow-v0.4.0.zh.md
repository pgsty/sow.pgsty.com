---
title: "SOW v0.4.0"
linkTitle: "SOW v0.4.0"
date: 2026-08-24
authors: [Vonng]
description: "SOW v0.4.0 减少重复校验，独立验证 RPM 密钥集合，支持目标重绑定，并改进迁移与发布恢复。"
categories: [Release]
tags: [release, managed, signing, publish, migration]
weight: 1
url: "/zh/blog/release/sow-v0.4.0/"
draft: false
---

SOW 0.4.0 改进了 Managed 仓库的校验与恢复。`check` 只对每个物理软件包计算一次内容哈希；RPM 验签分别判断各组密钥的信任结果；发布目标可通过有记录的重绑定操作修改公共 URL 或缓存时间。

Plain 行为与公共 `pool/`、`dists/` 布局保持不变。本文记录 0.4.0；升级到当前版本请按[安装指南](/zh/docs/start/install/)操作。

<span id="从-03-升级"></span>

## 从 0.3 升级到 0.4

停止工作区写入，备份完整工作区并保留硬链接。安装 0.4.0 后，先迁移每个已配置的 Repository，再继续维护：

```bash
set -euo pipefail
rsync -aH /srv/sow/ /srv/sow.backup-before-0.4.0/
sow repo migrate pigsty -C /srv/sow
sow repo migrate pgsql -C /srv/sow
sow check -r pigsty -C /srv/sow
sow check -r pgsql -C /srv/sow
```

本例的仓库名为 `pigsty` 与 `pgsql`，请换成 `sow.yml` 中的实际名称。保留备份用于回退：SOW 0.3 无法打开迁移后的数据库。

Schema v11 修复了 0.3 的状态错误：一个 Dist 仍为 dirty 时，Repository 可能错误显示 clean。现在，Dist 变更与仓库状态在同一事务中更新。迁移还修复发布与签名者记录；从未记录的历史签名身份仍标记为未验证。

Schema v12 为发布目标增加只追加的绑定历史。初次绑定、迁移回填与后续重绑定都有独立修订记录。

<span id="每个物理包体只做一次真实性认证"></span>

## 每个物理软件包只计算一次内容哈希

每次 `sow check` 对每个唯一物理软件包执行一次完整内容哈希，包括缓存指纹仍匹配的文件。同一文件的硬链接共用这个结果。校验结果绑定实际读取的文件，SOW 会检测检查期间的替换或修改。

检查保留的构建快照、最终清单与变更时，复用同一结果。增加 Dist 或保留的构建快照不会增加包哈希次数。DEB 与未签名 RPM 需要一次完整读取；已签名 RPM 最多再从主包头读到文件末尾，验证签名。

包缓存只查询本次选中的摘要，并按限定批次读取 SQLite。64 MiB 测试包的重复构建不读取包内容；指纹变化与缓存缺失共用一次校验。

<span id="独立-rpm-信任环"></span>

## 分别验证 RPM 密钥集合

RPM 签名包在每组候选密钥内独立检查。每个可识别签名包都必须在该组中通过验证，且至少一个通过的签名必须认证软件包载荷。

这保留了对历史 CentOS 签名与双签软件包的支持，也避免把不同密钥组中的部分成功结果拼成错误的单密钥验证结论。

当前策略密钥、保留的构建快照密钥与组合受信任密钥共用同一次签名读取。增加密钥只改变信任判断，不增加包读取次数。

<span id="安全重绑定目标与公共验证"></span>

## 修改发布目标设置

使用 `sow publish TARGET --rebind` 修改目标的可变配置，同时保留存储身份与恢复状态：

| 可通过 `--rebind` 修改 | 需要配置新目标 |
|---|---|
| 目标名称 | Repository 身份 |
| `public_endpoint` | Provider 或存储 `endpoint` |
| `max_cache_ttl` | Region、bucket 或 `prefix` |

普通发布会报告配置变化，并提示使用 `--rebind`。重绑定取得发布锁、记录修订，也可继续执行已作出提交决定但被中断的发布。清理未完成时，TTL 与 filesystem 公共 URL 的变更受到限制。此前记录的缓存截止时间继续生效。

<span id="恢复cli-与实现收敛"></span>

## 检查公共文件与恢复上传

Filesystem 与 R2 的 HTTP(S) 检查分别限制等待响应头和响应体停止传输的时间。只要持续接收数据，大文件传输可以超过两分钟。

SOW 检查普通客户端 URL。过期内容与 404 最多等待 `max_cache_ttl`；临时 408、425、429 与 5xx 响应使用较短重试时间。响应过大时校验失败。Filesystem 清理在删除后检查公共端点是否返回 404 或 410；R2 清理仍只报告候选对象。

其他发布改进包括：

- 创建目标绑定前检查 filesystem 路径别名，包括大小写不敏感卷上的别名。
- 中断的指针更新包含记录中的旧内容或新内容时，可继续执行；遇到其他内容则报告问题。
- 每次发布只检查发生变化的公共对象，不再下载完整构建快照。
- R2 使用可重试读写、空闲超时与限制并行数的条件式分段上传，完成上传前检查整对象 SHA-256。

## CLI 与维护修复

- 重复执行 `sow add` 时，即使包已在包池中，也会构建此前因 `--skip` 或配置变化而处于 dirty 状态的所选 Dist。
- `sow rm --check` 使用与删除相同的配置检查，并返回只读预览。
- 所有 Managed 命令提供可读文本输出。`sow.cli/v1` JSON 在命令失败时保留部分结果或诊断结果。
- 局部构建、Dist 变更、迁移、保留与垃圾回收过程保持签名者记录一致。
- 移除已退役的 APT 构建器、外部排序、空 Dist 与 Git 跟踪的 by-hash 实现。

<span id="验证与制品"></span>

## 构建与发布检查

本版使用 Go 1.27.0，0.3 使用 Go 1.26.5。AWS SDK、SQLite、压缩与密码学依赖同步更新。构建检查固定使用 staticcheck v0.8.1、deadcode v0.49.0 与 govulncheck v1.7.0。

发布检查覆盖 Go 测试、静态分析、漏洞与 RPM 分支源码检查、竞态测试、Linux amd64/arm64 构建，以及上述包读取次数限制。

本版包含四个 Linux/macOS 归档、两个 RPM、两个 DEB 与 `SHA256SUMS`。归档包含 `sow`、`README.md`、`CHANGELOG.md` 与 `LICENSE`。Linux 软件包随可执行文件安装协议文件。

<span id="获取发布版本"></span>

## 获取 0.4.0

从 [v0.4.0 GitHub Release](https://github.com/pgsty/sow/releases/tag/v0.4.0) 获取该版本制品与校验清单。安装后执行 `sow version`；0.3 工作区按上文迁移。

现在首次安装请使用[当前下载页](/zh/download/)。当前行为见 [Managed 工作区](/zh/docs/feature/managed/)、[签名模型](/zh/docs/feature/signing/)与[发布与恢复](/zh/blog/design/publication/)。
