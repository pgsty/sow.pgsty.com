---
title: "Managed 工作区"
linkTitle: "Managed 工作区"
description: "工作区 → 仓库 → Dist 三层模型、固定磁盘布局、sow.yml 如何驱动一切,以及发现与选择规则。"
url: "/zh/docs/feature/managed/"
weight: 300
icon: fa-solid fa-sitemap
---

当同一个仓库要维护好几个月 —— 包成批到达、由策略决定谁留下、事后还得说清楚什么时候变了什么 —— 你需要的是 Managed 模式。本页讲三层模型、它产出的布局,以及命令怎么判断你说的是哪个仓库、哪个 Dist。

## 三个层级

```text
Workspace 工作区                    发现与配置边界
└── Repository 仓库                 所有权边界:pool、dists、SQLite、锁、Generation
    └── Dist 发行版                 单一格式的具名成员集合
        └── Architecture View 架构视图   渲染投影 —— 不是成员关系
```

每层只做一件事,边界很硬:

**工作区(Workspace)**只拥有两样东西:根级 `sow.yml` 和 `.sow/` 状态目录。工作区根下其他任何东西都不属于 SOW。它是发现的单位 —— 命令从某个起始目录向上找到工作区 —— 也是架构许可表所在的地方。

**仓库(Repository)**固定在 `<workspace>/<name>`。你不能把它指到别处,没有 `path` 选项。一个 Repository 拥有自己的 `pool/`、`dists/`、SQLite、锁、恢复状态、Generation、保留代根、发布 checkpoint 与 GC 证据。两个 Repository 之间永不去重 —— 同一个包 add 进两个仓库就存两份,这是刻意的:这样删掉一个仓库永远不可能伤到另一个。

**Dist** 是一个单一格式(`rpm` 或 `deb`)的普通具名成员集合。名字对 SOW 是不透明字符串。`el9`、`trixie`、`el9-beta`、`customer-acme` —— 它们都不产生状态机、晋升流程或快照。想要一个 beta 频道,就建一个叫 `el9-beta` 的 Dist;含义存在于你的脑子和 `.repo` 文件里,不在 SOW 里。

**架构视图(Architecture View)**是 `build` 渲染出来的东西,不产生第二份成员关系。一个 `noarch` RPM 只有一个包对象、一条成员记录,构建时投影进每个适用视图。参见[包池与架构视图](/zh/docs/feature/views/)。

一个 Repository 可以同时拥有 RPM Dist 与 DEB Dist,共用同一个 `pool/`。

## 磁盘布局

Managed 路径从不由用户输入拼装,而是由解析后的真实工作区根、已校验的名称和固定相对片段推导出来 —— 这就是为什么符号链接替换和路径逃逸没有可攻击的面。

```text
<workspace>/
├── sow.yml                       # 唯一的配置文件
├── .sow/                         # 私有状态;绝不要对外服务
│   ├── workspace.lock
│   ├── workspace-ops/            # 工作区生命周期 journal
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db                 # 每个仓库一个 SQLite
│   └── <repo>/
│       ├── stage/                # 同文件系统的 staging 区
│       ├── recovery/             # 删除动作的原子移入目标
│       └── pending/              # --skip 的耐久 payload
└── <repo>/                       # 可对外服务的树
    ├── pool/                     # 不可变包字节
    └── dists/
        └── <dist>/               # 架构视图渲染在这里
```

执行过两次 `dist new` 与两次 `add` 之后的真实工作区:

```console
$ find .sow | sort
.sow
.sow/pigsty
.sow/pigsty.db
.sow/pigsty.db-shm
.sow/pigsty.db-wal
.sow/pigsty/pending
.sow/pigsty/recovery
.sow/pigsty/stage
.sow/repo-locks
.sow/repo-locks/pigsty.lock
.sow/workspace-ops
.sow/workspace.lock
```

`<repo>/` 下的一切是交付树 —— 你 rsync 或对外服务的就是它。`.sow/` 下的一切是私有状态,绝不能暴露;[对外服务](/zh/docs/tutorial/serving/)给出了在 nginx 里屏蔽它的写法。

名称必须匹配 `[a-z0-9][a-z0-9._-]*`,`.`、`..`、`.sow`、`pool`、`dists` 以及工作区保留名一律拒绝。

## `sow.yml` 驱动一切

只有一个配置文件,用严格 decoder 解析。未知字段不会被忽略 —— 它会失败。重复的规范化架构、非法名称或 format、Dist 架构不是工作区许可表的子集、非法 glob 或分类、不完整的 signing 块,同样失败。

```yaml
schema: sow/v3
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
targets:
  local:
    repository: pigsty
    provider: filesystem
    endpoint: file:///srv/mirror
    prefix: pigsty
    public_endpoint: file:///srv/mirror/pigsty/
    max_cache_ttl: 0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

`config show --all` 展开全部默认值与规范化别名,让你看到 SOW 实际的决定:

```console
$ sow config show --all
schema: sow/v3
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    protected: false
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
      trixie:
        format: deb
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

架构别名只在解析边界规范化一次:`amd64 → x86_64`,`arm64 → aarch64`。输出永远是 canonical family。生态名只在渲染出来的 DEB 视图目录名里出现(`binary-amd64`、`binary-arm64`)。

`config check` 不是 YAML lint。它会打开每个已初始化 Repository 的 SQLite,把候选配置与实际的 Dist、架构、成员集、Built 状态和签名可用性逐项比对。移除仍被成员或 Built 状态引用的架构族是预期拒绝(退出码 `6`);数据库或协议证据损坏是完整性错误(退出码 `5`)。每个写命令在写 journal 之前都跑同一套预检,所以 `config check` 能提前告诉你下一条 `add` 会不会被拒。

```console
$ sow config check
configuration valid: /data/ws repositories=1 dists=2
```

完整 schema(包括 `filesystem` 与 `r2` 发布目标)见
[`sow.yml` 配置参考](/zh/docs/reference/config/)。

## 发现:哪个工作区?

Managed 命令按以下顺序寻找最近祖先中的 `sow.yml`:

1. 给了 `-C/--workdir DIR`:只从 `DIR` 向上找。找不到就失败 —— 不会回退到当前目录。
2. 否则从当前目录向上找。
3. 仍未找到:从 `$SOW_DIR` 向上找。
4. 还是没有:失败,并提示 `sow init`、`--workdir` 与 `SOW_DIR`。

找到第一个 `sow.yml` 就停,不会越过它继续往上找"更好的那个"。

`--workdir` 不是 `chdir`。它只改变发现的起点。`sow add` 里的相对 `PATH` 仍然相对你真实的当前目录解析 —— 这正是 `sow add ./build/*.rpm -C /srv/ws` 应有的行为。

`sow create` 不参与上述任何一步。

## 选择:哪个仓库、哪个 Dist?

Repository 选择,按序:

1. 显式 `-r/--repo NAME`。
2. 命令起始目录位于 `<workspace>/<repo>/` 内。
3. 工作区只有一个 Repository。
4. 否则失败并列出候选。

Dist 选择,按序:

1. 一个或多个显式 `-d/--dist NAME`(可重复)。
2. 起始目录位于 `<workspace>/<repo>/dists/<dist>/` 内。
3. 选定 Repository 只有一个 Dist。
4. 否则失败并列出候选。

关键的不对称在这里:没给 `-d` 时,`build`、`check`、`status` 默认作用于选定 Repository 的**全部** Dist —— 对这几个命令而言,"没有过滤条件"解释成"全都要"是安全的。而 `add`、`rm`、`ls` 必须得到明确的 Dist 集合,因为猜一个包该落到哪里并不安全:

```console
$ sow ls
workspace discovery error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

退出码 `2`。所有推断都在路径类型与符号链接校验之后才进行。

## `init` 只做收敛,不做重置

`sow init` 的幂等性是设计出来的,它的规则是架构不变式而不是使用便利:

- **没有 `sow.yml`:** 创建一个,写入 `schema: sow/v3` 与 `architectures: [x86_64, aarch64]`,同时创建 `.sow/`。不自动创建任何 Repository。
- **已有合法配置:** 按稳定名称顺序补齐尚未初始化的部分 —— 缺失的 Repository 外壳、缺失的 SQLite、整个缺失的 Dist。新建的 Dist 立刻生成其当前有效架构的全部空视图。
- **已有有效数据库状态或有效协议指针:** 只校验。绝不覆盖、绝不清零 Generation、绝不重写字节。
- **Dist 已初始化之后又往配置里加了架构:** `init` 不渲染新视图、不推进 Generation。该 Dist 保持 dirty,等待显式 `build`。移除仍被成员或 Built 状态使用的架构族则失败。

```console
$ sow init .
initialized /data/ws: config_created=false repositories_initialized=0 dists_initialized=0
```

第三、第四条规则的意义在于:`init` 必须能安全地在装着真实内容的仓库上执行。它朝声明的配置收敛,但绝不会拿"还没初始化"当借口去重建一个本来就好好的东西。

对象按稳定顺序处理。如果靠前的配置、Repository 或 Dist 已经耐久提交,而靠后的对象失败了,已提交的计数会被保留:人类输出先报告已提交的结果,`--json` 保留结构化 result,命令以 `3`(部分成功)退出。如果此时还没有任何东西提交过,则按原始错误类别退出。

## 空 Dist 就是可消费的合法状态

`dist new` 建出来的 Dist,在你 add 第一个包之前就已经能被客户端消费。RPM Dist 每个架构族有一份合法的空 `repodata`;DEB Dist 有 `Packages`、`Packages.gz`、by-hash 条目和 `Release`。如果 Repository 配了元数据密钥,空 Dist 也一样签名。

这件事比听上去重要。它意味着"现在就把客户端指过去,内容以后再填"是可行的;也意味着从 Dist 里移除最后一个包之后,留下的是一份合法的已签名空索引,而不是一个坏掉的索引。

## Protected 仓库

```yaml
repos:
  pigsty:
    protected: true
```

`protected: true` 会拒绝 `repo rm`,即使加了 `-f`,返回退出码 `6`。它不限制别的:`add`、`rm`、`build` 和常规 Dist 维护照常。真要删这个 Repository,你必须先改 `sow.yml`、通过 `config check`,然后才能删 —— 这个摩擦正是该 flag 存在的意义。

## 继续阅读

- [包池与元数据视图](/zh/docs/feature/views/) —— `build` 到底写了什么
- [发布模型](/zh/docs/design/publication/) —— Generation 如何抵达目标
- [成员策略](/zh/docs/feature/policy/) —— `exclude` 与 `limit` 如何决定谁留下
- [第一个工作区](/zh/docs/start/workspace/) —— 本页的十分钟动手版
- [`sow.yml` 配置参考](/zh/docs/reference/config/) —— 完整 schema
