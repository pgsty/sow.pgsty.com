---
title: "系统模型"
linkTitle: "系统模型"
description: "连接软件包、Dist、Generation 与发布目标的对象模型和状态迁移。"
categories: [Design]
tags: [repository, dist, pool, generation]
url: "/zh/docs/design/model/"
weight: 200
icon: fa-solid fa-diagram-project
---

SOW 刻意把模型分层：配置表达意图，数据库记录有主状态，公共树是确定性投影。
任何一层都不能悄悄替代另一层。

## 对象层级

```text
Workspace
├── Repository
│   ├── Package Object
│   ├── Dist
│   │   └── Membership -> Package Object
│   ├── Desired 状态
│   ├── Built Generation
│   └── Retained Generation 引用
└── Publication Target
    └── Repository + provider + prefix
```

### Workspace

Workspace 提供发现、配置与协调，拥有 `sow.yml`、私有 `.sow/` 目录和稳定锁路径；
它不是包体去重域。

### Repository

Repository 是最小的自包含公共归档，也是软件包身份的作用域。它拥有一份 `pool/`、一组
`dists/`、一个状态数据库和一条 Generation 序列。即使输入相同，两个 Repository 也不共享
包体与计数器。

### Package Object

Package Object 由完成全部包签名后的最终 SHA-256 标识。名称、版本、release 与架构等逻辑坐标
只是元数据，digest 才是字节身份。重复加入同一 digest 是幂等操作；同一正典 Pool 路径出现
不同字节则是硬冲突。

### Dist 与 Membership

Dist 是一套 APT 或 RPM 发布策略及其成员集合。Membership 是多对多关系：一个 Package Object
可以属于多个 Dist，但不会因此多出一份正典包体。中性包（`all` / `noarch`）会投影到每个
适用架构视图中，逻辑上仍只有一条成员关系。

### Desired、Built 与 Generation

Desired 是配置和包操作想要的状态；Built 是最后一次完整渲染并校验通过的公共树。
Generation 是该 Built 状态的不可变清单，Changeset 则是两份清单之间的精确差异。

Desired 与 Built 分离后，中断状态可以被诚实描述：意图可能已经改变，但上一次提交的公共树
仍然有效。

### Publication Target

target 把一个 Repository 绑定到供应商 endpoint 与 prefix。发布尝试、已应用 checkpoint、
远端 inventory、grace 与删除证据都属于 target。构建 Repository 与目标无关，发布则不是。

## 状态流

```text
软件包输入
    -> 检查/签名/哈希
    -> Package Object + Membership
    -> Desired 状态
    -> 渲染并校验
    -> Built Generation + Changeset
    -> target 发布尝试
    -> applied checkpoint
```

每一条箭头都受 journal 或事务保护；后一阶段消费前一阶段的不可变身份，不重新解释可变路径。

## 公共状态与私有状态

| 公共：必须整体复制 | 私有：绝不能对外服务 |
|---|---|
| `<repo>/pool/` | `sow.yml` |
| `<repo>/dists/` | `.sow/` 数据库与 journal |
| 协议签名与索引 | 锁、stage、恢复前镜像 |
| Generation 描述的常规文件 | 凭据与供应商回执 |

只复制公共树可以得到一个有效的静态仓库，但它不是权威写入者：缺少匹配的私有状态时，
它无法安全续接发布历史、保留策略或垃圾回收。

## 锁边界

Workspace 生命周期操作取得 Workspace 锁；Repository 变更取得稳定 Repository 锁。
两者都需要时，固定先 Workspace、后 Repository，释放顺序相反。稳定锁路径避免 rename 或恢复
操作在新 inode 上意外形成第二个写入者。

模型假设每个配置 target prefix 只有一个权威 Workspace 且写权限独占；多个独立 Workspace
之间的分布式仲裁不在目标范围内。
