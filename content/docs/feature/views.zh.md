---
title: "包池与元数据视图"
linkTitle: "包池与视图"
description: "在 RPM 与 APT 视图间共用包文件，导出独立 RPM 仓库，并交付完整仓库。"
categories: [Feature]
tags: [pool, dist, rpm, deb]
url: "/zh/docs/feature/views/"
weight: 400
icon: fa-solid fa-layer-group
---

<span id="不变式" data-td-print-local></span>

Managed 仓库将每个包对象保存在 `pool/` 中。Dist 和架构视图只包含引用这些包字节的索引。

```text
<repo>/pool/                              包文件
<repo>/dists/<rpm-dist>/<arch>/repodata/   RPM 元数据
<repo>/dists/<deb-dist>/main/binary-*/     APT 元数据
```

存储范围是一个仓库。同一个包放入其他仓库或发布目标后，分别占用相应仓库或目标的命名空间。

<span id="构建完成的-repository" data-td-print-local></span>
<span id="rpm-view-使用计算出的父级相对-href" data-td-print-local></span>
<span id="为什么-view-只含元数据" data-td-print-local></span>
<span id="中性包只被选入不会复制" data-td-print-local></span>

## RPM 视图

RPM Dist 为每个配置架构生成一个元数据目录：

```text
demo/
├── pool/
│   ├── e/example/example-1.0-1.x86_64.rpm
│   └── d/demo-data/demo-data-1.0-1.noarch.rpm
└── dists/el9/
    ├── x86_64/repodata/
    │   ├── <sha256>-primary.xml.gz
    │   ├── <sha256>-filelists.xml.gz
    │   ├── <sha256>-other.xml.gz
    │   └── repomd.xml
    └── aarch64/repodata/
        └── ...
```

`x86_64` 视图包含 `x86_64` 和 `noarch` 包，`aarch64` 视图包含 `aarch64` 和 `noarch` 包。
两个视图引用同一份 `noarch` 文件。

包位置相对于架构目录：

```xml
<location href="../../../pool/d/demo-data/demo-data-1.0-1.noarch.rpm"/>
```

客户端指向 `dists/el9/x86_64/`，服务端提供完整 `demo/` 目录，使相对包路径可以解析。
`sow check` 检查索引路径没有逃出仓库，并指向预期包对象。

<span id="apt-view" data-td-print-local></span>

## APT 视图

APT 索引使用相对于仓库根的路径：

```text
Filename: pool/e/example/example_1.0-1_amd64.deb
```

每个配置架构在 `dists/<dist>/main/binary-<arch>/` 下有 `Packages`、`Packages.gz`
和 SHA-256 by-hash 条目。Dist 根包含 `Release`，已签名时还有 `InRelease`、`Release.gpg`。

`all` 包出现在每个适用架构索引中，包体仍只有一份包池对象。
没有每视图包副本，也没有每架构 `Release` 文件。

<span id="普通客户端与-reposync-是两份契约" data-td-print-local></span>

## 为 `dnf reposync` 导出

默认 `dnf reposync` 会拒绝越过其单仓库下载目录的 Managed RPM 路径。
此工作流可使用独立仓库导出：

```bash
sow export rpm-leaf el9 x86_64 /srv/exports/el9-x86_64 -r demo
```

导出包含本地包路径、独立 repodata、清单和 `.sow-export.json` 完成标记。
目标目录应位于仓库和所有已配置 filesystem 发布根之外。

默认复制文件。`--hardlink` 要求同一文件系统，使导出包与源包共用 inode，
因此应保持导出文件只读。导出不会创建 Dist 成员或保留构建快照，也不是 `sow publish` 的输入。

<span id="复制与发布" data-td-print-local></span>

## 交付完整仓库

在线更新使用已配置的发布目标。需要其他传输方式时，先将完整、已稳定的
`pool/ + dists/` 复制到单独暂存目录，检查副本后再切换上线。缓存中的索引所引用的包 URL
应保持可访问，直到缓存过期。完整传输流程见[对外服务](/zh/docs/tutorial/serving/)。
只复制某个 RPM 架构目录，会使包路径无法解析。

`sow changes 0` 在 `pool/` 下列出每个包一次，再列元数据和客户端入口。
它描述本地文件；目标进度与缓存处理由 `sow publish` 管理。

继续阅读[仓库布局](/zh/docs/reference/layout/)、
[对外服务](/zh/docs/tutorial/serving/)和 [`export`](/zh/docs/command/export/)。

<span id="继续阅读" data-td-print-local></span>
