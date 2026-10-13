---
title: "为什么 SOW 每个仓库只保留一棵包体树"
linkTitle: "单包体仓库"
date: 2026-08-05
lastmod: 2026-10-13
authors: [Vonng]
description: "每个仓库共用一个包池，各发行版视图只保存元数据，避免重复包副本。"
categories: [Design]
tags: [repository, pool, rpm, apt, compatibility, decision]
url: "/zh/blog/design/single-payload/"
aliases:
  - "/docs/design/single-payload/"
weight: 70
icon: fa-solid fa-layer-group
draft: false
---

这项决策起草于 2026-08-05，随 2026-08-08 的 SOW v0.2.0 发布。SOW 0.5.0 仍使用这一布局：
每个仓库保存一棵包体树，各发行版视图引用同一棵树。

<span id="最终决策"></span>

## 决策

每个 Repository 的公共目录如下：

```text
<repository>/
  pool/                         # 包体
  dists/
    <dist>/
      <architecture>/           # RPM 元数据
```

上图展示 RPM 视图。APT 索引位于 `dists/<dist>/main/binary-<architecture>/`，
`Release` 文件位于 `dists/<dist>/`。

一个包对象在一个仓库内只有一个包体路径。将同一个包加入多个 Dist 或架构视图，只增加成员关系和元数据引用。

复制、静态托管、鉴权和发布都以完整的 `pool/ + dists/` 根目录为单位。
单个架构目录是客户端视图，不是完整的软件仓库。

## 从 C2 开发线到 v0.2.0

早期 C2 开发线在根包池中保存一份包体，再在每个 RPM 视图内创建包体硬链接。
这让部分 `reposync` 客户端可以直接使用独立的架构目录，同时节省本地空间。

硬链接在其他环节带来几个问题：

- 对象存储把每条路径存为独立对象，重新产生包副本。
- 归档和跨文件系统复制可能丢失硬链接关系。
- 视图内的包路径看起来像独立文件，实际仍由仓库管理。
- 保留与回收容易依赖链接计数，而不是实际包引用。
- 仓库布局需要迁就特定镜像工具的输出目录要求。

v0.2.0 发布前，最终布局删除了 RPM 视图中的包体别名。归档中的 C2 文档描述的是该开发线。

<span id="元数据如何引用-pool"></span>

## 元数据如何引用包池

APT 的 `Filename` 是相对仓库根目录的路径，因此可以直接引用包体：

```text
Filename: pool/p/pkg/pkg_1.0_amd64.deb
```

RPM 的 `<location href>` 使用从视图目录到包池的相对路径：

```text
view:    dists/el9/x86_64/
payload: pool/p/pkg/pkg-1.0-1.x86_64.rpm
href:    ../../../pool/p/pkg/pkg-1.0-1.x86_64.rpm
```

渲染器和检查器使用同一个路径函数。函数计算相对路径、转义文件名，再检查解析结果是否仍指向仓库内的原包路径。

只要 `pool/` 与 `dists/` 的相对位置不变，就可以把整个公共目录复制到其他目录、HTTP 站点、桶或前缀，
无需改写元数据。

<span id="被否决的方案"></span>

## 其他方案

| 方案 | 未采用的原因 |
|---|---|
| 每个 RPM 视图放包体硬链接或副本 | 产生路径别名和重复对象存储键 |
| 包体符号链接 | 对象存储不支持，静态服务与归档的处理也不一致 |
| 使用 `/pool/...` 绝对路径 | 客户端可能从站点根目录解析，破坏带前缀的仓库 URL |
| 绝对 URL 或 `xml:base` | 将元数据绑定到一个站点，搬迁时需要修改 |
| CDN 改写或重定向对象 | 仓库依赖额外的路由配置 |
| 工作区或桶级共享包池 | 需要跨仓库协调锁、保留与删除 |

<span id="镜像工具兼容属于导出问题"></span>

## 为镜像工具导出独立目录

包管理器需要解析元数据引用并下载包体。镜像工具还可能要求所有软件包都位于指定视图目录之下。

需要独立 RPM 架构目录时，运行 `sow export rpm-leaf`。命令在仓库外生成包文件和指向本地文件的元数据。
默认复制包体；同一文件系统可使用 `--hardlink`，但导出包必须保持只读，因为写入硬链接也会修改包池文件。
导出目录不属于 Generation，不是发布源，也不参与成员关系或垃圾回收。

客户端与镜像工具测试见[兼容性参考](/zh/docs/reference/compatibility/)。
用 [`sow check`](/zh/docs/command/check/) 校验本地路径、摘要和文件引用，用对应客户端测试安装与镜像下载。

## 结果

- 包身份、成员关系、Generation、保留与本地 GC 都在仓库内管理。
- 发布尝试、检查点、远端清单、宽限期与删除记录按目标前缀管理。
- 每个包文件对应一个静态对象存储键。
- 删除包体前检查引用和文件身份，不依赖硬链接计数。
- 复制完整仓库根目录，或通过导出命令生成独立的 RPM 架构目录。

实现方式见[包池与元数据视图](/zh/docs/feature/views/)，状态与发布流程见
[系统模型](/zh/blog/design/model/)和[发布与恢复](/zh/blog/design/publication/)。
