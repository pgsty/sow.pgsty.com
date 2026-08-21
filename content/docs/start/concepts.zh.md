---
title: "核心概念"
linkTitle: "核心概念"
description: "SOW 模型：Plain 与 Managed、包池与视图、Desired Membership 与 Built Generation。"
categories: [Start]
tags: [plain, managed, repository, dist]
url: "/zh/docs/start/concepts/"
weight: 400
icon: fa-solid fa-diagram-project
---

## Plain 还是 Managed

两条运行路径相互独立。

| | Plain | Managed |
|---|---|---|
| 入口 | `sow create DIR` | `init`、`repo`、`dist`、`add`、`rm`、`build` |
| 状态 | 软件包目录 | `sow.yml` 加私有 SQLite/操作日志 |
| 公共布局 | 平面 RPM/DEB 索引 | Repository `pool/ + dists/` |
| 格式 | RPM 与 DEB 可共存于一个目录 | 每个 Dist 一种格式 |
| 架构视图 | 无 | 有 |
| 策略与审计 | 无 | 有 |
| 元数据签名与发布目标 | 无 | 有 |

目录内容已经等于目标仓库时使用 Plain。需要由 SOW 管理成员、策略、Generation、签名、
审计或发布时使用 Managed。

## Managed 层级

```text
Workspace                    /srv/sow
├── sow.yml                  配置
├── .sow/                    私有状态；绝不对外服务
└── Repository               /srv/sow/local
    ├── pool/                规范包体
    └── dists/
        └── Dist             一个具名 RPM 或 DEB 成员集
            └── views        按架构渲染的元数据
```

- **Workspace** 是配置与发现边界。
- **Repository** 是隔离、Generation、发布和公共树边界。不同 Repository 之间不去重包体。
- **Dist** 是单一包格式的具名成员集合。
- **架构视图** 是派生输出，不是第二套成员关系。`noarch` RPM 与 `all` DEB 会进入所有适用
  视图，但包池字节不重复。

## 一条规范包体路径

Package Object 以确切字节的 SHA-256 标识；逻辑坐标来自 RPM header 或 DEB control，
不来自文件名。

每个已接受包体在 Repository `pool/` 下只有一条规范路径。RPM 架构视图只含 `repodata/`，
包位置通过父级相对路径回到包池；APT `Packages` 直接指向同一包池。

普通包管理器与镜像工具是不同契约。默认 `dnf reposync` 会拒绝规范 RPM 视图中的父级跳转。
需要自包含 RPM 镜像 leaf 时，使用 `sow export rpm-leaf` 生成独立产物。

## Desired 与 Built

Managed 模式分别追踪意图与公共字节：

```text
add / rm -> Desired Membership (revision)
                    |
                  build
                    v
             Built Generation -> pool/ + dists/
```

`add` 与 `rm` 默认构建受影响的 Dist。`--skip` 只记录成员变更，Repository 会保持 `dirty`；
随后用 `sow build` 把 Desired 收敛为新的 Built Generation。

- `sow status` 低成本读取状态，并报告 `ready_to_copy`。
- `sow check` 执行完整只读交付证明。dirty 或 recovering 状态不可交付。
- `sow changes [BASE_GENERATION]` 描述某个已记录 Generation 到当前 Built Generation 的
  物理差异。它是证据与计划输出，不能替代发布恢复或远端验证。
- `sow publish TARGET` 通过配置的 Provider 发布已校验 Generation，并记录 target 级恢复与
  checkpoint 状态。

## 事务与失败状态

写操作由 Workspace 或 Repository 锁串行化，并在公共变更前记录意图。包体与不可变元数据
先准备，可变协议指针最后更新。下一条 writer 会先恢复被中断操作，再开始新工作。

| 状态 | 含义 |
|---|---|
| `clean` | Desired 与 Built 一致 |
| `dirty` | Desired 已变化；Built 仍是上一个已提交 Generation |
| `recovering` | 存在必须解决的非终态操作 |
| `error` | 持久证据冲突；SOW 拒绝猜测 |

用 `status` 诊断，用 `check` 做发布门禁。`ready_to_copy=false` 的 Repository 不应发布。

## 继续阅读

- [Managed 工作区](/zh/docs/feature/managed/)
- [包池与架构视图](/zh/docs/feature/views/)
- [事务与恢复](/zh/docs/feature/transactions/)
- [发布与恢复](/zh/docs/design/publication/)
