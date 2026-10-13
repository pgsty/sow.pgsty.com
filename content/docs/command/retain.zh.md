---
title: "sow retain"
linkTitle: "retain"
description: "保留或释放一个构建快照所需的包文件。"
categories: [Command]
tags: [cli, retention, generation]
url: "/zh/docs/command/retain/"
weight: 1600
icon: fa-solid fa-box-archive
---

`sow retain` 保留指定构建快照所需的包文件，防止本地 GC 回收。保留内容包括包文件与冻结清单；此命令不恢复或发布旧仓库视图。

## 语法

```text
sow retain add GENERATION [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
sow retain ls             [-C|--workdir DIR] [-r|--repo NAME] [--json]
sow retain rm GENERATION  [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

`GENERATION` 必须是大于零的十进制整数。

## retain add

传入当前构建快照的编号。SOW 校验该快照，保存清单，并记录 GC 需要保留的包文件。应在生成下一个构建快照前添加此记录。

```console
sow retain add 12 -r pgsql
retained generation 00000000000000000012: /srv/sow/.sow/pgsql/retained/00000000000000000012
```

重复添加同一个构建快照时，如果保留记录仍可通过校验，命令不产生变化。

## retain ls

列出仓库的保留记录。

```console
sow retain ls -r pgsql
GENERATION	RECORD_IDENTITY	PATH
00000000000000000012	678beeae...	/srv/sow/.sow/pgsql/retained/00000000000000000012
```

空列表也是成功结果。

## retain rm

移除指定构建快照的保留记录：

```console
sow retain rm 12 -r pgsql
removed retained generation 00000000000000000012
```

该命令不删除软件包体。指定的构建快照没有保留记录时，命令成功返回，不作修改。只有在其他保留记录与操作也不再
引用这些包体时，后续本地 [`sow gc`](/zh/docs/command/gc/) 才可能回收。

保留记录损坏时，`retain rm`、`retain ls`、本地 `gc` 与 `check` 都会报告错误。`check` 的 `retained` 层会指出受影响的构建快照。需要丢弃该损坏记录时：

1. 停止工作区写操作。
2. 将 `.sow/<repo>/retained/<GENERATION>` 移到工作区外的备份位置。
3. 再次运行 `sow check`。

移走记录也会移除它提供的 GC 保护。

## 参数

| 参数 | 适用命令 | 含义 |
|---|---|---|
| `-C, --workdir DIR` | 全部 | 工作区发现起点 |
| `-r, --repo NAME` | 全部 | 选择仓库 |
| `-T, --timeout DUR` | `add`、`rm` | 最长写锁等待时间 |
| `-N, --no-wait` | `add`、`rm` | 锁被占用时立即失败 |
| `--json` | 全部 | 输出 JSON |

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | 操作完成，包括空列表 |
| `1` | 文件系统或运行时 I/O 错误 |
| `2` | 构建快照编号格式无效、发现错误或隐式仓库选择有歧义 |
| `4` | `add`/`rm` 无法获取写锁 |
| `5` | 构建快照清单或仓库状态不一致 |
| `6` | 显式仓库未配置、`retain add` 指定的不是当前构建快照编号，或其他安全规则拒绝请求 |

## 参见

- [`sow gc`](/zh/docs/command/gc/) —— 回收保留状态不再需要的包文件
- [`sow changes`](/zh/docs/command/changes/) —— 查看构建快照差异
- [仓库布局](/zh/docs/reference/layout/) —— 私有保留记录位置
