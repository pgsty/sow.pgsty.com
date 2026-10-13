---
title: "sow init"
linkTitle: "init"
description: "初始化工作区及 sow.yml 中声明的仓库与 Dist。"
categories: [Command]
tags: [cli, managed, config]
url: "/zh/docs/command/init/"
aliases: ["/docs/reference/cli/init/"]
weight: 200
icon: fa-solid fa-seedling
---

`sow init` 创建工作区的 `sow.yml` 与私有状态目录 `.sow/`。如果配置中已声明仓库和 Dist，它会创建尚未初始化的对象。添加声明后，可再次运行此命令完成初始化。

## 语法

```text
sow init [DIR] [--json]
```

`DIR` 默认为当前目录。需要初始化其他目录时，将它的路径作为 `DIR` 传入。

## 说明

首次 `init` 写出最小配置与私有状态目录：

```console
sow init .
initialized /srv/repo: config_created=true repositories_initialized=0 dists_initialized=0
```

```console
cat sow.yml
schema: sow/v3
architectures:
  - x86_64
  - aarch64
```

```console
ls -a /srv/repo
.  ..  .sow  sow.yml
```

`.sow/` 保存私有状态、锁和恢复记录，目录权限为 `0700`。通过 HTTP 提供仓库目录时，保留 `.sow/` 为私有目录。

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `--json` | 输出 JSON | false |
| `-h, --help` | 显示帮助 | — |

## 幂等规则

新配置使用 `schema: sow/v3`，默认架构为 `x86_64` 与 `aarch64`，不声明任何仓库。使用 [`sow repo new`](/zh/docs/command/repo/) 创建仓库，或先编辑 `sow.yml` 声明仓库。

`init` 保留已有配置，初始化尚缺的声明对象。非空目录也可以使用，但其中的文件不能与 SOW 保留路径冲突。全部声明对象都已初始化时，本次初始化计数为零。

## 应用已声明的配置 {#收敛已声明的配置}

如果 `sow.yml` 里已经描述了仓库与 Dist，`init` 会为它们补齐缺失的目录树、SQLite 数据库与
空索引。已初始化的对象直接跳过，因此计数器准确反映本次运行做了什么。

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]

repos:
  pgsql:
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource]
      trixie:
        format: deb
  infra:
    protected: true
    dists:
      el9:
        format: rpm
```

```console
sow init .
initialized /srv/repo: config_created=false repositories_initialized=2 dists_initialized=3
```

```console
sow repo ls
NAME	PROTECTED	DISTS	GENERATION	STATUS	PACKAGES	MEMBERSHIPS
infra	true	1	1	clean	0	0
pgsql	false	2	2	clean	0	0
```

新 Dist 具有有效的空索引：RPM Dist 的每个架构视图有一份空
`repodata/`，DEB Dist 有空的 `Packages`/`Packages.gz`、`by-hash` 与 `Release`。

再次运行时，已有对象保持不变：

```console
sow init . --json
{"schema":"sow.cli/v1","command":"init","ok":true,"repository":null,"operation":null,"result":{"workspace":"/srv/repo","config_created":false,"repositories_initialized":0,"dists_initialized":0,"existing":["sow.yml"]},"errors":[]}
```

## 锁与恢复

初始化中断后，对同一目录重新运行 `sow init`。SOW 先完成或回滚被中断的操作，再初始化其余声明对象。有其他工作区写操作时，它会等待该操作结束。

## 示例

建好工作区后手工添加仓库：

```bash
mkdir -p /srv/repo
cd /srv/repo
sow init
sow repo new infra
sow repo new pgsql
sow dist new el9 --format rpm -r pgsql
sow dist new trixie --format deb -r pgsql
```

初始化当前目录之外的目录：

```bash
sow init /srv/repo
```

使用版本控制中的配置文件初始化：

```bash
install -m 0644 sow.yml /srv/repo/sow.yml
sow init /srv/repo
sow config check -C /srv/repo
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 工作区初始化成功，或已经初始化（no-op） |
| `1` | 写配置或状态目录时的运行时 I/O 错误 |
| `2` | 用法错误，或已存在的 `sow.yml` 解析/校验不通过 |
| `3` | 部分成功——部分声明的仓库/Dist 已提交，至少一个失败 |
| `5` | 工作区日志无法恢复到终态 |
| `6` | 已有文件与 SOW 保留路径冲突 |

## 参见

- [第一个工作区](/zh/docs/start/workspace/) —— 逐步操作示例
- [Managed 工作区](/zh/docs/feature/managed/) —— 三层模型
- [sow.yml 配置参考](/zh/docs/reference/config/) —— 全部配置键
- [sow repo](/zh/docs/command/repo/) 与 [sow dist](/zh/docs/command/dist/)
- [仓库布局](/zh/docs/reference/layout/) —— `.sow/` 里有什么
