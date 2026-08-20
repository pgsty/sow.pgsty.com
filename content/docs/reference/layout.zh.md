---
title: "仓库布局"
linkTitle: "仓库布局"
description: "SOW 0.2.0 创建的公共与私有路径,包括唯一规范包池与纯元数据视图。"
url: "/zh/docs/reference/layout/"
weight: 400
icon: fa-solid fa-folder-tree
---

SOW 0.2.0 的 Managed 布局只有一种:软件包体在 `pool/` 下只存一份,`dists/`
只保存客户端视图元数据。对外服务、复制或发布时,单位始终是完整仓库目录。

## Plain 模式

`sow create` 在现有软件包旁写入索引,不修改无关文件:

```text
/srv/offline/
├── blackbox_exporter-0.28.0-1.x86_64.rpm
├── libpq5_18.3-1.pgdg12+1_amd64.deb
├── repodata/
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   └── repomd.xml
├── Packages
├── Packages.gz
└── repo_complete                         # 仅 --pigsty 生成
```

平面 RPM 元数据引用裸文件名,平面 DEB 元数据使用 `./<filename>`。构建过程中出现的
`.sow-plain-*` 是私有 journal、stage 与 recovery 状态,不得服务或复制。

## Managed 工作区

```text
<workspace>/
├── sow.yml                               # 配置,保持私有
├── .sow/                                 # 数据库、锁、stage/recovery,保持私有
│   ├── workspace.lock
│   ├── workspace-ops/
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db
│   └── <repo>/
│       ├── stage/
│       ├── recovery/
│       └── pending/
└── <repo>/                               # 发布这个完整目录
    ├── pool/
    └── dists/
```

去重不跨仓库边界。`.sow/` 权限为 `0700`,可能包含尚未发布的包体、从凭据派生的状态与
恢复数据。

## 规范包池

每个包体只有一条规范路径:

```text
pool/<prefix>/<source>/<filename>
```

源码名取自 RPM `SOURCERPM` 或 DEB `Source`;缺失时回落到二进制包名。
前缀是首个小写字符,以 `lib` 开头时取前四个字符:

| Source | 示例 |
|---|---|
| `postgresql-18` | `pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb` |
| `blackbox_exporter` | `pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm` |
| `libfoo` | `pool/libf/libfoo/libfoo1_1.0-1_amd64.deb` |

Pool 对象不可变。从 Dist 删除成员关系不会立即删除字节；`sow gc` 只有在检查当前、保留、
恢复、发布以及活动维护操作等全部安全根后，才会处理不可达包体。

## RPM 纯元数据视图

```text
<repo>/
├── pool/
│   ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│   └── p/pev2/pev2-1.23.0-1.noarch.rpm
└── dists/el9/
    ├── x86_64/repodata/
    │   ├── <sha256>-primary.xml.gz
    │   └── repomd.xml
    └── aarch64/repodata/
        ├── <sha256>-primary.xml.gz
        └── repomd.xml
```

这里没有 `dists/<dist>/<arch>/pool/`。原生包只出现在匹配架构的元数据中,`noarch`
出现在每个架构视图中。rpm-md 回指规范包池:

```xml
<location href="../../../pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm"/>
```

该布局要求客户端在完整 Repository Root 内正确处理 rpm-md 相对路径；当前自动化矩阵尚未包含
现行 Managed DNF/YUM 验收门禁。默认 `dnf reposync` 会拒绝父级跳转 href，因为下载目标逃出
View Root。下游工具需要自包含 Leaf 时，请显式导出：

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

导出目录有自己的 `pool/` 和改写后的 href;它是兼容性产物,不是规范 Managed 仓库。

## DEB 视图

```text
dists/trixie/
├── Release
├── InRelease                         # 配置元数据签名时生成
├── Release.gpg                       # 配置元数据签名时生成
└── main/
    ├── binary-amd64/
    │   ├── Packages
    │   ├── Packages.gz
    │   └── by-hash/SHA256/<digest>
    └── binary-arm64/
        └── ...
```

`Packages` 从 archive 根引用同一规范包池:

```text
Filename: pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
```

`Release` 使用 SHA256 清单并声明 `Acquire-By-Hash: yes`。校验和命名的 rpm-md 文件与
APT by-hash 条目让旧元数据在可变指针最后替换时仍然可达。

## 发布目标

`filesystem` 与 `r2` 目标都会在配置前缀下得到同一棵逻辑公共树:

```text
<prefix>/
├── pool/
└── dists/
```

发布单位始终是完整仓库命名空间。不要只发布某一个 RPM 架构目录,它的 href 会有意回指
根包池。

## 名称与服务边界

仓库名与 Dist 名必须匹配 `[a-z0-9][a-z0-9._-]*`。`.`、`..`、`.sow`、`pool`、
`dists`、`sow.yml`、`workspace.lock`、`workspace-ops` 与 `repo-locks` 在相应位置为
保留名。SOW 会拒绝大小写不敏感的池路径冲突,使产物能在 Linux 与默认 macOS 文件系统间迁移。

> [!WARNING] 绝不要暴露 .sow
> Web 服务器应指向 `<workspace>/<repo>/`,而不是工作区根目录。公共仓库需要同时包含
> `pool/` 与 `dists/`;私有 `.sow/` 必须隐藏。

## 延伸阅读

- [视图与单副本存储](/zh/docs/feature/views/)
- [发布模型](/zh/docs/design/publication/)
- [对外服务](/zh/docs/tutorial/serving/)
