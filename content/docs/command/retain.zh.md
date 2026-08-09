---
title: "sow retain"
linkTitle: "retain"
description: "添加、列出与移除供本地垃圾回收使用的显式 Generation 保留根。"
url: "/zh/docs/command/retain/"
weight: 1600
icon: fa-solid fa-box-archive
---

`sow retain` 管理显式的本地 Generation 根。`retain add` 只能冻结当前 Built Generation；后续
构建使它成为历史版本后，该代所需的软件包体仍受保护。

## 语法

```text
sow retain add GENERATION [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
sow retain ls             [-C|--workdir DIR] [-r|--repo NAME] [--json]
sow retain rm GENERATION  [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

`GENERATION` 必须是大于零的十进制整数。

## retain add

要求 `GENERATION` 等于当前 Built Generation，校验后将其 Manifest 冻结到工作区私有状态中，
并添加显式 GC 根。不能在事后用 `retain add` 重建一个更老的 Generation。

```console
sow retain add 12 -r pgsql
retained generation 00000000000000000012: /srv/sow/.sow/pgsql/retained/00000000000000000012
```

保留记录只保护包体，不切换当前视图，也不执行发布。重复添加同一 Generation 时，只有已验证记录
与当前证据一致才可视为幂等。

## retain ls

列出显式保留记录。它是只读命令，因此不接受锁参数或 `--dist`。

```console
sow retain ls -r pgsql
GENERATION	RECORD_IDENTITY	PATH
00000000000000000012	678beeae...	/srv/sow/.sow/pgsql/retained/00000000000000000012
```

空列表也是成功结果。

## retain rm

只移除显式保留根：

```console
sow retain rm 12 -r pgsql
removed retained generation 00000000000000000012
```

该命令不删除软件包体。移除一个未被保留的 Generation 是幂等空操作。只有在其他安全根也无法
到达这些包体时，后续本地 [`sow gc`](/zh/docs/command/gc/) 才可能回收。

## 参数

| 参数 | 适用命令 | 含义 |
|---|---|---|
| `-C, --workdir DIR` | 全部 | 工作区发现起点 |
| `-r, --repo NAME` | 全部 | 选择 Repository |
| `-T, --timeout DUR` | `add`、`rm` | 最长写锁等待时间 |
| `-N, --no-wait` | `add`、`rm` | 锁被占用时立即失败 |
| `--json` | 全部 | 输出 `sow.cli/v1` Envelope |

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | 操作完成，包括空列表 |
| `1` | 文件系统或运行时 I/O 错误 |
| `2` | Generation 语法无效、发现错误或隐式 Repository 选择有歧义 |
| `4` | `add`/`rm` 无法获取写锁 |
| `5` | Generation Manifest 或 Repository 状态不一致 |
| `6` | 显式 Repository 未配置、`retain add` 不是当前 Built Generation，或其他安全规则拒绝请求 |

## 参见

- [`sow gc`](/zh/docs/command/gc/) —— 使用保留根执行回收
- [`sow changes`](/zh/docs/command/changes/) —— 查看 Built Generation 差异
- [仓库布局](/zh/docs/reference/layout/) —— 私有保留记录位置
