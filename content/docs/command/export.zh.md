---
title: "sow export"
linkTitle: "export"
description: "将一个已构建 RPM Dist 架构导出为独立兼容仓库。"
url: "/zh/docs/command/export/"
weight: 1800
icon: fa-solid fa-file-export
---

SOW 提供一个导出子命令：`sow export rpm-leaf`。它创建外部、独立的 RPM 仓库，
repodata 使用本地 `pool/...` href。

## 语法

```text
sow export rpm-leaf DIST ARCH DIR [--hardlink] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

| 参数 | 要求 |
|---|---|
| `DIST` | 已配置的规范 RPM Dist 名称 |
| `ARCH` | `x86_64` 或 `aarch64` |
| `DIR` | 不存在或为空，且不与 Repository、私有状态、filesystem 目标根重叠的目录 |

| 选项 | 含义 | 默认值 |
|---|---|---|
| `--hardlink` | 对可信、同文件系统、只读目标使用硬链接 | 复制文件 |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择 Repository | 选择规则 |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

该命令不接受 `--dist`、jobs、timeout 或锁参数。

## 输出

```console
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
exported RPM leaf el9/x86_64 generation=00000000000000000012 method=copy packages=84 to /srv/export/el9-x86_64
```

目标目录包含：

- 使用本地包体 href 重写的 RPM repodata；
- 所需软件包目录树；
- 导出 Manifest；
- `.sow-export.json` 来源记录。

源必须是已完成的 Built Generation。导出物是独立制品，不属于 Desired Membership、
Built Generation、发布输入或 GC 根。

## 复制与硬链接

复制是安全默认值。`--hardlink` 只适用于同一文件系统、且消费者无法修改的可信只读目标。硬链接
包体与 SOW 包池共享 inode，不能用于可写或不可信目标。

SOW 会拒绝与已配置 filesystem 发布根重叠的输出，避免导出物被误认为或修改 Managed 发布目标。

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | 独立 RPM leaf 导出完成 |
| `1` | 文件系统、复制、硬链接或元数据写入错误 |
| `2` | 命令语法、Dist/架构 Token 无效，或发现/隐式 Repository 选择有歧义 |
| `5` | 源 Generation 或 Repository 状态不一致 |
| `6` | 显式 Repository 未配置、Dist 不是 RPM、视图/签名者不可用，或目标不安全/非空/重叠 |

## 参见

- [平台与集成](/zh/docs/reference/compatibility/) —— 已验证与明确不支持的工作流
- [仓库布局](/zh/docs/reference/layout/) —— 源目录与导出边界
- [`sow publish`](/zh/docs/command/publish/) —— 向配置目标执行 Managed 交付
