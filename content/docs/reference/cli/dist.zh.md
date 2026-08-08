---
title: "sow dist"
linkTitle: "sow dist"
description: "列出、创建、查看与删除 Dist —— 客户端真正消费的、单一格式的具名成员集。"
url: "/zh/docs/reference/cli/dist/"
weight: 500
icon: fa-solid fa-layer-group
---

Dist 是一个仓库内、单一格式（`rpm` 或 `deb`）的具名包集合。客户端指向的就是它。一个仓库可以同时拥有
RPM Dist 与 DEB Dist，两者共用一份 `pool/`，但渲染进完全独立的 `dists/` 子树。

## 语法

```text
sow dist ls [-C DIR] [-r NAME] [--json]
sow dist new NAME --format rpm|deb [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow dist show NAME [-C DIR] [-r NAME] [--json]
sow dist rm NAME [-f|--force] [-C DIR] [-r NAME] [-T DUR | -N] [--json]
```

## 命名

Dist 名与仓库名规则相同：`[a-z0-9][a-z0-9._-]*`，排除 `.`、`..`、`.sow`、`pool`、`dists`。

对 SOW 而言这个名字是不透明字符串。`el9`、`trixie`、`el9-beta`、`customer-acme`、`2026-07-31` 都只是
名字——beta 频道、按客户切分的视图、快照，都是你自己施加的命名约定，不是 SOW 建模的功能。

## sow dist ls

只读平铺列出选定仓库的全部 Dist。

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
| `--json` | 输出版本化 JSON envelope | false |

架构按规范化 family 打印。JSON 输出同时给出两种写法，用它可以确认 DEB Dist 渲染的是
`binary-amd64` 与 `binary-arm64`：

```json
"architectures":[{"family":"x86_64","ecosystem_arch":"amd64"},{"family":"aarch64","ecosystem_arch":"arm64"}]
```

## sow dist new

创建一个普通的、后续可继续修改的 Dist。唯一的业务参数是 `--format`。

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
| `--json` | 输出版本化 JSON envelope | false |

`--format` 必填且取值封闭：

```console
sow dist new x -r alpha
usage error: dist new requires --format rpm|deb
```

```console
sow dist new x --format zip -r alpha
usage error: --format must be rpm or deb
```

没有 `--arch`。架构从工作区许可表继承；高级用户在 `sow.yml` 里为某个 Dist 声明子集来收窄。策略
（`limit`、`exclude`）同样只在 `sow.yml` 中配置，绝不在命令行上重复建模。

用相同名称与相同格式重跑 `dist new` 是收敛操作，只报告当前状态。同名但*格式不同*会被拒绝：

```console
sow dist new el9 --format deb -r alpha
operation rejected: managed: operation rejected: dist "el9" already exists with format rpm
```

### 三方事务

`dist new` 要在三个地方同时提交：`sow.yml` 条目、仓库数据库、磁盘目录树。它走 SQLite Operation
Journal（此时仓库数据库已存在，与 `repo new` 不同），并产生一个带空索引的新 Built Generation。

因此新建的 Dist 立刻具备协议完整的空发布面。RPM Dist 在每个架构视图下有一份空
`repodata/`；DEB Dist 有空的 `Packages`、`Packages.gz`、`by-hash/SHA256/` 条目，
以及 `Release`；配置签名时再生成 `InRelease` 与 `Release.gpg`。

## sow dist show

只读显示一个 Dist 的细节。

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
| `--json` | 输出版本化 JSON envelope | false |

JSON 形态额外给出 `effective_config_sha256`，即解析后 Dist 配置的摘要。当你改动 `limit`、`exclude`
或签名 key 时，正是这个摘要让 Dist 变 dirty——配置身份变了，已构建代就不再等于期望状态。

```console
sow dist show el9 -r pgsql --json
{"schema":"sow.cli/v1","command":"dist show","ok":true,"repository":"pgsql","operation":null,"result":{"name":"el9","format":"rpm","architectures":[{"family":"x86_64","ecosystem_arch":"x86_64"},{"family":"aarch64","ecosystem_arch":"aarch64"}],"desired_members":0,"built_members":0,"generation":"00000000000000000001","dirty":false,"status":"clean","effective_config_sha256":"a0b3ae2f943bc4fce951aaadda0fc8fb146ccf7944b0193a0dcc2b86ddc7ce7e","config":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":1,"exclude":[{"kind":["debuginfo","debugsource"]}]}},"errors":[]}
```

```console
sow dist show nope -r demo
operation rejected: managed: operation rejected: dist "nope" does not exist
```

## sow dist rm

删除一个 Dist 的 Membership 与衍生索引。

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
| `--json` | 输出版本化 JSON envelope | false |

### 删除 Dist 不会删除 pool 字节

删除 Dist 绝不会从 `pool/` 删包。整个 Dist 目录被移入恢复区后原子移除，包池完全不受影响：

```console
sow dist rm el9 -r pgsql -f
removed dist el9 from pgsql

find pgsql -type f
pgsql/pool/e/epel-release/epel-release-7-5.noarch.rpm
```

失去引用的 Pool 对象会继续保留，直到 `sow gc` 证明它不再被当前、保留、恢复、发布以及
活动维护操作等任何安全根引用。

仓库的 `protected: true` 只封死仓库删除；受保护仓库上的常规 Dist 维护照常进行。

## 示例

给一个仓库同时配上 RPM 与 DEB 两副面孔：

```bash
sow dist new el9 --format rpm -r pgsql
sow dist new trixie --format deb -r pgsql
```

加一个带独立保留策略的 beta 频道——先建 Dist，再在 `sow.yml` 里写策略并收敛：

```bash
sow dist new el9-beta --format rpm -r pgsql
$EDITOR sow.yml          # el9-beta: { limit: 0 }
sow config check
sow build -r pgsql -d el9-beta
```

哪些 Dist 落后于期望状态：

```bash
sow dist ls -r pgsql --json | jq -r '.result.dists[] | select(.dirty) | .name'
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 列出、创建、显示或删除成功；或 `dist new` 收敛了已存在的 Dist |
| `1` | 创建空索引时的运行时 I/O 或渲染错误 |
| `2` | 用法错误——`--format` 缺失或非法、工作区未找到、仓库选择有歧义 |
| `4` | 仓库锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | Operation Journal 的完整性或恢复错误 |
| `6` | 名称非法、Dist 不存在、同名不同格式冲突、非空但未给 `-f` |

## 参见

- [sow repo](/zh/docs/reference/cli/repo/) —— 上一层
- [包池与架构视图](/zh/docs/feature/views/) —— 一个 Dist 如何变成多个客户端可见视图
- [成员策略](/zh/docs/feature/policy/) —— 配置 `limit` 与 `exclude`
- [sow build](/zh/docs/reference/cli/build/) —— 改完策略后的收敛
- [仓库布局](/zh/docs/reference/layout/) —— RPM 与 DEB 的 `dists/` 结构
