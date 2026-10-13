---
title: "sow gc"
linkTitle: "gc"
description: "回收不再需要的本地包，或维护发布目标。"
categories: [Command]
tags: [cli, gc, retention, publish]
url: "/zh/docs/command/gc/"
weight: 1700
icon: fa-solid fa-recycle
---

使用 `sow gc` 回收本地不再需要的包文件。使用 `sow gc TARGET` 维护配置的发布目标。文件系统目标可以删除符合条件的对象；R2 目标只报告候选对象。

## 语法

```text
sow gc          [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
sow gc TARGET   [-C|--workdir DIR]                  [-T|--timeout DUR | -N|--no-wait] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 仅用于选择本地 GC 的仓库 | 选择规则 |
| `-T, --timeout DUR` | 最长仓库等锁时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

目标自身已绑定仓库，因此 `gc TARGET -r NAME` 属于用法错误。两种模式都不接受 `--dist`。

## 本地 GC

仓库完成构建且状态为 clean 时，可以执行本地 GC。状态为 dirty 时，先运行 `sow build`。只有以下记录都不再引用某个包时，GC 才会删除它：

- 当前期望成员、已构建成员，以及为旧客户端保留的旧成员记录；
- 显式 [`retain`](/zh/docs/command/retain/) 记录；
- 恢复状态与非终态操作记录；
- 发布记录；
- 活跃维护操作。

操作会记入日志。实际删除包文件时，仓库生成新的构建快照；没有符合条件的包时，命令不作修改。

```console
sow gc -r pgsql
local gc pgsql: generation=00000000000000000013 objects=4 bytes=1834200
```

## 目标 GC

目标 GC 等待配置的缓存宽限期到期，再检查哪些对象仍需保留：

| 存储类型 | 行为 |
|---|---|
| `filesystem` | 宽限期到期后，按条件删除合格对象，再验证公共 URL 已无法访问该对象，并记录结果 |
| `r2` | 保存候选对象报告，不删除对象 |

```console
sow gc prod
target gc pgsql/prod (filesystem): phase=done candidates=14 deleted=8 retained=6 pending=0
```

空操作表示当前没有到期维护任务。

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | GC 完成或没有合格对象 |
| `1` | 文件系统、存储服务、网络或其他运行时错误 |
| `2` | 用法、工作区发现、`sow.yml` 无效或隐式仓库选择有歧义 |
| `4` | 仓库写锁不可用 |
| `5` | 恢复、状态、回执或清单证据不一致 |
| `6` | 显式仓库/目标未配置或不安全，或删除被安全前置条件拒绝 |

## 参见

- [`sow retain`](/zh/docs/command/retain/) —— 保护包文件免于本地 GC 回收
- [`sow publish`](/zh/docs/command/publish/) —— 创建目标检查点与回执
- [发布模型](/zh/blog/design/publication/) —— 存储类型保证与缓存宽限期
