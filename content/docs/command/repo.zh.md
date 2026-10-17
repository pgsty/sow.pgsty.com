---
title: "sow repo"
linkTitle: "repo"
description: "创建、列出、查看、迁移和删除仓库。"
categories: [Command]
tags: [cli, repository, managed]
url: "/zh/docs/command/repo/"
aliases: ["/docs/reference/cli/repo/"]
weight: 400
icon: fa-solid fa-box-archive
---

`sow repo` 用于创建、列出、查看、升级和删除仓库。每个仓库在 `pool/` 中保存包文件，在 `dists/` 中保存索引。同一仓库的 Dist 共用包文件。

## 语法

```text
sow repo ls [-C DIR] [--json]
sow repo new NAME [-C DIR] [-T DUR | -N] [--json]
sow repo show [NAME] [-C DIR] [-r NAME] [--json]
sow repo migrate [NAME] [--abort] [-j N] [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow repo rm NAME [-f|--force] [-C DIR] [-T DUR | -N] [--json]
```

## 命名

仓库名必须匹配 `[a-z0-9][a-z0-9._-]*`，且不能是 `.`、`..`、`.sow`、`pool`、`dists`，也不能与工作区
保留文件冲突。

```console
sow repo new .sow
operation rejected: managed: operation rejected: name ".sow" must match [a-z0-9][a-z0-9._-]*
```

SOW 在 `<workspace>/<NAME>/` 创建仓库。

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
| `--json` | 输出 JSON | false |

`STATUS` 取值为 `clean`、`dirty`、`recovering` 或 `error`。各状态对客户端意味着什么，见
[事务与恢复](/zh/docs/feature/transactions/)。

## sow repo new

更新 `sow.yml`，然后创建 `<workspace>/<NAME>/{pool,dists}`、SQLite 数据库与私有状态目录。新仓库
尚未构建，构建快照编号为 0，状态为 clean。

```console
sow repo new pigsty
created pigsty: path=/srv/repo/pigsty protected=false dists=0 generation=0 status=clean packages=0 memberships=0
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

用 `NAME` 指定新仓库的名称。

对已存在的仓库再次运行时，命令报告当前状态，不会创建第二个仓库。

## sow repo show

只读显示一个仓库的细节。省略 `NAME` 时按 [CLI 全局约定](/zh/docs/command/) 中的仓库选择规则
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
| `--json` | 输出 JSON | false |

同时给出 `NAME` 与 `-r` 时，使用相同名称：

```console
sow repo show demo -r empty
operation rejected: repo show NAME "demo" and --repo "empty" select different repositories
```

## sow repo migrate

从 0.3 或 0.4 工作区升级到 SOW 0.6.0 时，使用 `repo migrate`。
已使用 0.5.0 的工作区采用 schema v13，无需迁移数据库。新建的 0.6.0 仓库也使用 schema v13。

1. 停止工作区写操作。
2. 备份整个工作区，并保留硬链接。
3. 逐个迁移已配置的仓库。
4. 对每个仓库运行 `build` 与 `check`。

```bash
rsync -aH /srv/sow/ /srv/sow.backup-before-0.6.0/
sow repo migrate pigsty -C /srv/sow
sow build -r pigsty -C /srv/sow
sow check -r pigsty -C /srv/sow
```

对其他仓库重复后三条命令。迁移结果包含 `schema_from` 与 `schema_to`；重复迁移报告 `13 -> 13`。Schema v13 增加包池路径查询索引。从 v0.3 迁移时，还会应用中间版本的状态与发布记录修复。

写操作要求当前 schema。兼容的只读命令可以查看旧状态，但不会升级数据库。迁移后使用 SOW 0.5 或更新版本；需要返回旧 schema 时，恢复备份。

`--abort` 在提交决策前放弃未完成的布局迁移计划，不会撤销已完成的 schema 升级。
对于早期 C2 迁移，SOW 核对仓库身份，以及现有日志和数据库中的控制记录。
记录冲突时停止中止操作。日志已绑定迁移计划时，还必须存在其记录的基准清单。

如果既有可信迁移标记已经存在，即使首份日志或基准清单尚未写入，也可以完成中止。
SOW 保留该标记，让下一次 `sow repo migrate NAME` 能重新规划并继续迁移。
记录提交意图后，只能继续完成迁移。

SOW 将非空暂存目录完整移入 `.sow/<repo>/abandoned/`。
保留路径或清理问题会写入 stderr 和 JSON 的 `warnings`。
暂存清理告警不会阻止中止操作。确认报告路径中的文件不再需要后，再自行清理。
公开目录保持不变。

尚未启动迁移的开发期 C2 仓库仍不支持直接迁移。
如果旧版中止操作已经移除了可信标记，恢复完整的匹配备份，或将原始软件包导入新工作区。

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-j, --jobs N` | 并行校验/渲染工作线程 | 逻辑 CPU 数 |
| `--abort` | 在提交决策前放弃维护尝试 | false |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 省略 `NAME` 时选择仓库 | 选择规则 |
| `-T, --timeout DUR` | 最长锁等待；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

## sow repo rm

删除整个仓库，包括 `sow.yml` 条目、数据库、`pool/` 中的包文件、`dists/` 中的索引与私有状态。

不加 `-f` 时，只能删除空仓库——没有 Dist、没有成员关系、没有软件包对象：

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
| `-f, --force` | 删除非空的、未受保护的仓库 | false |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

### 强制删除 {#-f-到底降级了什么}

使用 `-f` 删除非空仓库。设置了 `protected: true` 的仓库仍然受到保护。

## protected

`sow.yml` 中的 `protected: true` 阻止删除仓库，包括使用 `-f` 的情况：

```console
sow repo rm alpha -f
operation rejected: managed: operation rejected: repository "alpha" is protected
```

需要删除受保护仓库时，在 `sow.yml` 中将它的 `protected` 设为 `false`。运行 [`sow config check`](/zh/docs/command/config/)，再重试删除。

`protected` 只作用于仓库删除。`add`、`rm`、`build` 与 `dist rm` 照常工作：

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

创建仓库时不等待已被占用的锁：

```bash
sow repo new nightly -N
```

逐行显示仓库名称、状态与构建快照编号：

```bash
sow repo ls --json | jq -r '.result.repositories[] | "\(.name)\t\(.status)\tgen=\(.generation)"'
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 列出、创建、显示、迁移、放弃提交前的布局转换或删除成功；或 `repo new` 报告已存在的仓库 |
| `1` | 创建或删除目录树时的运行时 I/O 错误 |
| `2` | 用法错误、工作区未找到，或仓库选择有歧义 |
| `4` | 工作区锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | 工作区日志的完整性或恢复错误 |
| `6` | 名称非法、仓库不存在、非空但未给 `-f`、`protected`，或 `NAME` 与 `-r` 冲突 |

## 参见

- [sow dist](/zh/docs/command/dist/) —— 下一层
- [Managed 工作区](/zh/docs/feature/managed/) —— 三层模型与发现规则
- [事务与恢复](/zh/docs/feature/transactions/) —— 锁作用域与 `recovering` 状态
- [sow.yml 配置参考](/zh/docs/reference/config/) —— `protected` 与仓库级签名配置
- [仓库布局](/zh/docs/reference/layout/) —— 固定目录结构
