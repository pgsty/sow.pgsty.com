---
title: "包池与元数据视图"
linkTitle: "包池与视图"
description: "一份软件包、一个属主、纯元数据 APT/RPM 视图：正典包池寻址、中性包、搬迁与显式 reposync 导出。"
url: "/zh/docs/feature/views/"
aliases:
  - "/docs/design/single-payload/"
weight: 400
icon: fa-solid fa-layer-group
---

## 不变式

在一个 Repository 内，每个 live Package Object 在 `pool/` 下只有一条正典 payload 路径。
Dist 与架构 view 拥有元数据，不拥有包体 alias：

```text
<repo>/pool/...                              正典包体
<repo>/dists/<rpm-dist>/<arch>/repodata/... 纯 RPM 元数据
<repo>/dists/<deb-dist>/main/binary-*/...   纯 APT 元数据
```

相同 digest 出现在另一个 Repository 或发布 prefix 时，仍是另一个 owner 下的独立对象。
SOW 不会为了本地去重而制造共享的分布式所有权。

## 构建完成的 Repository

一个包含一份 `x86_64` 包与一份 `noarch` 包的 RPM Dist 形如：

```text
demo/
├── pool/
│   ├── c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
│   └── e/epel-release/epel-release-7-5.noarch.rpm
└── dists/el9/
    ├── aarch64/repodata/
    │   ├── <sha256>-primary.xml.gz
    │   ├── <sha256>-filelists.xml.gz
    │   ├── <sha256>-other.xml.gz
    │   └── repomd.xml
    └── x86_64/repodata/
        ├── <sha256>-primary.xml.gz
        ├── <sha256>-filelists.xml.gz
        ├── <sha256>-other.xml.gz
        └── repomd.xml
```

不存在 `dists/.../pool/` 子树。仍被保留的 live Generation 可以让多组内容寻址元数据并存；
`repomd.xml` 指针决定当前生效的是哪一组。

## RPM view 使用计算出的父级相对 href

rpm-md 相对架构 view 解析 `<location href>`。SOW 从实际 view 计算回到正典 Pool 的路径：

```xml
<location href="../../../pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm"/>
<location href="../../../pool/e/epel-release/epel-release-7-5.noarch.rpm"/>
```

深度从实际 view root 推导，不来自域名，也不写死部署路径。`sow check` 会解析、规范化每条
href，拒绝逃出 Repository 的路径，并证明它抵达预期 Pool 对象。

因此完整 Repository 根才是客户端与交付边界。DNF 指向 `dists/el9/x86_64/`，但对外服务或
复制时必须包含同级根 `pool/` 的整个 Repository。

## 为什么 view 只含元数据

如果把软件包复制到每个架构 view，在没有 inode 身份的存储系统上就会产生额外 object key
与重复上传。SOW 因此把包体所有权集中在 Repository 包池，让索引负责投影成员关系。
完整复制、归档或发布都能保持这份契约，无需依赖 hardlink。

“只存一份”的边界是一个 Repository 或一个发布前缀，不是 Workspace、bucket、账号或整套
系统。相同软件包位于不同 Repository 或 target 时仍有各自独立的 owner。

## 中性包只被选入，不会复制

`x86_64` view 选择 `x86_64 + noarch`；`aarch64` view 选择 `aarch64 + noarch`。
中性包仍只有一份 Pool 对象，每个 view 只增加一条指回它的元数据记录。

DEB 在 archive root 层面同理：`all` 包进入每个适用的 `Packages` 索引，`Filename: pool/...`
始终指向唯一正典包体。

## APT view

APT 原生把 `Filename` 定义成相对 archive root：

```text
Filename: pool/p/postgresql-18/libpq5_18.3-1_amd64.deb
```

SOW 在 `dists/<dist>/main/binary-<arch>/` 下渲染 `Packages`、`Packages.gz` 与 `by-hash`。
`Release`、`InRelease`、`Release.gpg` 是协议指针与签名。没有每 view 包体 alias，也没有
每架构 `Release` 存根。

## 普通客户端与 `reposync` 是两份契约

规范布局面向能消费完整 Repository 并正确处理协议相对路径的软件包客户端。默认 EL
`dnf reposync` 是另一份契约：它的 safe-write 检查会
拒绝规范化后落到 per-repository 下载目录上方的软件包路径。这是明确不支持的组合；该工作流
应使用导出的 Leaf。

需要自包含 RPM leaf 时，在 Repository 与所有已配置 filesystem 发布根之外创建导出：

```bash
sow export rpm-leaf el9 x86_64 /srv/exports/el9-x86_64
```

导出拥有自己的包体树、repodata、manifest 与 `.sow-export.json` 完成标记。默认复制；
`--hardlink` 是显式的同文件系统、可信只读优化。导出不会成为 Membership、Generation、
publish input 或 GC root。

## 复制与发布

正典正确性不依赖 inode 身份。优先使用已配置的 Publication Target。必须使用其他传输方式时，
用 `rsync`、`cp` 或 tar 把完整、稳定的 `pool/ + dists/` 复制到离线 staging，复验后再原子
切换上线；不要逐文件更新在线树。只复制某个 RPM 架构 Leaf 不受支持，因为其中元数据有意
引用同级根 Pool。

`sow changes` 只在 `pool/` 下列一次包体，随后是元数据与指针：

```text
add  payload   pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm  ...
add  payload   pool/e/epel-release/epel-release-7-5.noarch.rpm                  ...
add  metadata  dists/el9/x86_64/repodata/<sha256>-primary.xml.gz               ...
add  pointer   dists/el9/x86_64/repodata/repomd.xml                            ...
```

`dists/` 下不会出现 package payload 变更项。

## 继续阅读

- [Managed 工作区](/zh/docs/feature/managed/)——所有权与 Generation 状态
- [平台与集成](/zh/docs/reference/compatibility/)——已验证与明确不支持的组合
- [对外服务](/zh/docs/tutorial/serving/)——HTTP、复制与发布目标
- [仓库布局](/zh/docs/reference/layout/)——准确的公有/私有路径
