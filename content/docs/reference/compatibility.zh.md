---
title: "平台与集成"
linkTitle: "平台"
description: "支持的平台、文件系统要求、仓库格式、客户端与集成测试覆盖。"
categories: [Reference]
tags: [rpm, deb, yum, apt, object-storage]
url: "/zh/docs/reference/compatibility/"
aliases:
  - "/docs/design/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

SOW 在 Linux 和 macOS 上构建 RPM、DEB 仓库文件。工作区使用受支持的本地文件系统，
再为客户端配置 HTTP 或存储访问。

<span id="release-目标" data-td-print-local></span>

## 平台

| 操作系统 | `amd64` | `arm64` | 发布格式 |
|---|---:|---:|---|
| Linux | 是 | 是 | 归档、RPM、DEB |
| macOS | 是 | 是 | 归档 |
| Windows | 否 | 否 | — |

发布二进制使用 `CGO_ENABLED=0`，不需要语言运行时。源码构建要求 Go 1.27.2 或更新版本。
归档包含 README、更新日志、Apache-2.0 许可证与第三方许可声明；
Linux 软件包随二进制包含许可文件。用 `sow version` 查看版本、平台和构建工具链。

## 工作区文件系统

使用支持建议锁、`fsync` 和同文件系统原子重命名的本地 POSIX 文件系统。
NFS 等网络文件系统不是受支持的工作区位置。
macOS 上使用 APFS；所需原子目录交换不可用时，SOW 会拒绝构建。

工作区公开目录和私有暂存区放在同一文件系统。
只对外服务 `<workspace>/<repo>/`。完整的 `pool/ + dists/` 可以复制到其他存储，
无需附带私有数据库或日志。

仅大小写不同的包池完整路径会被拒绝。大小写不敏感文件系统还会拒绝源码目录的大小写别名。
大小写敏感卷上创建的仓库可能包含目标卷无法区分的源码目录，filesystem 发布会在开始前检查。
详见[布局](/zh/docs/reference/layout/)。

<span id="仓库客户端契约" data-td-print-local></span>

## 仓库格式与客户端

| 输出 | 客户端入口 | 包位置 |
|---|---|---|
| Plain RPM | `repodata/repomd.xml` | 与 `repodata/` 同级 |
| Plain DEB | `Packages` 或 `Packages.gz` | 与索引同级，使用平面 APT 源 |
| Managed RPM | `dists/<dist>/<arch>/repodata/repomd.xml` | 通过相对路径回到根 `pool/` |
| Managed DEB | `dists/<dist>/Release` 或已签名的 `InRelease` | 相对于仓库根的 `pool/` 路径 |

Managed APT 使用 component `main` 和 SHA-256 by-hash 索引。
元数据签名生成 RPM `repomd.xml.asc` 或 APT `InRelease`、`Release.gpg`。

### 发布时间

新的 Managed 操作在构建元数据时，会记录本次操作的发布时间；`sow repo migrate` 保持原有时间戳行为。
APT `Release` 日期、RPM `repomd.xml` 的 data timestamp 与元数据签名使用同一时间。
RPM `revision` 仍为构建快照（Generation）编号。

恢复操作复用已记录的时间。没有记录发布时间的旧日志保持原有时间戳行为。
没有实际变更的操作不会刷新发布时间。

### RPM 的 XML 与 SQLite 元数据

SOW 生成 gzip 压缩的 `primary`、`filelists`、`other` XML，不生成 SQLite 格式的
`primary_db`、`filelists_db`、`other_db`。两者是不同元数据格式；
只读取 `primary_db` 的工具需要增加 XML 输入支持或单独转换。

缺少 `primary_db` 本身不会阻止 YUM 读取仓库。上游 YUM 在没有可用 SQLite 索引时，
会读取 XML 并生成本地缓存，见 [YUM 元数据加载实现](https://github.com/rpm-software-management/yum/blob/master/yum/yumRepo.py)。
SOW 输出的 XML 使用 gzip，因此比较其他仓库或工具时，zstd 支持是另一个问题。

SOW 不生成 zchunk、modulemd 或源码包索引。客户端需要模块 profile 或
`dnf module install` 时，应保留提供模块元数据的工具。
将模块化包作为普通 RPM 安装时，按需配置客户端 `module_hotfixes`，详见
[迁移指南](/zh/docs/tutorial/yum-migration/)。

### `dnf reposync`

默认 `dnf reposync` 将下载限制在单仓库目录，因此会拒绝规范 Managed RPM 视图中指向父目录
的包路径。这符合其[安全写入路径规则](https://dnf-plugins-core.readthedocs.io/en/latest/reposync.html)。
该工作流使用 [`sow export rpm-leaf`](/zh/docs/command/export/) 生成自包含目录。

<span id="迁移已有-plain-yum-仓库" data-td-print-local></span>

### 已有 EL7 缓存

EL7 YUM 会把元数据 data timestamp 与已缓存仓库比较。
Plain `create --metadata-timestamp SECONDS` 可以保留并推进已有发布时间，默认值为 `0`。

导出的 RPM 仓库，以及 `sow repo migrate` 本次生成的 RPM 元数据，使用时间戳 `0`，没有覆盖选项。
之后的 Managed 构建使用其记录的发布时间。
对这些输出，如果现有客户端仓库 ID 已缓存正数时间戳，使用新仓库 ID，或清理该 ID 的元数据缓存。
只改变 base URL 不够。需要保留旧 ID 和缓存时，使用 Plain 模式，按
[YUM 迁移](/zh/docs/tutorial/yum-migration/) 的时间戳流程操作。

### RPM 签名

包签名工作流支持 RPM 格式 v4，不支持 RPM 格式 v6 的签名标签。
元数据密钥引用是独立功能，详见[签名](/zh/docs/feature/signing/)。

## 发布 Provider

| Provider | 发布 | 目标 GC |
|---|---|---|
| `filesystem` | 写入已有规范 `file://` endpoint 之下 | 缓存宽限期后条件删除，再验证公开入口已不可获取 |
| `r2` | 通过 S3 兼容存储操作写入 | 只报告候选，不删除远端对象 |

两者都在配置前缀下发布完整仓库。存储对应的 HTTP 服务、DNS、凭据、访问策略和缓存行为
需要另行配置。`public_endpoint` 告诉 SOW 从哪里验证公开内容，不会创建服务。
R2 公开 endpoint 必须使用 HTTP(S)，filesystem 还支持 `file://` 验证。

<span id="自动化集成矩阵" data-td-print-local></span>
<span id="部署门禁" data-td-print-local></span>

## 自动化覆盖

源码包含以下集成检查：

| 检查 | 环境 | 范围 |
|---|---|---|
| CLI 干净环境流程 | Linux CI | 交付二进制、混合 Plain 输出、Managed 初始化、RPM/DEB Dist、查询、构建与检查 |
| Plain APT 客户端 | `pgsty/u22` Ubuntu 22.04 容器 | 显式信任未签名源时的 HTTP 更新、包发现、版本选择、下载与安装 |
| RPM 分离签名切换 | AlmaLinux 8/9 与 `pgsty/el10` 容器 | `repomd.xml` 及分离签名切换时的 DNF 行为 |
| S3 兼容传输 | 固定版本的 PGSTY Silo 容器 | Bucket 列表、HEAD、GET、条件式单段 PUT、重放和对象 SHA-256 元数据 |
| 发布打包 | Linux CI | 四个归档、两个 RPM、两个 DEB、校验和、包内路径与许可文件 |

DNF 测试检查签名切换，APT 测试使用未签名 Plain 输出。
完整的已签名 Managed 安装及托管 R2 条件式分段上传完成，需要在部署环境检查。

切换客户端前，运行 `sow check`，发布到目标，再使用实际客户端配置刷新索引并安装一个包。
客户端设置见[对外服务](/zh/docs/tutorial/serving/)。
