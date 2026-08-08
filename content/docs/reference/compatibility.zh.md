---
title: "兼容性"
linkTitle: "兼容性"
description: "SOW 0.2.0 的已验证客户端、发布平台、reposync 边界与发布 Provider 状态。"
url: "/zh/docs/reference/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

SOW 0.2.0 输出标准 rpm-md 与 Debian archive 元数据。本页把普通客户端消费与兼容性
导出分开,也把集成测试证据与特定 Provider 的生产验证分开。

## 包管理器客户端

维护中的客户端矩阵覆盖刷新索引、发现软件包与安装:

| 客户端 | 已测行为 |
|---|---|
| AlmaLinux 8 / 9 / 10 `dnf` | `makecache` 与安装,包括仓库和包签名校验 |
| CentOS 7 `yum` 3.4.3 | 元数据与包列表,包括多版本 NEVRA 排序 |
| Debian 12 / 13 `apt` | 已签名 `InRelease`、by-hash 索引拉取与安装 |

`sow create` 生成的平面仓库可通过 `file://` 与 HTTP 被 `dnf`、`yum`、`apt` 消费。
平面 APT 仓库没有已签名 `Release`;请使用 `[trusted=yes]`,或在需要认证时采用已签名
Managed Dist。

## 规范 RPM 布局与 reposync

普通 DNF/YUM 消费支持纯元数据视图。默认 `dnf reposync` **不支持**直接镜像规范视图,
因为 rpm-md 包 href 使用 `../../../pool/...`,镜像工具会拒绝逃出 leaf 下载根的目标。

下游镜像流程应显式生成自包含产物:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

导出会把 href 改写为本地 `pool/`。应把导出验证与规范仓库验证分开;导出不会修改
Managed 仓库。

## 二进制平台

Release archive 使用 `CGO_ENABLED=0` 构建:

| 操作系统 | `amd64` | `arm64` |
|---|---|---|
| Linux | 支持 | 支持 |
| macOS (Darwin) | 支持 | 支持 |

Linux 另外提供 RPM 与 DEB 包。不支持 Windows:工作区模型依赖 POSIX 建议锁与原子 rename。

## 文件系统边界

Managed 仓库应在本地 POSIX 文件系统上构建。SOW 不声称 NFS 等网络文件系统正确,
因为事务模型依赖本地锁、fsync 与 rename 语义。v0.2.0 规范布局不要求 `pool/` 与
`dists/` 间使用硬链接;早先的视图级硬链接布局只是未发布原型。

提交完成后,完整公共仓库可以普通复制,也可以由 SOW 发布。始终一起保留 `pool/` 与 `dists/`。

## 发布 Provider

| Provider | v0.2.0 状态 |
|---|---|
| `filesystem` | 已实现;宽限期与缺失检查后可做条件式生命周期维护 |
| `r2` | 已通过 S3 兼容 API 实现;Integration CI 使用固定版本 MinIO 验证该路径 |
| Cloudflare R2 生产账户 | 授权、凭据与托管行为必须在目标环境另行验证 |
| R2 删除 | 有意禁用;`sow gc TARGET` 只持久化候选报告,绝不删除对象 |

这一边界很重要:S3 兼容集成测试通过是实现证据,并不证明某个 Cloudflare 账户或公共 CDN
已经正确配置。

## SOW 有意省略的元数据

| 不生成 | 后果 |
|---|---|
| SQLite repodata | DNF/YUM 使用 XML 元数据 |
| `modulemd` | 模块化流不在范围内 |
| zchunk | 客户端下载普通压缩元数据 |
| DEB MD5/SHA1 清单 | 要求 SHA256 |
| 源码包索引 | v0.2.0 管理二进制包 |

Managed DEB 视图发布 `by-hash/SHA256/`;RPM 视图使用校验和命名的元数据文件。
两者都让不可变元数据在可变指针切换时继续可达。

## 外部工具

元数据生成与解析都在进程内完成。RPM 包签名需要 `rpm` 与可用的 GPG 环境。
`agent://` 元数据 key 需要带 agent 的 `gpg`;`file://` 与 `env://` 元数据签名在进程内完成。

## 版本

```console
$ sow version
sow 0.2.0 darwin/arm64 go1.26.5
```

具体 OS、架构与 Go 版本取决于所运行二进制。Release 身份是 `v0.2.0`;
`sow.cli/v1`、`sow/v3`、`sow/export/v1` 是协议或 Schema 标识,不是产品版本。

## 延伸阅读

- [仓库布局](/zh/docs/reference/layout/)
- [配置参考](/zh/docs/reference/config/)
- [CLI:发布、保留、GC 与导出](/zh/docs/reference/cli/publication/)
