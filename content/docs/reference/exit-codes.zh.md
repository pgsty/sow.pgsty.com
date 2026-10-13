---
title: "退出码"
linkTitle: "退出码"
description: "退出码 0–6 与中断码 130 的含义和示例。"
categories: [Reference]
tags: [cli, output]
url: "/zh/docs/reference/exit-codes/"
weight: 500
icon: fa-solid fa-triangle-exclamation
---

<span id="1--运行时错误"></span>
<span id="2--用法发现或配置错误"></span>
<span id="6--预期拒绝"></span>

脚本使用退出码判断结果，具体原因读取错误诊断。SOW 各命令使用相同的退出码含义。

| 退出码 | 含义 | 下一步 |
|---|---|---|
| `0` | 成功或无需变更 | 查看结果；无需变更时可能报告 `noop: true` |
| `1` | 运行时 I/O、包解析、渲染或其他未分类错误 | 修正诊断指出的输入或环境问题后重试 |
| `2` | 命令、工作区查找或配置错误 | 检查 `sow help COMMAND`、选择参数和 `sow config check` |
| `3` | 部分成功 | 查看结果，区分已提交工作与失败项 |
| `4` | 无法取得写锁 | 稍后重试或增加 `--timeout` |
| `5` | 完整性/恢复错误，或仓库尚不可交付 | 查看 `status`、`check`；构建脏仓库或恢复已记录操作 |
| `6` | 操作被拒绝 | 修正错误指出的冲突、包引用、架构、签名或保护设置 |
| `130` | 命令收到 SIGINT 或 SIGTERM 而中断 | 按中断操作的类型选择恢复命令 |

<span id="0--成功或无操作"></span>
<span id="5--完整性恢复或不可交付"></span>

## 成功不一定表示可以交付

只要能够报告状态，`status` 就返回 `0`，包括 `dirty`、`recovering`、`error`。
其 `ready_to_copy` 字段是状态摘要，不是完整字节检查。交付前使用 `check`：

```bash
sow build -r demo
sow check -r demo
```

脏仓库的旧索引可以完全一致，但由于期望状态尚未构建，`check` 仍返回 `5`。
运行 `build` 后再检查。如果诊断指出包损坏或恢复证据冲突，先查明该错误；
具体处理方法见[故障处理](/zh/docs/reference/troubleshooting/)。

<span id="3--部分成功"></span>
<span id="在脚本里使用"></span>

## 部分成功

`add` 返回 `3`，表示至少一个输入被接受或复用，同时至少一个失败。
JSON 结果保留每个输入的处理结果。策略排除不算输入失败。
`init` 在创建部分已声明对象、后续对象失败时，也可能返回 `3`。

先保存输出与退出码，再决定是否继续：

```bash
#!/usr/bin/env bash
set -uo pipefail

sow add ./incoming/ -r demo -d el9 --json > add-result.json
rc=$?
case "$rc" in
  0) ;;
  3) jq '.result.items[] | select(.status == "failed")' add-result.json
     exit 3 ;;
  4) echo 'Repository is busy; retry later.' >&2
     exit 4 ;;
  *) exit "$rc" ;;
esac

sow check -r demo || exit $?
sow publish mirror
```

`mirror` 必须是 `demo` 的已配置发布目标。此脚本在部分成功时停止，
以便先检查失败输入，再决定发布。

<span id="130--中断"></span>
<span id="4--锁不可用"></span>

## 等待锁与中断

默认 `-T 0` 一直等待写锁，`-T 30s` 最多等待 30 秒，`-N` 只尝试一次。
占锁时返回 `4`；`-N` 与非零 `-T` 同用返回 `2`。

只读命令不接受这些选项。部分读命令使用共享锁获取一致快照；
`status` 无需等待仓库写者即可报告写锁状态。

SOW 处理 Ctrl-C 或 SIGTERM 中断时返回 `130`。上传进度超时等内部超时保留其普通错误分类。
中断不会撤销已经提交的工作。先检查状态，再按[事务与恢复](/zh/docs/feature/transactions/)
中对应的流程继续操作。

## JSON 错误

使用 `--json` 时，stdout 输出结果封装，stderr 输出诊断。
`errors` 数组使用下列分类：

| 退出码 | JSON `class` |
|---|---|
| `1` | `runtime` |
| `2` | `usage`、`discovery` 或 `config` |
| `3` | `partial` |
| `4` | `lock` |
| `5` | `integrity` |
| `6` | `rejected` |
| `130` | `interrupted` |

按退出码或分类判断，不解析错误消息文本。Plain `create` 向 stderr 打印其内部错误，
JSON 消息可能额外包含 CLI 分类前缀。即使 `ok` 为 `false`，诊断和部分成功结果也会保留。

详见 [JSON 输出](/zh/docs/reference/json/)与
[事务与恢复](/zh/docs/feature/transactions/)。

<span id="延伸阅读"></span>
