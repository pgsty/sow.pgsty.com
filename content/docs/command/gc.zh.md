---
title: "sow gc"
linkTitle: "gc"
description: "回收本地不可达包体，或对一个发布目标执行保守维护。"
url: "/zh/docs/command/gc/"
weight: 1700
icon: fa-solid fa-recycle
---

`sow gc` 有两种严格分离的模式：不带位置目标时，回收本地不可达包体；带 `TARGET` 时，维护一个
已配置发布目标。

## 语法

```text
sow gc          [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
sow gc TARGET   [-C|--workdir DIR]                  [-T|--timeout DUR | -N|--no-wait] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 仅用于选择本地 GC 的 Repository | 选择规则 |
| `-T, --timeout DUR` | 最长 Repository 等锁时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

目标自身已绑定 Repository，因此 `gc TARGET -r NAME` 属于用法错误。两种模式都不接受 `--dist`。

## 本地 GC

本地 GC 只删除所有安全根都无法到达的包池对象。安全根包括：

- 当前 Built Generation；
- 显式 [`retain`](/zh/docs/command/retain/) 记录；
- 恢复状态与非终态 Operation；
- 发布尝试及其证据；
- 活跃维护操作。

操作会记入日志。实际删除包体时，Repository 前进到新 Generation；没有合格对象时为幂等空操作。

```console
sow gc -r pgsql
local gc pgsql: generation=00000000000000000013 objects=4 bytes=1834200
```

## 目标 GC

目标维护使用发布 Checkpoint、不存在性证据与配置的 Cache Grace，具体行为取决于 Provider：

| Provider | 行为 |
|---|---|
| `filesystem` | 仅在 Grace 到期且已有存储/公开不存在性记录后，条件删除合格对象 |
| `r2` | 持久化精确的只报告候选集合；绝不发送对象删除请求 |

```console
sow gc prod
target gc pgsql/prod (filesystem): phase=done candidates=14 deleted=8 retained=6 pending=0
```

空操作表示当前没有到期维护任务，并不代表目标已经做过穷尽式重新验证。

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | GC 完成或没有合格对象 |
| `1` | 文件系统、Provider、网络或其他运行时错误 |
| `2` | 用法、工作区发现、`sow.yml` 无效或隐式 Repository 选择有歧义 |
| `4` | Repository 写锁不可用 |
| `5` | 恢复、状态、Receipt 或 Manifest 证据不一致 |
| `6` | 显式 Repository/目标未配置或不安全，或删除被安全前置条件拒绝 |

## 参见

- [`sow retain`](/zh/docs/command/retain/) —— 创建与移除显式本地根
- [`sow publish`](/zh/docs/command/publish/) —— 创建目标 Checkpoint 与 Receipt
- [发布模型](/zh/docs/design/publication/) —— Provider 保证与 Cache Grace
