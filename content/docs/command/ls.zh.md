---
title: "sow ls"
linkTitle: "ls"
description: "列出期望成员及其已构建位置。"
categories: [Command]
tags: [cli, managed]
url: "/zh/docs/command/ls/"
weight: 800
icon: fa-solid fa-list
---

`sow ls` 列出指定 Dist 的期望成员。每行还显示该包在整个仓库中的期望成员位置与已构建位置。可从输出中获取供 `show` 或 `rm` 使用的包引用。

## 语法

```text
sow ls [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择仓库 | [选择规则](/zh/docs/command/#repository-选择) |
| `-d, --dist NAME` | 选择 Dist；可重复 | [选择规则](/zh/docs/command/#dist-选择) |
| `--json` | 输出 JSON | false |

## 输出

```console
sow ls -r pigsty -d el9
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab	rpm:epel-release-0:7-5.noarch	el9	el9	pool/e/epel-release/epel-release-7-5.noarch.rpm
```

| 列 | 含义 |
|---|---|
| `SHA256` | 包内容的唯一标识，可直接传给 `show` 或 `rm` |
| `COORDINATE` | 规范的 `rpm:` 或 `deb:` 包引用 |
| `DISTS` | 整个仓库内的期望成员位置 |
| `BUILT_DISTS` | 当前构建快照中的成员关系 |
| `POOL_PATH` | 包文件相对于仓库的路径 |

首行显示所选 Dist 是否为 dirty。即使成员数量相同，配置变化也可能使 Dist 变为 dirty。

`-d` 按期望成员筛选包行。`DISTS` 与 `BUILT_DISTS` 列随后显示每个包在整个仓库中的全部位置。通过 `rm --skip` 移除的包不会出现在列表中，即使旧索引仍包含它。`BUILT_DISTS` 为空表示当前没有本地已构建 Dist 包含此包。

每个包只输出一行，多个 Dist 用逗号分隔。空 Dist 返回成功，输出中没有软件包行。

## 选择范围

`ls` 要求 Dist 集合无歧义。仓库包含多个 Dist 时，应传入一个或多个 `-d`，或从
`<repo>/dists/<dist>/` 内运行。

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

加上 `--json` 后，同一批记录位于 `result.packages` 中。

## 示例

列出尚未构建对象的精确引用：

```bash
sow ls -r pgsql -d el9 --json |
  jq -r '.result.packages[] | select(.built_dists | length == 0) | "sha256:" + .sha256'
```

按路径列出包体：

```bash
sow ls -r pgsql -d el9 --json | jq -r '.result.packages[].pool_path' | sort
```

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 已输出成员列表，包括空列表 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误、未发现工作区或隐式仓库/Dist 选择有歧义 |
| `5` | 仓库状态库不可读或不一致 |
| `6` | 显式指定的仓库或 Dist 未配置 |

## 参见

- [`sow show`](/zh/docs/command/show/) —— 查看一个已列出的对象
- [`sow where`](/zh/docs/command/where/) —— 在工作区中定位对象
- [`sow rm`](/zh/docs/command/rm/) —— 从期望成员集中移除引用
- [包引用](/zh/docs/reference/package-ref/) —— 包引用的写法
