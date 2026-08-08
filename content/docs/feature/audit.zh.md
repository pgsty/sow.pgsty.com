---
title: "可观测与审计"
linkTitle: "可观测与审计"
description: "正确使用 status、check、changes、retention 与操作日志，不混淆状态和证明。"
url: "/zh/docs/feature/audit/"
weight: 800
icon: fa-solid fa-magnifying-glass-chart
---

每个读取表面回答不同问题。

| 命令 | 问题 | 写入？ |
|---|---|---:|
| `status` | Repository 当前是什么状态？ | 否 |
| `check` | 所选 Repository 是否满足完整交付契约？ | 否 |
| `changes` | 两个 Built Generation 之间哪些物理文件不同？ | 否 |
| `log` | 记录了哪些操作与处置结果？ | 否 |
| `retain ls` | 哪些 Generation 是显式本地 GC root？ | 否 |

## `status`：低成本状态

```bash
sow status -r local
```

它报告 Desired revision、Built Generation、dirty Dist、pending 包体计数、锁状态与
`ready_to_copy`。它不哈希公共树，不恢复操作，也不构建。

| Repository 状态 | 含义 |
|---|---|
| `clean` | Desired 与 Built 一致 |
| `dirty` | Desired 已变化；公共树仍是上一份 Built Generation |
| `recovering` | 存在持久非终态操作 |
| `error` | 持久证据冲突，自动恢复无法安全决策 |

用 `status` 诊断，不要把它当成 `check` 的替代品。

## `check`：交付证明

```bash
sow check -r local
```

v0.2.0 checker 按顺序报告九层：

| 层 | 校验内容 |
|---|---|
| `config` | 严格配置与有效 Dist 输入 |
| `retained` | 显式保留 Generation 记录与冻结元数据 |
| `state` | SQLite schema 与关系状态 |
| `public-modes` | 公共文件/目录权限 |
| `package-bytes` | pool/pending object 与已记录 SHA-256 |
| `desired-membership` | 包身份、成员关系与架构一致性 |
| `index` | 渲染元数据与引用 closure |
| `signature` | 声明的元数据与 RPM 包信任要求 |
| `generation-manifest` | 已记录 Built manifest 与公共树 |

`check` 不写入也不修复。dirty 或 recovering Repository 不可交付，即使上一份已提交树仍可读取。
在发布流水线中执行 `check`，任何非零退出都应停止。

## `changes`：Generation 差异

```bash
sow changes -r local
sow changes 0 -r local
sow changes 42 -r local --json
```

- 不给 base：比较当前 Built Generation 与前一代；
- base `0`：描述完整当前公共树；
- base `N`：给出已记录 Generation `N` 到当前 Built 的净差异。

每行包含操作、phase、Repository 相对路径、大小与 SHA-256。phase 使用与本地构建相同的
payload、metadata、pointer、delete 词汇。

`changes` 是 manifest/差异表面。它不连接目标、不持久化远端 checkpoint、不执行 cache grace，
也不恢复中断传输。配置好的 live target 应使用 `sow publish TARGET`。离线复制应先 stage
完整树、复验，再原子切换上线。

## Generation 保留与 GC

```bash
sow retain add 42 -r local
sow retain ls -r local
sow retain rm 42 -r local
sow gc -r local
```

`retain add` 校验并冻结 Generation 的元数据与引用集合，不复制另一棵包体树。保留记录是显式
GC root。`retain rm` 移除该 root，本身不删除包字节。

本地 `sow gc` 只删除已证明不被当前状态、显式 retention、active recovery/publication 状态及
其他记录根引用的包体。Target GC 是另一项操作：`sow gc TARGET` 使用该 Provider 的安全模型。

普通构建会携带紧邻前一代的 RPM 不可变元数据与 APT by-hash object，让已读取旧指针的客户端
完成下载。这个有界协议窗口与显式 `retain` 是两回事。

## 操作日志

```bash
sow log -r local
sow log OPERATION -r local
sow log export operations.jsonl -r local
sow log prune 2026-01-01 -r local
```

日志按操作记录 kind/state、时间、配置/manifest identity、包处置、成员变化，以及适用时的
物理 changeset。

`log export` 输出稳定 JSONL，拒绝覆盖既有文件，并校验输出路径。`log prune` 接受日期或
RFC 3339 时间，只移除符合条件的终态审计记录；不会删除当前状态、恢复证据或仍被需要的
Generation manifest。

## 操作模式

```bash
sow build -r local
sow check -r local
sow publish public
```

`status` 用于监控，`check` 用于门禁，`publish` 用于目标变更，`log` 用于事后证据。

## 延伸阅读

- [Build 与 check 命令](/zh/docs/reference/cli/build/)
- [Log 命令](/zh/docs/reference/cli/log/)
- [发布生命周期](/zh/docs/reference/cli/publication/)
