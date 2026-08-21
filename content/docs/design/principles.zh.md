---
title: "设计原则"
linkTitle: "设计原则"
description: "SOW 用来约束所有权、派生状态、发布与证据的一组不变式。"
categories: [Design]
tags: [plain, managed, repository]
url: "/zh/docs/design/principles/"
weight: 100
icon: fa-solid fa-ruler-combined
---

SOW 首先不是一个“元数据生成器”，而是一个所有权与状态迁移系统，只是它的输出恰好是
APT 与 RPM 仓库。下面这些原则让整套系统保持可推理。

## 每个持久事实只有一个主人

每类持久事实都只有一个作用域与权威：

| 事实 | 所有者 |
|---|---|
| 包体与软件包身份 | Repository |
| Desired 成员关系与 Built 状态 | Repository |
| Generation 与 Changeset | Repository |
| 发布尝试与已应用 Checkpoint | Repository + target prefix |
| 远端 inventory、grace 与删除证据 | Repository + target prefix |

状态不会在 Repository 或发布前缀之间暗中共享。因此同一个包可以在不同 Repository 或
target 中各存一份；这是有意为之：本地去重不能制造分布式所有权。

## 正典数据与可重建投影

Managed 模式下 `pool/` 中的包体是正典数据；Plain 模式下，顶层包文件本身就是正典。
协议索引、架构视图、报告与兼容导出都是投影，永远不会成为包体的第二个主人。

耐久规则服从权威来源。Managed 通过有记录的操作移除投影，且只有计算完所有 live / retained
owner 的可达性才删除正典数据；Plain 则直接按当前包目录重新生成自有索引路径。

## 公共树是交付单元

Repository 根由 `pool/ + dists/` 组成；整棵树才是静态托管、复制、鉴权与发布单元。
某个 RPM 架构 leaf 是客户端视图，但它不是一个独立拥有状态的 Repository。

`sow.yml`、`.sow/`、锁、journal、凭据与恢复文件都是私有状态，绝不能随公共树对外服务。

## 包体做准备，指针做提交

发布顺序固定为：

```text
包体 -> 不可变/校验和命名的元数据 -> 可变指针 -> 宽限期 -> 删除
```

包体与不可变元数据可以提前写入而暂不可见；`repomd.xml`、`Release` 或 `InRelease` 这样的
协议指针才是提交边界。只有新指针已经持久化、旧读者与缓存窗口已经关闭后，旧对象才可删除。

## 恢复成本服从状态成本

Plain 没有需要保存的期望状态历史。它成本最低的正确恢复方式就是重新做一遍内容扫描并覆盖重建，
因此不保存事务 journal，也不花与包体大小成正比的 I/O 去证明上一次尝试。

Managed 状态不同。提交意图之前，如果精确 reconcile 能证明公共指针从未改变，操作可以放弃；
提交意图之后只能前向恢复。Managed 不猜测一次半完成发布“应该已经成功”，而是比较 journal、
manifest、checkpoint、供应商身份与公共树。

证据互相矛盾时操作必须停止。一次可见的拒绝，比仓库历史悄悄分叉更安全。

## 兼容性是一张矩阵

协议合规、普通客户端、镜像工具、对象存储布局、代理规范化与文件系统语义是不同问题。
SOW 分别记录它们，并用与结论对应的真实客户端或供应商验证。

因此规范 Repository 与导出的 RPM 镜像 leaf 是两种独立产物；其中一种产物的证据不能证明
另一种产物兼容。

## 证据不会自动升级

规格不是实现，单测不是真实客户端结果，本地 Hugo 构建也不是公网发布。日期化结果始终绑定
当时的源码 revision、环境与版本；布局变化后，必须重跑对应门禁，不能把旧 PASS 直接继承。

## 非目标让模型保持诚实

当前契约不承诺跨 Repository 去重、重叠多写者、bucket 全局协调、任意第三方镜像工具兼容，
也不在供应商缺少原子条件删除时承诺安全远端删除。这些排除项属于安全契约，不是“尚未补完”。
