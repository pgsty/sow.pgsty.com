---
title: "功能"
linkTitle: "功能"
description: "SOW 的工作原理与设计取舍:两条运行路径、包池投影、成员策略、签名、事务与审计。"
url: "/zh/docs/feature/"
weight: 300
icon: fa-solid fa-cubes
---

本板块讲机制。[上手指南](/zh/docs/start/)告诉你敲哪些命令,[教程](/zh/docs/tutorial/)带你走完整场景;这里回答的是下一个问题 —— *磁盘上到底发生了什么,以及为什么这样设计*。

每页都先给出它要保护的不变式,再讲实现该不变式的机制。如果你只想查语法,请直接看[参考](/zh/docs/reference/)。

## 哪一页回答哪个问题

| 问题 | 页面 |
|---|---|
| SOW 能做什么?与 `createrepo_c`、`reprepro` 相比如何? | [能力总览](/zh/docs/feature/overview/) |
| `sow create` 究竟写了什么?又拒绝碰什么? | [Plain 平面仓库](/zh/docs/feature/plain/) |
| 工作区、仓库、Dist 是什么关系?SOW 如何找到它们? | [Managed 工作区](/zh/docs/feature/managed/) |
| 同一份包字节为什么会同时出现在三个路径上? | [包池与架构视图](/zh/docs/feature/views/) |
| 我的包为什么返回 `excluded` 或 `limited`? | [成员策略](/zh/docs/feature/policy/) |
| 哪把钥匙签什么?换钥匙会发生什么? | [签名模型](/zh/docs/feature/signing/) |
| `add` 执行到一半机器掉电会怎样? | [事务与恢复](/zh/docs/feature/transactions/) |
| 如何证明当前这棵树可以安全发货? | [可观测与审计](/zh/docs/feature/audit/) |
