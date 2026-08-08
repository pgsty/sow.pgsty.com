---
title: "兼容性"
linkTitle: "兼容性"
description: "v0.2.0 在构建、客户端、镜像工具、文件系统与发布方面的确切证据。"
url: "/zh/docs/reference/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

本页只报告证据，不推导兼容性。元数据语法、clean-room CLI、真实包管理器、镜像工具与存储
Provider 是相互独立的检查。

## 当前自动化证据

| 表面 | 环境 | 现行检查真正证明了什么 | 没有证明什么 |
|---|---|---|---|
| v0.2.0 CLI clean room | Linux CI | 构建生产二进制；生成混合 Plain RPM/DEB 元数据；初始化 `sow/v3`；创建空 RPM/DEB Dist；添加 fixture；运行查询、build、check、changes、config 与 log | 没有真实包管理器或远端 Provider |
| Plain APT 客户端 | Ubuntu 22.04 容器 | 当前 `sow create` 结果通过 HTTP 被 `apt update`、发现并按精确版本安装；使用 `[trusted=yes]` 未签名平面源 | Managed APT、`Release` 签名或 `by-hash` 消费 |
| RPM detached-signature 探针 | AlmaLinux 8、9、10 容器 | `repomd.xml` 与分离签名串行变化时的真实 DNF 行为 | 当前 Managed CLI 布局、包安装、包签名或 `sow export rpm-leaf` |
| S3 兼容协议 fixture | 固定版本 MinIO | 独立 `internal/publish` Provider 实现的 S3 操作与条件删除失败行为 | 当前 `internal/v2/managed` 的 `sow publish r2` CLI 路径或 Cloudflare R2 账户 |

后两行是有价值的协议证据，但不能宣传成产品端到端兼容性。

## 当前客户端结论

- **已验证：** v0.2.0 CLI 生成的 Plain DEB 仓库，在显式信任时可由 Ubuntu 22.04 APT
  通过 HTTP 消费并安装。
- **格式已实现、当前缺少完整客户端门禁：** Plain/Managed rpm-md、Managed APT
  `Release`/`by-hash`、元数据签名与 RPM 包签名。
- **现行矩阵不声明：** CentOS 7、Debian 12/13、DNF 消费规范 Managed Repository、
  已签名 Managed APT 安装或完整已签名 DNF 安装。

缺少门禁表示当前未验证，不表示已知不兼容。

## 规范 RPM 布局与 `reposync`

Managed RPM view 只含元数据。包 href 从架构仓库基址 `dists/DIST/ARCH/` 解析回
Repository 包池：

```text
../../../pool/p/package/package.rpm
```

rpm-md 的包位置是相对 URL。默认 `dnf reposync` 使用 leaf-root 安全检查并拒绝这种父级跳转，
所以规范 Managed view 明确不支持作为默认 `reposync` 源。

需要自包含产物时执行：

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

导出会把包 href 改写为本地 `pool/`，且不修改 Repository。现行 Integration workflow
尚未用真实 `reposync` 客户端消费该导出，因此最后一层客户端门禁仍是未验证。

## 二进制平台

Release 配置构建以下 `CGO_ENABLED=0` Archive：

| 操作系统 | `amd64` | `arm64` |
|---|---:|---:|
| Linux | 构建 | 构建 |
| macOS (Darwin) | 构建 | 构建 |

Linux 还会生成 RPM 与 DEB 包。不支持 Windows。构建目标不等于证明所有操作系统版本/运行时
组合；当前自动化 clean-room 与客户端作业运行在 Linux。

## 文件系统边界

Managed 工作区应位于本地 POSIX 文件系统。正确性依赖建议锁、fsync、安全路径检查与原子
rename；不声明 NFS 等网络文件系统为受支持工作区位置。

已提交公共 Repository 是闭合的 `pool/ + dists/` 树，不依赖 view-local hardlink identity。
两者必须一起保留。发布时应优先使用配置 target，或由操作者控制 staging 后原子切换，
不要直接原地修改 live tree。

`filesystem` target 的 `file:///...` endpoint 目录必须预先存在，并解析为唯一规范真实目录。
缺失目录或 symlink alias 会被拒绝。全新 v0.2.0 本地运行已验证首次发布与幂等重放。

## 发布 Provider

| Provider | 已实现行为 | 当前证据边界 |
|---|---|---|
| `filesystem` | 发布、校验、checkpoint、grace、条件式生命周期维护 | 聚焦测试 + 全新本地 CLI 实跑 |
| `r2` | S3 兼容发布；target GC 只记录候选报告，绝不删除对象 | 源码与聚焦测试；没有当前真实 CLI/Provider 端到端实跑 |

`public_endpoint` 是 target 校验的一部分；它不会创建 Web 服务、CDN、bucket policy、DNS
或凭据。请在部署环境单独验证这些层。

## 有意省略的元数据

- SQLite rpm-md、zchunk 与 modulemd；
- 源码包索引；
- DEB MD5/SHA1 manifest；
- Plain 模式的 DEB `Release` 与签名。

## 外部工具

元数据生成与解析在进程内完成。RPM 包签名需要 `rpm` 与可用 GPG 环境。`agent://` 元数据
key 需要 `gpg` 与 `gpg-agent`；路径、`file://`、`env://` key 在进程内签名。

## 版本

```console
sow 0.2.0 darwin/arm64 go1.26.5
```

OS、架构与 Go 工具链取决于实际二进制。`sow/v3`、`sow.cli/v1` 是配置/协议标识。

## 延伸阅读

- [仓库布局](/zh/docs/reference/layout/)
- [发布命令](/zh/docs/reference/cli/publication/)
- [兼容性设计](/zh/docs/design/compatibility/)
