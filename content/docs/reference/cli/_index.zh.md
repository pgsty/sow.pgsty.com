---
title: "命令行参考"
linkTitle: "命令行"
description: "全部 sow 命令的完整参考，以及所有命令共享的全局约定。"
url: "/zh/docs/reference/cli/"
weight: 100
icon: fa-solid fa-terminal
---

本板块逐条记录 `sow` 的每个子命令：语法、参数、行为、真实转录与退出码。这一页讲清楚它们共有的部分
——工作区（Workspace）怎么发现、仓库（Repository）与 Dist 怎么选、锁怎么工作、`--json` 输出什么
——各命令页不再重复。

## 命令总表

`sow` 只有两条互相隔离的执行路径。`sow create` 是 Plain 平面模式：没有工作区、没有配置文件、没有
数据库。其余命令都是 Managed 托管模式，运行在一个工作区中。

| 命令 | 模式 | 用途 |
|---|---|---|
| [`sow create [DIR]`](/zh/docs/reference/cli/create/) | Plain | 就地生成平面 RPM/DEB 仓库 |
| [`sow init [DIR]`](/zh/docs/reference/cli/init/) | Managed | 初始化工作区，并收敛配置中声明的 Repository/Dist |
| [`sow config check`](/zh/docs/reference/cli/config/) | Managed | 只读校验 `sow.yml` |
| [`sow config show`](/zh/docs/reference/cli/config/) | Managed | 打印有效配置 |
| [`sow repo ls\|new\|show\|rm`](/zh/docs/reference/cli/repo/) | Managed | 管理仓库 |
| [`sow dist ls\|new\|show\|rm`](/zh/docs/reference/cli/dist/) | Managed | 管理 Dist |
| [`sow add PATH...`](/zh/docs/reference/cli/add/) | Managed | 把包加入期望成员集 |
| [`sow rm PACKAGE...`](/zh/docs/reference/cli/rm/) | Managed | 移除期望成员集 |
| [`sow ls` / `show` / `where`](/zh/docs/reference/cli/query/) | Managed | 查询成员、定位包 |
| [`sow build` / `status` / `check` / `changes`](/zh/docs/reference/cli/build/) | Managed | 收敛、观察、校验与差分 |
| [`sow log` / `log export` / `log prune`](/zh/docs/reference/cli/log/) | Managed | 操作审计账本 |

## 全局语法

```bash
sow [OPTIONS] COMMAND [ARGS]
```

不带参数运行 `sow` 会打印命令列表并退出 `0`。`sow help COMMAND` 与 `sow help COMMAND SUBCOMMAND`
打印各命令用法。`sow version` 与 `sow --version` 打印二进制身份：

```console
sow version
sow 0.2.0-dev darwin/arm64 go1.26.5
```

没有全局 `--format`、`--yes`、`--dry-run`、`-q/-v` 或 `--config`。未知参数一律报用法错误，绝不静默
忽略。

## 工作区发现

Managed 命令按以下顺序，向上寻找最近一个含 `sow.yml` 的祖先目录：

1. `-C/--workdir DIR` —— 从 `DIR` 开始向上查找。
2. 否则从当前工作目录开始。
3. 前两者都没找到，则从环境变量 `SOW_DIR` 指向的目录开始。
4. 仍然没有：以退出码 `2` 失败。

找到第一个 `sow.yml` 即停止，不会越过该工作区继续向上。

`--workdir` 只改变*发现的起始目录*，不执行 `chdir`。因此命令中的相对 `PATH`、`DIR`、`FILE` 仍然
相对你真实的当前目录解析。

```console
sow status
workspace discovery error: managed: workspace discovery or configuration error: workspace not found (searched cwd="/home/vonng"); run sow init or set --workdir/SOW_DIR
```

`sow create` 完全不参与发现算法。

## 仓库选择

需要一个仓库的命令按以下顺序解析：

1. 显式 `-r/--repo NAME`。
2. 起始目录位于 `<workspace>/<repo>/` 内。
3. 工作区恰好只有一个仓库。
4. 否则以退出码 `2` 失败并列出候选。

```console
sow status
workspace discovery error: managed: workspace discovery or configuration error: workspace has multiple repositories (infra, pgsql); select one with --repo
```

`repo new` 与 `repo rm` 用位置参数指定名称，不接受 `-r`。`sow where` 默认搜索全部仓库，`-r` 只用于
收窄范围。

## Dist 选择

需要一个或多个 Dist 的命令按以下顺序解析：

1. 一个或多个显式 `-d/--dist NAME`（该参数可重复）。
2. 起始目录位于 `<workspace>/<repo>/dists/<dist>/` 内。
3. 选定仓库恰好只有一个 Dist。
4. 否则以退出码 `2` 失败并列出候选。

`build`、`check`、`status` 在没有 `-d` 时默认作用于选定仓库的*全部* Dist；`add`、`rm`、`ls` 必须
得到明确的 Dist 集合：

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

`sow changes` 作用于整个仓库的 Generation，直接拒绝 `-d`。

## 锁

所有会取写锁的命令都接受 `-T/--timeout DUR` 与 `-N/--no-wait`。锁的作用域是仓库——`init`、
`repo new`、`repo rm` 例外，它们锁的是工作区。

| 参数 | 默认 | 含义 |
|---|---|---|
| `-T, --timeout DUR` | `0` | 等待锁的最长时间；`0` 表示无限等待。Go duration 语法（`500ms`、`30s`、`5m`、`1h`）。 |
| `-N, --no-wait` | false | 锁被占用时立即失败。 |

当 `--timeout` 非零时两者互斥。取锁失败退出 `4`：

```console
sow build -N
lock unavailable: managed: lock unavailable
```

只读命令从不取写锁。`sow status` 仍会报告锁状态，并在他人写入期间把仓库标为不可复制：

```console
sow status
repository=pigsty status=clean ready_to_copy=false revision=6 generation=6 dirty_dists= pending=0/0 locked=true
```

## 并发

`-j/--jobs N` 只出现在真正解析包、计算哈希、渲染索引或校验的命令上：`create`、`add`、`rm`、
`build`、`check`。默认取逻辑 CPU 数，最小值为 `1`。

```console
sow check -j 0
usage error: --jobs must be an integer greater than or equal to 1
```

并发不改变输出顺序、选择结果、版本比较与 Changeset 内容。

## JSON 输出

`--json` 在 stdout 输出一个版本化 envelope，人类可读的诊断信息仍走 stderr。

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

退出码非零时 `ok` 为 false，但 `result` 依然完整——部分成功的批次会同时列出所有已提交项与所有失败
项。`errors[]` 每项带 `code`、`class` 与 `message`：

```json
{"code": 3, "class": "partial", "message": "managed: batch partially succeeded"}
```

各命令的 result 结构见 [JSON 输出](/zh/docs/reference/json/)。

有三个命令即使*不加* `--json` 也在 stdout 打印结构化 JSON，因为它们的结果没有紧凑的表格形态：
`sow build`、`sow rm`、`sow show`。加上 `--json` 则套上标准 envelope。

## 退出码

| 码 | 含义 |
|---|---|
| `0` | 成功或幂等 no-op |
| `1` | 运行时 I/O、解析器、渲染器或签名错误 |
| `2` | 用法、工作区发现或配置错误 |
| `3` | 部分成功——至少一项已提交，至少一项失败 |
| `4` | 写锁不可用（`--no-wait` 或等待超时） |
| `5` | 完整性/恢复错误，或 `check` 判定当前结果不可交付 |
| `6` | 预期拒绝——冲突、protected、无匹配、架构不兼容 |

完整的触发条件与转录见 [退出码](/zh/docs/reference/exit-codes/)。
