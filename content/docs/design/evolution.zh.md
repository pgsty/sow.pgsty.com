---
title: "设计演进"
linkTitle: "设计演进"
description: "从 v0.1.0 仓库实验、未正式发布的 C2 原型，到当前 v0.2.0 单包体架构的演进路径。"
url: "/zh/docs/design/evolution/"
weight: 600
icon: fa-solid fa-timeline
---

SOW 的历史资料描述过几套实质不同的系统。Git 历史清理后，公开版本序列已经很简单：
**v0.1.0** 是研究基线，**v0.2.0** 是当前产品。C2 曾作为两者之间的开发布局存在，但从未
作为独立产品版本发布。

## 时间线

| 版本线 | 主要问题 | 物理模型 | 处置 |
|---|---|---|---|
| v0.1.0（2026-07-31） | 纳管 Pigsty 既有 APT/YUM 树并探索远端发布 | Git/CAS、route-aware 投影、edge/provider 契约 | 历史研究基线 |
| 未发布的 C2 原型 | 交付紧凑的 Plain + Managed 本地仓库管理器，并兼容默认 EL `reposync` | 根 Pool + view-local RPM 硬链接 | 只作为迁移输入；不是当前布局 |
| v0.2.0（2026-08-08） | 每个 Repository/prefix 只保留一份正典包体，并加入 target-scoped 发布 | 根 Pool + 纯元数据 view、显式导出、filesystem/R2 target | 当前版本线 |

产品不存在 v1 正式版本，也不存在 v0.3 产品线。`sow.cli/v1`、`single-payload-v1`、
`sow-rpm-leaf-v1` 这类名称是 wire/layout schema，不是 Git tag。

## v0.1.0 留下了什么

v0.1.0 大范围探索了既有仓库纳管、远端发布、供应商 fencing、边缘鉴权、迁移、恢复与大仓库证据。
它具体的 Git/CAS/route 模型后来被替换，但几条原则保留下来：

- 身份绑定最终字节；
- 配置、本地状态、公共状态与供应商状态各有其主；
- 发布是有顺序、可恢复的事务，不是一次 `rclone` 副作用；
- 破坏性操作需要精确 inventory 与供应商证据；
- 每项结论都要写明源码 revision、环境与验证层级。

原始 PRD、ADR、评审与日期化证据可从 v0.1.0 标签和 Git 历史查阅。它们是取证输入，
不是当前命令或布局文档。

## C2 原型与 `reposync`

发布前的 C2 布局使用一个正典根 Pool，并给每个 RPM view 建立本地硬链接 alias：

```text
pool/...                              正典包体
dists/el9/x86_64/pool/...             hardlink alias
dists/el9/x86_64/repodata/...         href="pool/..."
```

这样每个 RPM 架构 leaf 都是自包含的，默认 EL `reposync` 可以完整镜像；本地去重则依赖
同文件系统硬链接。上传到对象存储后，每条 alias 都会变成完整对象，这与更强的“每个发布
前缀只有一份包体”边界冲突。

C2 结果仍是那个原型的有效兼容性证据，但不能证明当前正典 Repository 支持默认 `reposync`。

## v0.2.0 为什么使用单包体

v0.2.0 把每个 Repository/publish prefix 只有一份正典 payload 设为不变式。RPM view 只保留
元数据，并计算回到根 Pool 的相对路径：

```text
pool/...                              唯一包体
dists/el9/x86_64/repodata/...         href="../../../pool/..."
```

APT 的 `Filename` 本来就相对 archive root，因此天然共享同一 Pool。完整 `pool/ + dists/`
Repository 可以普通复制、打包或上传，不依赖 inode 身份。需要自包含 RPM leaf 时，
`sow export rpm-leaf` 会显式生成外部副本；也可显式选择可信的同文件系统硬链接导出，
但重复成本不会再藏进正典仓库。

## 迁移边界

部分开发期工作区使用 `schema: sow/v2` 与 C2 物理布局；v0.2.0 新建的是 `schema: sow/v3`。
只读发现可以识别前一版，但普通 writer 不会暗中升级。只有 `sow repo migrate` 才进入
journaled transition：

```text
planned -> staged -> commit_intent -> pointer_rollforward
        -> grace -> alias_delete -> final_manifest -> done
```

commit intent 前，`sow repo migrate --abort` 可以恢复 C2；之后只能前滚。旧 metadata 可能仍被
客户端持有，因此 legacy alias 会保留到 grace 结束，再按精确 inventory 删除，绝不触碰根 Pool。

缺少安全条件删除的供应商应使用新的非重叠 prefix，并把旧 prefix 整体退役。SOW 不会虚构
“旧远端树已经物理去重”的证据。

## 历史资料策略

历史文件用于解释决策，维护文档用于解释产品。不要修改旧测试结果来迎合新实现；新行为写入
当前文档与 CHANGELOG，原始证据通过版本标签和 Git 历史查阅。
