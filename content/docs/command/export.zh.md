---
title: "sow export"
linkTitle: "export"
description: "将一个 RPM 架构视图导出为独立仓库。"
categories: [Command]
tags: [cli, rpm, dist]
url: "/zh/docs/command/export/"
weight: 1800
icon: fa-solid fa-file-export
---

`sow export rpm-leaf` 将一个 Dist 的指定架构导出为独立 RPM 仓库。它把软件包复制到外部目录，并将元数据中的包路径改为本地 `pool/...` 路径。

## 语法

```text
sow export rpm-leaf DIST ARCH DIR [--hardlink] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

| 参数 | 要求 |
|---|---|
| `DIST` | 已配置的规范 RPM Dist 名称 |
| `ARCH` | `x86_64` 或 `aarch64` |
| `DIR` | 不存在或为空，且不与仓库、私有状态、filesystem 目标根重叠的目录 |

| 选项 | 含义 | 默认值 |
|---|---|---|
| `--hardlink` | 对同一文件系统上的只读输出使用硬链接 | 复制文件 |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择仓库 | 选择规则 |
| `--json` | 输出 JSON | false |

## 输出

```console
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
exported RPM leaf el9/x86_64 generation=00000000000000000012 method=copy packages=84 to /srv/export/el9-x86_64
```

目标目录包含：

- 使用本地包路径的 RPM 元数据；
- 所需软件包目录树；
- 导出清单；
- `.sow-export.json` 来源记录。

源仓库必须为 clean，有已完成的构建快照，且没有未完成的操作。所选 RPM 视图必须属于当前构建快照。导出物独立于工作区，不会阻止 GC 回收源仓库中的包。

仓库含多个 Dist 时，后续构建可能只更新其他 Dist，而此 RPM Dist 保留旧 Generation。
无变化的 `build` 不会推进该 Dist。导出前，用 `sow dist show DIST` 与 `sow status` 检查两者编号。
在一次实际更新构建该 RPM Dist 后导出，或为此流程使用独立的 RPM 仓库。

导出失败后，修正报告的问题，再换一个不存在或为空的目录重试。失败的目标目录中可能留有部分文件。

`export rpm-leaf` 的 repomd data 时间戳固定为 `0`，没有
`--metadata-timestamp` 选项。因此导出物不能直接接管保留了正数时间戳缓存的同一个 EL7
repository ID；换 baseurl 本身不能解决。需要客户端采用新的 repository ID 或清理元数据缓存。
若必须保留旧 ID 和缓存继续更新，请使用带显式时间戳的 Plain `create`，按
[迁移指南](/zh/docs/tutorial/yum-migration/) 维护发布时间并重签 repomd。

## 复制与硬链接

默认复制文件。`--hardlink` 只适用于同一文件系统上的只读输出。修改硬链接包文件也会修改 SOW 包池中的源文件。

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | 独立 RPM 仓库导出完成 |
| `1` | 文件系统、复制、硬链接或元数据写入错误 |
| `2` | 命令语法、Dist/架构 Token 无效，或发现/隐式仓库选择有歧义 |
| `5` | 源构建快照或仓库状态不一致 |
| `6` | 显式仓库未配置、Dist 不是 RPM、视图/签名者不可用，或目标不安全/非空/重叠 |

## 参见

- [平台与集成](/zh/docs/reference/compatibility/) —— 客户端与工具兼容性
- [仓库布局](/zh/docs/reference/layout/) —— 源目录与导出边界
- [`sow publish`](/zh/docs/command/publish/) —— 向配置目标执行 Managed 交付
