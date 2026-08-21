---
title: "sow changes"
linkTitle: "changes"
description: "将 Built Generation 差异输出为确定性的 Repository 相对文件交付计划。"
categories: [Command]
tags: [cli, publish, generation]
url: "/zh/docs/command/changes/"
weight: 1400
icon: fa-solid fa-code-compare
---

`sow changes` 比较 Built Generation，输出物理的 Repository 相对文件差异。它不显示尚未构建的
Desired 变化，也不是远端事务协议。

## 语法

```text
sow changes [BASE_GENERATION] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择 Repository | [选择规则](/zh/docs/command/) |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

该命令作用于整个 Repository，明确拒绝 `-d/--dist`。

## 输出

```console
sow changes
base=4 generation=5 dirty=false
add	payload	pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm	19776	ffd9e7bd...
add	metadata	dists/el9/x86_64/repodata/5bc463cb...-primary.xml.gz	1460	5bc463cb...
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1514	05d3d5bf...
delete	delete	dists/el9/x86_64/repodata/0df96f0b...-primary.xml.gz	0	
```

各列依次为操作、阶段、Repository 相对路径、大小、SHA-256。

| 字段 | 取值 |
|---|---|
| 操作 | `add`、`update`、`delete` |
| 阶段 | `payload`、`metadata`、`pointer`、`delete` |

阶段描述 SOW 如何构建本地 Generation。不要把单行直接重放到线上目录；应使用
[`sow publish`](/zh/docs/command/publish/)，或先暂存完整副本再原子切换。

## Base Generation

不带参数时，SOW 比较当前 Built Generation 与它的前一代。

`BASE_GENERATION` 是 `0..当前代` 范围内的十进制整数。Base `0` 输出当前 Generation 的完整
交付清单，但不包含私有 `sow.yml` 与 `.sow/`。Base 等于当前代时输出空计划；从未构建的
Repository 同样输出空的 `0 -> 0` 计划。

```console
sow changes 99
operation rejected: managed: operation rejected: base generation 99 is outside 0..2
```

## dirty 与恢复状态

Desired 为 dirty 时，首行显示 `dirty=true`，但计划仍以当前 Built Generation 结束。私有 pending
包体尚不可交付，不会出现在结果中。

Repository 为 `recovering` 或 `error` 时，`changes` 拒绝输出计划，避免把待定文件动作误认为已完成
Generation。

## 示例

输出当前完整清单：

```bash
sow changes 0 -r pgsql --json > pgsql-current.json
```

生成 Repository 级计划后按路径筛选一个 Dist：

```bash
sow changes -r pgsql --json |
  jq '.result.changes[] | select(.path | startswith("dists/el9/"))'
```

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 已输出计划，包括空计划 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误、传入 `-d`、未发现工作区或隐式 Repository 选择有歧义 |
| `5` | Repository 处于 `recovering`/`error`，或状态证据不一致 |
| `6` | 显式 Repository 未配置，或 Base Generation 超出有效范围 |

## 参见

- [`sow build`](/zh/docs/command/build/) —— 创建下一代 Generation
- [`sow publish`](/zh/docs/command/publish/) —— 使用受支持的发布协议
- [`sow log`](/zh/docs/command/log/) —— 语义 Operation 及其文件动作
- [仓库布局](/zh/docs/reference/layout/) —— 公开/私有路径边界
