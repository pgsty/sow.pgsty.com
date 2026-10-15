---
title: "设计原则"
linkTitle: "设计原则"
date: 2026-08-08
lastmod: 2026-10-13
authors: [Vonng]
description: "SOW 为什么分别管理软件包存储、仓库构建与发布。"
categories: [Design]
tags: [plain, managed, repository]
url: "/zh/blog/design/principles/"
aliases:
  - "/docs/design/principles/"
weight: 60
icon: fa-solid fa-ruler-combined
draft: false
---

SOW 分别管理包存储、仓库构建和发布。以下原则说明各类状态由谁保存，以及操作如何使用这些状态。

<span id="每个持久事实只有一个主人" data-td-print-local></span>

## 每类记录由一个对象管理

| 记录 | 管理范围 |
|---|---|
| 包体与包身份 | Repository |
| Desired 成员关系与 Built 状态 | Repository |
| Generation 与变更集 | Repository |
| 目标绑定与修订记录 | Repository 与发布目标 |
| 发布尝试与检查点 | Repository 与目标前缀 |
| 远端清单与删除记录 | Repository 与目标前缀 |

每个 Repository 分别保存自己的包副本，每个发布目标也分别保存一份。
因此，各仓库和目标可以独立管理包的保留与删除。

<span id="正典数据与可重建投影" data-td-print-local></span>

## 保存包体，重建索引

Managed 模式将包体保存在 `pool/` 中；Plain 模式使用输入目录中的包体。
索引和架构视图描述这些包，可以重新生成。

Managed 垃圾回收只删除已无当前引用、保留引用和恢复引用的包。Plain 模式直接根据当前目录重建索引。

<span id="公共树是交付单元" data-td-print-local></span>

## 提供完整公共目录

Managed Repository 根目录包含 `pool/` 与 `dists/`。复制或提供整个根目录，客户端才能根据索引解析包路径。
如果消费者需要独立的 RPM 架构目录，使用 `sow export rpm-leaf`。

工作区的 `sow.yml` 和 `.sow/` 放在 HTTP 根目录之外，其中保存配置、数据库、锁、日志和恢复文件。

<span id="包体做准备指针做提交" data-td-print-local></span>

## 先上传包，再更新索引入口

发布按以下顺序执行：

```text
包体 -> 不可变元数据 -> 协议入口文件 -> 宽限期 -> 删除符合条件的文件
```

协议入口文件包括 `repomd.xml`、`Release` 和 `InRelease`。
SOW 先上传它们引用的文件，再更新入口文件。旧文件保留到宽限期结束，让缓存了旧索引的客户端仍可下载。

<span id="恢复成本服从状态成本" data-td-print-local></span>

## 按已记录的状态恢复

Plain 构建中断后，重新运行 `sow create`，扫描包目录并重建索引。

Managed 发布会记录计划和进度。记录提交意图前，SOW 可以核对状态并放弃该次发布。
记录提交意图后，重新运行 `sow publish TARGET` 完成已记录的更新。
文件身份冲突时，恢复会停止并指出需要检查的对象。

<span id="兼容性是一张矩阵" data-td-print-local></span>
<span id="证据不会自动升级" data-td-print-local></span>

## 用实际消费者检查布局

包管理器需要解析包 URL，镜像工具还可能限制输出目录结构。
完整 Repository 与导出的 RPM 叶目录应分别测试，并记录客户端版本与目录布局。
[兼容性参考](/zh/docs/reference/compatibility/)列出自动化覆盖范围。

<span id="非目标让模型保持诚实" data-td-print-local></span>

## 在本地协调写入

每个目标前缀由一个工作区负责写入。SOW 使用锁协调本地进程，不协调多个独立工作区。

R2 发布支持增量上传。R2 垃圾回收只报告候选并保留远端文件，因为该后端未实现所需的条件删除操作。
