---
title: "发布与恢复"
linkTitle: "发布与恢复"
description: "发布、恢复、保留与安全删除仓库对象的 target-scoped 状态机。"
url: "/zh/docs/design/publication/"
weight: 400
icon: fa-solid fa-arrows-rotate
---

构建与发布是两个独立状态迁移。构建产生与 target 无关的 Generation；发布把该 Generation
应用到一个供应商前缀，并记录足以在不猜测的前提下恢复的证据。

## 所有权拆分

| Repository 作用域 | Target prefix 作用域 |
|---|---|
| Package Object | Publication Attempt |
| Desired 与 Built 状态 | Applied Checkpoint |
| Generation 与 Changeset | 远端 inventory |
| retained 包体/元数据引用 | grace 与删除证据 |

这项拆分避免把 filesystem 发布成功当成 R2 的证据，也避免一个 target 的半完成尝试污染另一个。

## 发布阶段

```text
plan
  -> 只增不删的包体
  -> 校验和命名的元数据
  -> 持久 commit intent
  -> 按视图逐一写协议指针
  -> applied checkpoint
  -> grace
  -> 证据门禁删除
```

提交意图之前，只允许写 add-only object。`publish --abort` 可以 reconcile 并移除私有 filesystem
stage，但不会删除远端对象。SOW 保留精确的 abandoned-object evidence，让后续尝试可以安全识别
并复用相同字节。

首个可变 APT stable alias 或协议指针写入前，commit intent 必须已经持久化。此后唯一合法恢复
方向是前向。对象存储没有多 key 原子提交，因此 SOW 允许一个有界 mixed-generation 窗口，
并按确定顺序逐个把 view 前滚。

## 指针顺序

每个 view 都先安装不可变内容；签名伴随文件先于对应的可变指针：

```text
RPM: 校验和命名 repodata -> repomd.xml.asc -> repomd.xml
APT: by-hash/direct indexes -> Release.gpg -> InRelease/Release
```

因此客户端一旦看到新指针，就一定能取到它声明的全部对象与签名。

## 已发布指针栅栏

一个 configured target 已经拥有 Applied Checkpoint 后，本地配置不能静默撤销该 target 仍拥有的
公开 Dist、architecture 或签名指针。操作者必须先退役/解绑 target，或者用新名称和新 prefix
发布替代品。

这样，危险的“配置漏了一项”会变成显式生命周期决策。

## 不复制包体的保留机制

Retained Generation 保存元数据、manifest 与引用集合，不保存另一棵包体树。Repository-local
可达性包括：

- 当前 Desired/Built Membership；
- retained Generation 引用；
- active operation 与 migration journal；
- publication grace 与 recovery root。

只有正典 Pool 对象位于完整 closure 之外，且当前文件身份仍与候选记录精确一致时，本地 GC
才允许删除它。

## 远端删除是一项能力

远端物理删除还要求权威 inventory、target ownership、grace 到期、必要的缓存 absence evidence，
以及原子条件删除 primitive。无法满足这些条件的供应商仍可用于发布，但 SOW 只能报告不可达
候选，不能发出不安全的无条件删除。

0.3 设计对 Cloudflare R2 就采用这种处理：源码实现支持发布，但明确禁用远端物理删除。
把 v0.2 C2 树迁移到这类供应商时，使用新的非重叠 prefix，不尝试在旧前缀内原地清理 alias。

## 恢复结果

| 持久边界 | 合法结果 |
|---|---|
| 没有 commit intent | reconcile 后放弃或重试 |
| 已有 commit intent | 只能前滚 |
| 已有 Applied Checkpoint | 收敛并进入 grace |
| 证据互相矛盾 | 失败关闭，不虚构状态 |

同一规则也适用于 v0.2 到 0.3 的本地迁移：`repo migrate --abort` 只在提交意图前合法；
此后恢复必须完成 metadata-only 布局，并在 grace 结束后删除已记录的旧 alias。
