---
title: "能力总览"
linkTitle: "能力总览"
description: "v0.2.0 在仓库生成、Managed 状态、签名、发布与兼容性方面的实际能力。"
url: "/zh/docs/feature/overview/"
weight: 100
icon: fa-solid fa-table-list
---

SOW 0.2.0 是以单个自包含 Go 二进制交付的本地软件仓库管理器。仓库元数据在进程内生成，
SOW 本身不提供服务守护进程。

## 两条运行路径

| 能力 | Plain | Managed |
|---|---:|---:|
| RPM 与 DEB 元数据 | 是 | 是 |
| RPM + DEB 混合操作 | 同一目录 | 同一 Repository、不同 Dist |
| 持久成员关系与 Generation | 否 | 是 |
| 架构视图 | 否 | 是 |
| `exclude` 与版本 `limit` 策略 | 否 | 是 |
| 元数据签名 | 否 | RPM 与 DEB |
| RPM 包签名 | `--sign-with` | `never`、`fill`、`always` |
| 事务日志与恢复 | 无；重跑即重建 | Workspace、Repository、发布 |
| 审计日志与 JSONL 导出 | 否 | 是 |
| 发布目标 | 否 | filesystem 与 R2 |

Plain 与 Managed 不共享状态。`sow create` 不发现 Workspace；Managed 命令也不会把任意平面
目录当作状态接管。

## 仓库元数据

| 表面 | RPM/YUM | DEB/APT |
|---|---|---|
| 包事实来源 | RPM header | DEB control archive |
| 身份 | NEVRA + 确切字节 SHA-256 | `name=version:arch` + 确切字节 SHA-256 |
| 索引 | `primary`、`filelists`、`other`、`repomd.xml` | `Packages`、`Packages.gz`、`Release` |
| Managed 架构名 | `x86_64`、`aarch64` | `binary-amd64`、`binary-arm64` |
| 中性架构 | `noarch` | `all` |
| 不可变索引寻址 | 校验和命名 rpm-md | `by-hash/SHA256` |
| Managed 元数据签名 | `repomd.xml.asc` | `InRelease`、`Release.gpg` |

SOW 有意不生成 SQLite rpm-md、zchunk、modulemd 与源码包索引。DEB 元数据只使用 SHA-256，
不生成 MD5/SHA1 manifest。

## Managed 生命周期

Managed 模式提供：

- 严格 `sow/v3` 配置与向上 Workspace 发现；
- Repository 隔离、一条规范包池与纯元数据视图；
- Desired Membership、Built Generation、dirty 检测与物理 changeset；
- 有界锁、持久操作日志、崩溃恢复与 fail-closed 路径检查；
- `status`、九层 `check`、包查询与可导出操作日志；
- 显式 Generation 保留、本地 GC、target 级发布与 GC 状态；
- 为必须使用本地包 href 的流程生成自包含 RPM leaf。

## 签名与外部程序

使用路径、`file://` 或 `env://` 私钥引用的元数据签名在进程内完成。`agent://` 元数据 key
使用 `gpg`/`gpg-agent`。RPM 包签名会改写包体，因此使用环境中的 `rpm` 命令与 GPG 配置。
元数据生成、包解析、SQLite 状态与发布不需要外部命令行工具。

## 发布

每个 target 把一个 Repository 绑定到一个 Provider prefix：

| Provider | v0.2.0 行为 |
|---|---|
| `filesystem` | 发布并校验 Generation；通过已记录安全门禁后条件式执行生命周期删除 |
| `r2` | 通过 S3 兼容 API 发布；target GC 只报告候选，绝不删除对象 |

发布不等于 HTTP 服务。`public_endpoint` 用于描述 SOW 验证的公共表面；实际服务器、bucket、
CDN、凭据与访问策略由操作者提供。

## 平台与证据

Release 构建目标是 Linux/macOS 的 `amd64` 与 `arm64`，并使用 `CGO_ENABLED=0`。Managed
工作区依赖本地 POSIX 锁、fsync 与原子 rename；不声明网络文件系统为受支持构建位置。

客户端与 Provider 结论刻意窄于元数据格式能力。当前 CI 与本地证据、以及尚未完成的端到端
验证，见[兼容性](/zh/docs/reference/compatibility/)。

## 明确非目标

- 构建软件包；
- 提供 HTTP 服务或运营 CDN；
- 多 writer 或分布式协调；
- 跨 Repository 包体去重；
- 自动删除 R2 对象；
- module stream、源码包索引、SQLite rpm-md 或 zchunk；
- Web UI。

## 继续阅读

- [Plain 平面仓库](/zh/docs/feature/plain/)
- [Managed 工作区](/zh/docs/feature/managed/)
- [签名模型](/zh/docs/feature/signing/)
- [发布与恢复](/zh/docs/design/publication/)
