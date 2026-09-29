---
title: "SOW v0.1 到底证明了什么"
linkTitle: "v0.1 证据账本"
date: 2026-07-31
lastmod: 2026-08-28
authors: [Vonng]
description: "整理 v0.1 的 112 份日期化证据报告：真实客户端、规模、故障、迁移与 Provider 结论证明了什么，又从未证明什么。"
categories: [Design]
tags: [history, v0.1, evidence, compatibility, verification]
url: "/zh/blog/design/v01-evidence/"
weight: 90
icon: fa-solid fa-microscope
draft: false
---

> [!IMPORTANT] 版本绑定的证据
> 本页每项结果都只属于当时记录的 v0.1 源码、布局、Fixture 与环境，不能证明当前 SOW
> 的兼容性或发布就绪。

v0.1 归档包含 112 份日期化 Evidence Report，覆盖 2026-07-11 至 2026-07-31。把它们全部
发布成博客只会降低公共站点的可用性：其中很多是窄故障闭包、重复的 Current-source Audit，
或某个具体实现 Seam 的执行记录。

但直接丢弃也会损失同样重要的信息。这些报告说明：哪些设计决定来自真实客户端与反例，哪些只
达到 Local/Mock 层，以及团队在哪些地方拒绝把不完整证据包装成 PASS。

本文保留的正是这条边界。

## 证据时间线

| 时间 | 报告数 | 主要工作 |
|---|---:|---|
| 2026-07-11 | 3 | 真实 APT/DNF 基线、72,310 包 Manifest 扫描、50k Upstream Streaming |
| 2026-07-12 | 35 | APT/YUM 协议、CAS/GC、发布顺序、恢复、MinIO、性能、迁移、构建/供应链门禁与云验收夹具 |
| 2026-07-13 | 2 | RPM Trust Closure 与 Selected-set Materialization Recovery |
| 2026-07-14–16 | 14 | 旧拓扑、Family Migration、物理所有权、完整副本纳管与包签名 Inventory |
| 2026-07-17–20 | 39 | Cloudflare/R2/COS/Edge Safety、Provider Attestation、Cutover Receipt、配置上限与 Checkpoint-fenced Deletion |
| 2026-07-22 | 10 | Stage、Apply、Prune、Rollback 与 Residue Cleanup 的 Descriptor/Path Identity |
| 2026-07-26–29 | 7 | 递归持久性、Hostile Writer、Replacement Outcome、Preserved Audit 与 Provider 修正 |
| 2026-07-30–31 | 2 | Clean-room APT/YUM/Asset MVP 与最终 Legacy-source Baseline |

## 哪些结论有较强证据

### 真实客户端与大仓库

最早的证据没有只验证生成的 XML/Text，而是使用真实 APT 与 DNF，并显式测量规模：

- [真实 APT/DNF 客户端兼容](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-client-compat.md)；
- [72,310 包 Manifest 扫描](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-manifest-72k-performance.md)；
- [50k Upstream Streaming](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-upstream-50k-streaming.md)；
- 独立的 50k APT、YUM、Materialization、Publish Plan 与 Legacy Adoption 测试。

这些结果支撑了 Streaming 与 Bounded Concurrency 要求，但不证明后续每种布局都自动继承同样
的客户端行为与性能。

### 协议闭包与负反例

有些设计修正来自负面证明，而不是乐观实现：

- [APT Fixed-alias 负 PoC](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-apt-legacy-fixed-alias-negative-poc.md)
  表明旧客户端语义限制了 Alias 原子性声明；
- [YUM Raw-alias Signature-bridge 负 PoC](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-raw-alias-signature-bridge-negative-poc.md)
  区分旧 BaseURL 兼容与强 Generation-pinned Metadata；
- [YUM Generation Atomicity](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-generation-atomicity.md)
  精确记录哪些 Pointer 行为能原子化，哪些不能。

延续下来的教训不是 V1 URL Scheme，而是：看似合规的仓库与某个客户端事务，是两个不同结论。

### 故障与恢复

归档覆盖被中断的 Sync、Publish、Materialize、Snapshot、Archive 与 Remote Restore。后期报告
进一步把文件操作绑定到 Descriptor 与精确 Path Identity，并覆盖 Rollback、Quarantine 与
Preserved Evidence。

代表性记录包括：

- [Publish/Recovery 对抗审查](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-publish-recovery-adversarial-review.md)；
- [Selected-set Recovery Closure](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-13-selected-set-materialization-recovery.md)；
- [State-lock 与 Atomic Publication](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-19-state-lock-atomic-publication.md)；
- [Derived-state Replacement Outcome](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-28-derived-state-replacement-outcome.md)。

这也是当前 SOW 区分 Pre-commit Abandon、Post-intent Forward Recovery 与 Contradictory
Evidence 的原因，而不是只提供一个笼统的“重试”。

### 旧系统迁移

迁移证据枚举旧 Make Target、物理布局、Repository Family、Consumer Config、Package-signature
Inventory 与 Rollback，并在 Mutation 前使用 Read-only Copy 与精确 Receipt。

这证明了一条特定 Pigsty Cutover Path，却不支持把旧拓扑永久带进产品。最有价值的结果是一套
纪律：把迁移假设变成显式数据与可执行 Gate，切换结束后再让它退役。

### Provider 与 Edge 实验

归档包含真实和模拟的 R2、MinIO、Cloudflare、COS 与 Edge 工作。较强报告都明确声明范围：

- [真实 R2 Storage Protocol](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-18-real-r2-storage-protocol.md)；
- [R2 Publication Storage Transaction](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-r2-publication-storage-transaction.md)；
- [Full-provider Checkpoint-fenced Delete](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-full-provider-checkpoint-fenced-delete.md)；
- Cloudflare Bootstrap、Private Domain、Provider Attestation 与 Rollback 记录。

其中一些使用 Owner 指定的 Nonproduction Resource，另一些是 Offline 或 Mock Validation。
一项真实 R2 结果从未证明 COS 条件替换、EdgeOne Cache 行为或当前 SOW Target State Machine。

## 归档没有证明什么

即使证据很多，原文仍保留明确开放边界：

- 单个 PoC 不能证明所有 APT、DNF、Proxy、Mirror Tool 或 Provider；
- MinIO S3 兼容不等于 Cloudflare R2 或腾讯 COS 语义；
- Design/Adversarial Review 不是 Implementation Evidence；
- Local/Mock Provider 结果不是生产部署；
- PASS 始终绑定 Source Revision、Fixture、URL Layout 与环境；
- v0.1 证据不能验证后来的 Plain/Managed 或 Single-payload 设计。

这些限制是归档的优点，不应在整理历史时被“润色”掉。

## 哪些做法进入了设计方法

证据计划留下六条长期实践：

1. **标明证据层。** Design、Source、Unit/Fault Test、Real Client、Provider、Artifact 与
   Production 彼此独立。
2. **保留负结果。** 一个反例往往比另一个 Happy Path 更能定义安全边界。
3. **把 PASS 绑定到不可变输入。** Source Revision、Container/Client Version、Provider、
   Route 与 Fixture 都属于结果。
4. **把规模作为契约。** 大仓库必须测量 Memory、Call Count 与 Concurrency。
5. **证据随模型退役。** 历史证明可以解释过去，不能静默升级新布局。
6. **让构建与供应链检查长期存在。** Toolchain Portability、Dependency Vulnerability、
   Static Analysis、Dead-code Closure 与 Reproducible Delivery 是持续 Release Gate，不是一次性清理。

这些实践如今写入[设计原则](/zh/blog/design/principles/)与当前
[兼容性参考](/zh/docs/reference/compatibility/)。

## 第一手资料

不可变的 [v0.1.0 Evidence 目录](https://github.com/pgsty/sow/tree/v0.1.0/docs/evidence)
保留全部日期化报告。本文是维护中的解释，原文件则是审计轨迹。

继续阅读 [v0.2 重置](/zh/blog/design/v02-reset/)，可以看到这些教训如何在产品模型大幅缩小
后继续存在。
