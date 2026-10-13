---
title: "命令"
linkTitle: "命令"
description: "SOW 命令语法、选项、选择规则与退出码。"
categories: [Command]
tags: [cli]
url: "/zh/docs/command/"
aliases:
  - "/docs/reference/cli/"
  - "/docs/reference/cli/query/"
  - "/docs/reference/cli/build/"
  - "/docs/reference/cli/publication/"
weight: 450
icon: fa-solid fa-terminal
search_keywords: [CLI, 命令参考, sow help, 参数, 子命令]
search_boost: 1.5
---

本节列出命令语法、选择规则、输出与示例。使用 `sow help COMMAND` 或 `sow help COMMAND SUBCOMMAND` 查看已安装版本的选项。

本文用 Desired 表示期望状态，用 Built 表示已构建状态。构建快照（Generation）是一次已完成构建的结果。

## 命令索引

`sow create` 直接在目录中构建平面仓库。需要通过工作区管理软件包时，先运行 `sow init`。其他 Managed 命令使用已有工作区。`help` 与 `version` 可以在任意目录运行。

| 命令 | 模式 | 用途 |
|---|---|---|
| [`sow create [DIR]`](/zh/docs/command/create/) | Plain | 就地生成平面 RPM/DEB 仓库 |
| [`sow init [DIR]`](/zh/docs/command/init/) | Managed | 初始化工作区并创建已声明的仓库/Dist |
| [`sow config check\|show`](/zh/docs/command/config/) | Managed | 校验配置或打印有效配置 |
| [`sow repo ls\|new\|show\|migrate\|rm`](/zh/docs/command/repo/) | Managed | 创建、查看、升级或删除仓库 |
| [`sow dist ls\|new\|show\|rm`](/zh/docs/command/dist/) | Managed | 管理 Dist |
| [`sow add PATH...`](/zh/docs/command/add/) | Managed | 添加软件包并重建索引 |
| [`sow rm PACKAGE...`](/zh/docs/command/rm/) | Managed | 移除软件包并重建索引 |
| [`sow ls`](/zh/docs/command/ls/) | Managed | 列出期望成员及其已构建位置 |
| [`sow show PACKAGE`](/zh/docs/command/show/) | Managed | 查看一个软件包 |
| [`sow where PACKAGE`](/zh/docs/command/where/) | Managed | 在工作区中查找软件包 |
| [`sow status`](/zh/docs/command/status/) | Managed | 快速读取仓库状态 |
| [`sow build`](/zh/docs/command/build/) | Managed | 按期望状态生成构建快照 |
| [`sow check`](/zh/docs/command/check/) | Managed | 在交付前校验仓库 |
| [`sow changes [BASE_GENERATION]`](/zh/docs/command/changes/) | Managed | 比较两个构建快照的文件差异 |
| [`sow publish TARGET`](/zh/docs/command/publish/) | Managed | 将构建快照发布到配置目标 |
| [`sow retain add\|ls\|rm`](/zh/docs/command/retain/) | Managed | 保留旧构建快照所需的包文件 |
| [`sow gc [TARGET]`](/zh/docs/command/gc/) | Managed | 回收不再需要的本地包，或维护发布目标 |
| [`sow export rpm-leaf`](/zh/docs/command/export/) | Managed | 导出独立 RPM 仓库 |
| [`sow log [OPERATION]`](/zh/docs/command/log/) | Managed | 查询、导出和裁剪操作记录 |

## 全局语法

```text
sow [OPTIONS] COMMAND [ARGS]
```

不带参数运行 `sow` 会打印命令列表并退出 `0`。用 `sow help COMMAND` 或
`sow help COMMAND SUBCOMMAND` 查看内置帮助。`sow version` 与 `sow --version` 打印版本与构建信息。

选项只适用于列出该选项的命令。位置参数以 `-` 开头时，在它前面加 `--`。未知选项或重复的单值选项返回退出码 `2`。

## 工作区发现

Managed 命令按以下规则寻找最近的 `sow.yml`：

1. 有 `-C/--workdir DIR` 时从 `DIR` 开始，否则从当前目录开始。
2. 逐级向上查找，在第一个 `sow.yml` 停止。
3. 首次查找失败且设置了 `SOW_DIR` 时，再从该目录查找。显式 `-C` 会取代当前目录候选，
   但不会禁用 `SOW_DIR` 回退。
4. 仍未发现工作区则退出 `2`。

`--workdir` 只改变发现起点，不会切换进程工作目录；相对位置参数仍相对于真实当前目录解析。
`sow create` 完全不参与工作区发现。

## Repository 选择

需要唯一仓库的命令按以下顺序选择：

1. 显式 `-r/--repo NAME`；
2. 发现起点所在的仓库；
3. 工作区中唯一的仓库；
4. 否则退出 `2` 并列出候选项。

`repo new` 与 `repo rm` 用位置参数接收 `NAME`，不接受 `-r`。`sow where` 默认搜索所有
仓库，`-r` 只用于收窄范围。发布目标自身绑定仓库，因此 `publish TARGET` 与
`gc TARGET` 不再接受额外的仓库选择。

## Dist 选择

`add`、`rm`、`ls` 要求明确的 Dist 集合，并按以下顺序选择：

1. 一个或多个 `-d/--dist NAME`；
2. 发现起点所在的 Dist；
3. 所选仓库中唯一的 Dist；
4. 否则退出 `2` 并列出候选项。

其他命令采用以下默认范围：

- 未指定 `-d` 时，`build`、`check`、`status` 默认作用于全部 Dist；
- `show` 默认搜索所选仓库，`-d` 只用于收窄；
- `where` 默认跨工作区搜索全部匹配 Dist，`-r`/`-d` 用于收窄；
- `changes` 作用于整个仓库，不接受 `-d`。

## 锁

`create` 锁定目标目录。Managed 写操作通过工作区锁和仓库锁协调。`init` 会等待锁，不提供命令行超时选项。

其他写命令接受 `-T/--timeout DUR` 与 `-N/--no-wait`。默认 `--timeout 0` 表示无限等待。正数时长使用 `ms`、`s`、`m` 或 `h`，例如 `500ms`、`30s`、`5m`。`--no-wait` 在锁被占用时立即失败，不能与正数超时同时使用。无法获取锁时返回 `4`。

大多数 Managed 只读命令使用共享锁，会等待冲突的写操作完成；这些命令不接受等锁选项。`status` 通常只探测仓库锁，因此可以查看正在运行的写操作。按 Ctrl-C 可以取消等待。

## 并发

只有需要解析软件包、哈希包体、渲染索引或执行校验的命令才接受 `-j/--jobs N`：`create`、
`add`、`rm`、`build`、`check` 与 `repo migrate`。默认值是逻辑 CPU 数，且不得小于 `1`。

## JSON 输出

支持 `--json` 的命令在 stdout 输出一个带版本的封装，诊断信息仍写入 stderr：

```json
{
  "schema": "sow.cli/v1",
  "command": "add",
  "ok": true,
  "repository": "demo",
  "operation": "1430722512865805553",
  "result": {},
  "errors": []
}
```

任何非零退出都会令 `ok` 为 false；部分成功的批处理仍会返回已提交项与失败项。完整结果结构见
[JSON 输出](/zh/docs/reference/json/)。

交互操作使用文本输出，脚本使用 `--json`。`config show` 默认输出 YAML。`log export` 是例外：它直接输出 JSONL，不接受 `--json`。

## 退出码

| 代码 | 含义 |
|---|---|
| `0` | 成功或幂等空操作 |
| `1` | 运行时 I/O、解析、渲染、签名或传输错误 |
| `2` | 用法、工作区发现或配置错误 |
| `3` | 批处理部分成功 |
| `4` | 写锁不可用 |
| `5` | 完整性/恢复失败，或 `check` 判定目录不可交付 |
| `6` | 操作被拒绝：冲突、受保护对象、无匹配或架构不兼容 |
| `130` | 命令被 SIGINT 或 SIGTERM 中断 |

各命令的精确触发条件见[退出码](/zh/docs/reference/exit-codes/)。
