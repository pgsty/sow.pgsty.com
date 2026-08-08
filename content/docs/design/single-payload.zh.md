---
title: "单包体仓库"
linkTitle: "单包体布局"
description: "v0.2.0 如何让每个 Repository 只有一条正典包体路径，并渲染纯元数据 APT/RPM 视图。"
url: "/zh/docs/design/single-payload/"
weight: 300
icon: fa-solid fa-box-archive
---

v0.2.0 布局的目标很精确：在一个 Repository 及其每个发布前缀内，每个 live Package Object
恰好只有一条包体路径。

{{% alert title="当前版本布局" color="primary" %}}
这是 v0.2.0 的正典布局。未发布的 C2 原型工作区使用 `schema: sow/v2`，必须显式执行
`sow repo migrate`；新工作区使用 `sow/v3`。迁移 C2 工作区前请先读
[设计演进](/zh/docs/design/evolution/)。
{{% /alert %}}

## 正典目录树

```text
<repo>/
├── pool/                                      # 正典包体
│   └── <prefix>/<source>/<filename>
└── dists/                                     # 纯元数据投影
    ├── <rpm-dist>/<arch>/repodata/
    └── <deb-dist>/<component>/binary-<arch>/
```

正典布局中没有 `release/`、`reposync/`、每视图 `pool/`、每代包体树或每快照包体树。
`pool/ + dists/` 整体才是搬迁与发布单元。

“只存一份”的边界是一个 Repository 或一个 target prefix，不是 Workspace、bucket、账号或
整套系统。相同软件包位于不同 Repository/target 时仍是各自主权下的独立对象。

## APT 寻址

APT 原生把包路径定义为相对 archive root：

```text
Filename: pool/p/postgresql-18/libpq5_18.3-1_amd64.deb
```

客户端从同时包含 `dists/` 与 `pool/` 的 Repository 根出发，因此多个 suite 与架构索引可以
直接引用同一份正典 DEB，不需要包体别名。`Acquire-By-Hash: yes` 为索引提供不可变读取路径，
`Release` / `InRelease` 则继续充当提交指针。

`Filename` 是 archive path 的字面拼写，不是提前编码过的 URL；URI 编码只在获取层执行一次。

## RPM 寻址

RPM 元数据相对于架构视图解析 `<location href>`。v0.2.0 从实际 view root 计算到正典 Pool
对象的相对路径：

```text
dists/el9/x86_64/repodata/primary.xml.gz
  location href="../../../pool/p/pev2/pev2-1.23.0-1.noarch.rpm"
```

深度由路径计算，绝不写死。checker 会用 POSIX URL 语义解析并规范化 href，证明它落在同一
Repository 内预期的正典对象上。`/pool/...` 根绝对 URL、部署域名、absolute `xml:base`、
redirect object 与 edge rewrite 都不能成为正确性的前提。

HTTP 客户端可以在发请求前消解 dot segment；正典 object key 本身绝不含 `.` / `..`。
代理与对象存储的具体行为仍需要独立兼容门禁。

## 为什么取消包体硬链接

未正式发布的 C2 原型用硬链接把 RPM 包投影进每个架构视图。在单个 POSIX 文件系统上，
这些路径共享 inode，
本地磁盘成本很低，默认 EL `reposync` 也能工作。但对象存储没有 inode 身份：每条 alias 路径
都会成为一个完整对象和一次完整上传；Dist、架构、Generation 与快照越多，远端包体越膨胀。

v0.2.0 不再让文件系统实现细节定义正典正确性。普通 copy、tar 或对象存储上传即使丢失硬链接，
功能也必须保持不变。

## 搬迁契约

受支持的 handoff 复制一棵完整、稳定的 Repository 根：

1. 绑定一份不可变 Built Generation；
2. 复制 `pool/ + dists/` 中所有常规文件；
3. 按 Generation 复验 path、size 与 SHA-256；
4. closure 通过后才暴露目标。

只复制 `dists/<dist>/<arch>/` 不受支持，因为其中的元数据有意引用同级根 Pool。

## 兼容导出

如果操作者需要让默认 `reposync` 或旧工具消费自包含 RPM leaf，v0.2.0 显式生成外部导出：

```text
sow export rpm-leaf DIST ARCH DIR
```

导出必须位于正典 Repository 与所有已配置发布前缀之外。默认使用 copy；hardlink 需要显式
选择、同文件系统，且只适用于可信、只读、可随时丢弃的目录。导出不会成为 Membership、
Generation、publish input 或 GC root。

这样一来，重复包体是操作者主动选择的兼容成本，而不是正典仓库隐藏的属性。
