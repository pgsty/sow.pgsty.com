---
title: "sow build / status / check / changes"
linkTitle: "build / status / check / changes"
description: "把期望状态收敛成新的已构建代，以及告诉你当前处境的三条命令。"
url: "/zh/docs/reference/cli/build/"
weight: 900
icon: fa-solid fa-hammer
---

`status` 是低成本读取，`check` 是完整校验，`build` 是显式的 Desired-to-Built 收敛命令，
`changes` 给出 Generation 之间的物理文件差分。其他写命令也可能直接落成新 Generation；
这四条仍构成主要的观察与收敛闭环。

## 语法

```text
sow status [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow build [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
sow check [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow changes [BASE_GENERATION] [-C|--workdir DIR] [-r|--repo NAME] [--json]
```

## 状态模型

每个仓库同时维护两样东西：SQLite 中的 **Desired Revision（期望修订）**，以及磁盘上 `dists/` 树所
对应的 **Built Generation（已构建代）**。

| 状态 | 含义 | 客户端看到什么 |
|---|---|---|
| `clean` | Desired 与 Built 一致 | 每个视图都是最新且完整的 |
| `dirty` | Desired 领先——来自 `--skip` 或配置变化 | 旧的 Built 视图，仍然完整 |
| `recovering` | 存在未完成的 Operation，下一条写命令必须先恢复 | 最后一次完成的协议指针 |
| `error` | 自动恢复无法安全判定，需要人工介入 | 最后一次完成的视图，永不被覆盖 |

dirty 从不意味着索引写了一半。客户端永远沿协议指针读到一个完整的旧视图或完整的新视图。

## sow status

便宜、只读、不做哈希。报告仓库状态、Desired Revision、Built Generation、dirty 的 Dist、pending
载荷的数量与字节数、最近一条 Operation，以及锁状态。

```console
sow status
repository=pigsty status=clean ready_to_copy=true revision=11 generation=12 dirty_dists= pending=0/0 locked=false
```

```console
sow status -r pgsql
repository=pgsql status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=trixie pending=4/2326 locked=false
```

`ready_to_copy` 是低成本状态指标：为 false 时绝不能发布；为 true 也不等于深度完整性证明，
交付前仍须通过 `sow check`。

**只要状态可读，`status` 在任何状态下都返回 `0`**——clean、dirty、recovering、error 一视同仁——好让
脚本消费结构化状态而不是解析错误。只有状态数据库无法读取或解析时才返回非零（完整性错误）。需要
硬门禁时用 `sow check`。

```console
sow status -r demo --json
{"schema":"sow.cli/v1","command":"status","ok":true,"repository":"demo","operation":null,"result":{"repository":"demo","status":"dirty","ready_to_copy":false,"desired_revision":5,"built_generation":"00000000000000000004","dirty_dists":["el9"],"dirty_reasons":["dist el9 Desired and Built membership sets differ","one or more dists differ from their built projections"],"pending":{"count":1,"bytes":19776},"recent_operation":{"id":"3329269325810066022","kind":"add","state":"done_dirty","created_at":"2026-08-04T04:10:22.481991Z","updated_at":"2026-08-04T04:10:22.553516Z"},"repository_locked":false},"errors":[]}
```

`status` 从不执行恢复，也绝不把"存在一个旧但自洽的 Generation"误报为索引损坏。

## sow build

取得仓库写锁，先恢复任何未完成的 Operation，再把当前期望状态收敛成新的 Built Generation。

```console
sow build -r pgsql -d el9
{"operation":"4262183287563704350","repository":"pgsql","dists":["el9"],"desired_revision":6,"built_generation":"00000000000000000006","noop":false,"dirty":false}
```

| 参数 | 说明 | 默认 |
|---|---|---|
| `-j, --jobs N` | 并发 worker 数 | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 全部 Dist |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出版本化 JSON envelope | false |

不给 `-d` 时，`build` 收敛该仓库全部受影响的 Dist；给了 `-d` 则只收敛选中的，其余保持 dirty。

与 `rm`、`show` 一样，`build` 即使不加 `--json` 也在 stdout 打印结构化 JSON。

### 空操作构建

输入与 renderer 配置都没变时，`build` 什么也不做，也不推进 Generation：

```console
sow build
{"operation":"6295064788473690577","repository":"pigsty","dists":["el9","trixie"],"desired_revision":5,"built_generation":"00000000000000000005","noop":true,"dirty":false}
```

### 策略收敛是单向的

`build` 会重新执行当前策略，因此改完 `sow.yml` 里的 `limit` 或 `exclude` 后跑 `build` 就是应用它们
的标准做法。收紧策略会移除成员；放宽策略*不会*从 pool 里残留的字节反推出历史成员——请重新执行
`sow add`。

### 提交顺序

所有元数据先在同一文件系统上 stage、验证、签名，然后才切换。协议指针——RPM 的 `repomd.xml`、APT 的
`Release`/`InRelease`——最后替换；checksum 命名的元数据配合 APT by-hash，保证新旧客户端都不会取到
悬空引用。

一个 build Operation 可以覆盖多个 Dist。SOW 不承诺并发读者在同一瞬间看到所有 Dist 一起翻代；它承诺
的是每个协议视图始终自洽，且命令返回后本次 Operation 包含的全部 Dist 属于同一个
Built Generation。

### 恢复

`build` 是唯一显式的前滚恢复入口。它会先尝试完成或回滚可判定的非终态 Operation。`error` 状态专指
journal、数据库与文件证据互相矛盾、工具无法安全选择的情况——此时 `build` 拒绝覆盖，你需要从备份恢复
后再跑 `check`/`build`。没有可能猜错的 `repair --force`。

### 元数据签名

Managed 模式的元数据签名只由 `sow.yml` 控制，命令行没有覆盖开关。RPM 架构视图始终生成
`repodata/repomd.xml`；配置了 `signing.rpm.metadata.key` 时同时生成 ASCII-armored 的
`repodata/repomd.xml.asc`。DEB Dist 始终生成 `Release`；配置了 `signing.deb.metadata.key` 时同时
生成 clearsigned 的 `InRelease` 与分离式的 `Release.gpg`。改动 key 引用或 fingerprint 会让相关
Dist 变 dirty，下一次 `build` 重新签名并产生新的 Generation。

## sow check

对选定 Repository 与 Dist 做完整只读校验。v0.2.0 Repository 报告九个有序层。

```console
sow check
repository=pigsty status=clean ready_to_copy=true revision=5 generation=5
config	ok=true	checked=5
retained	ok=true	checked=0
state	ok=true	checked=1
public-modes	ok=true	checked=67
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=8
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=1
```

| 层 | 校验内容 | `checked` 计的是 |
|---|---|---|
| `config` | 该仓库的 `sow.yml` 可解析且通过校验 | 配置对象数 |
| `retained` | 显式保留 Generation 记录与冻结 manifest 可验证 | 保留记录数 |
| `state` | SQLite `quick_check`、外键，以及 journal/恢复证据 | 恒为 1 |
| `public-modes` | 对外服务目录树的文件与目录权限 | 检查的路径数 |
| `package-bytes` | 每个 pool 与 pending 载荷的 SHA-256 | 包对象数 |
| `desired-membership` | Membership 行在当前策略下能解析到真实对象 | 成员数 |
| `index` | 渲染出的索引与其声称的成员集一致 | Dist 数 |
| `signature` | 所有声明的签名都能验证通过 | 签名数 |
| `generation-manifest` | Built Generation Manifest 与磁盘文件一致 | 1 份 Manifest |

| 参数 | 说明 | 默认 |
|---|---|---|
| `-j, --jobs N` | 并发 worker 数 | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 全部 Dist |
| `--json` | 输出版本化 JSON envelope | false |

`check` 从不修复、从不构建、从不恢复 Operation。

### dirty 就是校验失败

仓库 dirty 时，`check` 会分别校验期望状态与旧的已构建代——然后判定该树尚不可交付，退出 `5`：

```console
sow check
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5
config	ok=true	checked=5
retained	ok=true	checked=0
state	ok=true	checked=1
public-modes	ok=true	checked=67
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=7
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=1
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

终态各层全过。这里的退出码 `5` 意思是"旧树完好，但它不是你要的东西"——去跑 `build`。这正是发布流水线
里应该有的门禁。

## sow changes

以交付计划的形式，打印两个已构建代之间的物理文件变化。

```console
sow changes
base=4 generation=5 dirty=false
add	payload	pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm	19776	ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16
add	metadata	dists/el9/x86_64/repodata/5bc463cb00bec4d6185ea593a6fa8f180f24d3251b498f5bbeb14875581c33cc-primary.xml.gz	1460	5bc463cb00bec4d6185ea593a6fa8f180f24d3251b498f5bbeb14875581c33cc
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1514	05d3d5bf0f9236626b22a8ae9c92853277fff506f5773fbc33316ea12683cf0b
delete	delete	dists/el9/x86_64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz	0
```

各列依次是 `op`、`phase`、相对 Repository 根的路径、大小与 SHA-256。`op` 取
`add`/`update`/`delete`；`phase` 取 `payload`/`metadata`/`pointer`/`delete`。这些 Phase 描述
SOW 如何在本地构建 Generation，不是远端事务协议。不要把行逐条重放到在线树；应使用
`sow publish`，或先完整复制到 staging，再原子切换。

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `--json` | 输出版本化 JSON envelope | false |

### BASE_GENERATION

不带参数时，`changes` 比较最近一个已构建代与它的前一代。

`changes 0` 给出当前已构建代的完整交付清单——`pool/` 与 `dists/` 下的每个文件，不含 `sow.yml`
与 `.sow/`：

```console
sow changes 0
base=0 generation=2 dirty=false
add	payload	pool/e/epel-release/epel-release-7-5.noarch.rpm	14524	d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab
add	metadata	dists/el9/aarch64/repodata/fb3777fe0da404b2ac78b26566e1eec95a4fc90f04b322e52925fc9baebb2764-primary.xml.gz	797	fb3777fe0da404b2ac78b26566e1eec95a4fc90f04b322e52925fc9baebb2764
add	pointer	dists/el9/x86_64/repodata/repomd.xml	1511	16d334bc2b1c20c27aac9f3a353b97018a994e55ef45acc90fa50dcf5b8268a4
```

超出范围的 base 会被拒绝：

```console
sow changes 99
operation rejected: managed: operation rejected: base generation 99 is outside 0..2
```

从未构建过任何东西的仓库输出空计划：

```console
sow changes -r empty
base=0 generation=0 dirty=false
```

### 只作用于仓库级

`changes` 是仓库级的 Generation 输出，拒绝 `-d`。只要某个 Dist 的话，按相对仓库根的路径过滤：

```console
sow changes -d el9
usage error: --dist is not allowed for changes
```

### dirty 与 recovering

dirty 的期望状态不进入 `changes`。输出会标记 `dirty=true`，终点仍然是当前的已构建代——私有 pending
载荷在这里不可见，因为它们还不属于可交付树：

```console
sow changes -r demo
base=3 generation=4 dirty=true
add	metadata	dists/el9/aarch64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz	140	0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f
```

仓库处于 `recovering` 或 `error` 时，`changes` 直接拒绝输出同步计划：未决的文件动作绝不能被当成一
个 Generation。

## 示例

标准的批量导入循环：

```bash
sow add /srv/build/ -R -r pgsql -d el9 --skip
sow status -r pgsql
sow build -r pgsql -j 12
sow check -r pgsql
```

用完整校验为发布把关：

```bash
sow check -r pgsql || { echo "不可交付"; exit 1; }
sow publish mirror
```

`mirror` 必须是该 Repository 已配置的 filesystem 或 R2 Target。使用其他传输方式时，应复制到
离线 staging 后原子切换，不能原地修改在线树。

导出 Generation Delta，用于审计或交付规划：

```bash
sow changes 41 -r pgsql --json > changes-41-current.json
```

最多等另一个写者 30 秒，然后放弃：

```bash
sow build -r pgsql -T 30s
```

## 退出码

| 命令 | 码 | 触发条件 |
|---|---|---|
| `status` | `0` | 状态可读——`clean`、`dirty`、`recovering`、`error` 一视同仁 |
| `status` | `2` | 工作区未找到或选择有歧义 |
| `status` | `5` | 状态数据库无法读取或解析 |
| `build` | `0` | 收敛成功，或无事可做 |
| `build` | `1` | 渲染、签名或 I/O 失败 |
| `build` | `2` | 用法错误或选择有歧义 |
| `build` | `4` | 锁不可用 |
| `build` | `5` | 恢复无法安全完成，或仓库处于 `error` |
| `build` | `6` | 配置拒绝当前状态，例如仍在使用的架构被从许可表中删除 |
| `check` | `0` | 九个终态层全过且可交付 |
| `check` | `1` | 校验过程中的 I/O 失败 |
| `check` | `2` | 用法错误或选择有歧义 |
| `check` | `5` | 某一层失败，或仓库 dirty 因而不可交付 |
| `changes` | `0` | 计划已打印，包括空计划 |
| `changes` | `2` | 给了 `-d`、选择有歧义，或工作区未找到 |
| `changes` | `5` | 仓库处于 `recovering` 或 `error` |
| `changes` | `6` | `BASE_GENERATION` 超出有效范围 |

## 参见

- [事务与恢复](/zh/docs/feature/transactions/) —— journal、锁模型与崩溃矩阵
- [可观测与审计](/zh/docs/feature/audit/) —— 这四条命令与 `sow log` 的配合
- [sow add](/zh/docs/reference/cli/add/) 与 [sow rm](/zh/docs/reference/cli/rm/) —— dirty 的来源
- [对外服务](/zh/docs/tutorial/serving/) —— 用 `ready_to_copy` 与 `changes` 做交付
- [退出码](/zh/docs/reference/exit-codes/) —— 为什么 dirty 仓库上的 `check` 退出 `5`
