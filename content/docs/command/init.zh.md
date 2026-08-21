---
title: "sow init"
linkTitle: "init"
description: "创建工作区，并收敛 sow.yml 中已声明的 Repository 与 Dist。"
categories: [Command]
tags: [cli, managed, config]
url: "/zh/docs/command/init/"
aliases: ["/docs/reference/cli/init/"]
weight: 200
icon: fa-solid fa-seedling
---

`sow init` 创建根级 `sow.yml` 与私有状态目录 `.sow/`，这两样东西让一个目录成为工作区（Workspace）。
它同时也是手写配置的收敛命令：如果 `sow.yml` 里已经声明了 Repository 与 Dist，`init` 会把还不存在
的那些实体化出来，已完成的原样跳过。

## 语法

```text
sow init [DIR] [--json]
```

`DIR` 默认为当前目录。`init` 不接受 `-C/--workdir`——位置参数已经明确指定了目标。

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

`.sow/` 里放着 `workspace.lock`、工作区生命周期命令使用的持久文件 journal `workspace-ops/`、
`repo-locks/`，以及后续每个 Repository 一个的 SQLite 数据库。它的权限是 `0700`，绝不能对外提供
HTTP 访问。

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `--json` | 输出版本化 JSON envelope | false |
| `-h, --help` | 显示帮助 | — |

## 幂等规则

`init` 被设计成可以反复运行——无论是在 provisioning 脚本里还是手工执行：

1. **创建新配置时写入 `schema: sow/v3` 与默认 `architectures: [x86_64, aarch64]`**。
2. **它从不自动创建 Repository**。请用 [`sow repo new`](/zh/docs/command/repo/)，或先在
   `sow.yml` 中声明。
3. **它从不覆盖已存在的 `sow.yml`**。重复运行只报告现状，并列出发现了什么：

   ```console
   sow init .
   initialized /srv/repo: config_created=false repositories_initialized=0 dists_initialized=0
   ```

4. **非空目录可以初始化**，但若已有文件与 SOW 保留路径冲突则失败。

## 收敛已声明的配置

如果 `sow.yml` 里已经描述了 Repository 与 Dist，`init` 会为它们补齐缺失的目录树、SQLite 数据库与
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

这样创建出来的 Dist 立刻具备协议完整的空发布面：RPM Dist 每个架构视图有一份空
`repodata/`，DEB Dist 有空的 `Packages`/`Packages.gz`、`by-hash` 与 `Release`。

再跑一次什么都不会变：

```console
sow init . --json
{"schema":"sow.cli/v1","command":"init","ok":true,"repository":null,"operation":null,"result":{"workspace":"/srv/repo","config_created":false,"repositories_initialized":0,"dists_initialized":0,"existing":["sow.yml"]},"errors":[]}
```

## 锁与恢复

工作区生命周期命令——`init`、`repo new`、`repo rm`——运行在目标 Repository 数据库存在之前或被删除
之后，因此它们使用 `.sow/workspace.lock` 加 `.sow/workspace-ops/` 里的持久文件 journal，而不是
SQLite Operation Journal。被中断的 `init` 会由下一条工作区生命周期命令前滚完成或回滚。

## 示例

建好工作区后手工添加 Repository：

```bash
mkdir -p /srv/repo && cd /srv/repo
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

从版本控制中的配置文件 provision：

```bash
install -m 0644 sow.yml /srv/repo/sow.yml
sow init /srv/repo
sow config check -C /srv/repo
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 工作区创建成功，或已收敛（no-op） |
| `1` | 写配置或状态目录时的运行时 I/O 错误 |
| `2` | 用法错误，或已存在的 `sow.yml` 解析/校验不通过 |
| `3` | 部分成功——部分声明的 Repository/Dist 已提交，至少一个失败 |
| `5` | 工作区 journal 无法恢复到终态 |
| `6` | 已有文件与 SOW 保留路径冲突 |

## 参见

- [第一个工作区](/zh/docs/start/workspace/) —— 十分钟带练版本
- [Managed 工作区](/zh/docs/feature/managed/) —— 三层模型
- [sow.yml 配置参考](/zh/docs/reference/config/) —— 全部配置键
- [sow repo](/zh/docs/command/repo/) 与 [sow dist](/zh/docs/command/dist/)
- [仓库布局](/zh/docs/reference/layout/) —— `.sow/` 里有什么
