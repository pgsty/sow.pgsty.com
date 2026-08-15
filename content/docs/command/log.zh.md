---
title: "sow log"
linkTitle: "log"
description: "读取操作审计账本、导出为 JSONL，并清理符合条件的终态记录。"
url: "/zh/docs/command/log/"
aliases: ["/docs/reference/cli/log/"]
weight: 1900
icon: fa-solid fa-clipboard-list
---

仓库内的每条写命令，都会*先*在该仓库的 SQLite 中提交一条应用级 Operation，然后才产生任何外部文件
副作用。这条记录让崩溃恢复成为可能——而当 Operation 进入终态之后，同一条记录就是你的审计轨迹。
`sow log` 读的就是它。

## 语法

```text
sow log [OPERATION] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME] [--json]
sow log export [FILE] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]
sow log prune BEFORE [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

## Operation 生命周期

读懂 `state` 字段，日志就读懂了一大半：

```text
planned → staged → applied → built → done
                        └────────→ done_dirty
   any nonterminal → recovering → built / rolled_back
   pre-apply error  → failed
```

| 状态 | 含义 |
|---|---|
| `planned` | 命令、参数、目标与预期动作已持久化 |
| `staged` | 新包/元数据已写入临时位置并校验通过 |
| `applied` | 期望状态与所需的私有 pending 载荷已提交 |
| `built` | 完整的静态 Generation 已切换 |
| `done` | 终态——一次正常成功的命令 |
| `done_dirty` | 终态——给了 `--skip`，公开树被有意保留在旧代 |
| `failed` | 终态——在 `applied` 之前失败，什么都没提交 |
| `rolled_back` | 终态——`applied` 之后失败，但进程安全地回滚了 |
| `recovering` | 非终态；下一条写命令必须先完成或回滚它 |

工作区生命周期命令（`init`、`repo new`、`repo rm`）走的是工作区文件 journal，不会出现在仓库的
SQLite 日志中。`dist new`/`dist rm` 会出现——那时仓库数据库已经存在。

## sow log

不带参数时，按由新到旧打印最近 50 条 Operation。

```console
sow log -r pigsty
```

输出节选，`operations` 数组中的一个 Operation 对象：

```json
{
  "id": "4262183287563704350",
  "kind": "build",
  "state": "done",
  "payload_json": "{\"version\":2,\"repository\":\"pigsty\",\"kind\":\"build\",\"config_sha256\":\"37eb6dcf...\",\"skip\":false,\"dists\":[\"el9\"],\"build_dists\":[\"el9\"],\"manifest_sha256\":\"678beeae...\"}",
  "result_json": "{\"dists\":1,\"dropped_pending\":[]}",
  "created_at": "2026-08-04T04:07:40.334787Z",
  "updated_at": "2026-08-04T04:07:40.907125Z"
}
```

`payload_json` 记录意图——包括当时生效配置的摘要 `config_sha256`，以及结果 Generation 的
`manifest_sha256`。`result_json` 记录结果。失败的 Operation 还会带 `error_class` 与
`error_message`：

```json
{
  "id": "5995346754219751025",
  "kind": "add",
  "state": "failed",
  "result_json": "{\"accepted\":0,\"failed\":1}",
  "error_class": "rejected",
  "error_message": "no input package was accepted"
}
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 只显示触及该 Dist 的 Operation | 全部 |
| `--json` | 输出版本化 JSON envelope | false |

### 查看单条 Operation

给出 Operation ID，就能得到它的完整状态迁移、耗时、包、成员与文件动作。

```console
sow log 4262183287563704350 -r pigsty
```

输出节选：

```json
{
  "duration_ms": 572,
  "events": [
    {"sequence": 0, "state": "planned",  "occurred_at": "2026-08-04T04:07:40.334787Z"},
    {"sequence": 1, "state": "staged",   "occurred_at": "2026-08-04T04:07:40.380963Z"},
    {"sequence": 2, "state": "applied",  "occurred_at": "2026-08-04T04:07:40.386186Z"},
    {"sequence": 3, "state": "built",    "occurred_at": "2026-08-04T04:07:40.904730Z"},
    {"sequence": 4, "state": "done",     "occurred_at": "2026-08-04T04:07:40.907125Z"}
  ],
  "packages": [],
  "memberships": [],
  "files": [
    {"sequence": 0, "action": "update", "phase": "pointer", "path": "dists/el9/aarch64/repodata/repomd.xml", "size": 1511, "sha256": "ef071821e06c9e86ab4f6d2a56906d82bb66df251e79d1086cfd44dc8395513e"},
    {"sequence": 1, "action": "update", "phase": "pointer", "path": "dists/el9/x86_64/repodata/repomd.xml",  "size": 1514, "sha256": "a31e90ec39169f0373b108458908333c96c5f600f3c63a50c44257856f0d2d55"}
  ]
}
```

`files` 数组使用与 [`sow changes`](/zh/docs/command/changes/) 相同的 `phase` 词表：`payload`、
`metadata`、`pointer`、`delete`。

### 按 Dist 过滤

`-d` 把列表限制为触及该 Dist 的 Operation——一个仓库服务多个发行版时很有用：

```bash
sow log -d trixie -r pigsty
```

## sow log export

把终态 Operation 以 JSONL 写出——每行一条完整的 Operation 明细记录——用于归档或送入日志管道。

```console
sow log export /srv/audit/pigsty-ops.jsonl -r pigsty
exported 12 operations to /srv/audit/pigsty-ops.jsonl
```

省略 `FILE` 或传 `-` 则写到 stdout：

```bash
sow log export - -r pigsty | gzip > pigsty-ops-$(date +%F).jsonl.gz
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 只导出触及该 Dist 的 Operation | 全部 |

`export` 没有 `--json`——JSONL *就是*它的输出格式。

### 它拒绝覆盖

目标已存在属于拒绝，绝不覆盖——审计导出不能静默毁掉上一份：

```console
sow log export /srv/audit/pigsty-ops.jsonl -r pigsty
operation rejected: export target already exists: /srv/audit/pigsty-ops.jsonl
```

`export` 同样拒绝父目录不是真实目录的目标——符号链接，或根本不存在的目录：

```console
sow log export /tmp/pigsty-ops.jsonl -r pigsty
log export parent is not a real directory
```

macOS 上 `/tmp` 是指向 `/private/tmp` 的符号链接，所以在那里会触发这条拒绝。请写到明确的真实路径。

## sow log prune

删除早于 `BEFORE` 且符合条件的终态审计记录，并安全压缩数据库。

```console
sow log prune 2027-01-01 -r pigsty
{"operation":"8150803833883584722","repository":"pigsty","before":"2027-01-01T00:00:00+08:00","pruned":1}
```

绝对时间戳会被回显，这样本地时区的解释永远不含糊。

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出版本化 JSON envelope | false |

`prune` 在仓库级工作，不接受 `-d`——清掉半条 Operation 只会留下毫无意义的记录。

### BEFORE 语法

`BEFORE` 是 ISO-8601 日期 `YYYY-MM-DD`（按本地时区零点解释），或带时区的 RFC 3339 时间戳。

```console
sow log prune yesterday -r pigsty
usage error: BEFORE must be YYYY-MM-DD or an RFC 3339 timestamp with timezone
```

### prune 永不删除什么

`prune` 在设计上是保守的。它绝不会删除：

- 非终态的 Operation；
- 当前恢复仍需要的记录；
- 当前的 Package 或 Membership 状态；
- Built Generation 或其 Changeset。

`pruned` 计数准确告诉你有多少条记录符合条件——通常少于截止时间之前的 Operation 总数。本版本中日志与
Changeset 位于同一个 SQLite 数据库，但保留规则不同。

## 示例

排查最近一次写入：

```bash
sow log -r pgsql --json | jq -r '.result.operations[0] | "\(.id)\t\(.kind)\t\(.state)"'
```

列出所有失败：

```bash
sow log -r pgsql --json | jq -r '.result.operations[] | select(.state=="failed") | "\(.id)\t\(.error_class)\t\(.error_message)"'
```

每月归档并收缩：

```bash
sow log export /srv/audit/pgsql-$(date +%Y%m).jsonl -r pgsql
sow log prune 2026-05-01 -r pgsql
```

哪条 Operation 最后触碰了某个 Dist：

```bash
sow log -d el9 -r pgsql --json | jq -r '.result.operations[0].id'
```

## 退出码

| 命令 | 码 | 触发条件 |
|---|---|---|
| `log` | `0` | 记录已打印，包括空账本 |
| `log` | `2` | 用法错误（包括非数字的 Operation ID）、工作区未找到，或选择有歧义 |
| `log` | `5` | 状态数据库不可读 |
| `log` | `6` | 给定的 Operation ID 不存在 |
| `log export` | `0` | 导出成功 |
| `log export` | `1` | 写目标时 I/O 失败，或父目录不是真实目录 |
| `log export` | `2` | 用法错误或选择有歧义 |
| `log export` | `6` | 目标已存在 |
| `log prune` | `0` | 清理完成，包括一条都没清 |
| `log prune` | `2` | `BEFORE` 格式非法、给了 `-d`，或选择有歧义 |
| `log prune` | `4` | 仓库锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `log prune` | `5` | 完整性或恢复错误 |

## 参见

- [可观测与审计](/zh/docs/feature/audit/) —— `log` 与 `status`、`check`、`changes` 的配合
- [事务与恢复](/zh/docs/feature/transactions/) —— 日志所记录的那个 journal
- [sow changes](/zh/docs/command/changes/) —— 语义 Operation 的物理对照物
- [JSON 输出](/zh/docs/reference/json/) —— 完整的 log result 结构
