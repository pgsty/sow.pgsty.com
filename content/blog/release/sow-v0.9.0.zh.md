---
title: "SOW v0.9.0"
linkTitle: "SOW v0.9.0"
date: 2026-11-27T13:30:00+08:00
lastmod: 2026-11-27
authors: [Vonng]
description: "平面仓库默认容错与 --strict 模式、RPM v6 与原生 OPENPGP 多签名验签、sow.yaml 支持，以及按 max_cache_ttl 直接生效的目标 GC 宽限期。"
categories: [Release]
tags: [release, plain, rpm, signing, gc]
weight: -70
url: "/zh/blog/release/sow-v0.9.0/"
release_url: https://github.com/pgsty/sow/releases/tag/v0.9.0
---

{{< release-card >}}

SOW 0.9.0 让平面模式的 `create` 与 `prune` 默认对异常包具备容错能力，新增完整的 RPM 格式 v6 与原生 OPENPGP 多签名验签支持，同时支持 `sow.yml` 与 `sow.yaml`，并让目标 GC 宽限期直接按 `max_cache_ttl` 生效。数据库继续使用 schema v13。

## 平面仓库默认容错 {#flat-fault-tolerance}

平面模式的 `sow create` 与 `sow prune` 现在默认跳过损坏、不可读、源码（`src`/`nosrc`）及坐标冲突的软件包（包括 Debian 版本等价冲突，例如 `1.0-1` 与 `1.00-1`），以及未匹配到的 `--protect` 包名，并发出告警，避免单个异常包阻断其余合法包的发布。需要遇错即停时，传入 `--strict`。

```bash
sow create /srv/flat                 # 跳过异常输入并输出告警
sow create /srv/flat --strict        # 遇到任何异常或冲突输入立即失败
sow prune /srv/flat --dry-run        # 安全预览被取代的旧版 RPM
```

- **按格式隔离失败：** 当某一种格式的全部候选包都解析失败时，SOW 会保留该格式原有的索引、历史记录与完成标记，同时正常发布另一种格式的合法包（包括全新的 `--pigsty` 目录）。
- **混合目录裁剪：** 在同时包含 RPM 与 DEB 的目录中，`sow prune` 只更新 RPM 索引、保持 DEB 索引原样，并在 `repo_complete` 中沿用仍在目录内的已记录 DEB 摘要，不再提前对尚未入索引的新 DEB 计算哈希。
- **结构化告警：** 文本模式将告警输出到 `stderr`；成功的 `--json` 输出将 `warnings` 与 `skipped` 写入 `stdout` 的 JSON 信封，保持 `stderr` 为空。
- **单遍扫描与变更检查：** SOW 在单遍读取的同时，继续在扫描后、发布前、签名替换前及删除前核对文件身份、大小与修改时间，避免重复全量解压回读。

## RPM v6、包解析与签名 {#rpm-v6-and-signing}

- **RPM 格式 v6 与原生 OPENPGP 签名：** 在平面 `create`、`prune`、`--sign-with` 以及 Managed `add`、`build`、`check` 中全面支持 RPM 格式 v6（lead 主版本 3 至 6、不带 `PAYLOADSHA256ALGO` 的 `PAYLOADSHA256`、以及原生 `RPMSIGTAG_OPENPGP` tag `278` 的 OpenPGP v4/v6 签名数组），包括双签与多签 RPM。存在 tag `278` 时，以其验证结果为准，不再由旧签名标签掩盖。
- **真实生态包兼容：** RPM 索引接受重复且值完全相同的主头标签（例如 EL10 包中重复出现的 `SOURCERPM`），同时继续拒绝取值冲突的主头标签与重复的签名头标签。二进制 `.deb` 的 `control` 文件中遗留的 Latin-1 字节（`>= 0x80`）会自动规范化为 UTF-8；`.asc` OpenPGP 密钥环兼容装甲围栏外的说明文本。
- **更丰富的签名算法与口令文件：** 元数据签名新增支持 ECDSA 与 DSA 密钥（与 RSA、EdDSA/Ed25519/Ed448 并列）。`--passfile`、`SOW_GPG_PASSFILE` 与 `passfile` 支持普通文件、符号链接（含 Kubernetes Secret 挂载）和命名管道（FIFO，2 秒超时），自动剥离可选 UTF-8 BOM 及末尾 LF/CRLF，并在工具失败时输出有界的 `stderr` 诊断摘要。

## 托管工作区、发布与 CLI {#managed-and-publication}

- **直接遵循 `max_cache_ttl` 宽限期：** 新建目标 GC 宽限期记录直接使用配置的 `max_cache_ttl`，移除了硬编码的 30 天下限和 24 小时附加缓冲。先前已记录的更晚 `NotBefore` 截止时间继续生效；NTP 时钟回拨会保留时间见证高水位，不再阻塞操作。
- **目标配置简化与安全校验：** `authoritative_workspace`、`single_writer` 与 `exclusive_write_authority` 省略时默认取 `true`（显式写 `false` 仍被拒绝）。R2 的 `region` 默认为 `auto`，支持带点号的桶名以及 `24h`、`0` 等简写时长并自动规范化；同一 `(endpoint, bucket, prefix)` 下即使 `region` 拼写不同（如 `auto` 与 `us-east-1`）也会拒绝重叠目标。
- **加固的公开 HTTP 校验：** 公开可见性检查支持跟随 CDN 重定向，逐跳禁止 HTTPS 降级到 HTTP，校验实际连接的拨号 IP 以拦截回环与链路本地地址，并拒绝经 HTTP 代理跳转至跨源地址。目标根目录中位于 `pool/` 与 `dists/` 之外的无害外部文件不再触发报错。
- **工作区配置、SQLite 与锁恢复：** 工作区统一支持 `sow.yml` 与 `sow.yaml`（同时兼容与 `sow.yml` 并存的旧仓库目录 `sow.yaml/`），显式传入 `-C`/`--workdir` 时不再回退到当前目录或 `SOW_DIR`。SQLite 先解析物理数据库路径再探测 `-wal`/`-shm`/`-journal` 伴随文件并强制单硬链接校验，移除了 Darwin 专用 C ABI 代码。已有数据的 `.sow/` 丢失 `workspace.lock` 时要求离线恢复，而 `sow init` 可在持有 `workspace.lock` 下修复缺失的单仓库锁文件。
- **托管运维改进：** `sow check` 将 `sow.yml` 中 `limit`/`exclude` 策略变化报告为 `dirty` 而非完整性错误，在硬链接断开后按内容摘要校验 APT `by-hash` 文件，并容忍 `.sow/` 中的 `.DS_Store`。`sow rm --check` 保持严格只读且不触碰 `.sow/<repo>/stage`，`sow add -R` 忽略不可读的非包文件，旧 schema v12 需迁移错误在所有命令中一致返回退出码 `6`，中断的 v0.7.1 空 `manifest` 数组本地 GC 计划现在可直接恢复。
- **CLI 与发布包简化：** 重复参数采用后者覆盖前者语义，布尔参数支持 `=true`/`=false`，接受 `--timeout 0s`，`sow log export FILE` 解析符号链接父目录（修复 macOS `/tmp`），发布归档与 Linux 安装包直接包含 `sow` 可执行文件与 `LICENSE`。

## 升级与下载 {#upgrade}

> [!WARNING]
> 升级前请检查是否将发布目标配置为 `max_cache_ttl: 0s`。新产生的目标 GC 宽限期记录不再自带 30 天下限，配置为 `0s` 时被取代的对象在下一次目标 GC 即可能达到清理条件；升级前已记录的较晚 `NotBefore` 截止时间仍继续生效。

0.5.0 至 0.8.0 的工作区保持使用 schema v13，无需数据库迁移。停止工作区写入，使用保留硬链接的方式备份整个工作区，安装 SOW 0.9.0，然后对每个仓库执行 `sow build` 与 `sow check`。此前在 0.7.1 中断且包含空 `manifest` 数组的本地 GC 计划，现在可直接由 0.9.0 恢复，无需先切回 0.7.1。详见[升级指南](/zh/docs/start/install/#upgrade-to-090)。

Linux 和 macOS 归档、Linux RPM 与 DEB 安装包及校验值见[下载页](/zh/download/)。[完整变更记录](https://github.com/pgsty/sow/compare/v0.8.0...v0.9.0)。

{{< release-assets src="release/sow-v0.9.0-checksums.txt" group="auto" >}}{{< /release-assets >}}
