---
title: "SOW v0.1 决策账本：哪些被保留，哪些已退役"
linkTitle: "v0.1 决策账本"
date: 2026-07-12
lastmod: 2026-08-28
authors: [Vonng]
description: "逐项整理 v0.1 现存的 44 份 ADR：当时解决什么问题，后来是延续、演化、仅服务迁移，还是随 V1 一同退役。"
categories: [Design]
tags: [history, v0.1, adr, decision, migration]
url: "/zh/blog/design/v01-decisions/"
weight: 100
icon: fa-solid fa-list-check
draft: false
---

> [!IMPORTANT] 历史决策账本
> v0.1.0 Tag 中现存 44 份 ADR，编号从 0001 到 0045，其中缺少 0006。
> 本文保留它们的意义，但不会把每份历史实现契约重新发布成当前指南。

即使实现已经退役，ADR 仍有价值：它记录团队拒绝忽略的失败模式、当时选择的边界，以及危险
操作进入执行前必须取得的证据。

下面把每项决策分为四种命运：

| 命运 | 含义 |
|---|---|
| **保留** | 原则以基本相同的边界继续存在于当前 SOW。 |
| **演化** | 问题与安全规则仍在，但所有权或实现已经改变。 |
| **迁移历史** | 决策只服务一次性的 Pigsty/V1 切换，不再是产品契约。 |
| **退役** | 决策属于已经退出当前 SOW 的 Git/CAS/Route/Edge 产品模型。 |

主要决策日期覆盖 2026-07-11 至 2026-07-28；ADR-0035 另有 7 月 29 日与 31 日的后续修订。
多数早期 ADR 在已经指导实现与证据工作的情况下，于 7 月 19 日集中进入 Git。v0.1.0 Tag Tree
已经核对，包含下表所代表的同一组 44 条 ADR Path。其中一条原文包含已废弃基础设施细节，因此
本文有意不提供直接 Deep Link。

## 核心状态、发布与信任

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| [0001](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0001-core-contracts.md) | Git 是正典状态，SHA-256 CAS 拥有包体，Ref 表达 View/History，发布按 Target Saga 执行。 | **演化。** Git/CAS/Route 所有权退役；单一 Owner、Pointer-last、独立 Target 状态与证据门禁保留。 |
| [0002](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0002-publication-routes-and-compatibility-gates.md) | Public Route、不可变 Generation 与 Client/Provider 兼容使用独立验收门。 | **演化。** Route 机制退役；协议、客户端与 Provider 证据仍然分开。 |
| [0003](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0003-snapshot-generation-copy-and-retention.md) | Snapshot 需要经过验证的 Generation Copy 与 Inventory-bound Retention。 | **演化。** CopyObject Snapshot Tree 退役；Retained Generation 只保存 Metadata 与 Refset，不复制包体。 |
| [0004](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0004-edge-token-verifier-deployment-contract.md) | Edge Token 验证与部署共享一套跨 Provider 版本化契约。 | **退役。** Edge Entitlement 不再属于 SOW Repository Engine。 |
| [0005](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0005-legacy-make-target-dispositions.md) | 每个旧 Make Target 明确映射到 SOW、Retire 或 Policy Reject。 | **迁移历史。** 映射完成切换使命后退出活动产品。 |
| [0007](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0007-pro-oss-unified-repository.md) | 公共包与 Gated 包共享一个正典仓库，而不是独立 Pro Bucket。 | **退役。** 商业 Edge 拓扑退出产品；更一般的单 Owner 原则保留。 |
| [0008](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0008-gc-reachability-and-confirmation.md) | GC 服从完整 Reachability，破坏性操作需要显式确认。 | **保留。** 当前本地/Target GC 仍要求闭包、精确身份、Grace 与能力。 |
| [0009](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0009-forward-only-remote-generation-restore.md) | Remote Generation 可见后只能前滚恢复，不能虚构回滚。 | **保留。** Commit Intent 仍是 Abandon/Reconcile 与 Forward-only 的边界。 |
| [0010](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0010-repository-signing-identity-and-rotation-boundary.md) | Metadata Signing 绑定精确公私钥身份，轮换是 Repository-wide Transition。 | **演化。** 当前 Signer Evidence 与 Trust Ring 保留精确身份，不再使用 V1 Ref 拓扑。 |
| [0011](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0011-evidence-bound-remote-deletion.md) | Remote Delete 必须具备 Target Ownership、Inventory、Checkpoint、Grace 与条件删除证据。 | **保留。** R2 无法满足原子条件删除，因此继续 Report-only。 |
| [0012](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0012-private-origin-deployment-contract.md) | Private Origin、Cache Topology 与精确 Purge Mapping 都是显式部署契约。 | **退役。** CDN/Private-origin 部署不属于当前 SOW。 |
| [0013](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0013-persisted-publication-plans-are-untrusted.md) | 持久化 Plan 只是需要重新验证的恢复输入，不能盲目重放。 | **保留。** Managed Recovery 仍会重新绑定 Plan、File、Target Identity 与公共证据。 |
| [0014](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0014-rpm-provenance-signature-evidence-boundary.md) | RPM Provenance 记录精确 Packet Evidence，并区分 Ingestion Policy 与历史证明。 | **演化。** 当前 Package Authentication 与独立 Trust Ring 替代 V1 Receipt 编码。 |
| [0015](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0015-target-identity-and-published-ref-state.md) | 配置只命名 Target，Published Ref 与 Checkpoint 属于正典状态。 | **保留。** Target-neutral Generation 与 Target-prefix Attempt/Checkpoint 仍是不同 Owner。 |
| [0016](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0016-frozen-vendor-sdk-boundary.md) | Cloud Adapter 使用具体、有界 SDK/API 契约，不建立通用 Provider 抽象。 | **演化。** 具体 Provider 边界保留，V1 Edge/COS 细节退役。 |
| [0017](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0017-rpm-package-keyring-and-cryptographic-verification.md) | 已接纳 RPM 签名必须在稳定 Repository Keyring 与已打开包体身份上闭合。 | **演化。** v0.4 独立 Multi-ring Verification 强化了同一信任边界。 |
| [0018](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0018-selected-set-local-materialization-transaction.md) | 选定包集合按一个有界本地事务完成 Stage、Validate、Commit 与 Recovery。 | **演化。** V1 Materialization 退役；当前 Plain/Managed Pointer-last Stage 保留事务原则。 |

## 旧拓扑、兼容性与迁移

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| [0019](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0019-frozen-el7-yum-metadata-compatibility.md) | 为旧客户端冻结 EL7 Metadata 格式与压缩行为。 | **迁移历史。** 当前平台支持以兼容性文档而非这份 Freeze 为准。 |
| [0020](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0020-legacy-physical-topology-and-route-ownership.md) | 每条旧物理 Path 与 Selector Group 都有明确 Owner。 | **迁移历史。** 它消除了切换歧义，但不是当前仓库模型。 |
| [0021](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0021-frozen-cross-el-yum-infra-compatibility-projection.md) | 以精确冻结证据复现跨 EL `yum/infra/{arch}` Projection。 | **迁移历史。** 这条特殊 Projection 已退出产品。 |
| [0022](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0022-package-repository-history-continuity.md) | 物理所有权变化不能破坏 Package Repository 历史连续性。 | **演化。** Generation、Retained Ref 与 Migration Journal 在没有 V1 Route 的情况下延续连续性。 |
| [0023](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0023-canonical-git-object-integrity.md) | 正典 Git Object 在接纳和使用前必须重新绑定精确字节。 | **演化。** Git Authority 退役；Descriptor/Path/Digest 身份检查保留。 |
| [0024](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0024-materialized-route-read-capabilities.md) | Materialized Route Receipt 是窄化的 Read/Retirement Capability。 | **演化。** Route Receipt 退役；Capability-bound 检查与删除保留。 |
| [0025](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0025-state-lock-process-instance-lease.md) | Lock 绑定精确 Process Instance 与稳定 inode，不按时间自动偷锁。 | **演化。** 稳定 Lock inode 与拒绝超时偷锁的原则保留，V1 Process-instance Lease 机制未保留。 |
| [0026](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0026-offline-archive-projection-intent.md) | Offline Archive 使用 Durable Intent 与严格 Archive Admission。 | **退役。** Offline Archive Projection 已离开当前范围。 |
| [0027](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0027-legacy-package-adoption-admission-and-canonicalization.md) | 旧包体只有通过 Path、Package 与 Provenance Admission 才进入正典状态。 | **迁移历史。** Adoption 计划结束；严格 Package Admission 以更窄形式保留。 |
| [0028](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0028-control-only-deb-inspection.md) | DEB 只打开 Metadata 所需的 Control Archive，并拒绝歧义 Container。 | **保留。** 窄解析与有界输入仍属于 APT Package Boundary。 |
| [0029](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0029-client-support-floor-and-el8-freeze-version.md) | Client Floor 与 EL8 Freeze 是显式 Owner Policy，不从代码猜测。 | **迁移历史。** 当前平台策略由兼容性参考与 Release Note 决定。 |
| [0030](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0030-audit-bound-legacy-yum-missing-body-prune.md) | 旧 YUM Missing Body 只能依据已评审 Blocker-set Digest 修复。 | **迁移历史。** 这项窄 Negative Provenance 例外没有变成通用 Ignore。 |
| [0031](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0031-legacy-pro-gated-activation-and-checksum-repair.md) | Gated 旧内容需要精确 Checksum Repair 与 Activation Evidence。 | **退役。** Pro Activation 离开范围；Fail-closed Repair 成为通用教训。 |

## Provider 与 Edge 控制面

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| 0032 | 只有一个 Owner 明确指定的 Cloudflare 测试 Tuple 可例外进入。 | **退役。** 它只是窄化的历史测试例外，从未成为通用部署规则。 |
| [0033](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0033-provider-scoped-readiness-registry.md) | Read-only Provider Readiness 拥有独立 Registry 与所有权证据。 | **退役。** Provider Bootstrap Registry 已离开当前 SOW。 |
| [0034](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0034-cloudflare-nonproduction-worker-bootstrap.md) | Worker Bootstrap 使用 Lease、两阶段恢复、精确资源与可逆状态。 | **退役。** Cloudflare Deployment 不再由 Repository Engine 负责。 |
| [0035](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0035-cloudflare-provider-attestation-and-log-sink-lease.md) | 使用前 Attest Provider Identity、Runtime Binding、Log Sink 与 Lease Ownership。 | **退役。** 这套 Edge 控制面退出产品。 |
| [0036](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0036-provider-delete-capability-and-checkpoint-fenced-fallback.md) | R2 缺少 Conditional DeleteObject，因此允许在确定性 Capability Probe 与多层 Identity/Fence Proof 后，显式启用 `checkpoint-fenced` 无条件删除降级。 | **演化；降级未继承。** Capability Probe 与 Fail-closed Default 保留，但当前 SOW 禁用 R2 Remote Delete，Target GC 只报告 Candidate。 |
| [0037](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0037-pre-upload-confidential-edge-denial-attestation.md) | Gated 发布必须在上传机密字节前证明 Edge Denial。 | **演化。** Edge 产品表面退役，暴露前证明鉴权的原则保留。 |
| [0038](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0038-yum-consumer-preflight-receipt.md) | YUM 切换需要绑定 Endpoint、Generation 与 Trust Bytes 的短期 Receipt。 | **迁移历史。** 它让危险切换可审计，随后退役。 |
| [0039](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0039-caret-url-wire-canonicalization.md) | Caret 在 Go、Edge、Log 与 Origin Route 中只有一种规范 URL 拼写。 | **演化。** 旧 Route 退役；Encode-once Path Canonicalization 保留。 |

## 有界配置与派生状态恢复

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| [0040](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0040-bounded-configuration-topology.md) | 在分配或执行前限制配置基数与展开后的拓扑。 | **保留。** 当前 Parser 与 State Wire 仍有显式 Size/Cardinality Limit。 |
| [0041](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0041-preserved-projection-orphan-quarantine.md) | 未知 Final Projection Stage 应保留审计，不得猜测删除。 | **演化。** 当前 Recovery 仍保留矛盾证据并 Fail Closed。 |
| [0042](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0042-derived-state-replacement-outcome.md) | Derived-state Replacement 有明确 Success、Rollback、Preserved 与 Blocked Outcome。 | **保留。** 当前 Operation 报告精确 Recovery Outcome，不折叠成简单成败。 |
| [0043](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0043-derived-state-hostile-writer-admission.md) | 文件 Mutation 绑定 Descriptor Identity，并诚实声明 Same-UID Hostile Writer 边界。 | **保留。** Path Safety Fail Closed，但不宣称保护超出 OS Ownership Boundary 的攻击面。 |
| [0044](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0044-preserved-projection-audit-retirement.md) | Preserved Audit Copy 只能通过精确 Capability 与 Confirmation Token 退役。 | **演化。** V1 命令退役；Capability-bound Deletion 原则保留。 |
| [0045](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0045-generic-derived-state-residue-recovery.md) | Unjournaled Residue 必须有有界分类器，不能静默接纳或删除。 | **保留。** 当前恢复仍区分 Known State、Safe Residue 与 Contradictory Evidence。 |

## 账本背后的共同模式

真正留下来的不是最复杂的 V1 机制，而是机制下面的小型不变式：

- 每个事实只有一个 Owner；
- Mutation 前绑定精确 Identity；
- 不可变内容先准备，Pointer 最后提交；
- Commit Intent 之后只能前向恢复；
- 删除前必须取得完整证据；
- 输入有明确上限，Non-goal 必须诚实；
- 兼容性结论绑定实际测试过的 Client/Provider。

Git Database、Route Graph、Edge Bootstrap 与迁移命令都可以替换，这些不变式不可以。它们如今
维护在[设计原则](/zh/blog/design/principles/)、[系统模型](/zh/blog/design/model/)与
[发布与恢复](/zh/blog/design/publication/)中。

不可变的 [v0.1.0 ADR 目录](https://github.com/pgsty/sow/tree/v0.1.0/docs/adr)仍是第一手
资料。下一篇文章继续汇总独立的 [v0.1 证据记录](/zh/blog/design/v01-evidence/)。
