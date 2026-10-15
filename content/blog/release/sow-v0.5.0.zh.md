---
title: "SOW v0.5.0"
linkTitle: "SOW v0.5.0"
date: 2026-09-29T00:00:00+08:00
lastmod: 2026-10-13
authors: [Vonng]
description: "SOW v0.5.0 新增 Plain RPM 发布时间参数，并修复仓库恢复、签名与包路径问题。"
categories: [Release]
tags: [release, plain, yum, signing, migration]
weight: -10
url: "/zh/blog/release/sow-v0.5.0/"
draft: false
---

SOW 0.5.0 为已有 YUM 仓库增加发布时间参数，并修复 Managed 仓库的恢复、签名和包路径处理。
构建过程也减少了对未变化软件包的重复校验。

安装方式见[下载 SOW](/zh/download/)。使用 0.3 或 0.4 Managed 工作区时，先迁移各个 Repository，再进行写操作。

<span id="升级与开发者说明" data-td-print-local></span>

## 升级 Managed 工作区

1. 停止向工作区写入的命令。
2. 备份完整工作区，包括 `sow.yml`、`.sow/` 和所有 Repository 根目录。
3. 安装 SOW 0.5.0。
4. 逐个迁移、构建并检查 Repository。将 `pgsql` 和 `/srv/sow` 换成实际名称与路径。

```bash
sow repo migrate pgsql -C /srv/sow
sow build -r pgsql -C /srv/sow
sow check -r pgsql -C /srv/sow
```

迁移将数据库更新到 schema v13。配置仍使用 `sow/v3`，公共目录仍由 `pool/` 和 `dists/` 组成。
首次构建刷新 RPM 认证与 APT 元数据记录；后续构建会复用匹配的 RPM 校验记录。

迁移后的数据库使用 SOW 0.5.0 或更新版本。备份与安装步骤见
[安装与升级](/zh/docs/start/install/#从-04-升级到-05)。

<span id="已有-yum-仓库的发布时间" data-td-print-local></span>

## 保持 YUM 发布时间递增

如果新 `repomd.xml` 中最大的 data 时间戳早于缓存值，EL7 YUM 可能拒绝新索引。
修改校验和、revision 或文件修改时间都不能替代这项比较。

替换已有元数据生成器时，使用新增参数：

```bash
# 根据仓库发布历史设置 PUBLISH_TIME。
sow create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
```

| 设置 | 结果 |
|---|---|
| 默认行为 | RPM data 时间戳仍为 `0` |
| `--metadata-timestamp SECONDS` | 设置三条 RPM data 记录的时间戳 |
| 取值范围 | `0` 到 `253402300799` 的整数 |
| Plain `repomd.xml` revision | 仍为 `0` |
| 软件包字节与 DEB 索引 | 不受此参数影响 |
| 压缩 XML 与 gzip 头 | 仅修改时间戳时保持不变 |

该参数只适用于 `create`，Managed 构建、发布和 RPM 叶目录导出均不接受它。
包字节与选项相同时，重复构建会生成相同元数据；强制重签软件包可能改变输入字节。

在维护脚本中保存已发布的最大时间戳。内容变化时递增时间戳，恢复旧包集合也按一次新发布处理。
如果之前的转换已将时间戳重置为零，用转换前的发布历史恢复该值。

<span id="验收外围维护流程" data-td-print-local></span>

如果客户端校验仓库签名，每次修改后都要签署最终的 `repomd.xml`。
`--sign-with` 签署 RPM 包，不会签署索引。
[YUM 迁移指南](/zh/docs/tutorial/yum-migration/)介绍时间戳选择、索引签名和已有客户端缓存的测试方法。

## 仓库与发布修复

- 删除 Dist 时，不再误删后来加入其他 Dist 的软件包。
- 提交 Desired 变更前，检查签名策略和包池路径冲突。
- 恢复操作保留已提交的软件包选择，并完成中断的清理。
- 已发布的包路径始终绑定原内容，本地垃圾回收也不会解除绑定。发布恢复不会用其他字节覆盖该路径。
- 仅大小写不同的文件名不能创建第二个 Pool URL，即使字节相同也不例外。
  大小写不敏感的工作区和文件系统目标还会拒绝目录别名。
- 并发执行 `export rpm-leaf --hardlink` 与 `check` 时，不再将未变化的包误报为损坏。
- 本地 `gc` 跳过包只存在于远端的发布记录。
- 输入路径可以经过符号链接父目录；软件包文件本身仍须通过文件检查。
- SQLite 检查点被读连接延迟时，不再将已完成的写入报告为失败。macOS 写连接使用 `fullfsync`。

## 签名与命令输出

APT 验签兼容 GnuPG 的末尾换行约定。新元数据签名使用 SHA-256，新的构建会检查签名密钥当前是否可用。
Agent 签名固定签名时间，并选择可用的签名子钥。新 APT 发布拒绝弱签名摘要；历史验签沿用记录中的规则。

`sow repo migrate` 报告迁移前后的 schema 版本。未迁移的 Repository 会给出迁移命令。
命令收到 SIGINT 或 SIGTERM 后返回退出码 `130`。全部被拒绝的 `add` 批次会显示各文件的错误。
`file://` R2 凭据必须指向普通文件。

<span id="rpm-依赖兼容性" data-td-print-local></span>

## RPM 依赖

新增回归用例覆盖事务前、事务后脚本依赖，包括 Cloudberry、Percona 和 Grafana 软件包使用的组合。
依赖渲染继续遵循现代 createrepo_c 的规则。上游变更见
[createrepo_c PR #427](https://github.com/rpm-software-management/createrepo_c/pull/427)。

软件包签名流程使用 RPM v4 格式。SOW 0.5.0 不支持 RPM v6 格式签名。
生成的仓库元数据使用 XML，不包含 SQLite rpm-md 或模块流。
格式与客户端覆盖见[兼容性](/zh/docs/reference/compatibility/)。

## 构建与安装包

源码构建需要 Go 1.27.1 或更新版本。本版使用 x/crypto v0.56.0 与 GoReleaser v2.18.2。
二进制归档和原生安装包均包含 `THIRD_PARTY_NOTICES`。

发布文件包括四个 Linux/macOS 归档、两个 RPM、两个 DEB 和 `SHA256SUMS`。
指定版本文件见 [v0.5.0 发布页](https://github.com/pgsty/sow/releases/tag/v0.5.0)。
兼容性测试位于 `qa/compat/`，性能测试位于 `qa/perf/`。S3 集成测试使用按摘要固定的 `pgsty/silo` 镜像。
