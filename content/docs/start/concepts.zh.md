---
title: "核心概念"
linkTitle: "核心概念"
description: "SOW 背后的模型:两种模式、四个层级,以及期望成员集与已构建代的分离。"
url: "/zh/docs/start/concepts/"
weight: 400
icon: fa-solid fa-diagram-project
---

跑完[快速上手](/zh/docs/start/quickstart/)、搭完[第一个工作区](/zh/docs/start/workspace/)之后,
只需要少数几个概念就能解释 SOW 的其余全部行为。本页讲清楚这些:两种模式与如何选型、
Managed 模型的四个层级,以及"你要什么"与"当前发布了什么"之间的分离。

## 建仓的两种方式

SOW 有两套互不相干的引擎。Plain 模式不读 `sow.yml`、不做工作区发现、不建数据库;
Managed 模式也绝不把一个普通目录当成仓库。选哪一条,是你要做的第一个决定。

| | Plain 平面模式 | Managed 托管模式 |
|---|---|---|
| 入口命令 | `sow create DIR` | `sow init`、`repo`、`dist`、`add`、`rm`、`build` |
| 布局 | 包与索引同处一个平面目录 | `pool/` 存字节,`dists/` 存发布视图 |
| 持久状态 | 无 —— **目录本身就是状态** | `sow.yml`、每仓库一份 SQLite、操作日志 |
| 你控制的对象 | 目录里放了哪些文件 | 哪些包是哪个 Dist 的成员 |
| 格式 | RPM 与 DEB 可同处一目录 | 每个 Dist 单一格式 |
| 架构 | 单一平面索引,不拆分 | 每个架构一个视图 |
| APT `by-hash` | 不支持 | 支持 |
| 签名 | RPM 包体签名(`--sign-with`) | RPM 与 DEB 元数据签名,外加 RPM 包体签名策略 |
| 成员策略 | 无 | `exclude` 模式排除 + `limit` 版本上限 |
| 审计 | 无 | 操作账本,可导出 JSONL |
| 更新成本 | 重扫整个目录 | 只重建受影响的 Dist |
| 对标传统工具 | `createrepo_c` + `dpkg-scanpackages` | `reprepro` |

当目录里**已经恰好**是你想发布的内容时,选 Plain:构建产物、从上游镜像拉下来的目录、
刻进光盘的离线包集。
一条命令,没有任何东西需要长期维护。

当你需要决定**哪些**包该进仓库时,选 Managed:一棵树里多个发行版、按架构分视图、
"每个包只留最新两个版本"、元数据签名,或者需要留下谁在什么时候改了什么的记录。

## Managed 层级模型

四个层级,各自拥有明确的东西:

```text
Workspace 工作区              /srv/sow
│  sow.yml   本工作区包含什么 —— 唯一事实来源
│  .sow/     锁、每仓库 SQLite、操作日志(绝不对外服务)
│
└── Repository 仓库           /srv/sow/pigsty
    │  拥有一个包池、一个数据库、一把锁
    │  与同级仓库之间不共享任何软件包对象
    │
    ├── pool/                 内容不可变的包体,每个对象只存一份
    │
    └── Dist 发行版           /srv/sow/pigsty/dists/el9
        │  单一格式(rpm 或 deb)的具名成员集合
        │
        ├── Architecture View 架构视图   dists/el9/x86_64/    x86_64 成员 + noarch
        └── Architecture View 架构视图   dists/el9/aarch64/   aarch64 成员 + noarch
```

**工作区(Workspace)** 只是发现与配置的边界,仅此而已。它在根目录只拥有两样东西:
`sow.yml` 和 `.sow/`。命令通过从当前目录逐级向上查找来定位它。

**仓库(Repository)** 是工作区根下的一个子目录,也是隔离单元。包池、数据库、锁、
恢复状态全都归它自己。两个仓库之间从不互相去重,正是这一点让删除其中一个变得安全。

**Dist** 是单一格式的具名软件包集合。名字就是一个普通标签 —— `el9`、`trixie`、`staging` ——
不附带任何内建的生命周期或晋级状态机。它是你的用户在 URL 里看到的那一段。

**架构视图(Architecture View)** 是 Dist 的渲染投影,不是另一份成员集合。把一个包加进 `el9`
只加一次,由 build 决定它出现在哪些视图里。RPM 视图用 family 规范名 `x86_64` 与 `aarch64`;
DEB 视图用生态名 `binary-amd64` 与 `binary-arm64`。你在配置或命令行里写 `amd64` / `arm64` 时,
SOW 在解析边界把它规范化成 `x86_64` / `aarch64`,此后一律输出规范名。

`noarch` 与 `all` 包是**中性(neutral)投影**,不是第三种架构。一个 `noarch` RPM 只有一个对象、
一条成员记录,build 把它投影进每个适用视图 —— 这就是 `pev2` 同时出现在 `x86_64/` 与
`aarch64/` 下的原因。

## 字节只存一份

包体只在仓库的 `pool/` 下存一份,按 Debian 惯例以首字母 + 源码包名分组。架构视图用**硬链接**
而不是副本引用这些字节,所以一个出现在两个视图里的 `noarch` 包链接数为 3,磁盘上仍只占一份空间。

这就是同一仓库的 `pool/` 与 `dists/` 必须位于同一文件系统的原因。硬链接不可用、或目标在另一个
设备上时,SOW 直接失败,不会静默退化成复制。用不保留硬链接的普通 `cp -r` 或 `rsync` 复制走,
仓库功能依然完好 —— 只是丢掉了去重带来的容量优势。

因为视图里放的是真实文件,`repodata` 里的包位置就是 `pool/p/pev2/…` 这样的相对路径,
不含逃出视图根的 `..`。正是这个细节让 `dnf reposync` 能正确镜像 SOW 仓库。

对象以其**确切字节**的 SHA-256 标识。它的逻辑坐标 —— RPM 是 NEVRA,DEB 是 `name=version:arch` ——
来自 RPM 头或 Debian control 文件,绝不来自文件名。一个被改名的包仍按它实际的身份建索引。
两个声称同一坐标但内容不同的包会被拒绝,而不是被悄悄合并。

## 期望成员集 vs 已构建代

这是 Managed 模式的核心。两种状态,分别追踪:

**期望成员集(Desired Membership)** 是你要什么。`add` 与 `rm` 维护它,并推进一个叫
`revision` 的计数器。它是纯逻辑集合 —— 包 X 属于 Dist Y —— 不涉及任何文件。

**已构建代(Built Generation)** 是 `pool/` 与 `dists/` 下当前实际发布的内容。`build` 产出它,
并推进一个单调递增的计数器 `generation`。

```text
sow add / sow rm  ────▶   期望成员集 Desired      revision 5
                                  │
                              sow build
                                  │
                                  ▼
                          已构建代 Built           generation 5
                                  │
                                  ▼
                          pool/ + dists/           可直接复制交付
```

当 Desired 领先于 Built 时,该 Dist 处于 **dirty(待构建)** 状态。`add` 与 `rm` 默认在返回前
完成构建,所以你很少见到 dirty 仓库。想攒几批变更再统一构建时,加 `--skip`:

```bash
sow add pkg/asciinema-3.2.1-1.x86_64.rpm -r pigsty -d el9 --skip
```

```console
add repository=pigsty operation=4281492977639306333 accepted=1 failed=0 memberships=+1/-0 revision=5 generation=4 dirty=true
item input="pkg/asciinema-3.2.1-1.x86_64.rpm" status=accepted format=rpm coordinate="asciinema-0:3.2.1-1.x86_64" sha256:11f56fbd54f23ce1b8d8866c67a91e0819bac3fa22d2ace681b411ac0fe26703 dists=el9:accepted
```

revision 走到 5,generation 停在 4,公开树字节不变 —— 新包待在客户端看不到的私有 pending 区:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4 dirty_dists=el9 pending=1/4429718 locked=false
```

关键信号是 `ready_to_copy=false`。dirty 不等于损坏 —— 磁盘上那一代 Built 完整且完全可对外服务 ——
它只是还没反映你最新的意图。`sow check` 把这判定为不可交付,退出码 `5`:

```console
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

准备好之后再收敛:

```bash
sow build -d el9
```

```console
{"operation":"1543183855804634265","repository":"pigsty","dists":["el9"],"desired_revision":5,"built_generation":5,"noop":false,"dirty":false}
```

```bash
sow status
```

```console
repository=pigsty status=clean ready_to_copy=true revision=5 generation=5 dirty_dists= pending=0/0 locked=false
```

Dist 变 dirty 的原因不止成员变化,**渲染输入**变化同样算:新增一个架构、改动 `exclude` 规则或
`limit` 上限、更换签名密钥,都会改变渲染器的产出,于是 SOW 把该 Dist 标记为 dirty 并等待你显式
`build`。没有任何东西会在你背后自动重建。

## 代际与变更计划

每一次真正改变了文件的 build 产生一个新的 generation。generation 单调递增,并且 SOW 会在磁盘上
把上一代的 metadata 文件与当前代并存 —— 刚开始下载的客户端能把这一轮拉完。`repomd.xml` 与
`Release` 永远只指向当前代。

`sow changes` 给出任意 base 代到当前代之间的物理差异,这正是你同步时需要的文件清单:

```bash
sow changes 4
```

```console
base=4 generation=5 dirty=false
add	payload	dists/el9/x86_64/pool/a/asciinema/asciinema-3.2.1-1.x86_64.rpm	4429718	11f56fbd54f23ce1b8d8866c67a91e0819bac3fa22d2ace681b411ac0fe26703
add	payload	pool/a/asciinema/asciinema-3.2.1-1.x86_64.rpm	4429718	11f56fbd54f23ce1b8d8866c67a91e0819bac3fa22d2ace681b411ac0fe26703
add	metadata	dists/el9/x86_64/repodata/26435ad6857a58369efe0b5ddfb955c1023c0af7d2a2cde9501b877c41728d58-filelists.xml.gz	795	26435ad6857a58369efe0b5ddfb955c1023c0af7d2a2cde9501b877c41728d58
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1514	ce90e820933f3daab456904a4531b54466ef28c50fbc87b1a6863d8bb42c3ff6
delete	delete	dists/el9/x86_64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz	0	
```

*(输出节选 —— 完整清单覆盖两个架构视图)*

第二列的四个阶段是一个**顺序**,也正是 SOW 自己写盘时使用的顺序:先 `payload`,再 `metadata`,
然后 `pointer`,最后 `delete`。先把字节发布出去、此时还没有任何东西引用它;等入口指向的内容
全部就位后再一次性换掉入口;最后才删除不再被引用的旧文件。按这个顺序应用计划的镜像端,
即使执行到一半也永远不会处于自相矛盾的状态。

`sow changes 0` 给出当前完整公开树的全量 add 集,适合用来初始化一个新镜像。

## 失败关闭(fail-closed)

SOW 宁可拒绝也不猜。分辨不出你指的是哪个仓库,它就明说,而不是随便挑一个。包被截断、
或包头与内容自相矛盾,整批输入一起拒绝,仓库保持 clean。记录的状态与磁盘上的文件对不上,
那是完整性错误,而不是可以悄悄"修复"的事情。

每个写操作都在触碰任何公开文件之前把意图写进持久日志,所以被中断的命令留下的是**可恢复状态**,
而不是写了一半的树。下一条写命令会先把上一个未完成的操作前滚或回滚,再执行自己的工作。
公开树永远不会撕裂。

退出码承载了这些区分,方便脚本据此分支:

| 码 | 含义 |
|---|---|
| `0` | 成功,或无事可做 |
| `1` | 运行时 I/O、解析器或渲染器错误 |
| `2` | 用法、发现或配置错误 |
| `3` | 部分成功 —— 已提交部分合法工作 |
| `4` | 锁不可用 |
| `5` | 完整性/恢复错误,或当前结果不可交付(含 dirty) |
| `6` | 预期拒绝 —— 冲突、protected、无匹配、架构不兼容 |

完整说明见[退出码](/zh/docs/reference/exit-codes/)。

## 继续深入

- [Plain 平面仓库](/zh/docs/feature/plain/) —— `sow create` 的保证,以及确定性输出如何实现。
- [Managed 工作区](/zh/docs/feature/managed/) —— 三层模型、固定布局与发现规则。
- [包池与架构视图](/zh/docs/feature/views/) —— 硬链接投影与 reposync 兼容性。
- [成员策略](/zh/docs/feature/policy/) —— `exclude` 与 `limit` 的精确语义。
- [签名模型](/zh/docs/feature/signing/) —— 两条互相独立的信任链。
- [事务与恢复](/zh/docs/feature/transactions/) —— 日志、锁与崩溃行为。
- [可观测与审计](/zh/docs/feature/audit/) —— `status`、`check`、`changes` 与操作账本。
