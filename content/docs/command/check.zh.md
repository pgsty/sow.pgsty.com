---
title: "sow check"
linkTitle: "check"
description: "交付前校验仓库文件、索引、状态与签名。"
categories: [Command]
tags: [cli, audit, signing]
url: "/zh/docs/command/check/"
weight: 1300
icon: fa-solid fa-list-check
---

交付 Managed 仓库前，使用 `sow check` 检查包哈希、状态、索引、签名与构建快照清单。此命令只读；如果期望状态与已构建状态不同，先运行 `sow build`。

## 语法

```text
sow check [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-j, --jobs N` | 并行校验工作线程数，不得小于 `1` | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择仓库 | [选择规则](/zh/docs/command/) |
| `-d, --dist NAME` | 校验指定 Dist；可重复 | 全部 Dist |
| `--json` | 输出 JSON | false |

## 校验层

仓库没有未完成的布局迁移时，`check` 按顺序报告九层校验：

| 层 | 校验内容 | `checked` 计数 |
|---|---|---|
| `config` | `sow.yml` 能否针对该仓库解析并通过校验 | 配置对象 |
| `state` | SQLite `quick_check`、外键、日志与恢复证据 | 一个状态库 |
| `public-modes` | 服务目录中所有文件与目录权限 | 已检查路径 |
| `retained` | 保留记录与保存的构建快照清单；损坏记录的处理方法见 [`retain rm`](/zh/docs/command/retain/#retain-rm) | 保留记录 |
| `package-bytes` | 包池与私有待构建包文件的 SHA-256 | 软件包对象 |
| `desired-membership` | 成员关系能否在当前策略下解析到真实对象 | 成员关系 |
| `index` | 渲染索引是否与其声明的成员关系一致 | Dist |
| `signature` | 所有已声明元数据/软件包签名是否有效 | 签名 |
| `generation-manifest` | 构建快照清单是否与磁盘文件一致 | 一个清单 |

仓库存在未完成的布局迁移时，`check` 报告 `config`、`state`、`public-modes` 与 `layout-transition`，随后停止。按报告中的 [`repo migrate`](/zh/docs/command/repo/#sow-repo-migrate) 指令完成或中止迁移。

### 软件包校验 {#物理证据与-io-契约}

每次运行都会重新计算包文件的哈希。同一物理文件的硬链接共用一次哈希结果。带签名的 RPM 还会进行签名校验。`checked` 统计软件包对象数量，不是文件读取次数。

```console
sow check
repository=pigsty status=clean ready_to_copy=true revision=5 generation=5
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=67
retained	ok=true	checked=0
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=8
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=1
```

## dirty 不可交付

dirty 仓库需要先构建，才能通过 `check`。旧构建快照与新的期望状态可以分别通过校验，但二者仍有差异：

```console
sow check
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5
...
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

此时退出 `5`。运行 [`sow build`](/zh/docs/command/build/) 后，再运行 `sow check`。

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 全部校验层通过，仓库可复制交付 |
| `1` | 校验期间发生 I/O 错误 |
| `2` | 用法错误、未发现工作区或隐式仓库选择有歧义 |
| `5` | 某个校验层失败，或仓库不可交付 |
| `6` | 显式指定的仓库或 Dist 未配置 |

## 参见

- [`sow status`](/zh/docs/command/status/) —— 快速查询状态
- [`sow build`](/zh/docs/command/build/) —— 按期望状态构建索引
- [退出码](/zh/docs/reference/exit-codes/) —— dirty 为什么映射到 `5`
- [可观测与审计](/zh/docs/feature/audit/) —— 组合使用校验与审计
