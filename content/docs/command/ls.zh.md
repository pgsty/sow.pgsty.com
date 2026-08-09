---
title: "sow ls"
linkTitle: "ls"
description: "列出所选 Dist 的期望成员与已构建成员。"
url: "/zh/docs/command/ls/"
weight: 800
icon: fa-solid fa-list
---

`sow ls` 是针对 Package Object 与 Dist Membership 的只读查询。它显示所选 Dist 应包含哪些包，
以及这些成员是否已经进入当前 Built Generation。

## 语法

```text
sow ls [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择 Repository | [选择规则](/zh/docs/command/#repository-选择) |
| `-d, --dist NAME` | 选择 Dist；可重复 | [选择规则](/zh/docs/command/#dist-选择) |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

该命令没有 `--pool`、`--match` 或输出格式参数。

## 输出

```console
sow ls -r pigsty -d el9
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab	rpm:epel-release-0:7-5.noarch	el9	el9	pool/e/epel-release/epel-release-7-5.noarch.rpm
```

| 列 | 含义 |
|---|---|
| `SHA256` | 不可变内容身份，可直接传给 `show` 或 `rm` |
| `COORDINATE` | 规范的 `rpm:` 或 `deb:` 包引用 |
| `DISTS` | 所选范围内的 Desired Membership |
| `BUILT_DISTS` | 当前 Built Generation 中的成员关系 |
| `POOL_PATH` | Repository 内的不可变包体路径 |

Desired 与 Built 不一致时，首行显示 `dirty=true`。`BUILT_DISTS` 为空表示该包已进入期望状态，
但客户端尚不可见；运行 [`sow build`](/zh/docs/command/build/) 完成收敛。

多个所选 Dist 共享同一对象时，只输出一行，成员列表用逗号分隔。空 Dist 只有表头、没有包行，
仍然是成功结果。

## 选择范围

`ls` 要求 Dist 集合无歧义。Repository 包含多个 Dist 时，应传入一个或多个 `-d`，或从
`<repo>/dists/<dist>/` 内运行。

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

该命令不获取写锁，也不重新哈希包文件。`--json` 在 `result.packages` 中返回同一批记录。

## 示例

列出尚未构建对象的精确引用：

```bash
sow ls -r pgsql -d el9 --json |
  jq -r '.result.packages[] | select(.built_dists | length == 0) | .sha256'
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
| `2` | 用法错误、未发现工作区或隐式 Repository/Dist 选择有歧义 |
| `5` | Repository 状态库不可读或不一致 |
| `6` | 显式指定的 Repository 或 Dist 未配置 |

## 参见

- [`sow show`](/zh/docs/command/show/) —— 查看一个已列出的对象
- [`sow where`](/zh/docs/command/where/) —— 在工作区中定位对象
- [`sow rm`](/zh/docs/command/rm/) —— 从期望成员集中移除引用
- [包引用](/zh/docs/reference/package-ref/) —— 可接受的身份写法
