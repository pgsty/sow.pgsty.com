---
title: "可观测与审计"
linkTitle: "可观测与审计"
description: "查看状态、验证仓库内容、比较构建快照，并读取操作历史。"
categories: [Feature]
tags: [audit, transaction]
url: "/zh/docs/feature/audit/"
weight: 800
icon: fa-solid fa-magnifying-glass-chart
---

用 `status` 查看状态，`check` 校验仓库，`changes` 查看文件变化，`log` 读取操作历史。

| 命令 | 回答的问题 |
|---|---|
| `status` | 是否需要构建或恢复？是否有写者活动？ |
| `check` | 状态、包字节、索引、签名是否一致且可以交付？ |
| `changes` | 两个构建快照之间有哪些本地文件变化？ |
| `log` | 执行了哪些操作，改变了什么？ |
| `retain ls` | 显式保留了哪些构建快照？ |

这些命令不修改仓库内容。

<span id="status低成本状态"></span>

## 查看状态

```bash
sow status -r demo
```

结果包含期望状态修订号、构建快照、脏 Dist、待构建包的数量与字节数、写锁状态及 `ready_to_copy`。

| 状态 | 含义 |
|---|---|
| `clean` | 期望状态与构建状态一致 |
| `dirty` | 成员或配置变化需要构建 |
| `recovering` | 已记录工作需要恢复或清理 |
| `error` | 记录或文件证据存在未解决错误 |

`status` 报告状态，不计算公开文件哈希。`dirty` 状态运行 `build`；
`recovering` 或 `error` 状态按诊断及[恢复流程](/zh/docs/feature/transactions/#恢复中断操作)处理。
交付前运行 `check`。

<span id="check交付证明"></span>

## 校验仓库

```bash
sow check -r demo
```

正常检查报告九层：

| 检查层 | 内容 |
|---|---|
| `config` | 配置与生效 Dist 设置 |
| `state` | SQLite schema 与关系状态 |
| `public-modes` | 公开文件和目录权限 |
| `retained` | 保留构建快照记录与元数据 |
| `package-bytes` | 包池和待构建包字节是否匹配记录的 SHA-256 |
| `desired-membership` | 包身份、架构和成员关系 |
| `index` | 索引内容和引用文件 |
| `signature` | 已配置的元数据与 RPM 包签名 |
| `generation-manifest` | 构建文件清单与公开目录是否一致 |

布局转换未完成时，改为报告 `config`、`state`、`public-modes`、`layout-transition`。
按 [`repo migrate`](/zh/docs/command/repo/#sow-repo-migrate) 的说明完成或中止迁移。

`check` 忽略缓存指纹，读取每份唯一物理包并计算哈希，不修复文件。
即使上一构建快照仍一致，脏仓库或恢复中的仓库也不能通过交付检查。

<span id="changesgeneration-差异"></span>

## 比较构建快照

```bash
sow changes -r demo
sow changes 0 -r demo
sow changes 42 -r demo --json
```

不传基线时与上一构建快照比较；基线 `0` 列出当前完整目录；基线 `42` 与已记录构建快照 42 比较。
各行按适用情况包含动作、阶段、仓库相对路径、大小和 SHA-256。

该比较不检查发布目标。用 `sow publish TARGET` 更新目标并继续中断传输，
用目标 GC 回收远端对象。

<span id="generation-保留与-gc"></span>

## 保留构建快照与回收无用包

`retain add` 只接受当前构建快照。若 `status` 显示构建快照为 42，应在后续构建替换它之前保留：

```bash
sow retain add 42 -r demo
sow retain ls -r demo
```

命令校验该构建快照，保存元数据与引用；包文件仍由共享包池保存。
不再需要构建快照 42 时，用 `sow retain rm 42 -r demo` 移除保留记录，
再用 `sow gc -r demo` 回收无用字节。本地 `gc` 要求仓库为 clean；有待构建变更时先构建。
期望成员、已构建成员、为旧客户端保留的成员记录，以及保留构建快照、恢复或发布状态
仍需使用的包都会保留。完整规则见 [`gc`](/zh/docs/command/gc/)。

普通构建保留的前一代元数据与显式保留功能相互独立。
目标清理使用 `sow gc TARGET`：filesystem 目标在缓存宽限期后支持条件删除，
R2 目标只报告候选，不执行删除。

<span id="操作日志"></span>

## 查看与导出日志

```bash
sow log -r demo
sow log OPERATION -r demo
sow log export operations.jsonl -r demo
sow log prune 2026-01-01 -r demo
```

日志记录操作状态、时间、包处理结果，以及适用的成员与文件变化。
操作详情还可能包含构建进度事件。

`log export` 将 JSON Lines 写入新文件或 stdout。`log prune` 接受日期或 RFC 3339 时间戳，
删除符合条件的终态审计记录。恢复所需记录和构建快照清单会保留。

脚本接口见 [JSON 输出](/zh/docs/reference/json/)，中断处理见
[事务与恢复](/zh/docs/feature/transactions/)。

<span id="操作模式"></span>
<span id="延伸阅读"></span>
