---
title: "事务与恢复"
linkTitle: "事务与恢复"
description: "恢复中断的 Managed 操作，了解本地构建顺序与锁行为。"
categories: [Feature]
tags: [transaction, generation, audit]
url: "/zh/docs/feature/transactions/"
weight: 700
icon: fa-solid fa-shield-halved
---

<span id="不变式"></span>

Managed 模式先记录变更，再应用变更。中断后，SOW 根据记录完成或回滚操作。
应使用哪个命令恢复，取决于中断的操作。

<span id="崩溃恢复"></span>

## 恢复中断操作

先查看记录的状态：

```bash
sow status -r demo
sow log -r demo
```

| 状态 | 下一步 |
|---|---|
| `clean` | 交付前运行 `sow check` |
| `dirty` | 运行 `sow build`，应用待构建的成员或配置变化 |
| `recovering` | 按下表选择与中断操作对应的恢复命令 |
| `error` | 根据诊断与日志检查报错文件或操作 |

| 中断操作 | 恢复命令 |
|---|---|
| `add`、`rm`、Dist 修改或构建 | `sow build -r demo` |
| `init`、`repo new` 或 `repo rm` | 重新运行对应的创建、删除命令 |
| 发布 | `sow publish TARGET` |
| Plain 索引生成 | 使用原选项重新运行 `sow create` |

先修正报错中的输入、配置或存储问题。恢复期间，工作区配置、数据库和私有状态应保持配套。
本地恢复完成后，运行 `sow check -r demo`。常见错误见[故障处理](/zh/docs/reference/troubleshooting/)，
发布恢复见 [`publish`](/zh/docs/command/publish/)。

<span id="两类持久日志"></span>
<span id="操作生命周期"></span>

## SOW 记录什么

| 记录 | 位置 | 用途 |
|---|---|---|
| 工作区生命周期日志 | `.sow/workspace-ops/active.json` | 协调配置与仓库创建、删除 |
| 仓库操作日志 | `.sow/<repo>.db` | 记录本地成员变更、构建与维护 |
| 发布状态 | `.sow/<repo>.db` | 记录目标绑定、固定的发布计划和进度 |

工作区生命周期恢复会比较当前 `sow.yml` 的摘要与日志中的新旧配置摘要。
配置替换决定该生命周期变更应回滚还是完成。两者都不匹配时，报告完整性错误。

仓库成员变更使用自己的状态转换：

```text
planned → staged → applied → built → done
                       └────────────→ done_dirty
```

| 状态 | 含义 |
|---|---|
| `planned` | 已记录操作及其范围 |
| `staged` | 已为下一阶段准备输入 |
| `applied` | 期望状态已提交，公开目录可能仍使用上一构建快照 |
| `built` | 已安装生成的公开目录 |
| `done` | 操作完成 |
| `done_dirty` | 期望状态已提交，仍需构建 |

其他终态包括 `rolled_back` 和 `failed`。用 `sow log OPERATION -r demo` 查看转换和时间。

`--skip` 通常以 `done_dirty` 结束。已识别的签名策略变化、构建计划固定前的配置变化，
或受支持的内部契约升级，也可能让已提交操作保留为脏状态。日志会记录原因。
需要时修正配置，再次运行 `build`。

<span id="提交顺序"></span>

## 本地构建顺序

SOW 在同一文件系统暂存并检查输出，再按以下顺序应用：

```text
包字节 → 元数据 → 客户端入口 → 过时元数据清理
```

1. 把包字节放入规范 `pool/` 路径。
2. 安装按校验和命名的 RPM 元数据，以及 APT 直接索引和 by-hash 索引。
3. 安装 RPM 的 `repomd.xml` 和已配置的签名，或适用的 APT `Release`、`InRelease`、
   `Release.gpg`。
4. 替换持久化后，清理过时元数据。

构建保留紧邻前一代的 RPM 不可变元数据和 APT by-hash 对象，供仍持有旧入口的客户端读取。
显式构建快照保留是独立功能，详见 [`retain`](/zh/docs/command/retain/)。

脏仓库仍服务最近完成的构建快照。多 Dist 操作中的各视图可能在不同时间切换。
远端 HTTP 请求和缓存也有各自的存续时间；在线目标更新应使用 `sow publish`。
`sow changes` 只列出本地文件变化，不执行发布或目标清理。

<span id="锁模型"></span>

## 锁与等待

SOW 通过建议锁协调进程。工作区生命周期使用 `.sow/workspace.lock`，
仓库写操作使用 `.sow/repo-locks/<repo>.lock`。需要两把锁时，先取工作区锁。

需要一致快照的读命令使用共享锁。`status` 探测仓库写锁，无需等写者结束即可报告活动状态。
Plain `create` 锁住目录及其父目录。

| 选项 | 行为 |
|---|---|
| `-T 30s` | 最多等待写锁 30 秒 |
| `-T 0` | 等待到锁可用，默认行为 |
| `-N` | 只尝试一次，占锁时立即退出 |

无法取得锁时退出码为 `4`。`-N` 与非零 `-T` 同用时退出码为 `2`。
只使用命令支持的锁选项；只读命令不接受这些选项。

<span id="fail-closed-的路径安全"></span>

## 文件系统要求

使用支持建议锁、`fsync` 和原子重命名的本地 POSIX 文件系统，macOS 使用 APFS。
公开文件与私有暂存区应位于同一文件系统。SOW 拒绝控制路径中的符号链接、
非预期文件类型和越界路径，并在替换或删除受控对象前检查文件身份。
网络文件系统不适合作为工作区。

仓库与 Dist 名称使用 `[a-z0-9][a-z0-9._-]*`，保留名称见
[仓库布局](/zh/docs/reference/layout/)。脚本如何处理中断、占锁和完整性错误，
见[退出码](/zh/docs/reference/exit-codes/)。

<span id="继续阅读"></span>
