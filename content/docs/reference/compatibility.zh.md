---
title: "平台与集成"
linkTitle: "平台"
description: "Release 目标、文件系统要求、仓库客户端、发布 Provider 与自动化集成覆盖。"
url: "/zh/docs/reference/compatibility/"
aliases:
  - "/docs/design/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

本页说明 SOW 提供哪些构建目标、工作区依赖什么存储语义，以及自动化集成具体覆盖哪些行为。
仓库生成在 SOW 二进制内部完成；部署后的最终门禁仍是实际软件包管理器。

## Release 目标

| 操作系统 | `amd64` | `arm64` | 制品 |
|---|---:|---:|---|
| Linux | 是 | 是 | 归档、RPM、DEB |
| macOS | 是 | 是 | 归档 |
| Windows | 否 | 否 | 不支持 |

Release 二进制使用 `CGO_ENABLED=0`，不需要语言运行时；项目使用 Go 1.26.5 构建。归档包含
`README.md`、`CHANGELOG.md` 与 Apache-2.0 `LICENSE`，Linux 软件包会随二进制安装同一份
协议文件。使用 [`sow version`](/zh/docs/command/) 查看产品版本、目标 OS/架构与构建工具链。

## 工作区文件系统

Managed 工作区应放在本地 POSIX 文件系统上。正确性依赖建议锁、`fsync`、基于描述符的路径
校验与同文件系统原子 rename；NFS 等网络文件系统不属于受支持的工作区位置。

公共 `<workspace>/<repo>/` 树是另一条边界：它是闭合的 `pool/ + dists/` 命名空间，可整根
复制或发布，不依赖 SQLite、私有 journal 或 view-local hardlink identity。必须保持完整
Repository，不得暴露 `.sow/`。

SOW 会拒绝符号链接控制路径、不安全普通文件、重叠 filesystem target，以及大小写折叠后冲突
的 Pool 路径，使同一个 Repository 可以在大小写敏感的 Linux 与默认大小写不敏感的 macOS
文件系统间移动。

## 自动化集成矩阵

| 表面 | 环境 | 已验证行为 |
|---|---|---|
| 生产 CLI 干净环境 | Linux CI | 构建交付二进制；生成混合 Plain RPM/DEB 元数据；初始化 `sow/v3`；创建 RPM/DEB Dist；加入 Fixture；执行查询、build、check、changes、config 与 log 命令 |
| Plain APT 客户端 | Ubuntu 22.04 容器 | 通过 HTTP 服务 `sow create` 输出；在显式信任未签名源时执行 `apt-get update`、包发现、精确版本选择、下载与安装 |
| RPM 分离签名切换 | AlmaLinux 8、9、10 容器 | 使用真实 DNF 客户端遍历 `repomd.xml` / `repomd.xml.asc` 串行切换状态，并固定各组合的成功/失败行为 |
| S3 兼容传输 | 固定 MinIO 容器 | 验证 Bucket 列表、HEAD、GET、仅创建 PUT、CAS PUT、重放、对象元数据与 Prefix 约束 |
| Release 打包 | Linux CI | 构建四个归档、两个 RPM、两个 DEB 与 `SHA256SUMS`；检查包内路径、Apache-2.0 元数据与协议文件字节 |

DNF 签名切换是协议测试，不是完整 Managed RPM 安装；APT 作业覆盖未签名 Plain 仓库，不覆盖
Managed 元数据签名。正式上线前，应使用部署中的确切 dnf/APT 版本、仓库 URL、访问策略与
签名策略完成验收。

## 仓库客户端契约

Plain RPM 仓库在包文件旁提供 `repodata/`；Plain DEB 仓库在包文件旁提供 `Packages` 与
`Packages.gz`。配置好客户端信任策略后，可通过 `file://` 或 HTTP 使用。

Managed 客户端必须消费完整 Repository Root：

- APT 索引位于 `dists/<dist>/main/binary-<arch>/`，并引用根级 `pool/`。`Release` 声明
  SHA-256 by-hash 索引；配置签名后增加 `InRelease` 与 `Release.gpg`。
- RPM 元数据位于 `dists/<dist>/<arch>/repodata/`，通过相对位置回指根级 `pool/`。必须服务
  整个 Repository，不能只发布一个架构目录。

默认 `dnf reposync` 会拒绝规范 Managed RPM 的父级相对包路径。该工作流应使用
[`sow export rpm-leaf`](/zh/docs/command/export/) 生成自包含副本。导出使用本地包路径并带有
完成清单，但不是第二个规范 Repository。

## 发布 Provider

| Provider | 契约 |
|---|---|
| `filesystem` | 发布到预先存在且安全的 `file://` endpoint 下。Target GC 只有在缓存 grace 与存储/公共缺失证据成立后，才执行精确条件删除。 |
| `r2` | 通过 S3 兼容存储传输发布。Target GC 只写入精确候选报告，绝不删除远端对象。 |

两种 Provider 都在配置 Prefix 下发布同一棵完整 `pool/ + dists/` 树。`public_endpoint` 属于
Target 校验的一部分；SOW 不创建 HTTP 服务、DNS 记录、Bucket Policy、CDN 或凭据。启用生产
发布前，应先在非生产 Prefix 验证这些由部署方负责的表面。

## 部署门禁

交付前必须通过深度校验，并检查物理变更计划：

```bash
sow check -r REPOSITORY
sow changes 0 -r REPOSITORY
```

发布后，再访问实际 `repomd.xml` 或 `Release` URL，并运行目标软件包管理器。本地构建、Provider
写入、HTTP 可达与客户端安装是四个独立检查。

相关契约见[仓库布局](/zh/docs/reference/layout/)、[签名模型](/zh/docs/feature/signing/)与
[发布与恢复](/zh/docs/design/publication/)。
