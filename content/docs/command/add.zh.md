---
title: "sow add"
linkTitle: "add"
description: "导入软件包、应用成员策略并构建本地索引。"
categories: [Command]
tags: [cli, managed, policy]
url: "/zh/docs/command/add/"
aliases: ["/docs/reference/cli/add/"]
weight: 600
icon: fa-solid fa-plus
---

`sow add` 将软件包导入指定 Dist，并构建本地索引。它从包头读取格式与架构，再应用各 Dist 的成员策略。需要分批导入后统一构建时，使用 `--skip`。需要更新远程目标时，在构建后运行 [`sow publish`](/zh/docs/command/publish/)。

## 语法

```text
sow add PATH... [-R|--recursive] [--skip] [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-R, --recursive` | 递归进入 `PATH` 目录的子目录 | 关闭（只扫顶层） |
| `--skip` | 只更新期望状态，不构建 | 关闭 |
| `-j, --jobs N` | 解析、哈希与渲染的并发工作线程数 | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

## 输入与目标

`PATH` 可以是文件或目录。目录默认只扫描顶层，除非你加 `-R`。

选择一个仓库和一个或多个 Dist。可用 `-r`、`-d` 指定，也可按[当前目录自动选择](/zh/docs/command/)。混合添加 RPM 与 DEB 时，每个包只进入格式相同的 Dist。没有兼容目标的包会被拒绝。

根据软件包适用的发行版选择 Dist。SOW 检查包格式与架构，不测试操作系统或依赖兼容性。

```console
sow add /srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=8677129233475584643 accepted=2 failed=0 memberships=+2/-0 revision=3 generation=3 dirty=false
item input="/srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm" status=accepted format=rpm coordinate="centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead dists=el9:accepted
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=accepted format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

汇总行给出操作记录 ID、逐项计数、成员增减、新的期望状态修订号、构建快照，以及仓库是否
留在 dirty 状态。随后是每个输入一行 `item`，顺序稳定。

## 逐项状态

每行 `item` 带一个总体 `status`，以及 `dists=` 中的逐 Dist 判定。

| 状态 | 含义 |
|---|---|
| `accepted` | 新建软件包对象，且至少增加一条成员关系 |
| `reused` | 内容已存在于本仓库；可能只是新增了成员关系引用 |
| `excluded` | 策略把它从所有目标 Dist 中移除——看 `dists=` 区分是 `excluded` 还是 `limited` |
| `failed` | 该包被拒绝，`error=` 字段说明原因 |

`reused` 表示复用已有内容：同一个文件加两次不会产生第二个对象或重复成员关系。默认重复执行
`add` 时还会构建所选 Dist。Dist 已是最新状态时，构建快照不变。先前 `--skip` 或配置变更留下
dirty 状态时，SOW 会补做构建，并可能生成新的构建快照：

```console
sow add /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=656950149626836753 accepted=1 failed=0 memberships=+0/-0 revision=4 generation=4 dirty=false
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=reused format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

把同一个对象加进第二个 Dist 同样是 `reused`——包池只保留一份，只是多了一条成员关系。
需要继续延后构建时，再次使用 `--skip`。

## 软件包架构 {#架构是读出来的不是猜的}

`add` 从包头读取格式与原生架构，再对照工作区许可表。架构不受支持或不在配置的许可表中时，该包会被拒绝：

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
item input="/srv/pkg/centos-release-3.1-1.i386.rpm" status=failed error="managed: operation rejected: unknown rpm package architecture \"i386\"; supported rpm package architectures are [x86_64, aarch64, noarch] (canonical families [x86_64, aarch64, neutral]); use a supported package or update only supported architecture families in sow.yml"
```

RPM 的 `noarch` 与 DEB 的 `all` 是架构中性（neutral）的。它们只产生一个软件包对象与一条
成员关系，但会渲染进目标 Dist 的每个有效架构视图。只有所选 Dist 会包含这些包。

## 策略：exclude 与 limit

SOW 将输入包与 Dist 的现有成员合并，先执行 `exclude`，再执行 `limit`。被策略移除的包会显示为 `excluded`，不算解析失败。

```console
sow add /srv/pkg/debs -r pgsql -d trixielim
add repository=pgsql operation=4142220455201181493 accepted=3 failed=0 memberships=+3/-0 revision=6 generation=6 dirty=false
item input="/srv/pkg/debs/libpq5-dbgsym_18.3-1_amd64.deb" status=excluded format=deb coordinate="libpq5-dbgsym=18.3-1:amd64" sha256:cf491b9d9b218fa49ad2b41b4740d62cd972e1b515bf33677c2c3ead75acc60a dists=trixielim:excluded
item input="/srv/pkg/debs/libpq5_18.2-1_amd64.deb" status=excluded format=deb coordinate="libpq5=18.2-1:amd64" sha256:fa84dc641b7c686be2f9b512311ad0b74eac03e2afc9eff7e9af75b82b68ff41 dists=trixielim:limited
item input="/srv/pkg/debs/libpq5_18.3-1_amd64.deb" status=reused format=deb coordinate="libpq5=18.3-1:amd64" sha256:491992c502113627d44d0d66a2b189cdaa8accff293ebaf84fe10ccbc9da574c dists=trixielim:accepted
item input="/srv/pkg/debs/libpq5_18.3-1_arm64.deb" status=reused format=deb coordinate="libpq5=18.3-1:arm64" sha256:3a2f7ef7cddfa3dc06280ef59eda1dab9724d57499931ee80758b11531c1f40c dists=trixielim:accepted
item input="/srv/pkg/debs/pg-sample_1.17-1_all.deb" status=reused format=deb coordinate="pg-sample=1.17-1:all" sha256:f23581c5164a143e5e902232589adf1d30b73ba3857a692a11da607f246aacc3 dists=trixielim:accepted
```

这里 `trixielim` 配了 `exclude: [{kind: [dbgsym]}]` 与 `limit: 1`。dbgsym 包被规则排除；
`libpq5 18.2-1` 因版本上限被移除并报告为 `limited`，`18.3-1` 被保留。两者的顶层状态都是 `excluded`，
用 `dists=` 字段区分。

`limit` 按 `(二进制包名, 规范架构)` 分组，因此 `18.3-1:amd64` 与 `18.3-1:arm64` 在 `limit: 1` 下都能
留下。同一次运行中，一个包可以被某个 Dist 接受、被另一个 Dist 跳过。

放宽 `exclude` 或 `limit` 后，需要重新运行 `sow add` 来恢复软件包。策略作用于期望成员，而不是 `pool/` 中的全部残留文件。

## 部分成功的批次

即使同批有失败项，合法且无冲突的包依然会提交。失败的输入原地不动，各自带自己的错误信息，命令退出
`3`：

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm /srv/pkg/centos-release-6-0.el6.centos.5.x86_64.rpm -r pigsty -d el9
add repository=pigsty operation=4623871845694427260 accepted=1 failed=1 memberships=+1/-0 revision=5 generation=5 dirty=false
item input="/srv/pkg/centos-release-3.1-1.i386.rpm" status=failed error="managed: operation rejected: unknown rpm package architecture \"i386\"; ..."
item input="/srv/pkg/centos-release-6-0.el6.centos.5.x86_64.rpm" status=accepted format=rpm coordinate="centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16 dists=el9:accepted
managed: batch partially succeeded
```

如果*每个输入都失败*，操作以退出码 `6` 被拒绝，期望成员与公开内容保持原样。人类输出会列出
每个失败输入及其原因，JSON 则在 `result.items` 中保留这些信息：

```bash
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
```

被策略排除不属于输入失败；全部被排除的批次可以正常成功，包括首次向空 Dist 添加时。
使用 SIGINT 或 SIGTERM 中断命令时，命令返回 `130`。使用原始输入文件重新执行；恢复会保留已经提交的成员变更。

包内容改变时，使用新的版本与文件名。本地 GC 后，已发布的包池路径仍然保留。路径冲突只拒绝对应输入，其他有效输入仍可成功。

重新添加同一个包时，保持文件名大小写一致。仅大小写不同的路径会产生冲突。在大小写不敏感的文件系统上，源码包目录名也必须可以区分，详见[工作区文件系统](/zh/docs/reference/compatibility/#工作区文件系统)。

## --skip

`--skip` 提交期望成员，保持 `pool/`、`dists/` 与构建快照不变。新包存放在私有待构建目录，供后续构建使用。期望状态与已构建状态不同时，仓库为 dirty；重复添加未变化的成员可以保持 clean。

```console
sow add /srv/pkg/tree -R --skip -r pgsql -d trixie
add repository=pgsql operation=8405631664133415270 accepted=6 failed=0 memberships=+4/-0 revision=4 generation=3 dirty=true
```

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

`pending=4/2326` 表示有 4 个包、共 2326 字节等待构建。构建成功后，实际采用的包进入公开目录，并出现在 [`sow changes`](/zh/docs/command/changes/) 的结果中。

批量导入时用 `--skip`，最后构建一次：

```bash
sow add /srv/build/ -R -r pgsql -d el9 --skip
sow status -r pgsql
sow build -r pgsql -j 12
sow check -r pgsql
```

## 处理顺序

SOW 检查软件包，并按配置为新 RPM 签名。随后执行 `exclude` 与 `limit`，记录最终成员；未设置 `--skip` 时，继续构建。

输入文件保持原样，签名在私有副本上完成。

## RPM 签名模式

Managed 模式的 RPM 包签名在 `sow.yml` 的 `signing.rpm.packages.mode` 中配置，命令行没有覆盖开关。

| 模式 | 行为 |
|---|---|
| `never` | 完整保留输入字节 |
| `fill` | 无签名或签名不受信任时用配置密钥签名；已有能被 `trusted_keys` 验证的签名则保持字节。配置了密钥时的默认值 |
| `always` | 确保最终包由配置密钥有效签名；否则对暂存副本重签 |

没有配置密钥时只能用 `never`。

重复导入时，SOW 复用内容相同的软件包。如果 RPM 只有签名不同，且已有包满足当前签名策略，也可以复用。包内容改变或已有签名不符合策略时，会产生坐标冲突。完整匹配规则见[签名模型](/zh/docs/feature/signing/)。

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 输入处理完成，包括按策略排除的输入；构建完成或已跳过 |
| `1` | 运行时 I/O、解析器、渲染器或签名失败 |
| `2` | 用法错误、工作区未找到，或仓库/Dist 选择有歧义 |
| `3` | 部分批次——至少一项已提交，至少一项失败 |
| `4` | 仓库锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | 完整性或恢复错误，包括在 `applied` 之后构建失败 |
| `6` | 全部输入失败，或选择范围、签名、状态前提不允许执行操作 |

## 参见

- [sow rm](/zh/docs/command/rm/) —— 反向操作
- [sow build](/zh/docs/command/build/) —— `--skip` 之后构建
- [成员策略](/zh/docs/feature/policy/) —— `exclude` 规则与 `limit` 语义详解
- [签名模型](/zh/docs/feature/signing/) —— 两条信任链与密钥引用
- [包引用](/zh/docs/reference/package-ref/) —— item 行中坐标的写法
