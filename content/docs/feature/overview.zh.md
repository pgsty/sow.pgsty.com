---
title: "能力总览"
linkTitle: "能力总览"
description: "SOW 在两条运行路径、两种包格式、签名与平台上的完整覆盖面,以及与 createrepo_c、reprepro 的对标结论。"
url: "/zh/docs/feature/overview/"
weight: 100
icon: fa-solid fa-table-list
---

SOW 是一个自包含的软件仓库管理器:一个纯静态 Go 二进制(`CGO_ENABLED=0`),在 Linux 与 macOS 上创建并维护 APT(DEB)与 YUM(RPM)软件仓库。它不调用 `createrepo_c`、`dpkg-scanpackages`、`reprepro` 或 `modifyrepo_c`,也不需要常驻进程。本页是覆盖面的地图,后续各页解释每一块是怎么实现的。

当前版本为 `sow 0.2.0`。

## 两条运行路径

SOW 提供两种建仓方式,二者刻意相互隔离。除底层的包解析器、渲染器、版本比较、锁和安全文件原语外,它们不共享任何东西。

| | Plain 平面模式 | Managed 托管模式 |
|---|---|---|
| 入口命令 | `sow create` | `sow init` / `repo` / `dist` / `add` / `build` |
| 输入 | 一个装着 `.rpm` / `.deb` 的目录 | 按路径 add 进工作区的包 |
| 产出布局 | 平面 —— 包与索引同目录 | Debian 风格 `pool/` + `dists/` 发布视图 |
| 持久状态 | 无(仅操作期间的临时 journal) | `sow.yml` + 每个仓库一个 SQLite |
| 配置 | 无 —— 不读任何配置文件 | `sow.yml`,严格校验 |
| 多架构 | 全部架构落进同一份平面索引 | 每个 Dist 每个架构一份渲染视图 |
| 历史 | 无 | 单调 Generation 与操作账本 |
| 对标 | `createrepo_c` + `dpkg-scanpackages` | `reprepro` |

手里已有一目录包、只想给它建个索引 —— 用 Plain。同一个仓库要按策略持续维护数月、并且需要审计线索 —— 用 Managed。

Plain 模式止于本地目录。Managed 模式既可以把结果作为普通文件服务或复制,也可以把已提交的
Generation 发布到配置好的 `filesystem` 或 `r2` 目标。参见[对外服务](/zh/docs/tutorial/serving/)
与[发布模型](/zh/docs/design/publication/)。

## 格式覆盖

| 能力 | RPM / YUM | DEB / APT |
|---|---|---|
| 生成的索引文件 | `repodata/`,含 `primary`、`filelists`、`other` 与 `repomd.xml` | `Packages`、`Packages.gz`、`Release` |
| 校验和 | SHA-256,metadata 文件按 checksum 命名 | 仅 SHA-256(不输出 MD5Sum/SHA1) |
| 包事实来源 | RPM 包头(绝不看文件名) | `.deb` 内的 `control` |
| 坐标(身份) | NEVRA | `name=version:arch` |
| 架构视图(Managed) | `x86_64`、`aarch64` | `binary-amd64`、`binary-arm64` |
| 免架构包 | `noarch` | `all` |
| by-hash 索引拉取 | 不适用 | 支持,`Acquire-By-Hash: yes` |
| 元数据签名 | `repodata/repomd.xml.asc` | `InRelease` 与 `Release.gpg` |
| 包体签名 | 嵌入式 OpenPGP 签名,`fill` / `always` 模式 | 不适用 |

一条命令同时处理两种格式。Plain 模式下,同时含 `.rpm` 与 `.deb` 的目录在一次操作里生成 `repodata/` 与 `Packages`。Managed 模式下,一个 Repository 可以同时拥有 RPM Dist 和 DEB Dist,共用同一个 `pool/`。

## 签名覆盖

存在两条彼此独立、分别配置的信任链,完整说明见[签名模型](/zh/docs/feature/signing/)。

| 信任链 | Plain 模式 | Managed 模式 | 客户端用什么验证 |
|---|---|---|---|
| 仓库元数据 | 不提供 | `signing.rpm.metadata.key`、`signing.deb.metadata.key` | dnf `repo_gpgcheck=1`、apt `Signed-By` |
| RPM 包体 | `create -S KEY [--overwrite]` | `signing.rpm.packages.mode: fill \| always` | dnf `gpgcheck=1` |

以 `file://` 或 `env://` 给出的元数据密钥由进程内 Go signer 使用,不需要外部工具。RPM 包体签名和 `agent://` 密钥引用会调用环境中的 `rpm` 与 `gpg`。

## 平台覆盖

二进制可构建 `darwin` 与 `linux` 的 `amd64` / `arm64` 版本。运行时不依赖包管理器、数据库服务或 Python 环境。

SOW 唯一会调用的外部程序是 `rpm`(RPM 包体签名)与 `gpg`(`agent://` 密钥引用)。如果仓库不签名,或只用 `file://`/`env://` 元数据密钥,那么除了 `sow` 二进制本身之外什么都不用装。

Managed 工作区必须在本地 POSIX 文件系统上构建,因为锁、fsync 与原子 rename 都属于事务
契约。当前 `pool/ + dists/` 布局不使用视图级硬链接:`pool/` 拥有包体,RPM 视图只含元数据。
参见[包池与元数据视图](/zh/docs/feature/views/)。

## 客户端兼容

下表每一行都在真实客户端上跑过:

| 客户端 | 版本 | 结果 |
|---|---|---|
| AlmaLinux 8 / 9 / 10 `dnf` | dnf4 | `repo_gpgcheck=1` + `gpgcheck=1` 下 `makecache` 与 `install` 通过 |
| CentOS 7 `yum` | 3.4.3 | `makecache` 通过,多版本 NEVRA 解析正确 |
| Debian 13 `apt` | 3.0.3 | `update`(InRelease 验签 + by-hash 拉取)与 `install` 通过 |
| Debian 12 `apt` | 2.6.1 | 同上;平面仓库经 `[trusted=yes]` 亦可用 |

默认 `dnf reposync` 有意不列为规范布局客户端:它的 safe-write 检查会拒绝
`../../../pool/...` 包 href。下游必须满足该契约时,请使用 `sow export rpm-leaf`。

完整矩阵(含 APT ≥ 1.2 的 by-hash 要求)见[兼容性](/zh/docs/reference/compatibility/)。

## 与 createrepo_c、reprepro 对标

这两个工具是 SOW 的对标基准。下表来自同一批包的并排实测,不是文档宣称。

| 维度 | SOW | createrepo_c | reprepro |
|---|---|---|---|
| RPM 元数据 | `primary`/`filelists`/`other`,语义等价 | 基准 | — |
| sqlite repodata | 不生成(明确非目标) | 默认生成 | — |
| DEB `Packages` 字段 | 等价,仅 SHA-256 | — | 基准,输出 MD5Sum + SHA1 + SHA256 |
| by-hash | 支持(`Acquire-By-Hash: yes`) | — | **不支持** |
| 包池布局 | `pool/<首字母>/<source>/`(无 component 层) | — | `pool/main/<首字母>/<source>/` |
| 每架构 `Release` 存根 | 不生成(apt 不需要) | — | 生成 |
| 平台 | Linux 与 macOS,单二进制 | 实际只在 Linux 上用 | 仅 Linux |
| 事务与崩溃恢复 | journal 前滚/回滚 | 无 | 数据库易损 |
| 审计 | 操作账本 + JSONL 导出 | 无 | 日志有限 |

有两个细节值得单独说明,因为迁移的人常会问:

与 `createrepo_c` 0.20.1 在 9 个测试包 + 87 个真实生产包上并排比对,`primary`、`filelists`、`other` 的全部字段语义一致 —— name、arch、EVR、checksum、各类 size、provides、requires flags、files、changelog、header range 都对得上。唯一差异:当某个 RPM 包头里 `/bin/sh` 同时以 pre 和非 pre 两个上下文出现时,SOW 去重保留一条,`createrepo_c` 保留两条。

与 `dpkg-scanpackages` 比对,`Packages` 字段一致,差别在于 SOW 只输出 `SHA256`(现代 APT 客户端不需要别的),并且对缺失字段(如 `Section`)直接省略而不是写空值。

如果你要迁移既有仓库,先读[从 createrepo_c / reprepro 迁移](/zh/docs/tutorial/migration/):就地接管一个目录会把旧工具的文件留在磁盘上,需要你自己清理。

## 性能锚点

macOS arm64 冷启动实测:

| 操作 | 规模 | 墙上时间 |
|---|---|---|
| `sow create` | 9 个 RPM | 0.31 s |
| `sow create` | 87 个 RPM,2.9 GB(全量 SHA-256) | 10.7 s |
| `sow add` + 自动 build | 9 个 RPM,31 MB | 约 1.3 s |
| 加入 retained/publication 层之前的历史 `sow check` | 16 包工作区 | 0.12 s |

需要解析、哈希、渲染或校验的命令都接受 `-j/--jobs N`,默认取逻辑 CPU 数。并行不改变输出:最终序列化按固定顺序完成,相同输入永远产生相同字节。

## 明确的非目标

以下不是"还没做完的功能",而是设计上排除的东西 —— 不会有空命令或隐藏 flag 假装它们存在:

- modulemd 的生成、注入与透传
- sqlite repodata 与 zchunk
- SRPM / DSC 源码索引
- 多写者与多机部署
- 跨仓库去重
- 远端多写者协调,以及充当 CDN
- 对 R2 目标执行破坏性 GC(R2 维护仅生成报告)
- 常驻服务或 Web UI
- 造包

SOW 管理权威工作区、已提交 Generation、显式发布目标、保留根与保守 GC。
它不会取代实际交付公共目录的 HTTP 服务或 CDN。

## 继续阅读

- [Plain 平面仓库](/zh/docs/feature/plain/) —— `sow create` 逐步做了什么
- [Managed 工作区](/zh/docs/feature/managed/) —— 三层模型
- [核心概念](/zh/docs/start/concepts/) —— 如果你还没读过这份更短的心智模型
