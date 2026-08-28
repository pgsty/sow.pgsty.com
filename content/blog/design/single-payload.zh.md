---
title: "为什么 SOW 每个仓库只保留一棵包体树"
linkTitle: "单包体仓库"
date: 2026-08-05
lastmod: 2026-08-28
authors: [Vonng]
description: "用唯一正典 Pool 与纯元数据视图，替代 RPM 视图内包体硬链接的设计决策。"
categories: [Design]
tags: [repository, pool, rpm, apt, compatibility, decision]
url: "/zh/blog/design/single-payload/"
aliases:
  - "/docs/design/single-payload/"
weight: 70
icon: fa-solid fa-layer-group
draft: false
---

这项决策起草于 2026-08-05 的 v0.2 发布前设计收敛阶段，并在 2026-08-08 随 SOW v0.2.0
正式交付，随后延续为 v0.3 与 v0.4 的布局契约。它记录的是架构选择，不是笼统的兼容性
PASS：协议闭包、普通软件包客户端、镜像工具、静态托管与对象存储始终属于彼此独立的证据层。

## 最终决策

每个 SOW Repository 只拥有一棵公共树：

```text
<repository>/
  pool/                         # 正典包体
  dists/
    <dist>/
      <architecture>/           # 只有协议元数据
```

一个 Package Object 在一个 Repository 内只有一个正典包体路径。把同一对象加入多个 Dist
或架构视图，只会增加 Membership 与元数据引用，不会再创建一份正典包文件。

完整的 `pool/ + dists/` 根目录才是受支持的复制、静态托管、鉴权与发布单元。单个架构
Leaf 只是客户端视图，不是独立拥有状态的仓库。

## 从 C2 开发线到 v0.2.0

早期发布前 C2 开发线已经把每个包在根 Pool 中存一份，但会在每个 RPM View 内再创建包体
硬链接。这套布局可以让选定的 `reposync` 客户端得到自包含 Leaf，同时避免在本地复制字节。

问题在于，这种 inode 优化无法穿过完整交付边界：

- 对象存储会把每条路径展开成独立 Key，别名重新变成重复包体；
- 归档与跨文件系统复制可能展开或丢失硬链接身份；
- View 内包路径看起来像正典数据，但所有权其实仍属于 Repository；
- Retention 与 GC 容易误把 link count 当作产品状态；
- 为迁就单个镜像工具，会迫使正典树服从它的本地输出假设。

在 v0.2.0 打 Tag 之前，最终单包体设计已经从正典 RPM View 中删除包体别名。归档中的 C2
文档仍准确描述那条开发线，但不能用来描述正式 v0.2.0 Release Tag。

## 元数据如何引用 Pool

APT 的 `Filename` 本来就是相对 Archive Root 的路径，因此软件包条目直接写正典路径：

```text
Filename: pool/p/pkg/pkg_1.0_amd64.deb
```

RPM 则根据实际 View 目录与正典 Pool 路径计算每个 `<location href>`：

```text
view:    dists/el9/x86_64/
payload: pool/p/pkg/pkg-1.0-1.x86_64.rpm
href:    ../../../pool/p/pkg/pkg-1.0-1.x86_64.rpm
```

Renderer 与 Checker 复用同一个路径函数：先规范化 Repository-relative Path，再计算字面父级
导航，对数据字节恰好转义一次，基于目录 URI 解析结果，并要求 Round Trip 精确回到原 Pool
路径、且不能离开 Repository。

这样公共树仍然可搬迁：只要 `pool/` 与 `dists/` 的相对关系不变，同一份字节无需改写
元数据，就可以复制到另一目录、HTTP Origin、Bucket 或 Prefix。

## 被否决的方案

| 方案 | 为什么不进入正典布局 |
|---|---|
| 每个 RPM View 放包体硬链接或副本 | 制造路径别名与重复对象 Key，把文件系统优化伪装成持久所有权 |
| 包体 Symlink | 无法移植到对象存储，在静态服务、归档与信任边界上也不安全 |
| 使用 `/pool/...` 绝对 href | 不同客户端会把它解释成 Host Root 或 Repository-relative，也会破坏非根 Prefix |
| 绝对 URL 或 `xml:base` | 把元数据绑定到单一 Origin，无法原样搬迁 |
| 依赖 CDN Rewrite 或 Redirect Object | 把外部 Router 变成仓库正确性的一部分 |
| Workspace 或 Bucket 全局 CAS | 引入 SOW 并不承诺的跨 Repository 所有权、锁、Retention 与删除协调 |

## 镜像工具兼容属于导出问题

普通软件包客户端只需解析元数据引用并取得包体；镜像工具还可能强制要求每个包都位于它收到的
View 目录之下。这是两种不同契约。

SOW 不会为了覆盖所有镜像工具而扭曲正典 Repository。需要独立 RPM Leaf 时，
`sow export rpm-leaf` 会在仓库外生成带本地元数据的兼容制品。默认使用 Copy；
`--hardlink` 只是受控只读边界内、同文件系统上的显式优化。导出目录不是 Generation、
发布源、Membership Owner 或 GC Root。

客户端与镜像工具结果统一记录在[兼容性矩阵](/zh/docs/reference/compatibility/)。
结构化 [`sow check`](/zh/docs/command/check/) 成功只能证明路径、摘要与闭包不变式，
不能把尚未运行的客户端或 Provider 单元格自动升级为 PASS。

## 结果

- Package Identity、Membership、Generation、Retention 与本地 GC 都保持 Repository Scope。
- Publication Attempt、Checkpoint、远端 Inventory、Grace 与删除证据保持 Target-prefix Scope。
- 每个正典文件一对一映射到静态对象 Key。
- 包体删除服从引用闭包与精确文件身份，不依赖 inode link count。
- 不支持只复制某个 RPM 架构 Leaf；应复制 Repository Root 或显式创建 Leaf Export。

当前实现机制见[包池与元数据视图](/zh/docs/feature/views/)；周边所有权与生命周期契约见
[系统模型](/zh/blog/design/model/)和[发布与恢复](/zh/blog/design/publication/)。
