---
title: "sow changes"
linkTitle: "changes"
description: "比较两个构建快照的文件差异。"
categories: [Command]
tags: [cli, publish, generation]
url: "/zh/docs/command/changes/"
weight: 1400
icon: fa-solid fa-code-compare
---

`sow changes` 列出基准构建快照与当前构建快照之间的文件差异。路径相对于仓库根目录。需要包含尚未构建的期望变化时，先运行 `sow build`。

## 语法

```text
sow changes [BASE_GENERATION] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择仓库 | [选择规则](/zh/docs/command/) |
| `--json` | 输出 JSON | false |

该命令作用于整个仓库，不接受 `-d/--dist`。

## 输出

```console
sow changes
base=4 generation=5 dirty=false
add	payload	pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm	19776	ffd9e7bd...
add	metadata	dists/el9/x86_64/repodata/5bc463cb...-primary.xml.gz	1460	5bc463cb...
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1514	05d3d5bf...
delete	delete	dists/el9/x86_64/repodata/0df96f0b...-primary.xml.gz	0	
```

各列依次为操作、阶段、仓库相对路径、大小、SHA-256。

| 字段 | 取值 |
|---|---|
| 操作 | `add`、`update`、`delete` |
| 阶段 | `payload`、`metadata`、`pointer`、`delete` |

此计划用于查看本地文件变化。需要交付时，使用 [`sow publish`](/zh/docs/command/publish/)，或暂存完整副本后再切换服务目录。

## 基准构建快照 {#base-generation}

不带参数时，SOW 比较当前构建快照与前一次构建快照。

`BASE_GENERATION` 是 `0..当前编号` 范围内的十进制整数。基准为 `0` 时输出当前构建快照的完整
交付清单，但不包含私有 `sow.yml` 与 `.sow/`。基准等于当前编号时输出空计划；从未构建的
仓库同样输出空的 `0 -> 0` 计划。

```console
sow changes 99
operation rejected: managed: operation rejected: base generation 99 is outside 0..2
```

## dirty 与恢复状态

期望状态尚未构建时，首行显示 `dirty=true`。结果仍以当前构建快照为终点，不包含待构建包文件。

仓库为 `recovering` 或 `error` 时，先按诊断信息恢复或修复仓库，再运行 `changes`。

## 示例

输出当前完整清单：

```bash
sow changes 0 -r pgsql --json > pgsql-current.json
```

生成仓库级计划后按路径筛选一个 Dist：

```bash
sow changes -r pgsql --json |
  jq '.result.changes[] | select(.path | startswith("dists/el9/"))'
```

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 已输出计划，包括空计划 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误、传入 `-d`、未发现工作区或隐式仓库选择有歧义 |
| `5` | 仓库处于 `recovering`/`error`，或状态证据不一致 |
| `6` | 显式仓库未配置，或基准编号超出有效范围 |

## 参见

- [`sow build`](/zh/docs/command/build/) —— 创建新的构建快照
- [`sow publish`](/zh/docs/command/publish/) —— 使用受支持的发布协议
- [`sow log`](/zh/docs/command/log/) —— 操作记录及其文件变化
- [仓库布局](/zh/docs/reference/layout/) —— 公开/私有路径边界
