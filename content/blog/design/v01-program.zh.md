---
title: "SOW v0.1 原始计划：软件仓库的 Git"
linkTitle: "v0.1 原始计划"
date: 2026-07-11
lastmod: 2026-08-28
authors: [Vonng]
description: "SOW 为什么最初选择 Git/CAS/Route/Edge 控制面，这套模型解决了什么，又为何后来围绕更小的 Repository Core 重置。"
categories: [Design]
tags: [history, v0.1, git, cas, publication, migration]
url: "/zh/blog/design/v01-program/"
weight: 110
icon: fa-solid fa-code-branch
draft: false
---

> [!IMPORTANT] 历史设计记录
> 本文描述 2026-07-11 启动、并在 2026-07-31 封存为 v0.1.0 源码基线的原始计划。
> Git/CAS/Route/Edge 产品模型已经退役；当前行为以 [SOW 文档](/zh/docs/)和维护中的
> [系统模型](/zh/blog/design/model/)为准。

SOW 最初并不是一个小型仓库索引器。原始目标是用一个 Go 控制面，替换 Pigsty 中庞大的
Makefile + rclone 工作流，统一管理 APT、YUM 与静态制品，覆盖本地状态、包生命周期、上游
同步、Channel、View、Snapshot、双云发布、CDN 行为、商业访问控制、迁移、恢复与验证。

当时采用的说法是：**“制品仓库的 Git”。** 这确实回应了一个真实问题：软件分发同时具有
不可变内容、可变名称、历史、晋级、发布与回滚。问题不在这个类比完全错误，而在它诱导 SOW
承担了过大的产品表面。

## 第一版设计要解决什么

旧系统已经发布了几十条被 APT、DNF、脚本与安装入口依赖的稳定 URL。替代系统既要保持这些
URL，又要提供 Makefile 工作流难以安全表达的能力：

- 每个已接纳包体只有一个身份；
- Desired State 与每朵云实际发布的状态分离；
- Snapshot 与历史保留不能靠猜测哪些文件仍然存活；
- 增量上传与 Purge 成本应与变更集成正比；
- Metadata 准备完成、Pointer 尚未发布时崩溃，系统仍可恢复；
- 上游索引、包签名与迁移例外都要有 Provenance；
- 商业私有对象不能通过公共索引或 Cache Key 泄漏；
- 兼容性必须来自真实 APT/DNF 客户端，而不只是元数据语法正确。

原始计划有意把这些问题视为同一套所有权系统。

## v0.1 选择的模型

### Git 是正典状态

`.sow/state` 是由内嵌 Go Git 库操作的普通 Worktree。Manifest、Ref、Provenance、配置摘要、
Target Checkpoint 与安全标签都是 Git 内容；SQLite 只是可以重建的查询投影。

这样，每次状态迁移都有持久历史，一次 Ref 更新可以成为本地 Commit Boundary。代价是：
包管理、发布、迁移与操作意图，都必须进入同一种 Git 形状的权威模型。

### CAS 拥有字节

包体进入以 SHA-256 命名的不可变 Pool；公开树通过 Hardlink 指向 Pool，因此能否回收由
Reachability 决定，而不是由文件名决定。这让本地去重与历史保留成本很低，但也要求 Pool 与
物化树位于同一文件系统，并把 Path、Receipt 与 inode 身份变成产品契约的一部分。

### Ref 表达产品语义

Repository、View、Snapshot、Stable、History 与每个 Target 的 Remote Ref 描述内容的意义和
保留边界。移动一个可变 View 不会删除 Stable 或历史可达性；删除 View 只改变引用，GC 始终是
另一项受证据约束的操作。

### 发布是一条 Saga

Cloudflare R2 与腾讯 COS 是相互独立的 Target。每个 Target 分别准备不可变对象、持久化
Commit Intent、移动协议 Pointer、Purge CDN、验证公共可见性，并推进自己的 Checkpoint。
一朵云成功后，不会仅因另一朵云失败而回滚。

当时已经形成了延续至今的顺序：

```text
不可变包体
  -> 不可变元数据
  -> 持久 Commit Intent
  -> 可变协议 Pointer
  -> 公共验证
  -> Checkpoint
  -> Grace
  -> 证据门禁删除
```

这套顺序延续至当前 SOW。

### Route 与 Edge 属于仓库正确性

公共树保持旧 URL，Generation-aware Route 选择不可变 Metadata；私有对象则位于 Cloudflare
Worker 与 EdgeOne 共享的 Edge 契约之后。鉴权必须先于 Origin 访问，Token 不得进入 Origin
URL、Cache Key 或日志。

这解决了机密性闭包，却也让 CDN Route、Token Verifier、Provider 部署、日志 Sink 与缓存拓扑
都变成仓库模型的前置条件。

## 这套设计为什么有吸引力

v0.1 具备不少强性质：

- 每个持久事实都有明确 Owner；
- 不可变字节与可变名称分离；
- 本地与各 Remote Target 的发布状态独立可观测；
- Pointer-last 发布让半完成工作可以恢复；
- GC 必须计算完整 Reachability Closure；
- Plan 与 Receipt 会重新验证，而不是盲目信任；
- Client、Provider 与实现证据彼此独立；
- 旧系统迁移面被当作数据，而不是口口相传的运维知识。

后续产品没有抛弃这些思想，而是在删掉大量承载机制后继续保留它们。

## 为什么后来必须重置

到七月底，SOW v0.1 已经包含：

- 作为内部数据库协议的 Git Commit 与 Ref；
- 全局 CAS 与 Hardlink Materialization；
- Route、View、Snapshot、Generation、Projection、Receipt 与 Lease；
- APT/YUM/Asset Sync 与旧系统迁移；
- Cloud SDK、Edge Bootstrap、Provider Attestation、Purge、Token 与私有 Origin；
- 44 份现存 ADR 文件和 112 份日期化 Evidence 报告。

每一项都在解决真实失败模式，但组合起来产生了几个问题。

第一，同一个包与公共路径被太多对象“拥有”：它同时是 CAS Object、Manifest Entry、View
Member、Materialized Route、Snapshot Reference 与 Remote Target Object。

第二，本地软件仓库生成与 Cloud/Edge 生命周期强耦合。只想构建一个 YUM 或 APT 仓库的用户，
也要承担商业访问控制和分布式发布的概念成本。

第三，迁移计划变成了永久产品子系统。旧拓扑、Make Target、CDN 行为和 Provider 例外在迁移
时很重要，却不应永久进入软件仓库抽象。

最后，在 Hostile Writer 与 Crash 条件下恢复每条派生 Path，需要的 Identity、Journal、
Quarantine 与 Retirement 机制，已经超过核心任务值得承担的复杂度。

Upstream Sync 与 Channel Promotion 也是一次有意的范围裁剪。V1 已为 Package Fetch 留下真实
Streaming、Fuzz、URL 与 Proof-order 证据，但 Acquisition 会引入自己的 Policy、Retry、
Provenance 与 Remote Ownership。重置把包获取改为外部输入问题，让 SOW 可以拥有 Repository
Admission 与 Publication，而不必同时成为万能 Mirror Orchestrator。

## 重置后保留下来的东西

| v0.1 教训 | 当前维护形态 |
|---|---|
| 每个持久事实只有一个 Owner | [系统模型](/zh/blog/design/model/)中的 Repository 与 Target-prefix 所有权 |
| 正典数据与投影不同 | 一个 `pool/` 加纯元数据 `dists/` |
| 包体先准备，Pointer 最后提交 | [发布与恢复](/zh/blog/design/publication/) |
| Commit 后只能前向恢复 | Managed Operation 与 Publication Journal |
| Plan 与 Path 都是不可信输入 | 精确身份、Containment 与 Rebind 检查 |
| 删除需要完整证据 | 引用闭包、Grace、Absence 与 Provider Capability |
| 生成的 Server Config 是派生状态 | 完整 Repository Root 是 Hosting Unit，Serving 仍由运维者显式配置 |
| 兼容性是一张矩阵 | [平台与集成](/zh/docs/reference/compatibility/) |
| 历史证据不会自动升级 | 日期化 Design 与 Release 记录 |

## 被淘汰的东西

- Git 产品状态与“SQLite 只是可丢弃缓存”的模型；
- 跨产品 CAS 与 Hardlink 物化层；
- Route/View/Snapshot 公共命令模型；
- 生成的 Nginx Include、Route Receipt 与 V1 Serving 控制状态；
- 内置 Upstream Sync、Promote 与旧 Make Target 迁移；
- 把 Edge Token Entitlement 与私有 Origin 当作仓库前置条件；
- 多云发布控制面与 Provider Bootstrap/Attestation；
- V1 专属 Projection Receipt、Lease、Quarantine 命令与恢复表面。

一些实现思想后来以更小的形式回归，但所有权边界已经改变：当前 SOW 首先是 Repository
Engine，而不是试图拥有周边所有问题的软件分发平台。

## 时间线

| 日期 | 里程碑 |
|---|---|
| 2026-07-11 | Goal、Brainstorm、技术调研、客户端与规模基线 |
| 2026-07-12 | Git/CAS/发布核心契约与首批协议/Provider 证据 |
| 2026-07-13–16 | 包信任、事务、旧拓扑与迁移闭包 |
| 2026-07-17–20 | Provider Bootstrap、Edge 机密性、删除能力与输入上限 |
| 2026-07-22–29 | Path Identity、Hostile Writer、Quarantine 与 Residue Recovery 强化 |
| 2026-07-30–31 | Clean-room MVP 证据与 v0.1.0 源码封存 |
| 2026-08-01 起 | Plain/Managed 重置，并最终移除 V1 Runtime |

## 第一手资料与后续记录

不可变的 [v0.1.0 `docs/` 树](https://github.com/pgsty/sow/tree/v0.1.0/docs)保留了原始
[架构契约](https://github.com/pgsty/sow/blob/v0.1.0/docs/architecture.md)、
[需求追踪](https://github.com/pgsty/sow/blob/v0.1.0/docs/requirements-traceability.md)、
[迁移材料](https://github.com/pgsty/sow/tree/v0.1.0/docs/migration)、ADR 与 Evidence。
这些文件用于解释历史实现，不能覆盖本站维护中的历史叙事或当前产品文档。

接下来可阅读 [v0.1 决策账本](/zh/blog/design/v01-decisions/)、
[v0.1 证据账本](/zh/blog/design/v01-evidence/)与
[v0.2 重置](/zh/blog/design/v02-reset/)。
