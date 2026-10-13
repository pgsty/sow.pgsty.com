---
title: "发布与恢复"
linkTitle: "发布与恢复"
date: 2026-08-08
lastmod: 2026-10-13
authors: [Vonng]
description: "SOW 如何上传仓库、继续中断的发布，以及清理不再使用的文件。"
categories: [Design]
tags: [publish, transaction, object-storage]
url: "/zh/blog/design/publication/"
aliases:
  - "/docs/design/publication/"
weight: 40
icon: fa-solid fa-arrows-rotate
draft: false
---

构建生成本地快照（Generation）。发布把快照中的文件上传到目标，并记录进度，以便中断后继续。
每个目标分别保存检查点，记录上次完成发布的内容。

<span id="所有权拆分"></span>

## 状态归属

| Repository 记录 | 目标记录 |
|---|---|
| 软件包、Desired 状态与 Built 状态 | 发布尝试与检查点 |
| Generation 与变更集 | 远端清单 |
| 保留的包和元数据引用 | 宽限期与删除记录 |

<span id="发布阶段"></span>
<span id="指针顺序"></span>

## 发布顺序

```text
固定发布计划
  -> 上传包体
  -> 上传不可变元数据
  -> 记录提交意图
  -> 按视图逐一更新协议入口文件
  -> 校验存储与公共 URL
  -> 记录已应用检查点
```

上传包体时，SOW 创建新对象或复用相同字节，不会用其他内容覆盖不可变路径。
修改第一个可变 APT 索引别名或协议入口文件前，SOW 会先记录提交意图。

每个视图都先上传引用内容，再更新入口文件：

```text
RPM: 校验和命名的元数据 -> repomd.xml.asc -> repomd.xml
APT: by-hash 与直接索引 -> Release.gpg -> InRelease/Release
```

更新期间，各视图可能暂时使用不同构建的索引。分离签名与索引也分两次写入。
因此，客户端可能需要重试索引刷新。公共校验完成后，SOW 才记录检查点。

<span id="公共验证"></span>

## 公共访问校验

SOW 通过 `public_endpoint` 下载变化的文件和受影响的索引入口，并核对内容。
未变化的软件包无需重复下载。

公共端点可能仍返回缓存中的旧文件。SOW 会在 `max_cache_ttl` 内等待并重试。
校验失败时，发布不会记录新的完成检查点。

<span id="恢复结果"></span>

## 继续或放弃发布

重新运行原来的 `sow publish TARGET` 命令即可继续。恢复沿用保存的计划，不会改用更新的本地构建。

| 已保存的状态 | 下一步 |
|---|---|
| 尚未记录提交意图 | 重试发布，或用 `--abort` 核对状态并放弃该次发布 |
| 已记录提交意图 | 重试发布，完成保存的更新 |
| 已记录检查点 | 完成剩余维护；目标已完成更新时无需再次上传 |
| 文件身份冲突 | 检查报错中的文件和目标配置，再重试 |

`--abort` 清理符合条件的私有文件系统暂存目录，保留远端对象，并记录已放弃的上传。
后续发布可复用字节相同的对象。

<span id="持久-target-identity-与-rebind"></span>

## 目标身份

存储身份由后端、端点、区域和桶组成；目标身份还包括前缀。首次发布将这些值绑定到 Repository，
后续发布据此查找对应历史。

修改目标名称、`public_endpoint` 或 `max_cache_ttl` 后，运行
[`sow publish TARGET --rebind`](/zh/docs/command/publish/#重绑定可变目标配置)。
SOW 会追加绑定修订记录。Repository、存储身份或前缀变化时，需要配置新目标。

修改 `max_cache_ttl` 前，先完成该目标尚未结束的维护。
文件系统目标正在执行条件删除时，需等删除流程完成后才能修改 `public_endpoint`。
缩短 TTL 不会提前结束已记录的缓存宽限期。

<span id="已发布指针栅栏"></span>

## 移除已发布的视图

目标仍在配置中且已有发布检查点时，SOW 会阻止撤销其现有 Dist、架构或签名入口。
需要停用该目标时，从 `sow.yml` 的 `targets` 中删除对应条目，再运行 `sow config check`。
这会保留旧远端文件与发布历史，不会删除远端仓库。

随后可以修改本地 Dist 配置并重建。要发布删减后的视图集合，配置一个使用不同前缀的新目标，并让客户端使用新 URL。
`--rebind` 不能修改目标前缀。配置规则见 [`sow publish`](/zh/docs/command/publish/)。

<span id="不复制包体的保留机制"></span>
<span id="远端删除是一项能力"></span>

## 保留与回收软件包

保留的 Generation 保存元数据、清单和指向共享 Pool 的包引用。本地垃圾回收会检查以下引用：

- 当前 Desired 与 Built 成员关系；
- 保留的 Generation；
- 进行中的操作与恢复日志；
- 发布恢复和宽限期。

只有引用全部消失，且文件仍与记录的身份一致时，SOW 才删除包。
因此，保留 Generation 可以保留其软件包，无需再复制一棵包目录。

文件系统目标删除要求清单完整、目标由当前工作区独占且宽限期已过。
SOW 按记录的文件身份执行条件删除，再检查公共端点是否已返回文件不存在，最后记录结果。
R2 目标 GC 只报告候选并保留对象。
