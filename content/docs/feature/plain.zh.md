---
title: "Plain 平面仓库"
linkTitle: "Plain 平面仓库"
description: "生成平面 RPM、DEB 索引，继续中断构建，并使用签名或 Pigsty 完成标记。"
categories: [Feature]
tags: [plain, rpm, deb]
url: "/zh/docs/feature/plain/"
weight: 200
icon: fa-solid fa-folder-open
---

用 `sow create` 为一个 RPM 或 DEB 软件包目录生成索引。索引与包文件放在一起。
该命令不读取 `sow.yml`，也不创建状态数据库。

```bash
sow create /srv/offline
```

<span id="契约" data-td-print-local></span>
<span id="扫描与输出规则" data-td-print-local></span>
<span id="输入与输出" data-td-print-local></span>

## 输入与输出 {#inputs-and-outputs}

SOW 只扫描目录顶层以 `.rpm` 或 `.deb` 结尾的普通文件，不递归，也不跟随包文件符号链接。
包名、版本和架构来自包内信息。默认容错模式下，SOW 会跳过损坏或不可读文件、源码 RPM（`src` 与 `nosrc`）以及坐标冲突（含 Debian 版本等价冲突，如 `1.0-1` 与 `1.00-1`）并输出告警，确保其余合法包仍能进入索引；传入 `--strict` 可在写入前遇错即停。

| 输入 | 生成文件 |
|---|---|
| RPM | `repodata/repomd.xml` 和 gzip 压缩的 `primary`、`filelists`、`other` XML |
| DEB | `Packages` 和 `Packages.gz` |
| 两种格式 | 两组索引 |

RPM 包路径使用文件名，DEB 的 `Filename` 使用 `./<文件名>`。SOW 会把所有有效版本收入索引。
当某一种格式的全部候选包都失败时，SOW 会保留该格式原有的索引、历史记录与完成状态，同时正常发布另一种格式的合法包（包括全新的 `--pigsty` 目录）。空目录在默认模式下仅输出告警，在 `--strict` 模式下（未加 `--pigsty` 时）会拒绝执行。文本模式将告警写入 stderr；成功的 `--json` 输出在 stdout 中返回 `warnings` 与 `skipped`，保持 stderr 为空。

默认保留包文件和无关文件。某种格式不再有包时，SOW 删除该格式的旧索引。
对于 RPM，SOW 保留当前与紧邻上一轮以校验和命名的元数据，删除更早的 SOW 格式元数据，并替换不完整输出。若已有的 `repomd.xml` 列出了 SOW 不生成的独立元数据（如 `group`、`updateinfo`、`modules`），`sow create` 会替换 `repomd.xml` 且不再带入这些条目，并在 `dropped_metadata`（`--json`）和 stderr 告警中报告被丢弃的类型（不包含 `*_db`、`*_zck` 等包索引编码）。磁盘上的非 SOW 文件（包括外部 `repomd.xml.asc` 签名）保持不变，需另行刷新。`sow create` 拒绝在 Managed `.sow` 工作区内部运行，未加 `--pigsty` 时也拒绝覆盖中断的 `.sow-prune-repo-complete` 标记。
生成目录的权限为 `0755`，生成文件为 `0644`。

<span id="单遍流水线" data-td-print-local></span>
<span id="最终-stat-校验保证什么" data-td-print-local></span>
<span id="确定性与-no-op" data-td-print-local></span>
<span id="构建与重复运行" data-td-print-local></span>

## 构建与重复运行 {#build-and-repeat}

普通未签名构建只读取每个选中包一次，同时计算 SHA-256 并解析元数据。
`--jobs` 控制并行数，默认为逻辑 CPU 数。SOW 根据解析结果生成并检查索引。

替换索引前，SOW 再次核对包文件列表、文件身份、权限、大小和修改时间。
构建期间应停止其他程序修改包文件。文件状态发生变化时，命令停止发布并返回退出码 `5`。

相同包字节和选项生成相同元数据。如果生成文件与现有文件相同，命令报告
文本字段 `noop=true` 或 JSON 字段 `noop: true`，保留现有文件。

RPM 元数据的 revision 和 data timestamp 默认都是 `0`。更新供 EL7 YUM 使用的已有仓库时，
请设置发布时间：

```bash
sow create /srv/offline --metadata-timestamp 1791849600
```

该选项只改变 `repomd.xml`，不改变压缩 XML、包文件或 DEB 索引。时间戳应从已有仓库的值
继续递增；操作方法见 [YUM 迁移](/zh/docs/tutorial/yum-migration/)。

<span id="发布与中断语义" data-td-print-local></span>

小文件 `.sow-plain-rpm-history.json` 跟踪 RPM 元数据保留范围。
没有变化的构建仍保留同一份上一轮索引。复制目录后还要继续构建时，一并保留该文件。
软件包保留仍由维护者负责，详见 [RPM 索引保留](/zh/docs/command/create/#keep-the-previous-rpm-indexes)。

## 清理旧版 RPM {#prune-superseded-rpms}

使用 [`sow prune`](/zh/docs/command/prune/) 在 Plain 目录中按每个 RPM `(name, arch)` 仅保留最高 EVR 版本：

```bash
sow prune /srv/offline --dry-run
sow prune /srv/offline
```

`sow prune` 同时支持 RPM v4 与 v6，按原生 `rpmvercmp` 规则（包含 `~` 预发布与 `^` 后置快照算符）比较版本。它先更新 `repodata/`，再删除被取代的 `.rpm` 文件，确保客户端不会看到指向缺失软件包的索引。默认容错模式下，损坏包、未匹配的 `--protect` 名称和同版本冲突（保留整个包名与架构分组）会输出告警并安全跳过；传入 `--strict` 可在发布前遇错即停。在 RPM 与 DEB 混合目录中，`sow prune` 保留 DEB 索引并在 `repo_complete` 中沿用仍在目录内的已记录 DEB 摘要，不提前对新到达的未索引 DEB 计算哈希。与 `sow create` 不同，当 `repodata/` 中含有非 SOW 外来元数据文件或 `repomd.xml.asc` 时，`sow prune` 在非预览执行时会拒绝运行。

<span id="构建中断" data-td-print-local></span>

## 构建中断 {#interrupted-builds}

SOW 先在暂存区生成并检查元数据，再替换公开文件。这些替换不构成跨全部 RPM 和 DEB 文件
的单个事务，中断可能留下混合版本或不完整索引。

再次运行相同的 `sow create` 命令即可。它会清理自己留下的临时文件，并根据目录中当前的包
重新生成索引。Plain 模式没有操作日志恢复，JSON 字段 `recovered` 始终为 `false`。

对在线服务，在单独目录构建，成功后再把完整目录切换上线。需要记录成员关系、构建快照和
事务恢复时，使用 [Managed 模式](/zh/docs/feature/managed/)。

<span id="--pigsty-marker-门禁" data-td-print-local></span>
<span id="pigsty-清理与完成标记" data-td-print-local></span>

## Pigsty 清理与完成标记 {#pigsty-cleanup-and-completion-marker}

```bash
sow create /srv/offline --pigsty
```

`--pigsty` 根据包内信息删除 DEB `i386` 包和 Patroni 3.0.4 包。
它不会仅因 RPM 架构为 `i386`、`i486`、`i586` 或 `i686` 而删除该包。

SOW 保留 `annobin-docs` 等文档包，除非命中上述清理规则。

索引更新和包清理完成后，SOW 写入 `repo_complete`。每行包含 SHA-256、两个空格和保留的
包文件名，按文件名排序。

SOW 在替换公开文件前移除旧标记，最后写入新标记。采用此约定的使用方应等待标记出现。
如果构建中断且标记缺失，再次运行带 `--pigsty` 的命令。目录已有 `repo_complete` 时，
不带 `--pigsty` 的命令会拒绝重建。

<span id="显式-rpm-签名" data-td-print-local></span>
<span id="rpm-包签名" data-td-print-local></span>

## RPM 包签名 {#rpm-package-signing}

```bash
sow create /srv/offline --sign-with 6D5C5A26C36B1F73
```

此选项为没有可解析内嵌签名的 RPM 签名。加上 `--overwrite` 可重签所有保留的 RPM。
签名需要主机上的 `rpm` 命令和可用 GPG 密钥。SOW 对暂存副本签名并检查，再先替换包文件、
后替换索引。这条路径会多次读取包字节。

密钥带口令时，可传入 `--passfile PATH` 或设置 `SOW_GPG_PASSFILE`；启用签名仍需
`--sign-with`。完整文件格式见[口令文件](/zh/docs/reference/config/#passfile)。
Plain 模式不读取 Managed 的 `sow.yml` 配置。

Plain 模式不签仓库元数据。Managed 元数据签名和包签名策略见[签名](/zh/docs/feature/signing/)。

<span id="锁与适用范围" data-td-print-local></span>
<span id="并发命令" data-td-print-local></span>

## 并发命令 {#concurrent-commands}

`sow create` 与 `sow prune` 锁定目标目录。它们只在绑定目标目录时短暂持有父目录锁，在等待繁忙目标前及绑定完成后即释放，因此相邻平面目录可并行运行。用 `-N` 在其他 SOW 写者占锁时立即退出，或用 `-T 30s` 最多等待 30 秒。默认等待到锁可用。

完整选项与结果字段见 [`sow create`](/zh/docs/command/create/)。

<span id="继续阅读" data-td-print-local></span>
