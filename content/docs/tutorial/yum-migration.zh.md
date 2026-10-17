---
title: "迁移已有 YUM 仓库"
linkTitle: "迁移 YUM 仓库"
description: "将已有平面 RPM 仓库切换至 SOW，保留客户端缓存兼容性、软件包信任与发布时钟。"
categories: [Tutorial]
tags: [yum, plain, migration, signing]
url: "/zh/docs/tutorial/yum-migration/"
weight: 150
icon: fa-solid fa-arrows-rotate
---

本指南适用于 RPM 与 `repodata/` 放在同一层目录的平面仓库，例如此前用 `createrepo_c`
维护的仓库。它使用 Plain `sow create`，不创建 Managed 工作区。以下命令以 **SOW 0.6.0** 为目标版本。

<span id="1-明确迁移范围" data-td-print-local></span>

## 1. 准备工作副本

备份当前软件包与元数据，再准备独立工作副本用于迁移。计划重签的 RPM 使用独立复制，不使用硬链接。检查已安装的二进制：

```bash
SOW="$(command -v sow)"
"$SOW" version
```

确认版本为 0.6.0。

| 检查项 | 操作 |
|---|---|
| 软件包布局 | Plain 只读取顶层普通 RPM；嵌套目录需要单独规划迁移 |
| 客户端功能 | Plain 生成 primary/filelists/other XML，不生成 SQLite 数据库或模块流 |
| 包信任 | 保留合法上游签名，或明确换成自己的密钥 |
| 索引信任 | 客户端启用 `repo_gpgcheck=1` 时，单独签署并验证新 `repomd.xml` |
| 已有客户端 | 保留旧缓存，使用原来的 URL 和 repo ID 验收 |

客户端使用模块过滤时，按需要保留仓库原有的 `module_hotfixes=1` 设置。Plain 元数据不包含模块流或 profile。

## 2. 保留发布时间历史

EL7 YUM 可能拒绝最大 data 时间戳早于缓存的新索引。读取当前 `repomd.xml` 与保留副本中的 `<data><timestamp>`，取客户端可能见过的最大值。如果在线索引被重置为零，从旧副本或发布记录恢复这个值。使用 data 时间戳，不使用 `revision` 或文件修改时间。

维护脚本需串行执行更新，并在服务目录之外保存最大发布时间。内容变化时，选择：

```text
下一次时间 = max(当前 Unix 秒, 已知的最大发布时间 + 1)
```

切换公开索引前保存所选时间戳。发布失败可以使序列跳号。恢复旧内容或迁移本地目录时，保留这份记录。`+1` 用于区分发布；EL7 也接受相等时间戳。

内容不变时，检查索引、引用文件校验和与签名后复用时间戳。零时间戳或已倒退的时间戳需要修复。每次传入当前时间都会改变 `repomd.xml`，此时 `create` 就无法报告空操作。

## 3. 构建并签署候选

下面演示一次重建。先准备独立的 `/srv/yum.candidate` 副本。
将 `HISTORICAL_MAX` 设为从当前索引、已保存的最大发布时间和可信历史中核实的最大值。
将 `SIGN_KEY` 设为元数据签名密钥的完整指纹。
示例用 Python 3 选择严格递增的时间：

```bash
set -euo pipefail
: "${SOW:?Set the path to the tested SOW binary}"
: "${HISTORICAL_MAX:?Set the verified historical maximum Unix second}"
: "${SIGN_KEY:?Set the full metadata signing fingerprint}"
PUBLISH_TIME=$(python3 -c 'import sys,time; h=int(sys.argv[1]); assert 0 <= h < 253402300799; print(max(int(time.time()), h+1))' "$HISTORICAL_MAX")

"$SOW" create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
gpg --batch --yes --armor --detach-sign --local-user "$SIGN_KEY" \
  --output /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
gpg --verify /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
```

发布候选目录前，在维护系统中记录 `PUBLISH_TIME`。核对 `gpg --verify` 显示的指纹与预期签名密钥是否一致。

`--sign-with KEY` 签署未签名 RPM，并保留已有签名，包括供应商签名。要把全部包签名换成自己的密钥，在候选副本中增加 `--overwrite`。这会改变包文件；`create` 根据签名后的结果生成索引。最后一次 `create` 完成后，再生成索引的分离签名。

<span id="4-切换前验收" data-td-print-local></span>

## 4. 测试候选仓库

让测试客户端通过原来的仓库 URL 访问候选目录。保留该客户端的旧缓存、仓库 ID 与签名设置，
然后刷新索引、下载并安装一个包。这样可以同时检查缓存兼容性、下载路径与签名。

如果迁移的是自动更新脚本，再检查两种情况：

1. 输入、选项与时间戳不变时，重复构建报告 `noop=true`。保留已有的有效索引签名。
2. 包内容变化时，脚本增加时间戳，同一个客户端能获取新版软件包。

与 `createrepo_c` 比较时，检查依赖含义与客户端行为；XML 排版可以不同。
详情见[平台与集成](/zh/docs/reference/compatibility/)。

<span id="5-发布与恢复资料保留" data-td-print-local></span>

## 5. 发布仓库

Plain 会替换多个文件，不提供整个目录的原子切换。发布层需要协调包文件、索引、分离签名以及
缓存的可见顺序。SOW 0.6.0 保留当前与紧邻上一轮以校验和命名的 RPM 元数据。
没有变化的运行仍保留同一份上一轮元数据。复制目录后还要继续构建时，一并保留 `.sow-plain-rpm-history.json`。
如果客户端缓存跨越多轮更新，在发布层继续保留所需的更早元数据与软件包。

保留原始备份与已保存的最大发布时间。回滚软件包内容时，把它当成更晚的一次发布重新建库、签名。只恢复旧
`repomd.xml`、却搭配已经改变的 RPM，会重新引入校验和或时间戳问题。

Plain 仓库使用上述检查；`sow check` 用于 Managed 仓库。命令参数见 [`sow create`](/zh/docs/command/create/)，包签名与元数据签名见[仓库签名](/zh/docs/tutorial/signing/)。
