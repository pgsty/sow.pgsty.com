---
title: "系统模型"
linkTitle: "系统模型"
date: 2026-08-08
lastmod: 2026-10-13
authors: [Vonng]
description: "工作区、仓库、发行版与构建快照如何组织软件包和发布记录。"
categories: [Design]
tags: [repository, dist, pool, generation]
url: "/zh/blog/design/model/"
aliases:
  - "/docs/design/model/"
weight: 50
icon: fa-solid fa-diagram-project
draft: false
---

SOW 用配置文件保存仓库设置，用 SQLite 记录托管状态，用公共目录向客户端提供文件。
模型分别记录选中的软件包、已完成的构建，以及已发布的内容。

<span id="对象层级"></span>

## 对象

```text
Workspace（工作区）
├── Repository（仓库）
│   ├── Pool：包对象
│   ├── Dist：成员关系与策略
│   ├── Desired（期望状态）
│   ├── Built Generation（已构建快照）
│   └── 保留的 Generation
└── 发布目标
    └── Repository + 存储后端 + 前缀
```

### Workspace

工作区包含 `sow.yml`、私有 `.sow/` 目录和稳定的锁文件。
它集中保存配置，让命令可以找到所选仓库。

### Repository

一个仓库拥有一份 `pool/`、一棵 `dists/` 目录、一个状态数据库和一条 Generation 序列。
包去重只在该仓库内进行。两个仓库即使输入相同，也各自保存一份包副本。

<span id="package-object"></span>

### 包对象

SOW 使用包签名完成后的 SHA-256 标识包对象。名称、版本、release 和架构描述软件包，摘要标识实际字节。
重复加入同一对象会复用已有文件。同一包池路径对应不同内容时，SOW 报告冲突。

<span id="dist-与-membership"></span>

### Dist 与成员关系

一个 Dist 为一种格式（RPM 或 DEB）选择软件包和设置。
同一个包可以属于多个 Dist，但只保存一个 Pool 文件。
架构中性包（`noarch` 或 `all`）出现在每个适用架构的视图中，无需复制包体。

### Desired、Built 与 Generation

Desired 状态记录所选软件包和配置，Built 状态记录上一次完成的构建。
Generation 是该次构建的不可变清单，变更集则比较两份清单。

`add --skip` 会修改 Desired 状态而不重建索引。构建中断也可能留下未完成的操作。
用 `sow status` 查看差异，用 `sow build` 应用待构建变更或完成恢复。

<span id="publication-target"></span>

### 发布目标

目标将一个仓库连接到存储后端和前缀。每个目标分别记录发布尝试、检查点、清单和清理状态。

目标身份与配置变更规则见[发布与恢复](/zh/blog/design/publication/#目标身份)。

## 状态流

```text
软件包输入
    -> 检查、按配置签名、计算哈希
    -> 包对象与成员关系
    -> Desired 状态
    -> 渲染并校验
    -> Built Generation 与变更集
    -> 目标发布尝试
    -> 已应用检查点
```

Managed 操作用事务和日志记录进度。恢复时，SOW 根据记录完成或回滚中断的步骤。

<span id="公共状态与私有状态"></span>

## 公共文件与私有文件

| 作为完整仓库提供访问 | 留在私有工作区中 |
|---|---|
| `<repo>/pool/` | `sow.yml` |
| `<repo>/dists/` | `.sow/` 数据库与日志 |
| 生成的索引与签名 | 锁、暂存和恢复文件 |

公共目录副本可以提供软件下载。要继续管理仓库，还需保留匹配的私有工作区。
只有公共副本时，无法恢复成员关系、保留记录或发布历史。

<span id="锁边界"></span>

## 锁与写入者

工作区和仓库各有自己的锁。多数读操作使用共享锁，写操作使用独占锁，避免多个进程同时修改同一份状态。
`sow status` 直接查询锁状态，便于查看正在进行的写入。

每个目标前缀必须由一个工作区负责写入。这些锁协调本地进程，不协调不同主机上的独立工作区。
