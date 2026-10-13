---
title: "仓库布局"
linkTitle: "仓库布局"
description: "查找包文件、仓库索引、私有状态和发布输出的位置。"
categories: [Reference]
tags: [repository, pool, dist]
url: "/zh/docs/reference/layout/"
weight: 400
icon: fa-solid fa-folder-tree
---

对外服务完整的 Managed 仓库目录：`pool/` 加 `dists/`。
工作区配置与 `.sow/` 状态应位于 Web 服务根目录之外。

<span id="plain-模式"></span>

## Plain 目录

```text
/srv/offline/
├── example-1.0-1.x86_64.rpm
├── example_1.0-1_amd64.deb
├── repodata/
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   └── repomd.xml
├── Packages
├── Packages.gz
└── repo_complete                     # 使用 --pigsty 时
```

`sow create` 在存在 RPM 时生成 RPM 元数据，存在 DEB 时生成 DEB 元数据。
RPM 位置使用文件名，DEB 使用 `./<文件名>`。构建期间使用私有 `.sow-plain-stage-*` 目录，
对外服务和复制时应排除这些目录。后续 `create` 会清理过时的 SOW 临时路径并重建索引。

## Managed 工作区

```text
<workspace>/
├── sow.yml                           # 工作区配置
├── .sow/                             # 私有状态
│   ├── workspace.lock
│   ├── workspace-ops/
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db
│   └── <repo>/
│       ├── stage/
│       ├── recovery/
│       ├── retained/
│       ├── transitions/
│       └── pending/
└── <repo>/                           # 公开仓库根
    ├── pool/
    └── dists/
```

数据库旁可能有 SQLite WAL 和共享内存文件。`.sow/` 与 pending 目录权限为私有的 `0700`。
待构建包文件使用 `0644`，进入公开路径时无需改变权限。

SOW 0.5 使用数据库 schema v13 和配置 schema `sow/v3`，两者是独立的版本标识。
执行 [`repo migrate`](/zh/docs/command/repo/#sow-repo-migrate) 前备份完整工作区。
数据库应与匹配的私有、公开状态一起保存；不要手动修改 schema 版本或可重建缓存。

<span id="规范包池"></span>

## 包池

```text
pool/<prefix>/<source>/<filename>
```

`source` 来自 RPM `SOURCERPM` 或 DEB `Source` 字段，规范化为源码包名。
字段缺失时使用二进制包名。前缀为首字符的小写形式；源码名以小写 `lib` 开头时，
取前四个字符并转为小写，不足四个字符则取全名。

| 源码名 | 示例路径 |
|---|---|
| `postgresql-18` | `pool/p/postgresql-18/libpq5_18.3-1_amd64.deb` |
| `example` | `pool/e/example/example-1.0-1.x86_64.rpm` |
| `libfoo` | `pool/libf/libfoo/libfoo1_1.0-1_amd64.deb` |

包对象不可变。移除成员关系后，字节仍可被构建、保留、恢复和发布记录使用。
这些记录都不再需要某个对象后，[`gc`](/zh/docs/command/gc/) 才会删除它。
每个仓库有独立包池。

<span id="rpm-纯元数据视图"></span>

## RPM Dist

```text
dists/el9/
├── x86_64/repodata/
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   ├── repomd.xml
│   └── repomd.xml.asc                # 配置元数据签名时
└── aarch64/repodata/
    └── ...
```

架构视图只包含元数据，包位置指向根包池：

```xml
<location href="../../../pool/e/example/example-1.0-1.x86_64.rpm"/>
```

原生架构包只出现在对应视图，`noarch` 包出现在全部配置视图。
旧的校验和命名元数据可能与当前文件共存，`repomd.xml` 选择当前生效的一组。

需要包路径都在目录内的独立副本时，使用 [`export rpm-leaf`](/zh/docs/command/export/)。

<span id="deb-视图"></span>

## DEB Dist

```text
dists/trixie/
├── Release
├── InRelease                         # 配置元数据签名时
├── Release.gpg                       # 配置元数据签名时
└── main/
    ├── binary-amd64/
    │   ├── Packages
    │   ├── Packages.gz
    │   └── by-hash/SHA256/<digest>
    └── binary-arm64/
        └── ...
```

`Packages` 使用相对仓库根的路径，如
`Filename: pool/e/example/example_1.0-1_amd64.deb`。
`Release` 包含 SHA-256 清单与 `Acquire-By-Hash: yes`。
架构为 `all` 的包进入每个适用索引。

<span id="发布目标"></span>

## 发布路径

两种发布 Provider 都接收相同公开布局：

```text
<prefix>/
├── pool/
└── dists/
```

导出拥有自己的包文件、元数据、清单和 `.sow-export.json` 完成标记。
它是独立交付制品，不是另一个 Managed 仓库。

<span id="名称与服务边界"></span>

## 名称与大小写

仓库、Dist 和目标名称使用 `[a-z0-9][a-z0-9._-]*`。
保留名称包括 `.`、`..`、`.sow`、`pool`、`dists`、`sow.yml`、`workspace.lock`、
`workspace-ops`、`repo-locks`。

新包池完整路径与已知路径仅大小写不同时会被拒绝，即使字节相同。
在大小写不敏感文件系统上，仅大小写不同的源码目录也会冲突；
在大小写敏感文件系统上，这些源码目录可以共存，因此迁移到大小写不敏感卷前应先检查。

继续阅读[视图](/zh/docs/feature/views/)、[对外服务](/zh/docs/tutorial/serving/)和
[平台](/zh/docs/reference/compatibility/)。

<span id="延伸阅读"></span>
