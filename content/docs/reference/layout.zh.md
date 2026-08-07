---
title: "仓库布局"
linkTitle: "仓库布局"
description: "SOW 创建的每一条路径、包池分组规则、名称约束,以及绝对不能对外暴露的目录。"
url: "/zh/docs/reference/layout/"
weight: 400
icon: fa-solid fa-folder-tree
---

SOW 的磁盘布局是**固定**的。没有 `path:` 配置项,没有模板,也没有办法把仓库挪到别处 ——
每一条路径都由工作区根目录、一个已校验的名称和固定的相对片段推导而来。
本页给出完整地图,让你清楚哪些该发布、哪些该复制、哪些必须留在本地。

## Plain 平面模式

`sow create` 把索引写在软件包旁边,不碰任何别的东西。你指向的那个目录仍然是一个
平面仓库(flat repository):包与元数据同处一层。

```text
/srv/offline/
├── blackbox_exporter-0.28.0-1.x86_64.rpm     # 你的文件,永不被修改
├── pev2-1.23.0-1.noarch.rpm                  # 你的文件
├── libpq5_18.3-1.pgdg12+1_amd64.deb          # 你的文件
├── repodata/                                 # SOW 生成,目录里有 RPM 时出现
│   ├── <sha256>-primary.xml.gz
│   ├── <sha256>-filelists.xml.gz
│   ├── <sha256>-other.xml.gz
│   └── repomd.xml
├── Packages                                  # SOW 生成,目录里有 DEB 时出现
├── Packages.gz
└── repo_complete                             # 仅 --pigsty 生成
```

RPM 与 DEB 索引可以共存:两种格式都在时,一条 `sow create` 同时写出两套。
只有上面这些路径属于 SOW —— 目录里其他文件保持原样。

平面元数据只引用同目录下的包,所以这个仓库通过 `file://` 和以该目录为文档根的 HTTP
消费方式完全一致:

```console
# repodata primary.xml —— location 是裸文件名
<location href="blackbox_exporter-0.28.0-1.x86_64.rpm"

# Packages —— Filename 是 ./文件名
Filename: ./libpq5_18.3-1.pgdg12+1_amd64.deb
```

生成的文件**不继承**调用者的 umask:`repodata/` 固定 `0755`;索引文件、`Packages`、
`Packages.gz` 与 `repo_complete` 固定 `0644`。

`sow create` 执行期间,目录里还会临时出现一批私有工作路径,名字都以 `.sow-plain-` 开头:
stage 目录(`.sow-plain-stage-*`)、持久 journal(`.sow-plain-operation.json`),以及
`--pigsty` 模式下存放待删除包的 recovery trash(`.sow-plain-recovery-*`)。成功时会被清理,
崩溃后由下一次运行清理。不要对外服务它们,也不要复制它们。

## Managed 托管模式

工作区根目录下只有两样东西:配置文件与私有状态目录。其余每一项都是一个仓库,
而**仓库目录**就是你对外发布的单位。

```text
<workspace>/
├── sow.yml                       # 配置文件 —— 不要对外服务
├── .sow/                         # 私有状态 —— 不要服务,也不要复制
│   ├── workspace.lock
│   ├── workspace-ops/            # init / repo new / repo rm 期间存放 active.json
│   ├── repo-locks/
│   │   └── <repo>.lock
│   ├── <repo>.db                 # 每仓库独立的 SQLite(含 -wal / -shm 协调文件)
│   └── <repo>/
│       ├── stage/                # 元数据先在这里生成校验,再原子换入
│       ├── recovery/             # 前镜像与等待删除的对象
│       └── pending/              # --skip 加入但尚未发布的包体,以 SHA-256 命名
└── <repo>/                       # ← 这个目录才是你要服务和 rsync 的
    ├── pool/
    └── dists/
```

私有状态目录权限是 `0700`。仓库锁位于一条稳定路径 `.sow/repo-locks/<repo>.lock`,
它永不移动 —— 这样恢复过程中即使替换了仓库私有状态,其他进程持有的锁也不会失效。

同一工作区内的两个仓库**不共享任何东西**:各自有独立的包池、SQLite、锁和代计数器。
两个仓库里字节完全相同的包会存两份 —— 去重不跨仓库边界。

### 仓库

```text
<workspace>/pigsty/
├── pool/
│   ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│   ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
│   ├── libf/libfoo/libfoo1_1.0-1_amd64.deb
│   ├── p/pev2/pev2-1.23.0-1.noarch.rpm
│   └── p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
└── dists/
    ├── el9/       # format: rpm
    └── trixie/    # format: deb
```

`pool/` 里每个包的字节只存一份,由仓库内所有 Dist 共享。包池中的内容不可变 ——
同一条路径永远是同样的字节。把包从某个 Dist 移除,移除的是成员关系而不是包池字节;
当前版本没有 GC。

### 包池分组规则

```text
pool/<prefix>/<source>/<filename>
```

`source` 是源码包名,取自 RPM 的 `SOURCERPM` 头或 DEB 的 `Source` control 字段。
字段缺失时回落到二进制包名,并记录一条 warning。这就是 `libpq5` 落在 `postgresql-18`
下面的原因:那是它的构建来源,也是 `reprepro` 采用的同一套分组。

`prefix` 遵循 Debian 规则 —— source 名的首字符;source 名以 `lib` 开头时取前四个字符:

| Source | 池前缀 | 示例路径 |
|---|---|---|
| `postgresql-18` | `p` | `pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb` |
| `blackbox_exporter` | `b` | `pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm` |
| `libfoo` | `libf` | `pool/libf/libfoo/libfoo1_1.0-1_amd64.deb` |

前缀统一转为 ASCII 小写;`source` 与 `filename` 保持原始大小写。
两个包如果完整池路径在大小写不敏感比较下会碰撞,会被直接拒绝 ——
这样在 Linux 上构建的仓库复制到默认的 macOS 文件系统上仍然有效。

与 `reprepro` 不同,包池里**没有 component 层**:路径是
`pool/<prefix>/<source>/`,不是 `pool/main/<prefix>/<source>/`。

### RPM Dist

一个 RPM Dist 为每个架构族渲染一个目录,每个目录都是完整、可独立消费的仓库:

```text
dists/el9/
├── x86_64/
│   ├── repodata/
│   │   ├── <sha256>-primary.xml.gz
│   │   ├── <sha256>-filelists.xml.gz
│   │   ├── <sha256>-other.xml.gz
│   │   ├── repomd.xml
│   │   └── repomd.xml.asc          # 仅配置了 signing.rpm.metadata.key 时生成
│   └── pool/                       # 指向仓库包池的硬链接
│       ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│       └── p/pev2/pev2-1.23.0-1.noarch.rpm
└── aarch64/
    ├── repodata/ ...
    └── pool/
        ├── b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
        └── p/pev2/pev2-1.23.0-1.noarch.rpm
```

每个视图包含本架构的原生包,加上全部中性(`noarch`)包。视图 `pool/` 下的条目是指向
仓库包池的硬链接 —— 同一个 inode,不额外占用磁盘:

```console
stat -f "%l links  inode=%i  %N" pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
    dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
    dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm

3 links  inode=206234569  pool/p/pev2/pev2-1.23.0-1.noarch.rpm
3 links  inode=206234569  dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
3 links  inode=206234569  dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

三个链接:根包池加两个视图。原生 x86_64 包则是两个 —— 根包池加它所属的那一个视图。

这样设计的原因是**客户端兼容性**。元数据用不含 `..` 的普通相对路径引用包:

```xml
<location href="pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm"/>
```

指向 `../../../pool/...` 的布局在 `dnf install` 下也能工作,但 `dnf reposync` 会拒绝 ——
规范化后的本地目标逃出了每仓库的下载根目录。硬链接视图让所有客户端都能正常工作,
`reposync` 也包括在内。

因为用的是硬链接,`pool/` 与 `dists/` 必须位于**同一个文件系统**。不满足时 SOW 会明确失败,
绝不静默退化为复制。用不保留硬链接的工具复制仓库(普通 `cp -r`、多数对象存储上传)
在功能上没问题 —— 只是失去去重、多占一份空间。

元数据文件以自身校验和命名,所以推进一代是**新增**文件,而不是覆盖某个客户端可能正在
下载的旧文件。`repomd.xml` 是唯一可变的指针,并且最后一个被原子替换。
系统保留上一代的元数据文件;更早的会出现在 `sow changes` 的 `delete` 阶段。

### DEB Dist

一个 DEB Dist 在固定的 `main` component 下为每个架构渲染一个 `binary-<arch>` 目录。
这里**没有**视图级包池 —— APT 从 archive 根解析 `Filename`:

```text
dists/trixie/
├── Release
├── InRelease                       # 仅配置了 signing.deb.metadata.key 时生成
├── Release.gpg                     # 同上
└── main/
    ├── binary-amd64/
    │   ├── Packages
    │   ├── Packages.gz
    │   └── by-hash/
    │       └── SHA256/
    │           ├── <Packages 的 sha256>
    │           ├── <Packages.gz 的 sha256>
    │           └── ...              # 保留上一代
    └── binary-arm64/
        └── ...
```

注意 DEB 视图用生态架构名(`amd64`、`arm64`),RPM 视图用族名(`x86_64`、`aarch64`),
两者出自同一份规范化配置。

`Packages` 里的条目相对 archive 根指向共享包池,也就是 `<repo>/pool/...` ——
这正是"要服务仓库目录而不是 Dist 目录"的原因:

```console
Filename: pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
```

`Release` 声明支持 by-hash,并且只带 SHA256 清单 —— 没有 MD5Sum,没有 SHA1:

```console
Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:07:16 UTC
X-SOW-Generation: 4
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 95e8c59d21d69285ac788bd8ea78b0544b0a1395ae9a0e3a700ec13b420e5c39 2245 main/binary-amd64/Packages
 4d658bdf6a542999f737e5f89e3bdb504c205fb85cda76f3e4b1ef73619c5900 751 main/binary-amd64/Packages.gz
 c924dbbd01d2e14bc3a4892a355b3674cb238f8315e55c609d25043568f59dc8 1122 main/binary-arm64/Packages
 a4289540a3224dbfbdf1c5b23db355c6541df34baf378070a493d9380f03b1ee 668 main/binary-arm64/Packages.gz
```

`by-hash/SHA256/` 的作用是:让刚刚取过 `Release` 的客户端在索引更新时不会扑空 ——
新索引发布的同时,旧索引仍可按摘要访问。APT 1.2 及以后版本会自动使用它。

空 Dist 同样是合法 Dist。没有任何包的 DEB Dist 会发布空的 `Packages`、对应的 `.gz`、
by-hash 条目和已签名的 `Release`;RPM Dist 则为每个架构发布空但可消费的 `repodata`。

## 名称

仓库名与 Dist 名必须匹配 `[a-z0-9][a-z0-9._-]*`,因为它们都会变成目录名,
必须在大小写敏感与不敏感的文件系统上表现一致。

下列名称是保留名,一律拒绝:

| 保留名 | 原因 |
|---|---|
| `.`、`..` | 路径穿越 |
| `.sow` | 私有状态目录 |
| `pool`、`dists` | 仓库固定子目录 |
| `sow.yml` | 配置文件 |
| `workspace.lock`、`workspace-ops`、`repo-locks` | 工作区状态路径 |

两个会在 SQLite 附属文件名上碰撞的仓库名也会被拒绝 ——
名为 `db` 的仓库和名为 `db.db` 的仓库会争夺 `.sow/db.db`:

```console
configuration error: ... repository names "db" and "db.db" collide at reserved state path "db.db"
```

## 服务什么,隐藏什么

{{% alert title="绝不要通过 HTTP 暴露 .sow" color="warning" %}}
`.sow/` 里有状态数据库、锁、staged 文件和 pending 包体存储。
把它暴露出去会泄露内部状态,还会让客户端下载到**刻意尚未发布**的软件包。
{{% /alert %}}

安全的做法是把 Web 服务器指向**某个仓库目录**,而不是工作区根目录:

```nginx
# 正确:文档根是一个仓库
location /pigsty/ {
    alias /srv/repo/pigsty/;
    autoindex on;
}
```

如果确实需要服务工作区根目录(比如把多个仓库放在同一前缀下),请显式拒绝私有路径:

```nginx
location ^~ /.sow  { deny all; }
location = /sow.yml { deny all; }
```

复制时同理。`sow changes 0` 列出的正是构成当前发布树的全部文件,
每一条路径都在 `pool/` 或 `dists/` 之下;`sow.yml` 与 `.sow/` 永远不会出现在其中,
因为它们不属于镜像。

```bash
# 发布一个仓库。--hard-links 保留视图去重。
rsync -a --hard-links --delete /srv/repo/pigsty/ mirror:/var/www/pigsty/
```

复制前先确认这棵树可交付:

```bash
sow check -r pigsty
```

处于 `dirty`(待构建)的仓库,其发布树仍然是上一次 build 留下的完整自洽版本 ——
只是还没反映你最新的改动。这种情况下 `sow check` 退出码为 `5`,
好让部署脚本停下来,而不是误把过期的树推上去。

## 延伸阅读

- [包池与架构视图](/zh/docs/feature/views/) —— 布局为什么长这样
- [对外服务](/zh/docs/tutorial/serving/) —— 完整的 Web 服务器配置
- [`sow changes`](/zh/docs/reference/cli/build/) —— 一次交付的精确文件清单
- [兼容性](/zh/docs/reference/compatibility/) —— 文件系统约束汇总
