---
title: "协同发布决策记录"
linkTitle: "发布决策"
date: 2026-08-14
lastmod: 2026-08-24
authors: [Vonng]
description: "SOW v0.4.0 保留原生发布 Provider 的最终决策，以及未交付的早期 rclone 提案边界。"
categories: [Design]
tags: [publish, transaction, object-storage, decision]
url: "/zh/blog/design/coordinated-publication/"
aliases:
  - "/docs/design/coordinated-publication/"
weight: 10
icon: fa-solid fa-cloud-arrow-up
draft: false
---

> [!IMPORTANT] SOW 0.4.0 已完成最终决策
> 本记录的早期版本曾提议采用 rclone Executor、`publish --dry-run` 与独立
> `sow audit` 命令。这些表面均未进入 0.4.0：SOW 不依赖 rclone，`publish` 没有
> `--dry-run`，`sow audit` 也不是有效命令。

本页保留决策边界，避免历史提案被误解为当前产品。规范行为以
[`sow publish`](/zh/docs/command/publish/)与
[发布与恢复](/zh/blog/design/publication/)为准。

## 最终决策

SOW 0.4.0 保留原生 `filesystem` 与 `r2` 发布 Provider。SOW 同时拥有 Repository 语义，以及
保持这些语义所需的传输操作：

- 冻结 Generation 与精确 Change Plan；
- 只创建的 Immutable Object 与 Conditional Mutable Write；
- 持久 Commit Intent 与确定性 Pointer 顺序；
- Attempt、Checkpoint、Inventory、Grace 与 Recovery Evidence；
- Provider 校验与 Canonical Public Visibility Check。

公开承诺保持克制：发布顺序确定、可重启，并最终收敛到一个冻结 Generation；但它不是覆盖所有
Object Key 的原子事务，也不创建 DNS、Bucket Policy、CDN 配置或客户端信任策略。

## 为什么没有采用 Executor 提案

通用 Bulk-copy Executor 会增加另一个需要版本化的依赖，同时削弱 Plan 中单个 Object 与其
Conditional-write Receipt 的一一对应关系。对于无法保留 SOW 逐对象 SHA-256 Metadata 的批量工具，
还需要引入第二套 Checkpoint Identity 模型。

0.4 因而选择强化既有、更小的传输边界：有界条件式 Multipart Upload、分阶段 Header 与 Idle
Progress Deadline、可重放安全操作的重试、精确 Changed-closure Verification，以及共用的 Public
HTTP Verifier。这样保留了现有 Checkpoint 模型，也避免把传输迁移伪装成普通升级。

## 0.4.0 实际交付

### 原生增量发布

`publish` 计算精确 Generation Delta，在 Pointer 之前写入 Payload 与校验和寻址 Metadata，持久化
Commit Intent，按确定顺序推进 View，验证 Provider/Public Evidence，并记录 Applied Checkpoint。
Target 已经是当前代时返回幂等 No-op。

### 操作者确认的 Rebind

`publish TARGET --rebind` 可修改 Target Name、`public_endpoint` 或 `max_cache_ttl`，同时保留稳定
Storage/Target Identity。Storage Endpoint、Provider、Region、Bucket、Repository 与 Prefix 变化
都必须配置新 Target。每次接受的 Rebind 都追加不可变 Audit Revision，并保留 Active
Commit-intent Attempt 的前滚恢复。

### 强化公共可见性

Filesystem 与 R2 HTTP(S) 目标共用 Canonical-GET Verification、陈旧内容的 Cache-TTL 处理、短有界
Transient Retry、独立 Header/Body-idle Deadline 与 Oversize Guard。Filesystem 条件删除还会等待
Canonical Public 404/410 Evidence。R2 删除仍保持禁用、只报告候选。

## 操作者流程

```bash
sow build -r pgsql
sow check -r pgsql
sow changes -r pgsql
sow publish prod
```

`changes` 是只读的本地 Generation Delta，不是远端 Dry Run。`publish` 只接受已配置 Target，并由
自身完成远端 Preflight。机器可读结果使用 `--json`。

报告配置漂移时，应先核对字段。只有允许的可变修正才使用 `--rebind`；Storage 或 Prefix 变化
必须创建新 Target。

## 恢复决策

```text
是否已经记录持久 Commit Intent？
├── 否 -> 重跑 publish，或对账后 publish --abort
└── 是 -> 重跑 publish；前滚是唯一合法方向
```

重复原命令就是 Resume 操作，不存在 `--resume`。Attempt、Checkpoint、Provider 或 Public Evidence
互相矛盾时失败关闭，不会选择一段看起来方便的历史。

## 明确边界

- 没有全前缀远端 `sow audit` 命令。`sow check` 证明本地 Repository；普通发布证明精确 Changed
  Closure 与受影响的 Public Pointer。
- R2 Target GC 记录精确、只报告的候选，绝不删除远端对象。
- 多独立写者、分布式锁、自动 Cache Purge、DNS 管理与任意 Executor Plugin 不属于当前契约。
- Provider 写入成功不代表包管理器验收；部署中的 dnf/APT Client 与签名策略是独立 Release Gate。

## 参考资料

- [当前发布与恢复模型](/zh/blog/design/publication/)
- [当前 `sow publish` 命令](/zh/docs/command/publish/)
- [平台与集成](/zh/docs/reference/compatibility/)
