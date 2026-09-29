---
title: "sow rm"
linkTitle: "rm"
description: "从选定 Dist 中移除期望成员，并提供不写盘的预览模式。"
categories: [Command]
tags: [cli, managed, policy]
url: "/zh/docs/command/rm/"
aliases: ["/docs/reference/cli/rm/"]
weight: 700
icon: fa-solid fa-minus
---

`sow rm` 把包从你选定的 Dist 的期望成员集中拿掉，并默认立即重建受影响的索引。它不会从 `pool/`
删除字节——成员关系与内容是两个概念,回收由独立的保守操作 `sow gc` 完成。

## 语法

```text
sow rm PACKAGE... [-c|--check] [--skip] [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-c, --check` | 只预览：计算并打印方案，不写任何东西 | 关闭 |
| `--skip` | 只更新期望状态，不构建 | 关闭 |
| `-j, --jobs N` | 并发 worker 数 | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出版本化 JSON envelope | false |

`--check` 与 `--skip` 互斥：

```console
sow rm epel-release -c --skip
usage error: --check and --skip are mutually exclusive
```

## 包引用

`PACKAGE` 接受五种形态。完整文法与歧义规则见[包引用](/zh/docs/reference/package-ref/)，简版如下：

| 形态 | 例子 |
|---|---|
| 内容哈希 | `sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab` |
| RPM 坐标 | `rpm:epel-release-0:7-5.noarch` |
| DEB 坐标 | `deb:libpq5=18.3-1:amd64` |
| 完整文件名 | `epel-release-7-5.noarch.rpm` |
| 裸二进制包名 | `epel-release` |

裸名表示*选定 Dist 中该名称的全部版本与原生架构*——正因如此，`sow rm patroni` 才是一条好用的下架
命令。非裸名的模糊短引用会失败并列出候选，而不是替你猜。

[`sow ls`](/zh/docs/command/ls/) 会直接打印精确的 `sha256:` 引用与规范化坐标，你不需要手工
拼接。

引用匹配不到任何东西属于拒绝，不是静默成功：

```console
sow rm nosuch -r pigsty -d el9
operation rejected: managed: operation rejected: package reference not found: package reference "nosuch" matches no Desired Membership
```

没有 `--allow-empty`、没有 `--all`、没有 `--yes`、没有 `--source-list`。

## 用 --check 预览

`-c/--check` 精确算出会移除什么、策略随后会怎么判定、以及立即构建会触碰哪些文件——并且什么都不写。

```console
sow rm centos-release -r demo -d el9 -c
preview repository=demo operation= dists=el9 memberships=2 revision=2 generation=00000000000000000003 dirty=false changes=2
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead
change op=update phase=pointer path="dists/el9/aarch64/repodata/repomd.xml" size=1509 sha256:1cfe38698967d11384f1a985618d75f5e690d1284accf951262fc663fa9afc81
change op=update phase=pointer path="dists/el9/x86_64/repodata/repomd.xml" size=1509 sha256:1cfe38698967d11384f1a985618d75f5e690d1284accf951262fc663fa9afc81
```

注意两个 `centos-release` 版本都被裸名命中了。`change` 行是一份真实交付计划，按
`payload → metadata → pointer → delete` 排列。其他程序需要对应的 `removed[]` 与 `changes[]`
数组时应使用 `--json`。

预览与写操作使用同一套候选配置和完整性预检；预览未通过门禁时，不能据此认为实际写入会成功。

`--check` 有意不取写锁。把它与锁参数一起用是用法错误，免得有人以为预览会排队等待写事务：

```console
sow rm centos-release -r pigsty -d el9 -c -T 5s
usage error: rm --check does not accept --timeout or --no-wait
```

## 默认行为：移除并重建

不带 `--check` 或 `--skip` 时，`rm` 提交期望状态变更，并在返回前重建每个受影响的 Dist。pool 对象
留在磁盘上。

```console
sow rm 'rpm:centos-release-0:6-0.el6.centos.5.x86_64' -r demo -d el9
removed repository=demo operation=2283442100870457321 dists=el9 memberships=1 revision=2 generation=00000000000000000003 dirty=false changes=8
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
```

汇总之后会为每个受影响文件输出一行 `change`（本次运行共八行）。加上 `--json` 后，同一结果
以稳定的标准 Envelope 返回。

移除一个 Dist 的最后一个成员是允许的。SOW 仍会渲染合法的空索引（配了 key 就带签名）——空的
`Packages` 配可验签的 `InRelease`，或每架构的空 `repodata/`。

## --skip

`--skip` 提交期望状态变更并把仓库标为 dirty，不触碰公开树。旧的 Built Generation 对客户端依然完全
自洽。

```console
sow rm 'rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64' --skip -r demo -d el9
removed repository=demo operation=314678479940914827 dists=el9 memberships=1 revision=4 generation=00000000000000000004 dirty=true changes=0
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead
```

```console
sow status -r pigsty
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5 dirty_dists=el9 pending=0/0 locked=false
```

`changes` 为空是因为什么都没构建。执行 [`sow build`](/zh/docs/command/build/) 收敛。

## 与策略的交互

移除属于期望状态编辑，因此策略会在新的候选集上重新求值——移除操作绝不会让先前被 `limit` 挤掉的包
复活。如果你从一个 `limit: 1` 的 Dist 里删掉 `libpq5 18.3-1`，`18.2-1` 不会回来；需要重新显式 add。

## 示例

安全下架——先预览，再执行：

```bash
sow rm patroni -r pgsql -d el9 -c
sow rm patroni -r pgsql -d el9
```

一次从两个 Dist 中移除同一个精确对象：

```bash
sow rm sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab -r pgsql -d el9 -d el9-beta
```

批量移除后只重建一次：

```bash
sow rm old-tool legacy-agent -r pgsql -d el9 --skip
sow build -r pgsql -d el9
sow check -r pgsql
```

把预览计划喂给其他工具：

```bash
sow rm patroni -r pgsql -d el9 -c --json | jq -r '.result.changes[] | "\(.phase)\t\(.op)\t\(.path)"'
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 成员已移除并重建，或 `--check` 预览已打印 |
| `1` | 运行时 I/O 或渲染失败 |
| `2` | 用法错误——`--check` 与 `--skip` 同用、`--check` 与锁参数同用、选择有歧义、工作区未找到 |
| `4` | 仓库锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | 完整性或恢复错误 |
| `6` | 引用无匹配，或非裸名的引用有歧义；整批拒绝，不删除任何成员 |

## 参见

- [包引用](/zh/docs/reference/package-ref/) —— 完整引用文法
- [`sow ls`](/zh/docs/command/ls/)、[`show`](/zh/docs/command/show/) 与 [`where`](/zh/docs/command/where/) —— 找到要移除的精确引用
- [sow add](/zh/docs/command/add/) —— 反向操作
- [sow build](/zh/docs/command/build/) —— `--skip` 之后的收敛
- [成员策略](/zh/docs/feature/policy/) —— 为什么被移除的成员不会复活
- [`sow retain`](/zh/docs/command/retain/) 与 [`sow gc`](/zh/docs/command/gc/) —— 何时可以回收字节
