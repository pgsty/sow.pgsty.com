---
title: "v0.2 重置：用 Plain 与 Managed 取代万能控制面"
linkTitle: "v0.2 Plain/Managed 重置"
date: 2026-07-31
lastmod: 2026-08-28
authors: [Vonng]
description: "SOW 如何用两条小型执行路径、明确所有权、SQLite 状态与仓库核心，替换 v0.1 的 Git/CAS/Edge 平台。"
categories: [Design]
tags: [history, v0.2, plain, managed, architecture, decision]
url: "/zh/blog/design/v02-reset/"
weight: 80
icon: fa-solid fa-arrows-rotate
draft: false
---

> [!IMPORTANT] 开发设计线不等于发布版本
> 归档中的“v0.2”设计线最初使用 C2 View-local RPM Hardlink。这是一条真实实现过的开发线，
> 但在最终 v0.2.0 Tag 之前已经被单包体设计替换。正式发布的 v0.2.0 已经使用唯一正典 Pool
> 与纯元数据 View。
>
> 归档中仍有数份 v0.2/v0.3 文件声称“v0.2.0”使用 C2 Hardlink；它们写于 Tag 产生之前，
> 当时的“v0.2.0”指计划中的 Build。实际交付边界由最终 0.2.0 Changelog、Release Note
> 与源码 Tag 决定，三者都记录唯一正典 Pool 与纯元数据 View。

2026-07-31，v0.1 源码基线刚刚封存，SOW 就开始了一次产品重置。目标不是挽救每个 V1 子系统，
而是找出能够替代 Pigsty 日常软件包构建，同时保留既有安全教训的最小 Repository 产品。

最终形成的边界沿用至今：**Plain** 负责可重建目录，**Managed** 负责长期 Repository 所有权。

## 为什么不在 V1 上逐步删功能

v0.1 把五类不同任务耦合在一起：

1. 构建有效 APT/YUM/Asset Repository；
2. 维护 Package History 与 Snapshot；
3. 迁移庞大的 Pigsty 旧拓扑；
4. 发布到多套 Cloud/CDN Target；
5. 执行商业 Edge Access Control。

逐项删除功能仍会保留 Git/CAS/Route 所有权模型。重置则直接追问：Repository Engine 真正需要
拥有哪些事实？

最初 Phase One 的边界与功能列表同样重要：

- 不使用 V1 Git Database、Route/Manifest/Quarantine 模型或全局 Content-addressed
  Product Layer；
- 不提供 Upstream Sync、Pull/Push/Copy/Move/Promote、Edge Entitlement、CDN Bootstrap
  或商业拓扑；
- 第一阶段不提供 Remote Publication/State、Object Storage、GC、Snapshot/Freeze、
  Managed Export 或 Serving；
- 不提供 Modulemd、Source-package Build、Web UI、跨 Repository 去重或 Multi-writer。

即使 V1 已经为 Upstream Sync 与 Channel Promotion 留下真实 Streaming、Fuzz 与确定性 Proof
证据，重置仍有意把它们移出产品。Package Acquisition 是输入边界，不应成为 Repository Engine
中的第二个 Owner。运维者可以用专门 Mirror/Download 工具准备包集合，再由 SOW 负责 Admission、
Membership、Build 与 Publication。部分 Phase-one 排除项——Publication、Retention、GC 与
External Export——在最终 v0.2.0 Tag 前，以更小的 Repository 所有权模型重新进入。

## 两条隔离的执行路径

### Plain：重建调用者拥有的目录

Plain 模式处理调用者拥有的 RPM/DEB 目录：

```bash
sow create /srv/repo
```

它扫描 Package、渲染协议 Metadata、验证结果并最后安装 Pointer。Plain 只拥有生成的 Metadata，
不拥有 Workspace、Repository Database、Generation History 或长期 Membership。

因为 Desired State 就是“当前目录里的 Package”，正确恢复方法是重新运行构建。后续版本进一步
贯彻这一原则，删除 Plain Journal 与重复包体读取。

### Managed：拥有生命周期与历史

Managed 模式引入包含多个独立 Repository 的 Workspace：

```text
Workspace
├── sow.yml
├── .sow/                    私有配置、锁、SQLite、Journal
└── <repository>/
    ├── pool/                正典包体
    └── dists/               客户端协议视图
```

每个 Repository 拥有自己的 Pool、Package Object、Membership、Desired State、Built
Generation、Changeset、Lock、Database 与 Recovery State。不同 Repository 不会暗中去重
或共享计数器。

Dist 是具名 RPM/DEB Membership Set。Architecture View 是 Membership 的投影，不是新的 Owner。
Neutral Package（`noarch` / `all`）会进入每个适用架构，但不会复制逻辑 Membership。

## 哪些决定替换了 V1 概念

| V1 概念 | v0.2 替代项 |
|---|---|
| Git Commit/Ref 正典状态 | Per-Repository SQLite 加显式 Filesystem/Journal Evidence |
| 全局 CAS 与 Route Materialization | Repository-owned Pool 与 Protocol View |
| View/Snapshot/Stable Ref Graph | Dist Membership、Desired Revision、Built Generation、Retained State |
| 一套万能命令面 | 封闭的 Plain 与 Managed CLI 契约 |
| 隐式旧拓扑 | 严格 `sow.yml`、显式 Name 与 Selector |
| 跨产品 Publication Saga | Repository Build 与 Target Publication 分离 |
| 直接复用 V1 Package | 只复用窄 Parser/Renderer/Version/Signing Port |

最关键的简化是：不借助 Git 或 Edge Router，也能完整解释私有控制状态与公共 Repository Byte。

## Desired 与 Built

Managed 模式把中断状态变成显式事实：

- **Desired State** 是 SQLite 中当前 Package 与 Membership 意图；
- **Built Generation** 是最近一次完整渲染并验证成功的公共树；
- **Changeset** 是两份 Built State 的精确差异。

Desired 可以前进，而 Built 继续保持有效。因此 Build 失败时，不需要假装公共树已经变化，也
不需要假装请求从未发生。Operation Journal 与 Status 会显示两者差异。

这个区别在后续所有版本中都保留。

## P0 到 P3

实现按依赖顺序推进：

| 阶段 | 契约 |
|---|---|
| P0 | Plain `create`、真实 RPM/DEB Metadata、签名、Pigsty Filter、Pointer-last Replacement |
| P1 | Workspace/Repository/Dist Lifecycle、严格 Config、Package Identity、Membership 与 Query |
| P2 | Add/Remove/Policy/Build、Journal、Crash Recovery 与 Safe Mutation |
| P3 | Check、Changeset、Handoff、规模、兼容性与 Clean-delivery Evidence |

每个阶段都有 API Contract、Implementation Spec、Adversarial Review 与 Traceability/
Acceptance Record。这些文档在构建 Release 时有用；其中长期有效的决定由本文提炼，不再分别
成为公共权威。

## C2 Hardlink 绕路

最初的 Managed RPM 布局在 Root Pool 保存正典文件，并在每个 Architecture View 下创建
Hardlink。Metadata 使用安全的本地 `pool/...` href。这套 C2 布局让固定的 AlmaLinux 9
`reposync` 流程通过，而且 Alias 共享 inode，因此本地字节没有重复。

隐藏代价出现在交付边界：

- Object Storage 会把每条 Path 展开成独立完整对象；
- Archive 与跨文件系统 Copy 可能丢失 Hardlink 身份；
- 每个 Dist/Architecture Alias 都看起来像另一份正典 Payload；
- Retention 与 GC 容易依赖 inode/link-count；
- 完整 Repository 无法一对一映射到 Static Object Key。

2026-08-05 的发布前设计快照准确记录了 C2 实现与本地验收，但它不是最终 v0.2.0 Release
Contract。

单包体契约起草于 8 月 5 日，8 月 7 日以“next”设计提交，并在 8 月 8 日 Tag 前完成实现。
因此正式 Release 已经交付：

```text
<repository>/
  pool/       每个 Package Object 一份正典包体
  dists/      纯元数据 APT/RPM View
```

默认 EL `reposync` 成为已接受兼容性限制；独立 RPM Leaf 改为显式外部 Export。完整理由见
[单包体仓库](/zh/blog/design/single-payload/)。

## 重置复用了什么

团队没有从空代码开始，而只保留不携带 V1 所有权假设的窄组件：

- RPM/DEB Parsing 与原生 Version Comparison；
- Metadata Rendering、Compression、Signing 与 Validation；
- Safe Filesystem Primitive；
- 选定 Client Fixture 与 Fault Pattern；
- 精确 Package Identity 与 Provenance Check。

Git State、Route Receipt、Edge Component、旧迁移机制与 Cloud Control Plane 只是参考材料或
删除候选，不是新 Core 的依赖。

## Release 证据边界

开发线在 8 月 1 日记录 P0/P1 Acceptance，8 月 2 日记录 P1–P3 Acceptance，8 月 5 日完成
一次本地 Release-gate Run。最终 v0.2.0 源码在单包体实现、Packaging 与 CI 修正进入后，于
8 月 8 日打 Tag。

最终 Release 还交付 Filesystem/R2 Publication、Retained Generation、外部 RPM Leaf Export
与本地 GC；R2 Remote Delete 从一开始就被禁用，Target GC 只保留并报告 Candidate。

这个区别非常重要：

- 8 月 5 日 C2 PASS 只证明产生它的开发快照；
- 8 月 8 日 v0.2.0 Tag 与 Release Note 定义实际交付；
- 后续 v0.3/v0.4 测试不会改写任何一项历史结果。

## 哪些东西仍在定义 SOW

- Plain 与 Managed 是隔离模式，恢复成本不同；
- Workspace 是 Config/Discovery Scope，Repository 是 Package/History Scope；
- Package Object Identity 不可变，Membership 是逻辑多对多关系；
- Desired 与 Built State 分离；
- 写入使用稳定 Lock、有界 Journal、Pointer-last Install 与 Fail-closed Recovery；
- CLI Syntax、JSON Envelope 与 Exit Class 构成封闭 Automation Contract；
- Protocol、Client、Mirror Tool 与 Provider 兼容性分别报告。

当前形态见[上手文档](/zh/docs/start/)、[系统模型](/zh/blog/design/model/)与
[设计原则](/zh/blog/design/principles/)。

## 第一手设计快照

- [v0.2 开发设计快照](https://github.com/pgsty/sow/tree/1e7eb5493cc349372fa40c2f8e6e44d8ddb7801b/design/v0.2)
  —— PRD、API、C2 Architecture、Review 与本地 Acceptance；
- [Single-payload “next” 设计](https://github.com/pgsty/sow/tree/8625f5090f5668c69c20f2f17b6466d1228d2fbe/design/next)
  —— 正式 Tag 前采纳的合同；
- [v0.2.0 发布注记](/zh/blog/release/sow-docs-launch/)与
  [v0.2.0 源码 Tag](https://github.com/pgsty/sow/tree/v0.2.0)
  —— 实际交付边界。

后续 v0.3 与 v0.4 的强化过程见[设计演进](/zh/blog/design/evolution/)。
