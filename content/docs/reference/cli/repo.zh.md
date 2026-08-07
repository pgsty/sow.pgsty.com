---
title: "sow repo"
linkTitle: "sow repo"
description: "列出、创建、查看与删除仓库 —— 锁、事务与 Generation 的边界。"
url: "/zh/docs/reference/cli/repo/"
weight: 400
icon: fa-solid fa-box-archive
---

一个仓库（Repository）独占一份 `pool/`、一份 `dists/`、一个 SQLite 数据库与一个私有状态目录。它是
锁、事务恢复、Generation 编号与 Changeset 的边界——跨仓库不去重，也不承诺跨仓库原子提交。
`sow repo` 管理的就是这条边界。

## 语法

```text
sow repo ls [-C DIR] [--json]
sow repo new NAME [-C DIR] [-T DUR | -N] [--json]
sow repo show [NAME] [-C DIR] [-r NAME] [--json]
sow repo rm NAME [-f|--force] [-C DIR] [-T DUR | -N] [--json]
```

## 命名

仓库名必须匹配 `[a-z0-9][a-z0-9._-]*`，且不能是 `.`、`..`、`.sow`、`pool`、`dists`，也不能与工作区
保留文件冲突。

```console
sow repo new .sow
operation rejected: managed: operation rejected: name ".sow" must match [a-z0-9][a-z0-9._-]*
```

路径不可指定。仓库永远位于 `<workspace>/<NAME>/`。

## sow repo ls

只读列出工作区里的全部仓库。

```console
sow repo ls
NAME	PROTECTED	DISTS	GENERATION	STATUS	PACKAGES	MEMBERSHIPS
infra	true	1	1	clean	0	0
pgsql	false	2	2	clean	0	0
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `--json` | 输出版本化 JSON envelope | false |

`STATUS` 取值为 `clean`、`dirty`、`recovering` 或 `error`。各状态对客户端意味着什么，见
[事务与恢复](/zh/docs/feature/transactions/)。

## sow repo new

原子更新 `sow.yml`，然后创建 `<workspace>/<NAME>/{pool,dists}`、SQLite 数据库与私有状态目录。新仓库
处于 Generation 0、clean 状态。

```console
sow repo new pigsty
created pigsty: path=/srv/repo/pigsty protected=false dists=0 generation=0 status=clean packages=0 memberships=0
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出版本化 JSON envelope | false |

`repo new` 取的是工作区锁而不是仓库锁——此时仓库数据库还不存在。它不接受 `-r`，位置参数已经指明了
目标。

对已存在的仓库再跑一次是收敛型 no-op，只报告当前状态，因此在 provisioning 脚本里是安全的。

## sow repo show

只读显示一个仓库的细节。省略 `NAME` 时按 [CLI 全局约定](/zh/docs/reference/cli/) 中的仓库选择规则
解析。

```console
sow repo show pigsty
repository pigsty:
  path: /srv/repo/pigsty
  protected: false
  dists: 2
  generation: 6
  desired_revision: 6
  status: clean
  packages: 5
  memberships: 8
  config: {"protected":false,"signing":{"rpm":{"packages":{"mode":"never"}}},"dists":{"el9":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":1,"exclude":[{"kind":["debuginfo","debugsource"]}]},"trixie":{"format":"deb","architectures":["x86_64","aarch64"],"limit":0,"exclude":null}}}
  dirty_reasons: []
  recent_operation: id=4142220455201181493 kind=add state=done error_class= created_at=2026-08-04T04:09:24.995538Z updated_at=2026-08-04T04:09:25.332772Z
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 省略 `NAME` 时用它选择仓库 | 按选择规则 |
| `--json` | 输出版本化 JSON envelope | false |

同时给出 `NAME` 与 `-r` 时两者必须一致；不一致会在读取任何状态前失败：

```console
sow repo show demo -r empty
operation rejected: repo show NAME "demo" and --repo "empty" select different repositories
```

## sow repo rm

删除一个仓库：它在 `sow.yml` 中的条目、数据库、`pool/`、`dists/` 与私有状态。绝不跟随符号链接，
也绝不越出固定的仓库路径。

不加 `-f` 时，只能删除空仓库——没有 Dist、没有 Membership、没有 Package Object：

```console
sow repo rm infra
removed repository infra
```

```console
sow repo rm pgsql
operation rejected: managed: operation rejected: repository "pgsql" is not empty; use --force
```

```console
sow repo rm pgsql -f
removed repository pgsql
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-f, --force` | 删除非空的、未 protected 的仓库 | false |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出版本化 JSON envelope | false |

### -f 到底降级了什么

`-f` 只放宽*为空*这一个前置条件。它不绕过路径安全检查、不绕过符号链接拒绝、也不绕过 `protected`
门禁。

## protected

`sow.yml` 中的 `protected: true` 直接封死仓库删除，加 `-f` 也不行：

```console
sow repo rm alpha -f
operation rejected: managed: operation rejected: repository "alpha" is protected
```

要删除受保护的仓库，必须先改 `sow.yml`，通过
[`sow config check`](/zh/docs/reference/cli/config/)，再重试。没有 `--yes`，也没有临时覆盖开关。

`protected` 只作用于仓库删除。受保护仓库上的包级操作不受影响——`add`、`rm`、`build`，乃至
`dist rm` 都照常工作：

```console
sow dist rm el9 -r alpha -f
removed dist el9 from alpha
```

## 示例

为两层结构创建仓库：

```bash
sow repo new infra
sow repo new pgsql
```

在 cron 任务中快速失败，而不是排队等另一个写者：

```bash
sow repo new nightly -N || echo "另一个写者持有工作区锁"
```

一行一个仓库地做审计：

```bash
sow repo ls --json | jq -r '.result.repositories[] | "\(.name)\t\(.status)\tgen=\(.generation)"'
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 列出、创建、显示或删除成功；或 `repo new` 收敛了已存在的仓库 |
| `1` | 创建或删除目录树时的运行时 I/O 错误 |
| `2` | 用法错误、工作区未找到，或仓库选择有歧义 |
| `4` | 工作区锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | 工作区 journal 的完整性或恢复错误 |
| `6` | 名称非法、仓库不存在、非空但未给 `-f`、`protected`，或 `NAME` 与 `-r` 冲突 |

## 参见

- [sow dist](/zh/docs/reference/cli/dist/) —— 下一层
- [Managed 工作区](/zh/docs/feature/managed/) —— 三层模型与发现规则
- [事务与恢复](/zh/docs/feature/transactions/) —— 锁作用域与 `recovering` 状态
- [sow.yml 配置参考](/zh/docs/reference/config/) —— `protected` 与仓库级签名配置
- [仓库布局](/zh/docs/reference/layout/) —— 固定目录结构
