---
title: "平台与集成"
linkTitle: "平台"
description: "Release 目标、文件系统要求、仓库客户端、发布 Provider 与自动化集成覆盖。"
categories: [Reference]
tags: [rpm, deb, yum, apt, object-storage]
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

Release 二进制使用 `CGO_ENABLED=0`，不需要语言运行时。源码 Module 要求 Go 1.27.1 或更新版本。
归档包含 `README.md`、`CHANGELOG.md`、Apache-2.0 `LICENSE` 与 `THIRD_PARTY_NOTICES`，
Linux 软件包也随二进制包含同一份协议与第三方许可声明。
使用 [`sow version`](/zh/docs/command/) 查看产品版本、目标 OS/架构与构建工具链。

## 工作区文件系统

Managed 工作区应放在本地 POSIX 文件系统上。正确性依赖建议锁、`fsync`、基于描述符的路径
校验与同文件系统原子 rename；NFS 等网络文件系统不属于受支持的工作区位置。macOS 上请使用
APFS：HFS+ 不支持原子目录交换，SOW 会拒绝构建。

公共 `<workspace>/<repo>/` 树是另一条边界：它是闭合的 `pool/ + dists/` 命名空间，可整根
复制或发布，不依赖 SQLite、私有 journal 或 view-local hardlink identity。必须保持完整
Repository，不得暴露 `.sow/`。

SOW 会拒绝符号链接控制路径、不安全普通文件、重叠 filesystem target，以及与已有或已发布
路径在大小写折叠后冲突的新 Pool 路径；这也包括以仅大小写不同的文件名加入完全相同的字节
（请使用原文件名加入）。在大小写不敏感的工作区文件系统上（例如 macOS 默认配置），SOW 还会
拒绝源目录与已有包仅大小写不同的新包（例如 `CaseDemo` 与 `casedemo`）；向位于大小写不敏感
卷上的 filesystem target 执行 `publish` 时，也会在创建 attempt 之前拒绝这类别名。在大小写
敏感的文件系统（Linux）上，这样的两个源目录彼此独立，因此同时包含两者的 Repository 不能
迁移到大小写不敏感的文件系统。

## 自动化集成矩阵

| 表面 | 环境 | 已验证行为 |
|---|---|---|
| 生产 CLI 干净环境 | Linux CI | 构建交付二进制；生成混合 Plain RPM/DEB 元数据；初始化 `sow/v3`；创建 RPM/DEB Dist；加入 Fixture；执行查询、build、check、changes、config 与 log 命令 |
| Plain APT 客户端 | Ubuntu 22.04 容器 | 通过 HTTP 服务 `sow create` 输出；在显式信任未签名源时执行 `apt-get update`、包发现、精确版本选择、下载与安装 |
| RPM 分离签名切换 | AlmaLinux 8、9、10 容器 | 使用真实 DNF 客户端遍历 `repomd.xml` / `repomd.xml.asc` 串行切换状态，并固定各组合的成功/失败行为 |
| S3 兼容传输 | 固定的 PGSTY Silo 容器（兼容 MinIO） | 验证 Bucket 列表、HEAD、GET、单段仅创建/CAS PUT、重放与对象 SHA-256 元数据；重试与 Prefix 约束由本地协议测试覆盖 |
| Release 打包 | Linux CI | 构建四个归档、两个 RPM、两个 DEB 与 `SHA256SUMS`；检查包内路径、Apache-2.0 元数据与协议文件字节 |

DNF 签名切换是协议测试，不是完整 Managed RPM 安装；APT 作业覆盖未签名 Plain 仓库，不覆盖
Managed 元数据签名。正式上线前，应使用部署中的确切 dnf/APT 版本、仓库 URL、访问策略与
签名策略完成验收。

当前 Silo 集成没有验证条件式 Multipart 完成。Multipart 的请求/协议测试单独存在，
不能据此认定真实 R2 兼容；该路径的验收还需要真实 R2 Multipart 测试。

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

Managed RPM 与 `export rpm-leaf` 的 repomd data 时间戳固定为 `0`，没有
`--metadata-timestamp` 选项。因此它们不能直接接管保留了正数时间戳缓存的同一个 EL7
repository ID；换 baseurl 本身不能解决。需要客户端采用新的 repository ID 或清理元数据缓存。
若必须保留旧 ID 和缓存继续更新，请使用带显式时间戳的 Plain `create`，按
[迁移指南](/zh/docs/tutorial/yum-migration/) 维护发布时间并重签 repomd。

## 迁移已有 Plain YUM 仓库

Plain 生成 primary、filelists、other 三份 XML，不生成旧式 SQLite 元数据或模块流。
普通 RPM 可以配合适当的 `module_hotfixes=1` 策略使用；模块 profile 与 `dnf module install`
需要另一套工作流。

EL7 YUM 会把 `repomd.xml` 中最大的 data 时间与缓存比较。SOW 0.5.0 新增
`create --metadata-timestamp SECONDS`，但默认仍为 `0`。已有在线仓库应使用不低于历史最大值
的时间，真实更新应继续递增；仅改变 revision 或文件 mtime 无效。调用者负责保存历史时间并
单独签署 `repomd.xml`。验收应保留原仓库 URL、ID、缓存和目标 GPG 检查策略。完整步骤见
[迁移指南](/zh/docs/tutorial/yum-migration/)。

RPM 依赖投影遵循现代 createrepo_c 对 `%pretrans`、`%posttrans` 依赖的处理方式。0.5 新增的
回归测试巩固了这一契约，没有修改解析器。旧版 createrepo_c 可能输出不同数量的依赖行或
`pre="1"` 属性；应比较依赖含义和真实客户端行为，不能只比行数。对应上游变更见
[PR #427](https://github.com/rpm-software-management/createrepo_c/pull/427)。

0.5.0 暂不支持 RPM v6 包格式的签名；新的签名 tag 可能被当作未签名，签名或验签流程因而
拒绝该包。签名工作流请使用 RPM v4 格式包，不应期待 SOW 保留或验证 RPM v6 格式的签名。

## 发布 Provider

| Provider | 契约 |
|---|---|
| `filesystem` | 发布到预先存在且安全的 `file://` endpoint 下。Target GC 只有在缓存 grace 与存储/公共缺失证据成立后，才执行精确条件删除。 |
| `r2` | 通过 S3 兼容存储传输发布。Target GC 只写入精确候选报告，绝不删除远端对象。 |

两种 Provider 都在配置 Prefix 下发布同一棵完整 `pool/ + dists/` 树。`public_endpoint` 属于
Target 校验的一部分；SOW 不创建 HTTP 服务、DNS 记录、Bucket Policy、CDN 或凭据。启用生产
发布前，应先在非生产 Prefix 验证这些由部署方负责的表面。

Filesystem 与 R2 的 HTTP(S) 端点共用 canonical-GET 内容 verifier；Filesystem 还可使用基于
描述符的 `file://` 校验，R2 公共端点则必须为 HTTP(S)。Target Name、`public_endpoint` 与
`max_cache_ttl` 只能通过显式 [`publish --rebind`](/zh/docs/command/publish/#重绑定可变目标配置)
修改；Storage Identity 与 Prefix 不可变。

## 部署门禁

交付前必须通过深度校验，并检查物理变更计划：

```bash
sow check -r REPOSITORY
sow changes 0 -r REPOSITORY
```

发布后，再访问实际 `repomd.xml` 或 `Release` URL，并运行目标软件包管理器。本地构建、Provider
写入、HTTP 可达与客户端安装是四个独立检查。

相关契约见[仓库布局](/zh/docs/reference/layout/)、[签名模型](/zh/docs/feature/signing/)与
[发布与恢复](/zh/blog/design/publication/)。
