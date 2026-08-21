---
title: "sow build"
linkTitle: "build"
description: "将 Desired Membership 与渲染配置收敛为完整 Built Generation。"
categories: [Command]
tags: [cli, managed, generation]
url: "/zh/docs/command/build/"
weight: 1200
icon: fa-solid fa-hammer
---

`sow build` 是显式的 Desired-to-Built 收敛命令。它获取 Repository 写锁，恢复任何可裁决的
未完成 Operation，渲染并验证完整 Generation，最后切换协议指针。

## 语法

```text
sow build [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-j, --jobs N` | 并行 Worker 数，不得小于 `1` | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择 Repository | [选择规则](/zh/docs/command/) |
| `-d, --dist NAME` | 构建指定 Dist；可重复 | 全部受影响 Dist |
| `-T, --timeout DUR` | 最长等锁时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 将结果包装进 `sow.cli/v1` Envelope | false |

不带 `-d` 时，SOW 收敛所选 Repository 中全部受影响 Dist；带 `-d` 时只收敛指定 Dist，
未选择的变化继续保持 dirty。

## 结果

即使不带 `--json`，命令专用结果也是 JSON：

```console
sow build -r pgsql -d el9
{"operation":"4262183287563704350","repository":"pgsql","dists":["el9"],"desired_revision":6,"built_generation":"00000000000000000006","noop":false,"dirty":false}
```

加上 `--json` 后，该结果包装进标准 Envelope。

## 空操作构建

成员关系、相关策略、渲染设置与签名配置均未变化时，`build` 是幂等空操作，不增加 Generation：

```console
sow build
{"operation":"6295064788473690577","repository":"pigsty","dists":["el9","trixie"],"desired_revision":5,"built_generation":"00000000000000000005","noop":true,"dirty":false}
```

## 策略收敛

`build` 会重新执行当前 `exclude` 与 `limit` 策略。收紧策略可能移除 Desired Membership；
放宽策略不会从残留包池字节恢复历史成员，需要重新运行 [`sow add`](/zh/docs/command/add/)。

## 提交与恢复

SOW 在同一文件系统暂存新元数据，验证完成后再切换可变协议指针。RPM 校验和命名元数据与 APT
by-hash 确保新旧读者看到的视图始终自洽。

Pending 包体提升采用有界单写者 group commit。每批最多 512 个对象或 1 GiB：先创建 Pool
链接并持久化所有不同的目标父目录，再删除 pending 名称并持久化共享 pending 目录。中断只会
留下 pending-only、指向同一 inode 的双链接或 Pool-only 状态，都能按 journal 恢复；不会
持久地同时丢失两个名称。

一个 Operation 可以覆盖多个 Dist。每个 Dist 始终暴露完整视图；`build` 返回时，本次包含的所有
Dist 属于同一个 Built Generation。

开始新工作前，`build` 会尝试前向恢复或安全回滚非终态 Operation。如果日志、数据库与文件系统
证据互相矛盾，Repository 进入 `error`，`build` 拒绝猜测；不存在强制修复参数。

## 进度事件

耗时较长的构建会向 Operation Log 追加结构化 `build_progress` 记录。每条事件包含 `phase`、
`completed`、`total` 与 `jobs`。当前阶段为：

- `rendering`；
- `promoting_payload`；
- `publishing_dists`；
- `normalizing_public_tree`；
- `finalizing`。

这些事件不会推进 Operation 状态，也不会在每次更新后 checkpoint SQLite；它们只用于审计
与可观测性，不参与恢复决策。使用 [`sow log OPERATION`](/zh/docs/command/log/#查看单条-operation)
查看明细。

## 元数据签名

Managed 元数据签名只从 `sow.yml` 读取，没有命令行 Key 覆盖。配置的 Key 引用或指纹改变时，
相关 Dist 变为 dirty，下一次 build 重新签名。

- RPM：总是生成 `repodata/repomd.xml`；配置签名后额外生成 `repomd.xml.asc`。
- DEB：总是生成 `Release`；配置签名后额外生成 `InRelease` 与 `Release.gpg`。

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 收敛成功或无需操作 |
| `1` | 渲染、签名或文件系统错误 |
| `2` | 用法错误、未发现工作区或隐式 Repository 选择有歧义 |
| `4` | Repository 写锁不可用 |
| `5` | 无法安全完成恢复，或 Repository 处于 `error` |
| `6` | 显式范围未配置，或当前配置拒绝既有状态 |

## 参见

- [`sow status`](/zh/docs/command/status/) —— 判断是否需要收敛
- [`sow check`](/zh/docs/command/check/) —— 验证构建结果
- [`sow changes`](/zh/docs/command/changes/) —— 查看生成的文件差异
- [事务与恢复](/zh/docs/feature/transactions/) —— 完整提交协议
