---
title: "命令"
linkTitle: "命令"
description: "SOW CLI 的完整语法、参数、行为、输出与退出码。"
url: "/zh/docs/command/"
aliases:
  - "/docs/reference/cli/"
  - "/docs/reference/cli/query/"
  - "/docs/reference/cli/build/"
  - "/docs/reference/cli/publication/"
weight: 450
icon: fa-solid fa-terminal
---

每条顶层命令单独成页；`config`、`repo`、`dist`、`retain`、
`export`、`log` 等命令组在同一页说明其子命令。

二进制内置的 `sow help` 是语法权威。本手册在此基础上补充选择规则、状态变化、输出契约、
失败行为与可直接使用的示例。

## 命令索引

`sow create` 是 Plain 模式的仓库命令，直接作用于目录。`sow init` 用于启动 Managed 模式，
必要时会创建 `sow.yml`；其余有状态命令发现既有工作区。`help` 与 `version` 是工具命令，
不需要进入任何模式。

| 命令 | 模式 | 用途 |
|---|---|---|
| [`sow create [DIR]`](/zh/docs/command/create/) | Plain | 就地生成平面 RPM/DEB 仓库 |
| [`sow init [DIR]`](/zh/docs/command/init/) | Managed | 初始化工作区并收敛已声明的 Repository/Dist |
| [`sow config check\|show`](/zh/docs/command/config/) | Managed | 校验配置或打印有效配置 |
| [`sow repo ls\|new\|show\|migrate\|rm`](/zh/docs/command/repo/) | Managed | 管理 Repository；`migrate` 是专用维护命令 |
| [`sow dist ls\|new\|show\|rm`](/zh/docs/command/dist/) | Managed | 管理 Dist |
| [`sow add PATH...`](/zh/docs/command/add/) | Managed | 将软件包加入期望成员集 |
| [`sow rm PACKAGE...`](/zh/docs/command/rm/) | Managed | 从期望成员集中移除软件包 |
| [`sow ls`](/zh/docs/command/ls/) | Managed | 列出期望成员与已构建成员 |
| [`sow show PACKAGE`](/zh/docs/command/show/) | Managed | 查看一个 Package Object |
| [`sow where PACKAGE`](/zh/docs/command/where/) | Managed | 在整个工作区定位 Package Object |
| [`sow status`](/zh/docs/command/status/) | Managed | 快速读取 Repository 状态 |
| [`sow build`](/zh/docs/command/build/) | Managed | 将 Desired 状态收敛为 Built Generation |
| [`sow check`](/zh/docs/command/check/) | Managed | 校验配置、状态、包体、视图、签名与清单 |
| [`sow changes [BASE_GENERATION]`](/zh/docs/command/changes/) | Managed | 将 Generation 差异输出为文件交付计划 |
| [`sow publish TARGET`](/zh/docs/command/publish/) | Managed | 将已验证 Generation 发布到配置目标 |
| [`sow retain add\|ls\|rm`](/zh/docs/command/retain/) | Managed | 管理显式保留的 Generation 根 |
| [`sow gc [TARGET]`](/zh/docs/command/gc/) | Managed | 回收本地不可达包体，或维护发布目标 |
| [`sow export rpm-leaf`](/zh/docs/command/export/) | Managed | 生成独立的 RPM 兼容 leaf |
| [`sow log [OPERATION]`](/zh/docs/command/log/) | Managed | 查询、导出与裁剪 Operation 审计账本 |

## 全局语法

```text
sow [OPTIONS] COMMAND [ARGS]
```

不带参数运行 `sow` 会打印命令列表并退出 `0`。用 `sow help COMMAND` 或
`sow help COMMAND SUBCOMMAND` 查看内置帮助。`sow version` 与 `sow --version` 打印二进制身份。

SOW 没有全局 `--format`、`--yes`、`--dry-run`、`-q`、`-v` 或 `--config`。未知参数直接按
用法错误处理。

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

需要唯一 Repository 的命令按以下顺序选择：

1. 显式 `-r/--repo NAME`；
2. 发现起点所在的 Repository；
3. 工作区中唯一的 Repository；
4. 否则退出 `2` 并列出候选项。

`repo new` 与 `repo rm` 用位置参数接收 `NAME`，不接受 `-r`。`sow where` 默认搜索所有
Repository，`-r` 只用于收窄范围。发布目标自身绑定 Repository，因此 `publish TARGET` 与
`gc TARGET` 不再接受额外的 Repository 选择。

## Dist 选择

`add`、`rm`、`ls` 要求明确的 Dist 集合，并按以下顺序选择：

1. 一个或多个 `-d/--dist NAME`；
2. 发现起点所在的 Dist；
3. 所选 Repository 中唯一的 Dist；
4. 否则退出 `2` 并列出候选项。

其他命令有意采用不同规则：

- 未指定 `-d` 时，`build`、`check`、`status` 默认作用于全部 Dist；
- `show` 默认搜索所选 Repository，`-d` 只用于收窄；
- `where` 默认跨工作区搜索全部匹配 Dist，`-r`/`-d` 用于收窄；
- `changes` 作用于整个 Repository，明确拒绝 `-d`。

## 锁

除 `init` 外，写命令接受 `-T/--timeout DUR` 与 `-N/--no-wait`。`init` 获取 Workspace 锁，且不提供
命令行超时覆盖；其他锁均为 Repository 级，但 `repo new` 与 `repo rm` 同样使用 Workspace 锁。
`--timeout 0` 表示无限等待；正数使用 Go duration，例如 `500ms`、`30s`、`5m`。`--no-wait`
立即失败；它与正数 timeout 互斥。获取锁失败退出 `4`。

只读命令不获取写锁；`status` 仍会报告 Repository 是否正被写者持锁。

## 并发

只有需要解析软件包、哈希包体、渲染索引或执行校验的命令才接受 `-j/--jobs N`：`create`、
`add`、`rm`、`build`、`check` 与 `repo migrate`。默认值是逻辑 CPU 数，且不得小于 `1`。

## JSON 输出

支持 `--json` 的命令在 stdout 输出一个带版本的 Envelope，诊断信息仍写入 stderr：

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

部分命令在不带 `--json` 时也会输出命令专用结构化 JSON，避免把复杂结果压扁丢失信息。各命令页
会明确说明；`--json` 始终选择标准 Envelope。

## 退出码

| 代码 | 含义 |
|---|---|
| `0` | 成功或幂等空操作 |
| `1` | 运行时 I/O、解析、渲染、签名或传输错误 |
| `2` | 用法、工作区发现或配置错误 |
| `3` | 批处理部分成功 |
| `4` | 写锁不可用 |
| `5` | 完整性/恢复失败，或 `check` 判定目录不可交付 |
| `6` | 可预期拒绝：冲突、受保护对象、无匹配或架构不兼容 |

各命令的精确触发条件见[退出码](/zh/docs/reference/exit-codes/)。
