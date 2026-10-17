---
title: "故障处理"
linkTitle: "故障处理"
description: "处理数据库迁移、待构建变更、中断发布、锁等待和完整性错误。"
url: "/zh/docs/reference/troubleshooting/"
categories: [Reference]
tags: [cli, recovery, troubleshooting]
weight: 80
icon: fa-solid fa-wrench
---

先查看报错信息和[退出码](/zh/docs/reference/exit-codes/)。
运行 Managed 命令时，明确指定工作区与仓库，检查对应状态：

```bash
sow version
sow status -C /srv/sow -r pgsql
sow log -C /srv/sow -r pgsql
```

将以下示例中的 `/srv/sow`、`pgsql` 和目标名 `prod` 换成实际配置。

## 数据库需要迁移

SOW 0.6.0 与 0.5.0 均使用 schema v13。从 0.5.0 升级无需迁移数据库。
对于 0.3 或 0.4 工作区，先停止写入并备份完整工作区，再运行：

```bash
sow repo migrate pgsql -C /srv/sow
sow build -C /srv/sow -r pgsql
sow check -C /srv/sow -r pgsql
```

对每个仓库重复这些步骤。兼容的只读命令仍可检查旧 schema，但不会自动迁移数据库。
详见[升级说明](/zh/docs/start/install/#升级到-060)。

## 状态显示有待构建变更

`add --skip`、`rm --skip` 和配置修改可能使 Desired 状态领先于 Built 状态。
应用待构建变更，然后检查结果：

```bash
sow build -C /srv/sow -r pgsql
sow check -C /srv/sow -r pgsql
```

本地构建更新本地索引。要更新已配置的远端目标，还需执行 `sow publish prod -C /srv/sow`。
状态字段见 [`sow status`](/zh/docs/command/status/)。

## 命令执行中断

Plain 模式下，解决报错中的输入或文件系统问题后，重新运行原来的 `sow create` 命令，保留原定的 Pigsty、时间戳和签名选项。

`add`、`rm`、Dist 修改或构建中断时，查看 `sow log`，修正报错原因，再对该仓库运行 `sow build` 完成恢复。
已提交的 Desired 变更仍属于待构建内容。`init`、`repo new` 或 `repo rm` 中断时，重新运行对应的生命周期命令，恢复工作区日志。

发布中断时，恢复存储和公共端点的访问，再次发布同一目标：

```bash
sow publish prod -C /srv/sow
```

SOW 会继续保存的发布尝试。尚未记录提交意图时，可用 `sow publish prod --abort -C /srv/sow`
放弃该次发布。已记录提交意图后，重新发布以完成更新。详见[发布恢复](/zh/docs/command/publish/)。

## 已提交变更后的错误

数据库提交与后续维护是两个步骤。成员关系或构建已经提交后，仍可能发生检查点或清理错误。
SOW 会在命令输出中保留已提交结果，不会把这些项目报告为已回滚。

先查看命令结果与 `sow status`，再用 `sow log` 查看对应操作。
按诊断提示继续执行相应命令。确认结果前，保留原始输入文件。

## 发布目标配置发生变化

比较 `sow.yml` 与报错中的目标。如果有意修改目标名称、`public_endpoint` 或 `max_cache_ttl`，运行：

```bash
sow publish prod --rebind -C /srv/sow
```

Repository、后端、存储端点、区域、桶或前缀变化时，需要新建目标。
修改 TTL 前，先完成未结束的目标维护。详见[目标绑定](/zh/docs/command/publish/)。

## 命令等待锁

另一个进程正在使用工作区或仓库。等待该命令结束，或通过正常的进程控制方式停止它，然后重试。

对于支持锁选项的写命令，锁忙时需要立即返回可用 `--no-wait`，需要限制等待时间可用 `--timeout 30s`。
这些选项不适用于 `init` 或读命令。共享锁读操作会等待写入者结束，或由你取消命令；`status` 通常直接报告锁状态。保留锁文件，SOW 依靠这些稳定路径协调进程。
详见[全局选项](/zh/docs/command/)。

## 软件包、签名或路径校验失败

根据报错中的文件和检查阶段定位原因：

| 错误 | 处理方法 |
|---|---|
| 同一 Pool 路径对应不同字节 | 比较输入包与已有包。不同内容使用新包版本和新文件名。仅换输入目录不会改变 Pool URL。 |
| 文件名仅大小写不同 | 使用已记录的拼写。大小写别名不能创建第二个 Pool URL。 |
| Pool 文件丢失或被修改 | 从匹配的备份恢复原字节，再运行 `sow check`。 |
| 签名密钥不可用 | 检查配置的密钥、私钥访问、GPG agent 和当前密钥有效期，修正后重试构建。 |
| RPM 不满足信任策略 | 检查包签名与配置的公钥。详见[签名教程](/zh/docs/tutorial/signing/)。 |
| 公共 URL 返回旧内容 | 检查 HTTP 根目录、URL 前缀、缓存和 `max_cache_ttl`，然后重试发布。 |

`sow check` 报告完整性错误，不会改写损坏数据。排查时保留报错路径与操作 ID。
[目录布局](/zh/docs/reference/layout/)介绍包池、生成索引和私有状态各自保存的文件。
