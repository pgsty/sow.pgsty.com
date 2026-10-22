---
title: "sow create"
linkTitle: "create"
description: "在软件包所在目录生成 RPM 与 DEB 索引。"
categories: [Command]
tags: [cli, plain, rpm, deb]
url: "/zh/docs/command/create/"
aliases: ["/docs/reference/cli/create/"]
weight: 100
icon: fa-solid fa-folder-tree
---

`sow create` 在软件包所在目录生成 RPM 与 DEB 索引。需要平面仓库时使用此命令，无需创建 Managed 工作区。`DIR` 默认为当前目录。

## 语法

```text
sow create [DIR] [-j N] [--metadata-timestamp SECONDS] [--pigsty] [-S KEY [--overwrite]] [-T DUR | -N] [--json]
```

## 说明

`create` 读取 `DIR` 顶层的普通文件，按发现的内容渲染对应索引：有 RPM 就生成 `repodata/`，有 DEB 就
生成 `Packages` 与 `Packages.gz`，混合目录两套一起生成。架构全部来自包头——Plain 模式没有架构参数，
也没有架构许可表。

索引使用相对包路径：RPM 使用文件名，DEB 使用 `./<文件名>`。可以通过 HTTP 提供整个包目录，也可以将它作为本地 `file://` 软件源。

默认情况下，`create` 只更新索引并保留包文件。`--pigsty` 会删除符合规则的包，`--sign-with` 会用签名副本替换 RPM。

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-j, --jobs N` | 处理软件包的并发工作线程数 | 逻辑 CPU 数 |
| `--metadata-timestamp SECONDS` | RPM repomd 的 data 时间戳，取值 `0` 至 `253402300799` 的 Unix 秒；不影响 DEB、包时间或 gzip 头 | `0` |
| `--pigsty` | 启用 Pigsty 兼容清理与完成标记 | 关闭 |
| `-S, --sign-with KEY` | 用 GPG 密钥 ID 或指纹为未签名 RPM 补签 | 关闭 |
| `--overwrite` | 重签全部 RPM；必须与 `--sign-with` 同用 | 关闭 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |
| `-h, --help` | 显示帮助 | — |

## 扫描规则

- 只考虑顶层、以 `.rpm` 或 `.deb` 结尾的普通文件。
- 不递归、不跟随符号链接、不读工作区配置。
- 所有有效版本都进入索引。两个文件对应同一逻辑坐标但内容不同时，命令报错。
- 默认模式要求至少有一个支持的包。`--pigsty` 允许清理后没有包，并为该空目录写入完成标记。

```console
sow create /srv/empty
plain: scan /srv/empty: no supported top-level regular RPM or DEB packages
```

## 包 I/O 与最终校验

`create` 运行期间，保持输入目录不变。SOW 扫描软件包后，会在替换索引前检查文件是否变化。检测到变化时返回退出码 `5`。使用 `--jobs` 设置处理软件包的并发数。

## 确定性输出与幂等

不强制重签软件包时，相同的软件包与时间参数生成相同的元数据。`repomd.xml` 的 `<revision>` 和 data 时间戳默认为 `0`；`--metadata-timestamp` 只修改 data 时间戳。对未变化的目录使用相同选项重跑时，SOW 不改写文件，并报告 `noop=true`：

```console
sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=false recovered=false

sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=true recovered=false
```

## 保留上一轮 RPM 索引

SOW 0.6.1 保留当前与紧邻上一版 `repomd.xml` 引用的、以校验和命名的 RPM 元数据。
客户端已获取上一版索引时，仍可在更新后下载这些元数据文件。
没有变化的运行不会推进保留窗口。

隐藏文件 `.sow-plain-rpm-history.json` 记录这些引用。复制目录后继续构建时，一并保留该文件。
它是保留记录，不是恢复日志；Plain 模式仍通过重建恢复。

此窗口不保留已删除的包文件，也不保留全部历史索引。
如果客户端缓存跨越多轮更新，在发布层保留所需的软件包与元数据。

## repo_complete 标记 {#repo_complete-门禁}

如果目录中有 `repo_complete`，使用 `--pigsty` 将它与索引一起更新。不带 `--pigsty` 运行会返回错误：

```console
sow create /srv/pigsty
plain: marker gate /srv/pigsty/repo_complete: repo_complete exists; use --pigsty or remove it explicitly before rebuilding
```

需要保留完成标记时，添加 `--pigsty` 后重跑；不再使用此标记时，先将它移走。

## 已有 YUM 仓库的发布时间

`--metadata-timestamp` 设置 RPM repomd 的 data 时间戳，不改变软件包、压缩 XML 文件或 DEB 索引。默认值为 `0`，范围为 `0..253402300799` Unix 秒。此选项从 SOW 0.5.0 开始提供。

EL7 YUM 会拒收最大 data 时间戳早于本地缓存的元数据。替换已有元数据生成器时，选择不低于历史已发布最大值的时间。内容变化时，至少增加一秒，以区分各次更新。

```bash
sow create /srv/flat --metadata-timestamp "${PUBLISH_TIME:?Set the publication time}"
```

记录发布时间，并在每次更新时传入。省略此选项会重新使用 `0`。恢复旧包集合也属于新发布，因此仍需递增时间戳。使用秒值，不要传毫秒值或未来日期。

如果客户端验证 `repomd.xml.asc`，repomd 变化后需要重新生成该签名。`create` 不签署 repomd，也不更新或删除旧的分离签名。

完整流程见[迁移现有 YUM 仓库](/zh/docs/tutorial/yum-migration/)。

## --pigsty

`--pigsty` 按以下规则清理包文件，并写入完成标记：

1. 删除解析架构为 `i386` 的 DEB；RPM 不会仅因为架构是 `i386/i486/i586/i686` 而被删除。
2. 删除二进制包名恰为 `patroni` 且上游版本恰为 `3.0.4` 的 RPM/DEB。RPM 比较 `VERSION`，忽略
   epoch 与 release；DEB 先剥掉 epoch 与 Debian revision 再比。`3.0.4+foo` 不算命中。
3. 全部索引渲染成功后写出 `repo_complete`：剩余顶层 RPM/DEB 的 SHA-256，按文件名字节序排序，
   格式为 `<sha256><两个空格><basename>`。

```console
sow create /srv/pigsty --pigsty
created /srv/pigsty: rpm=2 deb=0 signed=0 removed=2 marker=true noop=false recovered=false
```

```console
cat /srv/pigsty/repo_complete
b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead  centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab  epel-release-7-5.noarch.rpm
```

清理仅处理解析成功且命中规则的顶层普通包文件。

`annobin-docs` 等文档包会保留，除非命中上述规则。

SOW 先撤下已有的 `repo_complete`，再替换索引；新元数据安装后删除命中规则的包，
最后写入新的完成标记。调用方看到标记缺失时，应等待构建完成。

## RPM 包签名

`-S/--sign-with KEY` 通过本地 RPM/GPG 环境为 RPM 包签名。使用 16 位十六进制密钥 ID，或 40/64 位指纹；可以带 `0x` 或 `0X` 前缀。运行前，在该环境中配置私钥与口令。

- 默认只给没有可解析嵌入 OpenPGP 签名的 RPM 补签；已有签名的包保持原字节。
- `--overwrite` 必须与 `--sign-with` 同用，改为对全部保留 RPM 执行 `rpm --resign`。
- SOW 对临时副本签名，确认包身份与内容未变后替换原 RPM。索引描述最终签名后的文件。
- `--pigsty` 清理后至少要保留一个顶层 RPM，且 `PATH` 中要有 `rpm`。

```console
sow create /srv/flat -S 0123456789ABCDEF --overwrite
plain: sign rpm epel-release-7-5.noarch.rpm: rpm executable is required for --sign-with
```

```console
sow create /srv/deb-only -S 0123456789ABCDEF
plain: sign rpm: --sign-with requires at least one retained top-level RPM package
```

```console
sow create /srv/flat --overwrite
usage error: --overwrite requires --sign-with
```

```console
sow create /srv/flat -S ZZZZ
usage error: --sign-with must be a 16, 40, or 64 hexadecimal GPG key ID/fingerprint
```

## 锁与中断恢复 {#锁staging-与覆盖重建}

`create` 在更新索引期间锁定目标目录。使用 `--timeout` 或 `--no-wait` 控制等待锁的时间。

中断可能使部分索引已更新、部分仍未更新。使用原定选项重新运行 `sow create`，按当前软件包重新生成全部索引。Plain 模式从头重建，因此结果字段 `recovered` 始终为 `false`。

使用 `--pigsty` 时，在 `repo_complete` 出现后再对外提供仓库。需要操作日志恢复时，使用 Managed 模式。

## 示例

给混合目录建索引：

```console
sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

```console
ls /srv/flat
centos-release-6-0.el6.centos.5.x86_64.rpm
centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
epel-release-7-5.noarch.rpm
libpq5_18.3-1_amd64.deb
Packages
Packages.gz
repodata
```

机器可读结果：

```console
sow create /srv/flat --json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,"result":{"dir":"/srv/flat","rpm":3,"deb":1,"kept":["centos-release-6-0.el6.centos.5.x86_64.rpm","centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm","epel-release-7-5.noarch.rpm","libpq5_18.3-1_amd64.deb"],"removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

用八个工作线程构建 Pigsty 平面仓库，并使用根据发布历史选定的时间：

```bash
sow create /www/pigsty -j 8 --pigsty --metadata-timestamp "${PUBLISH_TIME:?Set the verified publication time}"
```

调用者负责记录该时间，并在客户端要求时为生成的 `repomd.xml` 签名。

失败时的 JSON 结果：

```console
sow create /srv/empty --json
{"schema":"sow.cli/v1","command":"create","ok":false,"repository":null,"operation":null,"result":null,"errors":[{"code":6,"class":"rejected","message":"operation rejected: plain: scan /srv/empty: no supported top-level regular RPM or DEB packages"}]}
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 索引写出成功，或输入未变化产生 no-op |
| `1` | 目录不可读或不存在、包解析失败、渲染失败、签名工具失败 |
| `2` | 用法错误——时间戳非法或重复指定、`--overwrite` 未配 `--sign-with`、密钥格式非法、`--no-wait` 与非零 `--timeout` 同用 |
| `4` | 目录写锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | 发布前输入文件发生变化，或受控输出路径未通过完整性检查 |
| `6` | 未找到受支持的包、已有 `repo_complete` 但未使用 `--pigsty`、对 DEB-only 目录用 `--sign-with`、坐标冲突 |

## 参见

- [Plain 平面仓库](/zh/docs/feature/plain/) —— `create` 背后的设计
- [快速上手](/zh/docs/start/quickstart/) —— 五分钟平面仓库演练
- [仓库布局](/zh/docs/reference/layout/) —— 平面目录树长什么样
- [仓库签名](/zh/docs/tutorial/signing/) —— 生成与使用签名密钥
- [迁移现有 YUM 仓库](/zh/docs/tutorial/yum-migration/) —— 替换已有的元数据生成流程
