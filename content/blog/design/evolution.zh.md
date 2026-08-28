---
title: "SOW 设计演进：从 Route Graph 收敛到 Repository Core"
linkTitle: "设计演进"
date: 2026-08-10
lastmod: 2026-08-28
authors: [Vonng]
description: "v0.1 如何退役、v0.2 如何交付单包体 Repository Core，以及 v0.3-v0.4 如何继续强化。"
categories: [Design]
tags: [architecture, repository, migration, decision]
weight: 20
url: "/zh/blog/design/evolution/"
icon: fa-solid fa-code-branch
draft: false
---

本文对应 2026-08-10 围绕 Repository Core 完成的 SOW 收敛决策。它从早期规划、ADR、评审、
迁移与验证目录中提炼值得维护的结论，但不会把每份过程制品都变成另一套产品文档。

部分封存目录使用“v0.2”“v0.3”表示连续的发布前设计线；下文版本号只指正式 Git Tag。
C2 硬链接开发线在 v0.2.0 打 Tag 之前已经被替换。

## 简要历史

| 版本线 | 设计中心 | 历史状态 |
|---|---|---|
| v0.1 | Git/CAS 所有权、Route-aware Materialization、Edge 鉴权、Provider 工作流与 Pigsty 迁移 | 已发布 v0.1.0；后续被取代 |
| v0.2 | 本地 Plain/Managed 引擎、Repository Scope 单包体树、纯元数据视图、Retained Generation 与 Target Scope 发布 | 已发布 v0.2.0；公共布局延续至今 |
| v0.3 | 移除 V1、Package Facts 缓存、Plain 单遍构建与包体有界组提交 | 已发布 v0.3.0；公共布局不变 |
| v0.4 | 单遍校验、独立 RPM Trust Ring、显式 Target Rebind，以及迁移/恢复强化 | 本文更新时的当前发布基线 |

每条已发布版本线的精确代码与陈述，仍保存在
[v0.1.0](https://github.com/pgsty/sow/tree/v0.1.0)、
[v0.2.0](https://github.com/pgsty/sow/tree/v0.2.0)、
[v0.3.0](https://github.com/pgsty/sow/tree/v0.3.0) 与
[v0.4.0](https://github.com/pgsty/sow/tree/v0.4.0) 源码 Tag 中。

## v0.1：问题很有价值，产品概念太多

第一版计划探索了一套宽广的软件分发控制面：Git-backed Canonical State、CAS、Route 与 View、
Materialized Snapshot、远端 Provider、Edge 鉴权、旧系统迁移与证据门禁删除。四十五份 ADR
和庞大的验证树，把许多单点失败模式都写得很清楚。

这些工作留下了可复用的安全思想，但组合后的产品表面过大。太多概念都可能拥有或重新解释同一份
包体与公开路径；在小型本地仓库模型稳定之前，Edge、Provider、Migration 与 Repository 已经
彼此耦合。

因此 v0.2 重置时淘汰了 Git 正典产品状态、独立 CAS 产品层、Route/View/Snapshot 抽象、
把 Edge Entitlement 作为仓库前置条件的设计，以及“用一个模型同时拥有本地生成、远端分发、
旧系统迁移与 CDN 策略”的目标。

## v0.2：先建立小而明确的所有权模型

v0.2 有意把产品拆成两条运行路径：

- **Plain** 扫描调用者拥有的目录，就地重建 RPM 或 DEB 元数据。
- **Managed** 拥有一个包含独立 Repository 的 Workspace；每个 Repository 都有自己的 Pool、
  Dist、SQLite 状态、锁、Operation 与恢复证据。

这次重置建立了沿用至今的持久对象词汇：Package Object、Membership、Desired/Built State、
Generation、Changeset 与显式 Operation Journal。它还确定了稳定锁文件、Pointer-last 文件替换、
Fail-closed 恢复，以及“测试或规格不能自动升级成真实客户端证据”的原则。

开发过程中，C2 布局仍会在每个 RPM View 中创建包体硬链接。封存档案准确记录了这条发布前
设计线，但不能把它重新标注成正式 v0.2.0 Tag 已交付的行为。

## v0.2.0：把 Repository Root 变成交付单元

2026-08-05 的单包体决策从 RPM View 中移除了正典包体别名，并在三天后的 v0.2.0 正式交付。
一个 Repository 只有一个正典 `pool/` 与纯元数据 `dists/`；完整根目录才是复制、托管、
鉴权与发布单元。

v0.2.0 同时明确了状态归属：

- Package Object、Desired/Built、Generation、Changeset 与本地 Retention 属于 Repository。
- Publication Attempt、Applied Checkpoint、远端 Inventory、Grace 与删除证据属于一个
  Repository 加一个 Target Prefix。

设计明确否决跨 Repository 去重与分布式 Prefix 仲裁。这些不是“还没做的优化”，而是会改变
所有权与失败模型的另一类产品。兼容性导出始终位于正典状态之外。

## v0.3：在同一模型上做减法与优化

v0.3 保持 v0.2.0 公共布局不变。它删除退役的 V1 CLI/Runtime 与迁移 Harness，引入
Package Facts 缓存，把 Plain 生成简化为可重建的单遍投影，批量展开 Membership，并用有界
组提交替代逐对象 Promotion。这些变化减少了工作量与代码表面，但没有改变 Repository
`pool/ + dists/` 的所有权。

## v0.4：强化证据，不再增加一套模型

v0.4 保持 v0.2.0 引入、v0.3 优化的公共布局不变，把重点放在完整性与恢复。Managed 深度校验
收敛成有界单遍契约；
RPM Trust 必须来自一条独立验证的 Trust Ring，不能拼接无关密钥的证据；可变 Target 设置只能
通过显式、可审计的 Rebind 修正；Migration、Publication Recovery 与公共交付检查也得到强化。

早期协同发布提案曾考虑把批量传输交给 rclone。最终决策继续使用原生 Provider，因为发布正确性
取决于 Provider Receipt、精确对象身份、提交顺序、Checkpoint State、公共可见性与恢复，
而不只是字节传输。

## 每次重构都保留下来的原则

v0.1 的产品模型虽然被淘汰，其中真正有用的教训仍然保留：

- 每个持久事实都需要一个明确 Owner；
- 包体与可重建投影不能共享 Authority；
- 不可变包体与元数据先准备，可变 Pointer 最后提交；
- Commit 之后只能前滚恢复，证据矛盾必须 Fail Closed；
- 删除需要同时满足可达性、Grace、所有权与 Provider Capability；
- Path、Client、Mirror、Provider、Release 与 Deployment 属于独立证据门禁；
- 历史 PASS 始终绑定当时的版本、源码与环境。

这些原则如今落在一套更小的对象模型中，详见[设计原则](/zh/blog/design/principles/)、
[系统模型](/zh/blog/design/model/)、[单包体仓库](/zh/blog/design/single-payload/)与
[发布与恢复](/zh/blog/design/publication/)。

## 文档权威边界

现在的维护边界很简单：

- [SOW 文档](/zh/docs/)定义当前用户可见的命令、配置、格式与运维行为。
- 本设计专栏定义维护中的设计理由与按日期记录的决策历史。
- [发布注记](/zh/blog/release/)定义版本级交付与升级声明。
- 源码 Tag 保存精确的历史实现、测试与已被取代的原始文字。

原始规划 Prompt、中间评审、生成的证据摘要与废弃规格仍是历史材料。它们可以解释一个结论如何
形成，但不再是与本站并行的文档权威。
