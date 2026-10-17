---
title: "sow log"
linkTitle: "log"
description: "查看、导出和裁剪操作记录。"
categories: [Command]
tags: [cli, audit]
url: "/zh/docs/command/log/"
aliases: ["/docs/reference/cli/log/"]
weight: 1900
icon: fa-solid fa-clipboard-list
---

`sow log` 列出仓库操作记录，并查看单次操作的详情。使用 `log export` 将已结束的操作导出为 JSONL，使用 `log prune` 从数据库中删除符合条件的旧记录。

## 语法

```text
sow log [OPERATION] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME] [--json]
sow log export [FILE] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]
sow log prune BEFORE [-C|--workdir DIR] [-r|--repo NAME] [-T|--timeout DUR | -N|--no-wait] [--json]
```

## sow log

不带参数时，按由新到旧打印最近 50 条操作记录。

```console
sow log -r pigsty --json
```

输出节选，`operations` 数组中的一个操作记录对象：

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

`payload_json` 记录意图——包括当时生效配置的摘要 `config_sha256`，以及生成的构建快照的
`manifest_sha256`。`result_json` 记录结果。失败的操作记录还会带 `error_class` 与
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
| `-d, --dist NAME` | 只显示触及该 Dist 的操作记录 | 全部 |
| `--json` | 输出 JSON | false |

### 查看单条 Operation

传入操作记录 ID 查看摘要。加上 `--json` 后，可在 `result.detail` 中读取完整状态变化、耗时、软件包、成员与文件记录。

```console
sow log 4262183287563704350 -r pigsty --json
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

Build 操作记录还会包含进度事件。它们保持当前 state，并把版本化对象放入 `detail_json`：

```json
{
  "state": "applied",
  "detail_json": "{\"version\":1,\"kind\":\"build_progress\",\"phase\":\"rendering\",\"completed\":1,\"total\":2,\"jobs\":8}"
}
```

阶段包括 `rendering`、`promoting_payload`、`publishing_dists`、`normalizing_public_tree` 与 `finalizing`。可用这些记录查看长时间构建的进度。

新的元数据构建操作还会在 `payload_json` 中记录 `publication_time`。
该字段是精确到秒的 UTC 时间戳，恢复时用于生成相同时间的元数据与签名。
旧日志与布局迁移可能没有此字段。

### 按 Dist 过滤

`-d` 把列表限制为触及该 Dist 的操作记录——一个仓库服务多个发行版时很有用：

```bash
sow log -d trixie -r pigsty
```

## 操作状态 {#operation-生命周期}

`state` 字段表示操作进行到哪一步：

```text
planned → staged → applied → built → done
                        └────────→ done_dirty
   any nonterminal → recovering → built / done / done_dirty / rolled_back / failed
   pre-apply error  → failed
```

| 状态 | 含义 |
|---|---|
| `planned` | 命令、参数、目标与预期动作已持久化 |
| `staged` | 新包/元数据已写入临时位置并校验通过 |
| `applied` | 期望状态与所需的私有待构建包文件已提交 |
| `built` | 已切换到新构建快照 |
| `done` | 终态——一次正常成功的命令 |
| `done_dirty` | 操作已结束，仍有变化需要构建，通常出现在 `--skip` 之后 |
| `failed` | 终态——在 `applied` 之前失败，什么都没提交 |
| `rolled_back` | 终态——恢复在操作记录改变 Desired 之前放弃了它，例如被中断命令留下的 `planned` 操作记录 |
| `recovering` | 非终态；下一条写命令必须先完成或回滚它 |

仓库日志包含 `dist new` 和 `dist rm`。工作区操作 `init`、`repo new`、`repo rm` 使用独立的恢复记录，不出现在这里。

## sow log export

将已结束的操作导出为 JSONL，每行包含一次操作的完整记录，可用于归档或日志分析。

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
| `-d, --dist NAME` | 只导出触及该 Dist 的操作记录 | 全部 |

`export` 直接输出 JSONL，不接受 `--json`。

### 输出路径 {#它拒绝覆盖}

在已有目录中选择一个新文件名。文件已存在时，`log export` 返回 `6`。直接父目录必须是真实目录，不能是符号链接。在 macOS 上使用 `/private/tmp/file.jsonl`，不要使用 `/tmp/file.jsonl`。

## sow log prune

删除早于 `BEFORE` 且符合条件的已结束操作记录，并回收数据库空间。如果其他读连接正在使用数据库，记录可以先删除，空间回收会延后。此时结果显示 `compaction_deferred: true`。关闭读连接后，再运行 `prune` 回收空间。

```console
sow log prune 2027-01-01 -r pigsty
pruned log repository=pigsty operation=8150803833883584722 before=2026-12-31T16:00:00.000000000Z operations=1
```

输出以 UTC 显示截止时间（此处工作站时区为 UTC+8）。若有读者使空间回收
被推迟，输出会多一行 `log deletion committed; space reclamation deferred while the database is busy`；
使用 `--json` 时，日志 ID 与 `compaction_deferred` 位于 `result` 中。

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

`prune` 作用于整个仓库，不接受 `-d`。

### BEFORE 语法

`BEFORE` 是 ISO-8601 日期 `YYYY-MM-DD`（按本地时区零点解释），或带时区的 RFC 3339 时间戳。

```console
sow log prune yesterday -r pigsty
usage error: BEFORE must be YYYY-MM-DD or an RFC 3339 timestamp with timezone
```

### prune 保留的记录 {#prune-永不删除什么}

`prune` 保留以下记录：

- 非终态的操作记录；
- 当前恢复仍需要的记录；
- 当前的软件包或成员状态；
- 构建快照及其文件差异记录。

`pruned` 显示已删除的操作记录数。

## 示例

排查最近一次写入：

```bash
sow log -r pgsql --json | jq -r '.result.operations[0] | "\(.id)\t\(.kind)\t\(.state)"'
```

从最近 50 条记录中筛选失败的操作：

```bash
sow log -r pgsql --json | jq -r '.result.operations[] | select(.state=="failed") | "\(.id)\t\(.error_class)\t\(.error_message)"'
```

归档记录，再删除指定日期之前的旧记录：

```bash
sow log export /srv/audit/pgsql-$(date +%Y%m).jsonl -r pgsql
sow log prune 2026-05-01 -r pgsql
```

查看最后修改某个 Dist 的操作：

```bash
sow log -d el9 -r pgsql --json | jq -r '.result.operations[0].id'
```

## 退出码

| 命令 | 码 | 触发条件 |
|---|---|---|
| `log` | `0` | 记录已打印，包括空账本 |
| `log` | `2` | 用法错误（包括非数字的操作记录 ID）、工作区未找到，或选择有歧义 |
| `log` | `5` | 状态数据库不可读 |
| `log` | `6` | 给定的操作记录 ID 不存在，或给出了多个不同的 `-d` |
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
- [事务与恢复](/zh/docs/feature/transactions/) —— 中断后的恢复过程
- [sow changes](/zh/docs/command/changes/) —— 比较构建前后的文件差异
- [JSON 输出](/zh/docs/reference/json/) —— 完整的日志结果结构
