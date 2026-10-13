---
title: "SOW v0.1 决策账本：哪些被保留，哪些已退役"
linkTitle: "v0.1 决策账本"
date: 2026-07-12
lastmod: 2026-10-13
authors: [Vonng]
description: "逐项整理 v0.1 现存的 44 份 ADR：当时解决什么问题，后来是延续、演化、仅服务迁移，还是随 V1 一同退役。"
categories: [Design]
tags: [history, v0.1, adr, decision, migration]
url: "/zh/blog/design/v01-decisions/"
weight: 100
icon: fa-solid fa-list-check
draft: false
---

v0.1.0 标签中有 44 份架构决策记录（ADR），编号为 0001 至 0045，缺少 0006。
每份 ADR 记录一个问题、当时的决策及实现必须满足的条件。
下表说明仓库模型变化后，各项决策的后续情况。

| 状态 | 含义 |
|---|---|
| **保留** | 原则以基本相同的范围继续用于当前 SOW。 |
| **演化** | 问题仍在，但所有权或实现已经改变。 |
| **迁移历史** | 决策用于 Pigsty/V1 切换。 |
| **退役** | 决策属于已移除的 Git/CAS/Route/Edge 模型。 |

决策日期从 2026-07-11 到 7 月 28 日，ADR-0035 另有 7 月 29 日与 31 日的修订。
多数早期 ADR 在实现开始后，于 7 月 19 日集中进入 Git。
ADR-0032 包含已废弃的基础设施细节，因此这里只提供摘要。

## 核心状态、发布与信任

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| [0001](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0001-core-contracts.md) | Git 是权威状态，SHA-256 CAS 保存包体，引用表达视图与历史，发布按各目标的事务流程执行。 | **演化。** Git/CAS/Route 所有权已退役，单一所有者、协议指针最后提交、独立目标状态与执行前检查得以保留。 |
| [0002](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0002-publication-routes-and-compatibility-gates.md) | 分别验证公共路由、不可变 Generation（构建快照）和客户端、存储服务兼容性。 | **演化。** Route 机制已退役，协议、客户端和存储服务仍分别验证。 |
| [0003](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0003-snapshot-generation-copy-and-retention.md) | 快照需要经过验证的 Generation 副本，并按清单保留。 | **演化。** 通过 CopyObject 复制快照树的方式已退役；保留的 Generation 只保存元数据与引用集合，不复制包体。 |
| [0004](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0004-edge-token-verifier-deployment-contract.md) | 边缘令牌验证与部署采用同一套跨服务商、带版本的接口。 | **退役。** 边缘访问权限不再由 SOW 仓库引擎管理。 |
| [0005](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0005-legacy-make-target-dispositions.md) | 逐项决定旧 Make 目标是由 SOW 接替、退役，还是因策略限制而拒绝。 | **迁移历史。** 完成切换后退出产品。 |
| [0007](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0007-pro-oss-unified-repository.md) | 公共包与受访问控制的包共用一个仓库。 | **退役。** 商业边缘服务拓扑退出产品，单一所有者原则保留。 |
| [0008](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0008-gc-reachability-and-confirmation.md) | 垃圾回收计算完整引用关系，删除前要求显式确认。 | **演化。** 当前 GC 检查引用关系与精确身份，旧 `--apply --confirm` 接口已退役；远端删除还检查缓存宽限期与存储服务能力。 |
| [0009](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0009-forward-only-remote-generation-restore.md) | 远端 Generation 可见后，通过前向恢复完成发布。 | **保留。** 提交意图仍是放弃或核对未提交操作与前向恢复之间的边界。 |
| [0010](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0010-repository-signing-identity-and-rotation-boundary.md) | 元数据签名绑定精确公私钥身份，密钥轮换作为整个仓库的状态变化处理。 | **演化。** 当前签名者记录与信任环仍检查精确身份，不再使用 V1 引用拓扑。 |
| [0011](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0011-evidence-bound-remote-deletion.md) | 远端删除需要目标所有权、清单、检查点、宽限期与条件删除能力。 | **保留。** R2 不满足所需的原子删除能力，因此只报告候选对象。 |
| [0012](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0012-private-origin-deployment-contract.md) | 明确规定私有源站、缓存拓扑与缓存清理映射。 | **退役。** CDN 与私有源站部署不属于当前 SOW。 |
| [0013](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0013-persisted-publication-plans-are-untrusted.md) | 持久化计划是恢复输入，使用前要重新验证。 | **保留。** Managed 恢复仍会重新验证计划、文件、目标身份和公共交付结果。 |
| [0014](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0014-rpm-provenance-signature-evidence-boundary.md) | RPM 来源记录保留精确签名包数据，并区分接纳策略与历史证明。 | **演化。** 当前包认证与独立信任环替代了 V1 回执编码。 |
| [0015](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0015-target-identity-and-published-ref-state.md) | 配置负责命名目标，已发布引用与检查点属于持久状态。 | **保留。** Generation 与目标无关；发布尝试和检查点按目标前缀保存。 |
| [0016](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0016-frozen-vendor-sdk-boundary.md) | 云适配器使用具体、有界的 SDK/API 接口。 | **演化。** 具体存储服务接口保留，V1 Edge/COS 细节退役。 |
| [0017](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0017-rpm-package-keyring-and-cryptographic-verification.md) | 在稳定的仓库密钥环中验证 RPM 签名，并绑定已打开包体的身份。 | **演化。** v0.4 的独立多信任环验证强化了这一规则。 |
| [0018](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0018-selected-set-local-materialization-transaction.md) | 选定包集合在一个有界本地事务中完成暂存、验证、提交与恢复。 | **演化。** Managed 操作使用恢复日志；Plain 暂存元数据并最后替换指针，中断后重新构建。 |

## 旧拓扑、兼容性与迁移

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| [0019](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0019-frozen-el7-yum-metadata-compatibility.md) | 为旧客户端固定 EL7 元数据格式与压缩行为。 | **迁移历史。** 当前支持平台见兼容性文档。 |
| [0020](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0020-legacy-physical-topology-and-route-ownership.md) | 为每条旧物理路径与选择器分组指定所有者。 | **迁移历史。** 用于消除切换歧义，未进入当前仓库模型。 |
| [0021](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0021-frozen-cross-el-yum-infra-compatibility-projection.md) | 根据固定验证结果复现跨 EL 的 `yum/infra/{arch}` 投影。 | **迁移历史。** 这项特殊投影已退出产品。 |
| [0022](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0022-package-repository-history-continuity.md) | 物理所有权变化时保留包仓库历史。 | **演化。** Generation、保留引用与迁移日志继续保存历史，不再依赖 V1 Route。 |
| [0023](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0023-canonical-git-object-integrity.md) | 接纳或使用保存仓库状态的 Git 对象前，重新核对其内容。 | **演化。** Git 权威状态已退役，文件描述符、路径与摘要检查保留。 |
| [0024](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0024-materialized-route-read-capabilities.md) | 物化路由回执只授予限定范围的读取与退役权限。 | **演化。** 路由回执已退役，检查和删除仍限定对象与操作范围。 |
| [0025](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0025-state-lock-process-instance-lease.md) | 锁绑定具体进程实例与稳定 inode，不因等待超时而夺锁。 | **演化。** 稳定锁 inode 与不按时间夺锁的规则保留，V1 进程实例租约已退役。 |
| [0026](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0026-offline-archive-projection-intent.md) | 创建离线归档前持久化意图，并严格检查输入。 | **退役。** 离线归档投影已退出产品范围。 |
| [0027](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0027-legacy-package-adoption-admission-and-canonicalization.md) | 旧包体通过路径、包内容与来源检查后，才纳入仓库管理。 | **迁移历史。** 旧包纳管计划已结束，包接纳检查以更小的范围保留。 |
| [0028](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0028-control-only-deb-inspection.md) | 检查 DEB 时只打开元数据所需的 control 归档，拒绝有歧义的容器。 | **保留。** DEB 解析仍限定读取范围与输入大小。 |
| [0029](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0029-client-support-floor-and-el8-freeze-version.md) | 由所有者明确规定最低客户端版本与 EL8 固定版本。 | **迁移历史。** 当前平台策略见兼容性参考与发布注记。 |
| [0030](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0030-audit-bound-legacy-yum-missing-body-prune.md) | 仅依据已评审的问题集合摘要，修复旧 YUM 索引中缺失的包体引用。 | **迁移历史。** 这项来源例外没有变成通用忽略选项。 |
| [0031](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0031-legacy-pro-gated-activation-and-checksum-repair.md) | 启用受访问控制的旧内容前，修复精确校验和并记录启用结果。 | **退役。** 商业版本启用流程退出产品，无法验证时停止修复的原则保留。 |

<span id="provider-与-edge-控制面"></span>

## 云端与边缘控制面

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| 0032 | 只允许一组由所有者指定的 Cloudflare 测试资源例外通过。 | **退役。** 这是针对特定测试的历史例外。 |
| [0033](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0033-provider-scoped-readiness-registry.md) | 服务就绪检查使用独立注册表与所有权记录。 | **退役。** 服务初始化注册表已退出 SOW。 |
| [0034](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0034-cloudflare-nonproduction-worker-bootstrap.md) | Worker 初始化使用租约、两阶段恢复、精确资源身份与可逆状态。 | **退役。** Cloudflare 部署不再由仓库引擎负责。 |
| [0035](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0035-cloudflare-provider-attestation-and-log-sink-lease.md) | 使用前验证服务身份、运行时绑定、日志接收端与租约所有权。 | **退役。** 这套边缘控制面已退出产品。 |
| [0036](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0036-provider-delete-capability-and-checkpoint-fenced-fallback.md) | R2 缺少条件 DeleteObject；能力探测与重复身份检查通过后，可显式启用 `checkpoint-fenced` 无条件删除。 | **演化；删除降级未继承。** 能力探测和条件不足时停止的规则保留。当前 SOW 禁用 R2 远端删除，只报告 GC 候选对象。 |
| [0037](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0037-pre-upload-confidential-edge-denial-attestation.md) | 上传机密字节前，先证明边缘服务会拒绝未授权访问。 | **退役。** 边缘访问控制现由外部部署负责。 |
| [0038](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0038-yum-consumer-preflight-receipt.md) | YUM 切换需要有有效期的回执，绑定精确端点、Generation 与信任数据。 | **迁移历史。** 用于核对客户端切换，随后退役。 |
| [0039](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0039-caret-url-wire-canonicalization.md) | 脱字符在 Go、边缘服务、日志与源站路由中采用唯一 URL 编码。 | **演化。** 旧路由已退役，路径只编码一次的规范保留。 |

## 有界配置与派生状态恢复

| ADR | 原始决策 | 后续命运 |
|---|---|---|
| [0040](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0040-bounded-configuration-topology.md) | 分配内存或执行前，限制配置条目数与展开后的拓扑大小。 | **保留。** 当前解析器与状态格式仍有明确大小和数量上限。 |
| [0041](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0041-preserved-projection-orphan-quarantine.md) | 保留未知的最终投影暂存目录，以便核查。 | **演化。** 当前恢复仍保留冲突记录，并在无法核实时停止。 |
| [0042](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0042-derived-state-replacement-outcome.md) | 派生状态替换明确区分成功、回滚、保留与阻塞结果。 | **演化。** Managed 日志记录操作阶段；记录状态与文件不一致时停止恢复。 |
| [0043](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0043-derived-state-hostile-writer-admission.md) | 文件修改检查描述符身份，并规定同一操作系统用户恶意并发写入的保护范围。 | **保留。** 路径检查拒绝身份变化，操作系统权限仍负责隔离其他写入者。 |
| [0044](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0044-preserved-projection-audit-retirement.md) | 只有匹配精确操作权限与确认令牌，才可删除保留的核查副本。 | **演化。** V1 命令已退役，删除前限定对象与操作权限的规则保留。 |
| [0045](https://github.com/pgsty/sow/blob/v0.1.0/docs/adr/0045-generic-derived-state-residue-recovery.md) | 对无日志残留进行有界分类，不能静默接纳或删除。 | **保留。** 当前恢复仍区分已知状态、安全残留与冲突记录。 |

## 账本背后的共同模式

延续下来的决策有几条共同规则：

- 每个事实只有一个所有者。
- 修改前检查精确身份。
- 不可变内容就绪后，再提交协议指针。
- 提交意图持久化后，通过前向恢复完成操作。
- 删除前检查引用关系与删除条件。
- 限制输入大小，明确产品范围。
- 记录实际验证过的客户端与存储服务。

当前实现见[设计原则](/zh/blog/design/principles/)、[系统模型](/zh/blog/design/model/)与
[发布与恢复](/zh/blog/design/publication/)。

不可变的 [v0.1.0 ADR 目录](https://github.com/pgsty/sow/tree/v0.1.0/docs/adr)仍是第一手
资料。下一篇文章继续汇总独立的 [v0.1 证据记录](/zh/blog/design/v01-evidence/)。
