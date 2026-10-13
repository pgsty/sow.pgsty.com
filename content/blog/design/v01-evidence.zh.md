---
title: "SOW v0.1 到底证明了什么"
linkTitle: "v0.1 证据账本"
date: 2026-07-31
lastmod: 2026-10-13
authors: [Vonng]
description: "汇总 v0.1 的 112 份验证报告，涵盖客户端兼容性、规模、恢复、迁移与云存储行为。"
categories: [Design]
tags: [history, v0.1, evidence, compatibility, verification]
url: "/zh/blog/design/v01-evidence/"
weight: 90
icon: fa-solid fa-microscope
draft: false
---

v0.1 归档包含 112 份报告，日期从 2026-07-11 到 7 月 31 日。
它们记录了客户端测试、规模测量、故障恢复、迁移和云存储实验。
本文汇总主要结果，并链接到代表性报告。

每项结果对应报告中记录的源码版本、测试数据、客户端与环境。
当前支持情况见[兼容性参考](/zh/docs/reference/compatibility/)。

## 证据时间线

| 时间 | 报告数 | 主要工作 |
|---|---:|---|
| 2026-07-11 | 3 | 真实 APT/DNF 基线、72,310 个包的清单扫描、5 万个上游包的流式处理 |
| 2026-07-12 | 35 | APT/YUM 协议、CAS/GC、发布顺序、恢复、MinIO、性能、迁移、构建与供应链检查、云测试工具 |
| 2026-07-13 | 2 | RPM 信任验证与选定包集合的物化恢复 |
| 2026-07-14–16 | 14 | 旧拓扑、仓库族迁移、物理所有权、完整副本纳管与包签名清单 |
| 2026-07-17–20 | 39 | Cloudflare/R2/COS/边缘服务安全、服务身份验证、切换回执、配置上限与检查点约束下的删除 |
| 2026-07-22 | 10 | 暂存、应用、清理、回滚与残留删除中的文件描述符和路径身份 |
| 2026-07-26–29 | 7 | 递归持久化、恶意并发写入、替换结果、保留核查副本与存储服务修正 |
| 2026-07-30–31 | 2 | 从空环境验证 APT/YUM/静态制品最小可用产品，核对最终旧版源码基线 |

## 哪些结论有较强证据

### 真实客户端与大仓库

最早的测试使用真实 APT 与 DNF 客户端，并测量处理大仓库的成本：

- [真实 APT/DNF 客户端兼容](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-client-compat.md)；
- [72,310 个包的清单扫描](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-manifest-72k-performance.md)；
- [5 万个上游包的流式处理](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-11-upstream-50k-streaming.md)；
- 独立的 5 万包 APT、YUM、物化、发布计划与旧包纳管测试。

这些测量支持了大仓库采用流式处理与有界并发的要求。

### 协议完整性与异常情形 {#协议闭包与负反例}

失败的实验找出了协议设计的限制：

- [APT 固定别名反例](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-apt-legacy-fixed-alias-negative-poc.md)
  表明旧客户端行为限制了别名切换的原子性。
- [YUM 原始别名与签名桥接反例](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-raw-alias-signature-bridge-negative-poc.md)
  区分旧 BaseURL 兼容与固定到 Generation（构建快照）的元数据。
- [YUM Generation 原子性](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-yum-generation-atomicity.md)
  记录哪些协议指针操作可以原子化，哪些不能。

这些实验说明，协议格式与客户端事务需要分别测试。

### 故障与恢复

归档测试了同步、发布、物化、快照、归档和远端恢复被中断的情况。
后期报告进一步检查文件描述符与精确路径身份，并覆盖回滚、隔离和保留核查记录。

代表性记录包括：

- [发布与恢复对抗审查](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-12-publish-recovery-adversarial-review.md)；
- [选定包集合的物化恢复](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-13-selected-set-materialization-recovery.md)；
- [状态锁与原子发布](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-19-state-lock-atomic-publication.md)；
- [派生状态替换结果](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-28-derived-state-replacement-outcome.md)。

这些测试促成了不同恢复路径：放弃未提交的工作，完成提交意图之后的工作，或在记录冲突时停止。

### 旧系统迁移

迁移报告枚举了旧 Make 目标、物理布局、仓库族、客户端配置、包签名清单和回滚方式。
修改前先使用只读副本，并核对精确回执。

这项工作验证了一条具体的 Pigsty 切换路径，也建立了一种方法：
把迁移假设记录为数据，在每一步前检查，切换结束后移除迁移代码。

<span id="provider-与-edge-实验"></span>

### 云存储与边缘服务实验

归档包含真实和模拟的 R2、MinIO、Cloudflare、COS 与边缘服务测试。
代表性报告包括：

- [真实 R2 存储协议](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-18-real-r2-storage-protocol.md)；
- [R2 发布存储事务](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-r2-publication-storage-transaction.md)；
- [完整存储服务的检查点约束删除](https://github.com/pgsty/sow/blob/v0.1.0/docs/evidence/2026-07-20-full-provider-checkpoint-fenced-delete.md)；
- Cloudflare 初始化、私有域名、服务身份验证和回滚记录。

<span id="归档没有证明什么"></span>

部分测试使用指定的非生产资源，另一些离线运行或使用模拟服务，报告中分别注明。
在 R2、MinIO 或 COS 上测得的存储行为，对应具体服务与所测 API。

## 哪些做法进入了设计方法

这项工作形成了六条实践：

1. **说明测了什么。** 区分源码检查、模拟故障、客户端测试与真实服务测试。
2. **保留失败结果。** 记录设计在什么条件下无法工作。
3. **随结果记录输入。** 保存源码版本、容器与客户端版本、存储服务、路由和测试数据。
4. **测量规模。** 记录大仓库的内存、调用次数与并发行为。
5. **重新测试新布局。** 历史结果与产生它的模型一起保存。
6. **检查每次发布构建。** 测试支持的平台，扫描依赖并运行静态分析。检查能否重现构建结果。

这些实践用于当前[设计原则](/zh/blog/design/principles/)与
[兼容性参考](/zh/docs/reference/compatibility/)。

## 第一手资料

[v0.1.0 验证报告目录](https://github.com/pgsty/sow/tree/v0.1.0/docs/evidence)保留全部报告，
包括命令、结果和测试条件。

继续阅读 [v0.2 重置](/zh/blog/design/v02-reset/)，了解这些经验如何用于更小的产品模型。
