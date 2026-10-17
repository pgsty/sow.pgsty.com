---
title: "sow dist"
linkTitle: "dist"
description: "创建、列出、查看和删除 RPM 或 DEB 发行版集合。"
categories: [Command]
tags: [cli, dist, managed]
url: "/zh/docs/command/dist/"
aliases: ["/docs/reference/cli/dist/"]
weight: 500
icon: fa-solid fa-layer-group
---

`sow dist` 管理客户端使用的发行版集合。每个 Dist 只包含 RPM 或 DEB 中的一种格式。同一仓库内的 Dist 共用 `pool/`，在 `dists/` 下各有独立索引。

## 语法

```text
sow dist ls [-C DIR] [-r NAME] [--json]
sow dist new NAME --format rpm|deb [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow dist show NAME [-C DIR] [-r NAME] [--json]
sow dist rm NAME [-f|--force] [-C DIR] [-r NAME] [-T DUR | -N] [--json]
```

## 命名

Dist 名与仓库名规则相同：`[a-z0-9][a-z0-9._-]*`，排除 `.`、`..`、`.sow`、`pool`、`dists`。

选择能说明发行版或渠道的名称，例如 `el9`、`trixie` 或 `el9-beta`。SOW 不根据名称推断包格式或策略。

## sow dist ls

列出所选仓库的全部 Dist。

```console
sow dist ls -r pigsty
NAME	FORMAT	ARCHITECTURES	DESIRED	BUILT	GENERATION	DIRTY	DIRTY_REASONS
el9	rpm	x86_64,aarch64	0	0	1	false	[]
trixie	deb	x86_64,aarch64	0	0	2	false	[]
```

`DESIRED` 与 `BUILT` 是成员计数。两者不一致时，`DIRTY_REASONS` 会说明原因：

```console
sow dist ls -r demo
NAME	FORMAT	ARCHITECTURES	DESIRED	BUILT	GENERATION	DIRTY	DIRTY_REASONS
el9	rpm	x86_64,aarch64	2	1	4	true	["Desired and Built membership sets differ"]
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `--json` | 输出 JSON | false |

表格显示架构族，JSON 还给出包生态使用的架构名。以下摘录展示 `result.dists` 中一个条目的
`architectures` 字段，对应的 DEB 视图目录为 `binary-amd64` 与 `binary-arm64`：

```json
{
  "architectures": [
    {"family": "x86_64", "ecosystem_arch": "amd64"},
    {"family": "aarch64", "ecosystem_arch": "arm64"}
  ]
}
```

即使成员数量相同，仓库中未完成的维护操作也可能使 Dist 显示为 dirty。
判断 Dist 是否可以交付前，查看 `dirty_reasons` 与 `sow status`。

## sow dist new

使用 `--format rpm` 或 `--format deb` 创建 Dist。

```console
sow dist new el9 --format rpm -r pigsty
created el9: format=rpm architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
```

```console
sow dist new trixie --format deb -r pigsty
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=2 dirty=false
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `--format FORMAT` | 必填；`rpm` 或 `deb` | — |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

`--format` 必填，只接受 `rpm` 或 `deb`：

```console
sow dist new x -r alpha
usage error: dist new requires --format rpm|deb
```

```console
sow dist new x --format zip -r alpha
usage error: --format must be rpm or deb
```

新 Dist 继承工作区的架构列表。需要选择架构子集或设置 `limit`、`exclude` 时，编辑 `sow.yml`，再运行 `sow config check` 与 `sow build`。

名称与格式已经存在时，`dist new` 报告当前状态。同名但格式不同会被拒绝：

```console
sow dist new el9 --format deb -r alpha
operation rejected: managed: operation rejected: dist "el9" already exists with format rpm
```

### 创建与恢复 {#三方事务}

`dist new` 更新 `sow.yml` 并构建新 Dist。操作中断后，运行 `sow build` 恢复。

新 Dist 具有有效的空索引。RPM Dist 在每个架构视图下有一份空
`repodata/`；DEB Dist 有空的 `Packages`、`Packages.gz`、`by-hash/SHA256/` 条目，
以及 `Release`；配置签名时再生成 `InRelease` 与 `Release.gpg`。

## sow dist show

显示一个 Dist 的详细信息。

```console
sow dist show trixielim -r pgsql
dist trixielim:
  format: deb
  architectures: x86_64,aarch64
  desired_members: 3
  built_members: 3
  generation: 6
  status: clean
  dirty: false
  dirty_reasons: []
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `--json` | 输出 JSON | false |

JSON 还包含 `effective_config_sha256`，即解析后的 Dist 配置摘要。
修改 `limit`、`exclude` 或签名密钥后，当前配置可能与构建快照不同。
SOW 会将该 Dist 标为 dirty，重新构建后恢复一致。

```console
sow dist show el9 -r pgsql --json
{"schema":"sow.cli/v1","command":"dist show","ok":true,"repository":"pgsql","operation":null,"result":{"name":"el9","format":"rpm","architectures":[{"family":"x86_64","ecosystem_arch":"x86_64"},{"family":"aarch64","ecosystem_arch":"aarch64"}],"desired_members":0,"built_members":0,"generation":"00000000000000000001","dirty":false,"status":"clean","effective_config_sha256":"a0b3ae2f943bc4fce951aaadda0fc8fb146ccf7944b0193a0dcc2b86ddc7ce7e","config":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":1,"exclude":[{"kind":["debuginfo","debugsource"]}]}},"errors":[]}
```

```console
sow dist show nope -r demo
operation rejected: managed: operation rejected: dist "nope" does not exist
```

## sow dist rm

删除一个 Dist 的成员关系与衍生索引。

```console
sow dist rm el9 -r pgsql
operation rejected: managed: operation rejected: dist "el9" is not empty; use --force
```

```console
sow dist rm el9 -r pgsql -f
removed dist el9 from pgsql
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-f, --force` | 删除成员与索引，但保留 pool 中的包 | false |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

### 删除 Dist 不会删除 pool 字节

SOW 删除该 Dist 的配置、成员关系与索引。包文件仍保存在 `pool/` 中：

```console
sow dist rm el9 -r pgsql -f
removed dist el9 from pgsql

find pgsql -type f
pgsql/pool/e/epel-release/epel-release-7-5.noarch.rpm
```

运行 [`sow gc`](/zh/docs/command/gc/) 可以回收当前状态与保留状态都不再需要的包文件。

如果已配置的目标发布过这个 Dist，移除会被拒绝。详见[移除已发布视图](/zh/docs/command/publish/#移除已发布视图)。

仓库的 `protected: true` 只阻止仓库删除；受保护仓库上的常规 Dist 维护照常进行。

## 示例

在同一个仓库中创建 RPM 与 DEB Dist：

```bash
sow dist new el9 --format rpm -r pgsql
sow dist new trixie --format deb -r pgsql
```

创建 beta Dist，在 `sow.yml` 中设置包保留策略，再构建：

```bash
sow dist new el9-beta --format rpm -r pgsql
$EDITOR sow.yml          # el9-beta: { limit: 0 }
sow config check
sow build -r pgsql -d el9-beta
```

列出需要构建的 Dist：

```bash
sow dist ls -r pgsql --json | jq -r '.result.dists[] | select(.dirty) | .name'
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 列出、创建、显示或删除成功；或 `dist new` 报告已存在的 Dist |
| `1` | 创建空索引时的运行时 I/O 或渲染错误 |
| `2` | 用法错误——`--format` 缺失或非法、工作区未找到、仓库选择有歧义 |
| `4` | 工作区或仓库锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | 操作日志的完整性或恢复错误 |
| `6` | 名称非法、Dist 不存在、同名不同格式冲突、非空但未给 `-f` |

## 参见

- [sow repo](/zh/docs/command/repo/) —— 上一层
- [包池与架构视图](/zh/docs/feature/views/) —— 一个 Dist 如何变成多个客户端可见视图
- [成员策略](/zh/docs/feature/policy/) —— 配置 `limit` 与 `exclude`
- [sow build](/zh/docs/command/build/) —— 修改策略后重新构建
- [仓库布局](/zh/docs/reference/layout/) —— RPM 与 DEB 的 `dists/` 结构
