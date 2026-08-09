---
title: "sow add"
linkTitle: "add"
description: "把包加入期望成员集，执行成员策略，并重建受影响的索引。"
url: "/zh/docs/command/add/"
aliases: ["/docs/reference/cli/add/"]
weight: 600
icon: fa-solid fa-plus
---

`sow add` 是主要的写入路径。它解析你指定的包，从包头推导格式与架构，执行 Dist 的成员策略，并且——
除非你加 `--skip`——在返回前重建全部受影响的索引。命令退出码为 `0` 时，客户端已经能看到新包了。

## 语法

```text
sow add PATH... [-R|--recursive] [--skip] [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-R, --recursive` | 递归进入 `PATH` 目录的子目录 | 关闭（只扫顶层） |
| `--skip` | 只更新期望状态，不构建 | 关闭 |
| `-j, --jobs N` | 解析、哈希与渲染的并发 worker 数 | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出版本化 JSON envelope | false |

## 输入与目标

`PATH` 可以是文件或目录。目录默认只扫描顶层，除非你加 `-R`。

最终必须确定恰好一个仓库与至少一个目标 Dist——见[选择规则](/zh/docs/command/)。RPM 与 DEB
混合批次是允许的：每个包只会被考虑放进格式相同的目标 Dist；一个包如果没有任何兼容目标，则该包失败。

SOW 绝不从 manifest、目录名或宿主机 OS 推断目标。

```console
sow add /srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=8677129233475584643 accepted=2 failed=0 memberships=+2/-0 revision=3 generation=3 dirty=false
item input="/srv/pkg/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm" status=accepted format=rpm coordinate="centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead dists=el9:accepted
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=accepted format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

汇总行给出 Operation ID、逐项计数、成员增减、新的 Desired Revision、Built Generation，以及仓库是否
留在 dirty 状态。随后是每个输入一行 `item`，顺序稳定。

## 逐项状态

每行 `item` 带一个总体 `status`，以及 `dists=` 中的逐 Dist 判定。

| 状态 | 含义 |
|---|---|
| `accepted` | 新建 Package Object，且至少增加一条 Membership |
| `reused` | 内容已存在于本仓库；可能只是新增了 Membership 引用 |
| `excluded` | 策略把它从所有目标 Dist 中移除——看 `dists=` 区分是 `excluded` 还是 `limited` |
| `failed` | 该包被拒绝，`error=` 字段说明原因 |

`reused` 就是幂等的样子。同一个文件加两次不会产生第二个对象，也不会推进 Generation：

```console
sow add /srv/pkg/epel-release-7-5.noarch.rpm -r pigsty -d el9
add repository=pigsty operation=656950149626836753 accepted=1 failed=0 memberships=+0/-0 revision=4 generation=4 dirty=false
item input="/srv/pkg/epel-release-7-5.noarch.rpm" status=reused format=rpm coordinate="epel-release-0:7-5.noarch" sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab dists=el9:accepted
```

把同一个对象加进第二个 Dist 同样是 `reused`——包池只保留一份，只是多了一条 Membership。

## 架构是读出来的，不是猜的

`add` 从包头读取格式与原生架构，再对照工作区许可表。不在许可表中的架构会让该包失败，并明确告诉你
要改什么：

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
item input="/srv/pkg/centos-release-3.1-1.i386.rpm" status=failed error="managed: operation rejected: unknown rpm package architecture \"i386\"; supported rpm package architectures are [x86_64, aarch64, noarch] (canonical families [x86_64, aarch64, neutral]); use a supported package or update only supported architecture families in sow.yml"
```

它不会创建目录，也不会修改 `sow.yml`。

RPM 的 `noarch` 与 DEB 的 `all` 是架构中性（neutral）的。它们只产生一个 Package Object 与一条
Membership，但会渲染进目标 Dist 的每个有效架构视图。它们不会自动扩散到你没有用 `-d` 选中的 Dist。

## 策略：exclude 与 limit

合并进目标 Membership 之后，SOW 会在完整的 Dist 候选集上重新求值 `exclude`，再求值 `limit`。被策略
移除的包会被明确报告，不算解析失败。

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
`libpq5 18.2-1` 在版本上限下输给了 `18.3-1`，报告为 `limited`。两者的顶层状态都是 `excluded`，
靠 `dists=` 字段区分。

limit 按 `(二进制包名, 原生架构)` 分组，因此 `18.3-1:amd64` 与 `18.3-1:arm64` 在 `limit: 1` 下都能
留下。同一次运行中，一个包可以被某个 Dist 接受、被另一个 Dist 跳过。

{{% alert title="被策略移除的成员不会复活" color="warning" %}}
`exclude` 与 `limit` 移除的是真实的期望成员。之后放宽策略不会把它们变回来——`pool/` 里残留的字节
不构成候选集。请重新执行 `sow add`。
{{% /alert %}}

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

如果*一个都没被接受*，整个操作以退出码 `6` 被拒绝，仓库保持原样：

```console
sow add /srv/pkg/centos-release-3.1-1.i386.rpm -r pigsty -d el9
operation rejected: managed: operation rejected: no input package was accepted
```

没有 rejected/隔离目录。

## --skip

`--skip` 在期望状态提交后就停下。公开的 `pool/` 与 `dists/` 字节不变，Built Generation 保持原位，
仓库变为 dirty。新包字节被持久保存在私有 pending 存储中，直到下一次 build 才发布。

```console
sow add /srv/pkg/tree -R --skip -r pgsql -d trixie
add repository=pgsql operation=8405631664133415270 accepted=6 failed=0 memberships=+4/-0 revision=4 generation=3 dirty=true
```

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

`pending=4/2326` 表示私有存储里有 4 个对象、共 2326 字节在等待。它们不会出现在
[`sow changes`](/zh/docs/command/changes/) 中——只有成功的 build 才会把它们提升进可交付树。

批量导入时用 `--skip`，最后一次性收敛：

```bash
sow add /srv/build/ -R -r pgsql -d el9 --skip
sow status -r pgsql
sow build -r pgsql -j 12
sow check -r pgsql
```

## 处理顺序

一次 `add` 的执行顺序如下：

1. 取得仓库写锁，并恢复任何未完成的 Operation。
2. 在 SQLite 中提交一条 `planned` Operation。
3. 只读解析输入，计算逻辑坐标与输入字节 SHA-256（RPM 还会计算 signature-neutral payload digest）。
4. 校验架构许可表，并查询已有坐标。
5. 只对确实全新的坐标，在 stage 副本上执行可选的 RPM 签名并计算最终 SHA-256，再校验内容与路径唯一
   性。
6. 合并目标 Membership，然后在完整 Dist 集合上执行 `exclude` 与 `limit`。
7. 提交期望状态；新字节写入私有 pending 内容存储。
8. 除非给了 `--skip`，把仍被需要的 pending 对象发布进 `pool/` 并渲染索引——一次命令中每个 Dist 最多
   构建一次。

任何模式下，输入文件都不会被修改、移动或删除。

## RPM 签名模式

Managed 模式的 RPM 包签名在 `sow.yml` 的 `signing.rpm.packages.mode` 中配置，命令行没有覆盖开关。

| 模式 | 行为 |
|---|---|
| `never` | 完整保留输入字节 |
| `fill` | 无签名或签名不受信任时用配置 key 签名；已有能被 `trusted_keys` 验证的签名则保持字节。配置了 key 时的默认值 |
| `always` | 确保最终包由配置 key 有效签名；否则对 stage 副本重签 |

没有配置 key 时只能用 `never`。

由于签名包含非确定字段，SOW 无法先重签再比较最终哈希。重试幂等因此建立在坐标上：输入字节完全相同
则直接复用；RPM signature-neutral digest 相同、且既有对象满足当前策略时也复用。payload digest 不同，
或既有对象已不满足策略，则是硬冲突——`add` 不会静默地对同一坐标原地重签。

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 全部输入被接受或复用；索引已重建（或因 `--skip` 跳过） |
| `1` | 运行时 I/O、解析器、渲染器或签名失败 |
| `2` | 用法错误、工作区未找到，或仓库/Dist 选择有歧义 |
| `3` | 部分批次——至少一项已提交，至少一项失败 |
| `4` | 仓库锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | 完整性或恢复错误，包括在 `applied` 之后构建失败 |
| `6` | 一个都没接受——架构不受支持、没有兼容的目标 Dist，或坐标冲突 |

## 参见

- [sow rm](/zh/docs/command/rm/) —— 反向操作
- [sow build](/zh/docs/command/build/) —— `--skip` 之后的收敛
- [成员策略](/zh/docs/feature/policy/) —— `exclude` 规则与 `limit` 语义详解
- [签名模型](/zh/docs/feature/signing/) —— 两条信任链与 key 引用
- [包引用](/zh/docs/reference/package-ref/) —— item 行上打印的坐标文法
