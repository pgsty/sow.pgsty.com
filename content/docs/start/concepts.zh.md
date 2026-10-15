---
title: "核心概念"
linkTitle: "核心概念"
description: "了解两种运行模式，以及工作区、仓库、Dist、包池与构建快照的关系。"
categories: [Start]
tags: [plain, managed, repository, dist]
url: "/zh/docs/start/concepts/"
weight: 400
icon: fa-solid fa-diagram-project
---

<span id="选择模式" data-td-print-local></span>

## 选择模式 {#plain-还是-managed}

| 需求 | Plain | Managed |
|---|---|---|
| 为软件包目录生成索引 | `sow create DIR` | 用 `sow add` 导入软件包 |
| 保存配置与成员关系 | 目录内容就是状态 | `sow.yml` 与私有 SQLite 数据库 |
| 组织软件包 | 一个平面目录，可同时包含 RPM 与 DEB | 具名 Dist，每个 Dist 一种格式 |
| 生成架构视图 | 不支持 | 支持 |
| 过滤软件包、限制版本数 | `--pigsty` 提供 Pigsty 约定 | 每个 Dist 单独配置 |
| 签名 RPM 软件包 | 支持 | 支持 |
| 签名仓库元数据 | 在 SOW 外单独签名 | 在 `sow.yml` 配置密钥 |
| 记录构建快照与发布状态 | 在 SOW 外管理 | 内置 |

如果目录已包含全部待发布软件包，使用 Plain。如果需要由 SOW 持续管理成员与仓库，使用 Managed。

<span id="工作区repository-与-dist" data-td-print-local></span>

## 工作区、仓库与 Dist {#managed-层级}

```text
Workspace                    /srv/sow
├── sow.yml                  配置
├── .sow/                    私有状态
└── Repository               /srv/sow/local
    ├── pool/                软件包文件
    └── dists/
        └── Dist             具名 RPM 或 DEB 软件包集合
            └── views        各架构的元数据
```

**工作区（Workspace）** 保存一个或多个仓库的配置与私有状态。

**仓库（Repository）** 拥有自己的包池、Dist、构建历史与发布目标。对外提供完整的 `pool/` 与 `dists/` 目录树；把 `sow.yml` 和 `.sow/` 留在 HTTP 文档根目录之外。

**Dist** 选择一种格式的软件包。例如，`el9` 放 RPM，`bookworm` 放 DEB。名称由你指定；SOW 不会检查软件包是否兼容名称所指的操作系统。

**架构视图** 保存某个架构的元数据。SOW 把 RPM `noarch` 与 DEB `all` 包加入每个适用的视图。

<span id="每个软件包只存一份" data-td-print-local></span>

## 每个软件包只存一份 {#一条规范包体路径}

SOW 用完整包文件的 SHA-256 标识 **包对象（Package Object）**，从包内元数据读取包名、版本与架构。

同一个仓库内，每个接受的软件包在 `pool/` 下只有一条路径。多个 Dist 可以引用这条路径。不同仓库使用各自的包池。

RPM 元数据通过相对路径引用包池，APT `Packages` 使用相对于仓库根目录的路径。对外服务或复制时，保留完整仓库目录树。

部分镜像工具（包括默认 `dnf reposync`）拒绝 RPM 中指向父目录的路径。为这些工具使用 [`sow export rpm-leaf`](/zh/docs/command/export/) 导出独立 RPM 仓库。

<span id="期望成员与构建快照" data-td-print-local></span>

## 期望成员与构建快照 {#desired-与-built}

**期望成员（Desired membership）** 是每个 Dist 选中的软件包集合。
**Generation（构建快照）** 标识一次已完成的构建及其文件清单。Built Generation 指当前已完成的构建。
包文件保存在共享包池中，每次构建无需另存一份。

```text
add / rm → 期望成员 → build → 构建快照
```

`add` 和 `rm` 默认在更新成员后构建受影响的 Dist。使用 `--skip` 时只更新成员。完成一批跳过构建的变更后，或修改构建、签名配置后，执行 `sow build`。

| 命令 | 用途 |
|---|---|
| `sow status` | 读取当前状态与 `ready_to_copy` 值 |
| `sow check` | 检查软件包、索引、签名与状态记录，不修改文件 |
| `sow changes [BASE_GENERATION]` | 列出指定快照到当前构建的文件变更 |
| `sow publish TARGET` | 检查当前构建并发布到已配置目标 |

<span id="理解仓库状态" data-td-print-local></span>

## 理解仓库状态 {#事务与失败状态}

| 状态 | 含义 | 下一步 |
|---|---|---|
| `clean` | 成员与配置符合已构建结果 | 可以检查或发布 |
| `dirty` | 成员或配置变更需要构建 | 执行 `build`，再执行 `check` |
| `recovering` | 被中断的操作需要恢复 | 按报错与[恢复步骤](/zh/docs/reference/troubleshooting/#命令执行中断)处理 |
| `error` | 状态记录或文件发生冲突 | 查看报错与操作日志 |

使用 [`sow log`](/zh/docs/command/log/) 查看失败或中断的操作记录。

## 继续阅读

- [Managed 工作区](/zh/docs/feature/managed/)
- [包池与架构视图](/zh/docs/feature/views/)
- [事务与恢复](/zh/docs/feature/transactions/)
- [发布与恢复](/zh/blog/design/publication/)
