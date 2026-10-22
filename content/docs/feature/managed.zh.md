---
title: "Managed 工作区"
linkTitle: "Managed 工作区"
description: "工作区结构、包成员关系、配置、查找规则与初始化。"
categories: [Feature]
tags: [managed, repository, dist, generation]
url: "/zh/docs/feature/managed/"
weight: 300
icon: fa-solid fa-sitemap
---

定期更新的仓库适合使用 Managed 模式。SOW 记录包成员关系、执行 Dist 策略、构建元数据，
并保留操作历史。

<span id="三个层级" data-td-print-local></span>

## 工作区、仓库与 Dist

```text
Workspace（工作区）
└── Repository（仓库）
    └── Dist（软件包集合）
        └── Architecture view（架构视图）
```

| 术语 | 用途 |
|---|---|
| 工作区 | 保存 `sow.yml`、私有 `.sow/` 状态和允许的架构族 |
| 仓库 | 拥有独立包池、Dist、SQLite 数据库、构建快照（Generation）和发布状态 |
| Dist | 按名称组织一组包，格式为 `rpm` 或 `deb` |
| 架构视图 | 为某种架构的客户端提供 Dist 中的包索引 |

一个仓库可以同时包含 RPM 和 DEB Dist。`el9`、`trixie`、`el9-beta` 等 Dist 名称由你指定，
不会自动检查操作系统兼容性，也不会建立版本晋级流程。

同一包可以属于一个仓库中的多个 Dist，无需复制包文件。架构无关包在每个 Dist 中有一份
成员关系，并出现在该 Dist 的各个适用架构视图中。不同仓库分别保存自己的包对象。

<span id="磁盘布局" data-td-print-local></span>

## 公开文件与私有状态

```text
<workspace>/
├── sow.yml
├── .sow/
│   ├── workspace.lock
│   ├── workspace-ops/
│   ├── repo-locks/<repo>.lock
│   ├── <repo>.db
│   └── <repo>/
│       ├── stage/
│       ├── recovery/
│       ├── pending/
│       ├── retained/
│       └── transitions/
└── <repo>/
    ├── pool/
    └── dists/
```

对外服务或发布完整的 `<workspace>/<repo>/` 目录。`sow.yml` 和 `.sow/` 保持私有。
需要保留可继续工作的工作区时，一起备份配置、私有状态和包文件。
详见[仓库布局](/zh/docs/reference/layout/)。

<span id="sowyml-驱动一切" data-td-print-local></span>
<span id="protected-仓库" data-td-print-local></span>

## 创建与配置

```bash
sow init /srv/repo
sow repo new demo -C /srv/repo
sow dist new el9 --format rpm -r demo -C /srv/repo
sow dist new trixie --format deb -r demo -C /srv/repo
```

初始配置使用 `schema: sow/v3`，架构族为 `[x86_64, aarch64]`。
除非配置中已经声明仓库，`init` 不会创建仓库。仓库与 Dist 的创建、删除命令会更新 `sow.yml`。

编辑 `sow.yml` 设置架构限制、成员策略、签名和发布目标，然后检查配置：

```bash
sow config check -C /srv/repo
sow config show --all -C /srv/repo
```

解析器拒绝未知字段。`config check` 还会比较配置与已初始化状态，并解析签名引用。
`config show --all` 展开默认值。配置接受 `amd64`、`arm64`，分别规范化为
`x86_64`、`aarch64`；DEB 索引仍使用原生名称 `amd64`、`arm64`。

要防止整个仓库被删除，设置 `protected: true`。它会阻止 `repo rm`，包括带 `-f` 的调用，
但不限制包和 Dist 的修改。

<span id="空-dist-也有合法协议发布面" data-td-print-local></span>

## 期望状态与构建状态

期望状态记录各 Dist 应包含哪些包；构建状态记录最近完成的元数据构建快照。

默认情况下，`add` 和 `rm` 更新成员后会构建相关输出。带 `--skip` 时，只更新成员关系，
不构建。新包字节先保存在私有 `pending/` 中，构建时再进入包池。

```bash
sow add ./incoming/ -C /srv/repo -r demo -d el9 --skip
sow status -C /srv/repo -r demo
sow build -C /srv/repo -r demo
sow check -C /srv/repo -r demo
```

`dirty` 表示仓库需要构建，公开目录仍对应上一次完成的构建快照。
策略、架构或签名变化也会使 Dist 变脏。成员关系或构建状态仍引用某个架构时，不能从配置删除它。

新 Dist 会立即获得各架构的有效空索引。已配置元数据签名时，空 Dist 也会签名。
移除最后一个成员后，索引为空，但入口仍保留。

<span id="发现哪个工作区" data-td-print-local></span>

## 查找工作区

Managed 命令按以下顺序查找最近祖先目录中的 `sow.yml`：

1. 指定 `-C/--workdir DIR` 时从 `DIR` 开始，否则从当前目录开始。
2. 没有找到工作区时，从 `$SOW_DIR` 开始查找。
3. 两次都没有找到时，返回工作区发现错误。

命令使用找到的第一个配置，即使该配置有错误。`--workdir` 只改变工作区查找起点，
不改变进程目录。相对输入路径仍相对于当前目录：

```bash
sow add ./build/example.rpm -C /srv/repo -r demo -d el9
```

查找起点可以是符号链接，但搜索沿输入路径的祖先目录进行。工作区内的符号链接会阻止
隐式推断仓库或 Dist。需要时使用物理工作区路径，并明确指定 `-r`、`-d`。

Plain 命令 `sow create` 不参与工作区查找。

<span id="选择哪个仓库哪个-dist" data-td-print-local></span>

## 选择仓库与 Dist

仓库选择使用第一个可用结果：

1. 显式 `-r/--repo NAME`。
2. 工作区查找起点所在的仓库。
3. 工作区中唯一的仓库。

`add`、`rm` 和 `ls` 按以下顺序选择 Dist：

1. 显式 `-d` 参数；可重复使用，选择多个 Dist。
2. 工作区查找起点所在的 Dist。
3. 所选仓库中唯一的 Dist。

如果仍有多个选择，命令要求显式指定。

`build`、`check` 和 `status` 默认覆盖所选仓库的全部 Dist。
`show` 搜索所选仓库，`where` 搜索工作区全部仓库。支持 `-d` 的命令可用它缩小范围。
各命令的选择规则见[命令参考](/zh/docs/command/)。

<span id="状态数据库与软件包事实" data-td-print-local></span>
<span id="init-只做收敛不做重置" data-td-print-local></span>

## 重复初始化与升级

再次运行 `init` 会补齐配置中尚未初始化的仓库和 Dist。已有状态只做检查，不重置构建快照。
给已有 Dist 新增架构后，运行 `build` 生成新视图。

初始化已提交部分对象、后续又失败时，命令返回退出码 `3` 并报告已完成内容。
修正错误后再次运行 `init`。

SOW 0.6.1 与 0.5.0、0.6.0 均使用数据库 schema v13。从这两个版本升级均无需迁移数据库。
对于 0.3 或 0.4 工作区，先备份完整工作区，再执行
[`sow repo migrate`](/zh/docs/command/repo/#sow-repo-migrate)。
不要手动修改 SQLite schema 版本。

数据库还缓存解析后的包信息。后续构建可以复用缓存和文件指纹；`sow check` 则读取包字节
并计算哈希，执行完整一致性检查。

继续阅读[成员策略](/zh/docs/feature/policy/)、[视图](/zh/docs/feature/views/)和
[事务与恢复](/zh/docs/feature/transactions/)。

<span id="继续阅读" data-td-print-local></span>
