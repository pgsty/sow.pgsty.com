---
title: "JSON 输出"
linkTitle: "JSON 输出"
description: "查阅 JSON 响应字段、包与操作标识、错误和各命令结果。"
categories: [Reference]
tags: [cli, output, json]
url: "/zh/docs/reference/json/"
weight: 600
icon: fa-solid fa-code
---

<span id="stdout-与-stderr"></span>

数据命令使用 `--json` 后，会向 stdout 输出一个以换行结束的 JSON 文档，诊断写入 stderr。
`log export` 例外：它输出 JSON Lines，不接受 `--json`。

```bash
sow status -r demo --json | jq '.result.status'
```

<span id="信封结构"></span>

## 顶层封装

每个 JSON 响应都有七个字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `schema` | 字符串 | `sow.cli/v1` |
| `command` | 字符串 | 包含子命令的名称，如 `repo ls` |
| `ok` | 布尔值 | 命令成功；存在错误时为 `false` |
| `repository` | 字符串或 null | 响应关联的所选仓库 |
| `operation` | 字符串或 null | 命令对应的操作或发布身份 |
| `result` | 对象或 null | 命令数据；失败时也可包含有用的部分结果或诊断 |
| `errors` | 数组 | 包含 `code`、`class`、`message` 的错误对象 |

配置检查成功的示例：

```json
{
  "schema": "sow.cli/v1",
  "command": "config check",
  "ok": true,
  "repository": null,
  "operation": null,
  "result": {"workspace": "/srv/repo", "repositories": 1, "dists": 2},
  "errors": []
}
```

实际输出只有一行，路径和计数随工作区变化。没有产生有意义结果就失败时，通常为
`result: null`。失败的 `check` 和部分成功的 `add` 仍可返回有用结果；
`ok` 为 false 时也应保留它们。

<span id="errors"></span>

### 错误

```json
{"code":3,"class":"partial","message":"managed: batch partially succeeded"}
```

按 `code` 或 `class` 判断，不解析消息文本。分类有 `runtime`、`usage`、`discovery`、
`config`、`partial`、`lock`、`integrity`、`rejected`、`interrupted`。
分类对应关系和下一步见[退出码](/zh/docs/reference/exit-codes/)。

<span id="operation-id-是字符串"></span>
<span id="generation-id-是固定宽度字符串"></span>

### 身份标识

操作 ID 与构建快照 ID 保持字符串类型。操作 ID 可能超出 JavaScript 精确整数范围。
构建快照 ID 是补零至 20 位的十进制字符串：

```json
{"operation":"8632724976452398569","built_generation":"00000000000000000004"}
```

此规则适用于 `generation`、`built_generation`、`base_generation` 和表示构建快照的 `base`。
期望状态修订号和计数仍是 JSON 数字。

顶层 `operation` 的取值如下：

| 命令 | 值 |
|---|---|
| `add`、非预览 `rm`、`build`、本地 `gc` | 已分配的日志 ID |
| `publish`、`publish --abort` | 已有的发布尝试 ID |
| `log ID` | 请求的操作 ID |
| 其他命令 | `null`；`log prune` 将 ID 放在 `result.operation` |

`operation` 为 null 不表示只读命令。`where` 的顶层 `repository` 为 null，
具体仓库名称在位置记录中。

<span id="各命令的-result-形态"></span>
<span id="create"></span>

## Plain `create`

| 结果字段 | 含义 |
|---|---|
| `dir` | 已索引目录的绝对路径 |
| `rpm`、`deb` | 进入索引的包数量 |
| `kept` | 排序后的保留包文件名 |
| `removed` | `--pigsty` 删除的文件 |
| `marker` | 是否生成完成标记 |
| `marker_sha256` | 标记摘要，生成标记时存在 |
| `noop` | 无需改变公开文件 |
| `recovered` | 始终 `false`，Plain 没有日志恢复 |
| `signed`、`signer` | 已签名文件名和可用的签名者身份 |

<span id="init"></span>
<span id="config-check-与-config-show"></span>

## 初始化与配置

| 命令 | 结果 |
|---|---|
| `init` | `workspace`、`config_created`、`repositories_initialized`、`dists_initialized`、`existing` |
| `config check` | `workspace`、`repositories`、`dists` |
| `config show` | 生效配置：`schema`、`architectures`、`repos`，以及存在时的 `targets` |

解析后的签名设置可包含公钥指纹和证书快照摘要。指纹和摘要数组各自排序，不能按下标配对。
详见[配置参考](/zh/docs/reference/config/#密钥引用)。

<span id="repo-ls--repo-new--repo-show"></span>
<span id="dist-ls--dist-new--dist-show"></span>

## 仓库与 Dist

`repo ls` 返回 `result.repositories[]`；`repo new` 与 `repo show` 直接返回一个仓库对象。
常见字段为 `name`、`path`、`protected`、`dists`、`generation`、`desired_revision`、
`status`、`packages`、`memberships`、`config`。
有相应信息时还会出现 `dirty_reasons`、`recent_operation`。操作摘要包含
`id`、`kind`、`state`、`created_at`、`updated_at` 和可选 `error_class`。
`status.pending_operation`、`status.recent_operation` 也使用这一结构。

`packages` 统计已存储包对象，`memberships` 统计期望 Dist 成员关系。
一个对象属于两个 Dist 时，分别计为一个包、两份成员关系。

`dist ls` 返回 `result.dists[]`；`dist new` 与 `dist show` 直接返回一个 Dist 对象：
`name`、`format`、`architectures`、`desired_members`、`built_members`、`generation`、
`dirty`、`status`、`effective_config_sha256`、`config`，以及可选 `dirty_reasons`。

每个架构条目有 `family` 和 `ecosystem_arch`。例如 DEB 的规范族为 `x86_64`，
生态名称为 `amd64`。

`repo rm` 和 `dist rm` 返回 `name`、`removed`、`noop`。
`repo migrate` 返回 `repository`、`repository_id`、`from_layout`、`to_layout`、
`schema_from`、`schema_to`、`phase`、`generation`、`grace_not_before`、`legacy_aliases`、
`complete`。没有宽限期截止时间时，`grace_not_before` 为 null。
各阶段含义见 [`repo migrate`](/zh/docs/command/repo/#sow-repo-migrate)。

<span id="add"></span>
<span id="rm"></span>
<span id="build"></span>

## `add`、`rm` 与 `build`

三者都报告操作后的仓库状态：`repository`、`desired_revision`、`built_generation`、`dirty`。

`add` 还返回 `operation`、`accepted`、`failed`、`memberships_added`、`memberships_removed`
和 `items[]`。每项包含 `input`、`status`；有相应信息时，还包含 `format`、`coordinate`、
`sha256`、各 Dist 的 `dists` 结果映射及 `error`。

| 输入状态 | 含义 |
|---|---|
| `accepted` | 新包进入成员集合 |
| `reused` | 复用已有包对象，成员关系仍可能改变 |
| `excluded` | 策略导致所有选中 Dist 都未接受该包 |
| `failed` | 输入失败，查看 `error` |

每个 Dist 的结果为 `accepted`、`excluded` 或 `limited`。一个包在不同 Dist 中可以有不同
结果。`limit` 移除旧版本时，成员移除计数会增加。

`rm` 返回可选的 `operation`、`removed[]`、所选 `dists`、`changes[]` 和 `check`。
每条 `removed` 记录包含 `dist`、`sha256`、`coordinate`、`name`。
预览时 `check: true`；只有 `prediction_complete: true` 才表示预期文件列表完整。
`rm` 不删除包池字节。

`build` 返回 `operation`、考虑的 `dists` 和 `noop`。无需变更时不创建新构建快照。

<span id="status"></span>
<span id="check"></span>

## `status` 与 `check`

`status` 返回 `status`、`ready_to_copy`、`desired_revision`、`built_generation`、
`dirty_dists`、`dirty_reasons`、`pending`、`repository_locked`。
可选字段有 `pending_operation`、`recent_operation`、`lock_holder`。

`status` 为 `clean`、`dirty`、`recovering` 或 `error`。`pending` 包含 `count`、`bytes`。
成功的状态查询可以返回任何仓库状态。`ok: true` 表示查询成功。发布或复制前，用 `check` 做完整校验。

`check` 返回 `repository`、`status`、`ready_to_copy`、`built_generation`、
`desired_revision` 和 `layers[]`。每层有 `name`、`ok`、`checked`、`issues`。

正常检查层依次为 `config`、`state`、`public-modes`、`retained`、`package-bytes`、
`desired-membership`、`index`、`signature`、`generation-manifest`。
存在活动布局转换时，改为前三层加 `layout-transition`。
脏仓库可以通过各项一致性检查，但仍因尚不可交付而返回 `5`。

## `changes`

结果包含 `repository`、`base`、`generation`、`dirty`、`changes[]`，每项变更包含：

| 字段 | 取值 |
|---|---|
| `op` | `add`、`update`、`delete` |
| `phase` | `payload`、`metadata`、`pointer`、`delete` |
| `path` | 相对仓库根的路径，使用 `/` 分隔 |
| `size`、`sha256` | 新增或更新文件有此字段，删除项省略 |

不传基线时与上一构建快照比较；基线 `0` 列出当前完整目录；数字基线与指定的已记录构建快照比较。
这是本地文件差异，远端变更使用 `publish` 和目标 `gc`。

<span id="ls--show--where"></span>

## 包查询

| 命令 | 结果字段 |
|---|---|
| `ls` | `repository`、所选 `dists`、`dirty`、`packages[]` |
| `show` | `repository`、`package` |
| `where` | `reference`、`locations[]` |

包对象包含 `sha256`、`format`、`coordinate`、`architecture`、`canonical_arch`、`pool_path`、
`filename`、`size`、`name`、`source`、`version`、`kind`、`storage`、`created_revision`、`dists`、
`built_dists`。可选字段包括 `epoch`、`release`、RPM 的 `payload_sha256`、`signature_key`，以及 `warning`。

`architecture` 是原生名称（如 `noarch`、`amd64`），`canonical_arch` 为
`x86_64`、`aarch64` 或 `neutral`。`storage` 为 `pool` 或 `pending`，不表示远端发布状态。
`dists` 是期望成员，`built_dists` 是上次构建成员。
包对象的 `coordinate` 不含格式前缀，加上 `format + ":"` 后才是 CLI 坐标引用。
`where` 位置记录的坐标已含此前缀。每个位置包含 `repository`、`dists`、
`built_dists`、`sha256` 和 `coordinate`。

<span id="publishretaingcexport"></span>

## 发布与维护

| 命令 | 主要结果字段 |
|---|---|
| `publish` | `repository`、`target`、`provider`、`generation`、可选 `attempt`/`checkpoint`、`phase`、`objects`、`noop` |
| `publish --abort` | `repository`、`target`、`provider`、`attempt`、`phase`、`objects` |
| `retain add/rm` | `repository`、`record`、`record_identity`、`path` |
| `retain ls` | `repository`、`generations[]` |
| 本地 `gc` | 可选 `operation`、`repository`、`base_generation`、`generation`、`objects`、`bytes`、`noop` |
| 目标 `gc` | `repository`、`target`、`provider`、`phase`、`reports`、`candidates`、`deleted_objects`、`deleted_bytes`、`retained_objects`、`pending_grace`、`completed_attempts`、`noop` |
| `export rpm-leaf` | `repository`、`repository_id`、`generation`、`dist`、`arch`、`directory`、`method`、`signed`、`signer_identity`、`packages`、`files`、`manifest_sha256` |

`publish --rebind` 使用普通 publish 结果结构。R2 目标 GC 只报告候选，不删除远端对象。

<span id="log"></span>
<span id="log-export-不是信封"></span>

## 操作日志

`log` 返回 `repository` 和按新到旧排序的 `operations[]`。
`log ID` 返回 `repository` 与 `detail`，后者包含 `operation`、`duration_ms`、`events`、
`packages`、`memberships` 和 `files`。

| 详情数组 | 记录字段 |
|---|---|
| `events` | `sequence`、`state`、`detail_json`、`occurred_at` |
| `packages` | `sequence`、`input_path`、`disposition`；可选 `package_sha256`、`coordinate`、`error_class`、`message`、`dists` |
| `memberships` | `sequence`、`dist`、`package_sha256`、`action` |
| `files` | `sequence`、`action`、`phase`、`path`；可选 `size`、`sha256` |

`payload_json`、`result_json` 和事件的 `detail_json` 是包含 JSON 的字符串，
需要时再解析一次：

```bash
sow log -r demo --json \
  | jq '.result.operations[] | .payload_json | fromjson'
```

`log prune` 返回 `operation`、`repository`、`before`、`pruned`、`compaction_deferred`。
仅日期参数按机器本地时区解析，`before` 包含解析后的时间戳。

`log export` 每行输出一个完整操作记录，没有顶层封装：

```bash
sow log export operations.jsonl -r demo
sow log export - -r demo
```

文件目标必须尚不存在，其直接父目录必须是真实目录，不能是符号链接。

<span id="一个完整例子"></span>

## 在脚本中使用检查结果

```bash
#!/usr/bin/env bash
set -euo pipefail
sow check -r demo --json | jq -e '.ok' >/dev/null
sow changes 0 -r demo --json \
  | jq -r '.result.changes[] | [.phase, .op, .path] | @tsv'
```

此脚本检查本地仓库并输出当前文件清单。需要发布时，对已配置目标运行 `sow publish TARGET`。

<span id="延伸阅读"></span>
