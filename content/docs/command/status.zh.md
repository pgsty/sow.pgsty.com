---
title: "sow status"
linkTitle: "status"
description: "查看仓库状态、待构建数据与锁占用情况。"
categories: [Command]
tags: [cli, managed, audit]
url: "/zh/docs/command/status/"
weight: 1100
icon: fa-solid fa-gauge-high
---

`sow status` 显示仓库是否需要构建、待构建数据量及写锁占用情况。它读取已记录状态，不扫描包文件内容。需要验证文件内容时，使用 [`sow check`](/zh/docs/command/check/)。

## 语法

```text
sow status [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择仓库 | [选择规则](/zh/docs/command/) |
| `-d, --dist NAME` | 只查看指定 Dist；可重复 | 全部 Dist |
| `--json` | 输出 JSON | false |

## 仓库状态 {#repository-状态}

SOW 记录期望的软件包集合，以及上一次构建完成的构建快照。

| 状态 | 含义 | 下一步 |
|---|---|---|
| `clean` | 期望状态与已构建状态一致 | 复制仓库前运行 `check` |
| `dirty` | 两种状态不同，常见于 `--skip` 或配置变化之后 | 运行 `build` 应用变更 |
| `recovering` | 本地仓库操作被中断 | 运行 `build` 恢复 |
| `error` | 状态、文件或恢复记录需要处理 | 查看 `dirty_reasons`，运行 `check` 与 `log` |

## 输出

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

人类可读输出包含仓库状态、`ready_to_copy`、期望状态修订号、构建快照、
受影响 Dist、待处理对象数量/字节数与写锁状态。

JSON 结果还包含 `dirty_reasons` 与最近一次操作记录：

```json
{
  "repository": "demo",
  "status": "dirty",
  "ready_to_copy": false,
  "desired_revision": 5,
  "built_generation": "00000000000000000004",
  "dirty_dists": ["el9"],
  "dirty_reasons": ["dist el9 Desired and Built membership sets differ"],
  "pending": {"count": 1, "bytes": 19776},
  "repository_locked": false
}
```

`ready_to_copy` 汇总已记录的状态。为 false 时，`dirty_reasons` 给出原因。文件内容由 [`sow check`](/zh/docs/command/check/) 校验。

仓库中未完成的维护操作也会影响 Dist 状态，即使期望成员与已构建成员相同。
查看 `dirty_reasons` 和待处理操作，再按提示执行相应的恢复命令。
`dist ls` 与 `dist show` 也会反映该状态。

## 读取行为 {#只读契约}

`status` 读取状态，不迁移或修复数据库。它可以读取 schema v6、v12 与当前 v13 数据库。不支持或无法读取的状态返回 `5`。对旧工作区执行写操作前，先备份，再逐个运行 [`sow repo migrate`](/zh/docs/command/repo/#sow-repo-migrate)。

## 退出行为

只要状态可读，`status` 在 `clean`、`dirty`、`recovering`、`error` 四种状态下都返回 `0`。
脚本应读取结构化状态，而不是把后三者当作命令执行失败。

| 代码 | 触发条件 |
|---|---|
| `0` | 仓库状态可读 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误、未发现工作区或隐式仓库选择有歧义 |
| `5` | 状态库不可读或不一致 |
| `6` | 显式指定的仓库或 Dist 未配置 |

## 参见

- [`sow build`](/zh/docs/command/build/) —— 构建仓库的待处理变更
- [`sow check`](/zh/docs/command/check/) —— 检查文件完整性
- [`sow log`](/zh/docs/command/log/) —— 查看这里报告的最近操作记录
- [事务与恢复](/zh/docs/feature/transactions/) —— 状态变化与指针安全
