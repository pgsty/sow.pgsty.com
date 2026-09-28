---
title: "SOW v0.5.0"
linkTitle: "SOW v0.5.0"
date: 2026-09-28T00:00:00+08:00
authors: [Vonng]
description: "SOW v0.5.0 为 Plain RPM 仓库增加显式发布时间，在保留确定性构建的同时，支持迁移已有 YUM 仓库维护流程。"
categories: [Release]
tags: [release, plain, yum, signing, migration]
weight: -10
url: "/zh/blog/release/sow-v0.5.0/"
draft: false
---

SOW 0.5.0 主要解决已有平面 YUM 仓库接入 SOW 时的兼容问题。核心新增功能是
`sow create --metadata-timestamp SECONDS`：替换原有元数据生成器时，发布者可以保留合法的
发布时间，兼容已有 EL7 YUM 客户端的缓存。

安装方式见[下载页面](/zh/download/)，已有工作区的升级步骤见
[安装与升级](/zh/docs/start/install/#从-04-升级到-05)。

## 已有 YUM 仓库的发布时间

EL7 YUM 会比较新 `repomd.xml` 中最大的元数据时间戳与本地缓存。如果新索引的时间更早，
YUM 可能拒收它并继续使用旧索引。新的 checksum、不同的 revision 或更新的文件修改时间，
都不能替代这项比较。

此前 Plain `create` 始终写入零时间戳，便于复现输出，但直接接管已有正时间戳的在线仓库时会
遇到上述问题。0.5 增加了显式指定发布时间的入口：

```bash
# PUBLISH_TIME 由发布者根据已记录的发布历史选择。
sow create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
```

`SECONDS` 接受 `0` 到 `9223372036854775807` 的整数。负数、非整数、溢出或重复参数会作为
用法错误拒绝。该参数只属于 `create`，不是 Managed `build`、`publish` 或 RPM leaf export
的选项。

| 项目 | 0.5 的行为 |
|---|---|
| 默认 data 时间戳 | 仍为 `0` |
| 显式时间戳 | 写入 RPM `repomd.xml` 的三条 data 记录 |
| `repomd.xml` revision | Plain 模式仍为 `0` |
| RPM 字节与包时间 | 此参数不改变它们 |
| 压缩 XML 与 gzip 头 | 只改此参数时保持原字节 |
| DEB 索引 | 不受此参数影响 |
| 重复构建元数据 | 包字节与选项相同，输出相同，空跑不写文件；强制重签属于另外的包修改操作 |

SOW 不会自动读取当前时钟，也不会替调用者维护发布时间。维护脚本应在上传目录外保存历史最大
发布时间；内容不变且现有索引、签名有效时复用它们，真正更新时递增时间。恢复旧包集合也属于
一次新发布，不能把发布时间一起倒退。若此前转换已经把在线索引重置为零，重建历史下限时还要
纳入可信的转换前备份。

`repomd.xml` 一旦变化，原有分离签名就不再有效。发布者必须重新签名、验签后再对外提供索引。
`--sign-with` 签署的是 RPM 包，不会签署 `repomd.xml`。
[迁移指南](/zh/docs/tutorial/yum-migration/)说明完整操作顺序，以及 SOW 命令与外围维护流程
各自负责的工作。

## RPM 依赖兼容性

依赖投影继续采用现代 createrepo_c 对事务前、事务后脚本依赖的处理规则。本次增加了这些阶段
单独出现，以及 Cloudberry、Percona、Grafana 软件包中实际阶段组合的回归用例。

这次增加的是测试覆盖，既没有修改依赖解析，也没有退回 createrepo_c 0.20.1 的输出规则。
依赖条目数量或 `pre="1"` 属性不同，本身不代表依赖丢失。相关上游变更见
[createrepo_c PR #427](https://github.com/rpm-software-management/createrepo_c/pull/427)。

## 维护集成实际验证了什么

配套的 Pigsty 维护工作覆盖 10 个平面仓库：PGSQL 的 EL7–10 共八个架构目录，以及 INFRA
的两个架构目录，共 17,571 个 RPM。时间戳修复保持全部 17,343 个 PGSQL RPM 及其压缩 XML
原字节不变；INFRA 中两个原本未签名的包完成补签。之后再次运行维护流程，10 个仓库均未替换
任何仓库文件。

保留缓存的客户端验收覆盖 EL7 双架构，以及 EL8、EL9、EL10 的 arm64。每个环境都使用同一
URL 和 repo ID，在不清理 metadata 缓存的情况下，从旧索引切换至修复仓库，再切换至下一次
真实内容更新。10 个切换场景全部通过索引检查、实际包下载和验签，且同时开启包与仓库签名检查。

这些结果属于上述维护集成的验收，不代表安装过所有 RPM，或覆盖所有 YUM/DNF 配置。
维护脚本保存时钟、复用签名、选择性重签的能力，也不属于 `sow create` 新增的内置功能。
Plain 仍是平面目录的多文件重建流程：不生成旧式 SQLite 元数据或模块流，也不提供整个仓库的
原子切换。

## 升级与开发者说明

- 已有 0.4 Managed 工作区升级不增加数据库迁移步骤。内部 Schema v12、`sow/v3` 配置以及
  公共 `pool/ + dists/` 布局保持不变。仍在使用 0.3 数据库的工作区，必须先完成
  [既有的显式迁移](/zh/docs/command/repo/#sow-repo-migrate)。
- 长期维护的文档集中在本站。兼容性与性能检查分别移至 `qa/compat/`、`qa/perf/`，共享 RPM
  测试夹具移至 `internal/testdata/`；干净源码交付清单同步采用这些路径。
- 源码最低工具链仍为 Go 1.27.0。v0.4.0 之后的这批变更没有升级依赖或工具链。
- 本地发布前检查全部通过：全量 Go 测试、race、静态分析、漏洞与上游来源检查、确定性源码
  交付、四个 Linux/macOS 归档，以及各两个 RPM、DEB 的构建和包内容校验。

新建平面目录仍可沿用 `sow create DIR`。对于已有在线 YUM 仓库，请先阅读
[迁移已有 YUM 仓库](/zh/docs/tutorial/yum-migration/)，并在切换维护命令前确认实际二进制的
`create --help` 中列出了 `--metadata-timestamp`。
