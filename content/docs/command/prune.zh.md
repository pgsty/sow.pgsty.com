---
title: "sow prune"
linkTitle: "prune"
description: "在平面仓库中保留最新 RPM 版本。"
categories: [Command]
tags: [cli, plain, rpm]
url: "/zh/docs/command/prune/"
weight: 110
icon: fa-solid fa-scissors
---

`sow prune` 按包名和架构保留 Epoch/Version/Release 最高的 RPM，重建平面索引，再删除旧版本。此命令需要 SOW 0.7.0 或更新版本。

## 语法

```text
sow prune DIR [--dry-run] [--protect NAME]... [-j N] [--metadata-timestamp SECONDS] [-T DUR | -N] [--json]
```

`DIR` 必填。命令只扫描顶层普通二进制 RPM 文件，不扫描子目录，不发现工作区，也不读取 `sow.yml`。

## 预览与清理

在本地发布源目录执行此命令。使用缓存旧索引的客户端可能仍需要旧 RPM，发布流程应考虑这一点。

```bash
sow prune /srv/candidate --dry-run
sow prune /srv/candidate --protect age_18 --protect age_18-llvmjit
```

`--dry-run` 执行校验并报告候选项，不修改文件。预览和正式执行时应使用相同的保护选项。

`--protect NAME` 保留该精确包名在所有架构下的全部版本。可重复指定，不接受模式匹配。每个名称都必须匹配到软件包；拼写错误会在修改前返回退出码 `2`。同一包名、架构分组中 EVR 相等的文件会被拒绝，受保护的分组也不例外。

## 选项

| 选项 | 行为 |
|---|---|
| `--dry-run` | 校验并预览删除候选项，不写文件 |
| `--protect NAME` | 保留精确包名的全部版本，可重复指定 |
| `-j, --jobs N` | 软件包检查并发数，默认为 CPU 数量 |
| `--metadata-timestamp SECONDS` | 索引发布时间，以 Unix 秒表示；与 `create` 相同，默认为 `0` |
| `-T, --timeout DUR` | 限制等待目录锁的时间 |
| `-N, --no-wait` | 目录锁被占用时立即失败 |
| `--json` | 返回标准 JSON 信封 |

`--timeout` 与 `--no-wait` 互斥。Prune 不签署软件包或仓库元数据，也不接受 `--pigsty`。

## 完整性与恢复

每个被删版本对应的替换 RPM 必须通过包内摘要校验。SOW 将摘要校验和索引记录的内容绑定到稳定的文件身份，包括文件变更时间。在每次删除前和操作完成前重新检查替换包。一旦检测到变化，就停止后续删除；原地改写后恢复大小和修改时间也会被检测到。

筛选后的索引先发布，再删除软件包。如果索引已发布或部分文件已删除后发生错误，结果会报告实际变化，并返回部分完成退出码 `7`；中断返回 `130`。已经删除的软件包不会恢复。解决报告的问题后，重新运行相同命令。

已有的 `repo_complete` 标记会在修改期间撤下，仅在成功完成后刷新。中断后会保留待完成状态。如果原先没有标记，Prune 不会创建标记，也不会应用 `create --pigsty` 的包排除规则。

JSON 结果包含 `kept`、`candidates`（每个旧路径及替换包）、`removed`、`index_updated`、`dry_run` 和 `noop` 等字段。

## 支持的仓库

Prune 拒绝 Managed 工作区、DEB 包或索引、包文件符号链接、源码 RPM、RPM v6 包，以及存在 `repodata/repomd.xml.asc` 的仓库。如果已有 `repomd.xml` 登记了 SOW 不生成的独立元数据，例如软件包组、updateinfo、modules 或未知类型，也会拒绝执行。包索引的其他编码，如 SQLite 和 zchunk，仍然允许。

关于明确移除附加元数据后重建候选仓库的步骤，以及元数据时间戳行为，参阅 [`sow create`](/zh/docs/command/create/)。
