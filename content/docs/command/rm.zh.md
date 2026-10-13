---
title: "sow rm"
linkTitle: "rm"
description: "从指定 Dist 移除软件包，或预览结果。"
categories: [Command]
tags: [cli, managed, policy]
url: "/zh/docs/command/rm/"
aliases: ["/docs/reference/cli/rm/"]
weight: 700
icon: fa-solid fa-minus
---

`sow rm` 从指定 Dist 移除软件包，并重建本地索引。使用 `--check` 预览删除结果，使用 `--skip` 延后构建。包文件仍保留在 `pool/` 中，由 [`sow gc`](/zh/docs/command/gc/) 回收不再需要的文件。

## 语法

```text
sow rm PACKAGE... [-c|--check] [--skip] [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-c, --check` | 预览移除结果，不修改仓库 | 关闭 |
| `--skip` | 只更新期望状态，不构建 | 关闭 |
| `-j, --jobs N` | 并发工作线程数 | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 按选择规则 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

`--check` 与 `--skip` 互斥：

```console
sow rm epel-release -c --skip
usage error: --check and --skip are mutually exclusive
```

## 包引用

`PACKAGE` 支持以下五种写法。完整格式与匹配规则见[包引用](/zh/docs/reference/package-ref/)，简版如下：

| 写法 | 示例 |
|---|---|
| 内容哈希 | `sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab` |
| RPM 坐标 | `rpm:epel-release-0:7-5.noarch` |
| DEB 坐标 | `deb:libpq5=18.3-1:amd64` |
| 完整文件名 | `epel-release-7-5.noarch.rpm` |
| 裸二进制包名 | `epel-release` |

裸包名匹配所选 Dist 中该名称的全部版本与架构。其他引用形式必须唯一标识一个对象。有歧义时，命令返回错误并列出候选项。

[`sow ls`](/zh/docs/command/ls/) 会直接打印精确的 `sha256:` 引用与规范化坐标，你不需要手工
拼接。

引用没有匹配的软件包时，命令返回错误：

```console
sow rm nosuch -r pigsty -d el9
operation rejected: managed: operation rejected: package reference not found: package reference "nosuch" matches no Desired Membership
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
以稳定的标准封装返回。

移除一个 Dist 的最后一个成员是允许的。SOW 仍会渲染合法的空索引（配了密钥就带签名）——空的
`Packages` 配可验签的 `InRelease`，或每架构的空 `repodata/`。

## 用 --check 预览

`-c/--check` 预览移除结果与本地文件变化，不修改仓库。`removed` 只列出引用匹配到的成员。如果当前策略连带移除了其他成员，`changes` 会包含相关索引变化；实际执行后，`sow log` 会将这些成员计入移除数量。

```console
sow rm centos-release -r demo -d el9 -c
preview repository=demo operation= dists=el9 memberships=2 revision=2 generation=00000000000000000003 dirty=false changes=2
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead
change op=update phase=pointer path="dists/el9/aarch64/repodata/repomd.xml" size=1509 sha256:1cfe38698967d11384f1a985618d75f5e690d1284accf951262fc663fa9afc81
change op=update phase=pointer path="dists/el9/x86_64/repodata/repomd.xml" size=1509 sha256:1cfe38698967d11384f1a985618d75f5e690d1284accf951262fc663fa9afc81
```

两个 `centos-release` 版本都被裸包名匹配。`change` 行描述预期的本地文件变化，按 `payload → metadata → pointer → delete` 排列。脚本可用 `--json` 读取 `removed[]` 与 `changes[]` 数组。

预览会校验候选配置与既有状态。它使用共享锁，可以等待写操作完成，但不接受 `--timeout` 或 `--no-wait`：

```console
sow rm centos-release -r pigsty -d el9 -c -T 5s
usage error: rm --check does not accept --timeout or --no-wait
```

## --skip

`--skip` 提交期望变更，公开目录保持不变。结果与已构建状态不同时，仓库为 dirty。如果移除的只是尚未构建的新成员，仓库也可能直接恢复为 clean。

```console
sow rm 'rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64' --skip -r demo -d el9
removed repository=demo operation=314678479940914827 dists=el9 memberships=1 revision=4 generation=00000000000000000004 dirty=true changes=0
membership dist=el9 name="centos-release" coordinate="rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64" sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead
```

```console
sow status -r pigsty
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5 dirty_dists=el9 pending=0/0 locked=false
```

`changes` 为空是因为什么都没构建。执行 [`sow build`](/zh/docs/command/build/) 构建待处理变更。

## 与策略的交互

移除后，SOW 对剩余成员重新执行策略。如果从 `limit: 1` 的 Dist 中移除 `libpq5 18.3-1`，先前被排除的 `18.2-1` 仍保持排除。需要恢复它时，运行 `sow add`。

## 示例

先预览移除结果，再执行：

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

将预览结果传给其他工具：

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
- [sow build](/zh/docs/command/build/) —— `--skip` 之后构建
- [成员策略](/zh/docs/feature/policy/) —— 如何重新添加被移除的成员
- [`sow retain`](/zh/docs/command/retain/) 与 [`sow gc`](/zh/docs/command/gc/) —— 何时可以回收包文件
