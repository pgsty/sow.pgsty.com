---
title: "sow status"
linkTitle: "status"
description: "快速读取 Repository 的收敛、可交付、待处理包体、最近 Operation 与锁状态。"
url: "/zh/docs/command/status/"
weight: 1100
icon: fa-solid fa-gauge-high
---

`sow status` 是低成本的 Repository 状态查询。它读取状态，但不哈希文件、不验签、不恢复
Operation、不构建元数据，也不获取写锁。

## 语法

```text
sow status [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择 Repository | [选择规则](/zh/docs/command/) |
| `-d, --dist NAME` | 只查看指定 Dist；可重复 | 全部 Dist |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

## Repository 状态

每个 Repository 同时跟踪 SQLite 中的 Desired Revision，以及公开 `dists/` 树对应的
Built Generation。

| 状态 | 含义 | 公开视图 |
|---|---|---|
| `clean` | Desired 与 Built 一致 | 当前且完整的 Generation |
| `dirty` | Desired 已领先，常见于 `--skip` 或配置变化之后 | 上一个完整 Generation |
| `recovering` | 存在非终态 Operation，下一条写命令必须先恢复 | 上一个已完成的协议指针 |
| `error` | 自动恢复无法安全裁决 | 保留上一个完整视图，不尝试覆盖 |

dirty 不代表仓库只写了一半。协议指针最后切换，因此读者看到的始终是完整旧视图或完整新视图。

## 输出

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

人类可读输出包含 Repository 状态、`ready_to_copy`、Desired Revision、Built Generation、
受影响 Dist、待处理对象数量/字节数与写锁状态。

JSON 结果还包含 `dirty_reasons` 与最近一次 Operation：

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

`ready_to_copy=false` 是明确警告；`true` 只是廉价状态判断，并非字节级完整性证明。交付前应运行
[`sow check`](/zh/docs/command/check/)。

## 只读契约

`status` 不迁移也不修复状态。Repository 数据库无法安全读取时，命令退出 `5`；请先执行
诊断信息明确指出的维护命令，再重新查询。

## 退出行为

只要状态可读，`status` 在 `clean`、`dirty`、`recovering`、`error` 四种状态下都返回 `0`。
脚本应读取结构化状态，而不是把后三者当作命令执行失败。

| 代码 | 触发条件 |
|---|---|
| `0` | Repository 状态可读 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误、未发现工作区或隐式 Repository 选择有歧义 |
| `5` | 状态库不可读或不一致 |
| `6` | 显式指定的 Repository 或 Dist 未配置 |

## 参见

- [`sow build`](/zh/docs/command/build/) —— 收敛 dirty Repository
- [`sow check`](/zh/docs/command/check/) —— 完整的完整性/可交付门禁
- [`sow log`](/zh/docs/command/log/) —— 查看这里报告的最近 Operation
- [事务与恢复](/zh/docs/feature/transactions/) —— 状态变化与指针安全
