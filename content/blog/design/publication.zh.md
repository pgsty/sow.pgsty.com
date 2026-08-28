---
title: "发布与恢复"
linkTitle: "发布与恢复"
date: 2026-08-08
lastmod: 2026-08-24
authors: [Vonng]
description: "发布、恢复、保留与安全删除仓库对象的 target-scoped 状态机。"
categories: [Design]
tags: [publish, transaction, object-storage]
url: "/zh/blog/design/publication/"
aliases:
  - "/docs/design/publication/"
weight: 40
icon: fa-solid fa-arrows-rotate
draft: false
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

## 持久 Target Identity 与 Rebind

Target 有两层嵌套身份：Storage Identity 覆盖 Provider、Endpoint、Region 与 Bucket；Target
Identity 再加入公共树 Prefix。首次绑定后，Repository Identity、两层 Target Identity 与三个
Authority Acknowledgement 都不可变。这样配置文件变化时，Attempt、Checkpoint、Grace 与
Maintenance 才不会被错误解释成另一命名空间的证据。

Target Name、`public_endpoint` 与 `max_cache_ttl` 只能通过显式
[`publish --rebind`](/zh/docs/command/publish/#重绑定可变目标配置) 修改。首次绑定、迁移回填与
每次接受的 Rebind 都追加不可变 Binding Revision。Rebind 与 Publish 使用同一组独占锁，并在
事务内重查不可变字段；Storage 或 Prefix 变化必须使用新 Target。

Target Maintenance 未完成时，TTL 无论增加还是减少都被冻结；Filesystem Conditional-delete
Workflow 还会冻结 `public_endpoint`。改变当前 TTL 不会重写历史 Grace：删除资格时间取已存
Deadline 与 Applied Checkpoint 加当前 Grace Minimum 中更晚的一个。

## 发布阶段

```text
plan
  -> 只增不删的包体
  -> 校验和命名的元数据
  -> 持久 commit intent
  -> 按视图逐一写协议指针
  -> Provider 与 Canonical Public Verification
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

## 公共验证

日常发布验证精确 Changed Closure 与所有受影响的最终 Pointer，不会从公网重新下载每个未变化
Package。Provider Receipt 与 Public Visibility 是两种独立证明。Filesystem 与 R2 HTTP(S)
目标共用 Canonical-GET Verifier：响应 Header 与 Body Idle 分别计时；Size+1 防止超长响应；
408/425/429/5xx 使用短有界重试；陈旧内容或缺失对象按 Cache TTL 重试。

No-cache 请求只是 Revalidation Hint；只有之后的普通 Canonical GET 看到期望字节，发布才能写入
Checkpoint。Filesystem 条件删除以 HTTP 404/410 证明公共缺失；陈旧 200 会重试至 TTL。
`file://` 则使用精确、基于描述符的缺失证明。R2 Public Absence 与远端删除仍保持禁用。

Filesystem 别名会在持久绑定前按 Prospective Canonical Path 检查，包括大小写不敏感卷上的大小写
别名。Backend/Path Preflight 失败不会创建 Binding Row，也不会创建 Target Prefix。

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
- active operation 与 recovery journal；
- publication grace 与 recovery root。

只有正典 Pool 对象位于完整 closure 之外，且当前文件身份仍与候选记录精确一致时，本地 GC
才允许删除它。

## 远端删除是一项能力

远端物理删除还要求权威 inventory、target ownership、grace 到期、必要的缓存 absence evidence，
以及原子条件删除 primitive。无法满足这些条件的供应商仍可用于发布，但 SOW 只能报告不可达
候选，不能发出不安全的无条件删除。

`r2` Provider 采用这种处理：发布路径已实现，但明确禁用远端物理删除，target GC 只报告候选。

## 恢复结果

| 持久边界 | 合法结果 |
|---|---|
| 没有 commit intent | reconcile 后放弃或重试 |
| 已有 commit intent | 只能前滚 |
| 已有 Applied Checkpoint | 收敛并进入 grace |
| 证据互相矛盾 | 失败关闭，不虚构状态 |
