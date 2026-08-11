---
title: "SOW v0.3.0"
linkTitle: "SOW v0.3.0"
date: 2026-08-10
author: "冯若航"
description: "SOW v0.3.0 减少 Plain 与 Managed 仓库的重复包体工作，引入软件包事实缓存与有界提交，强化持久性，并收敛发布质量门禁。"
categories: [发布]
tags: [发布, sow]
weight: 5
url: "/zh/blog/release/sow-v0.3.0/"
draft: false
---

SOW 0.3.0 围绕性能、持久性与产品边界完成了一次集中改进：Plain 仓库生成只需一遍包体处理；
Managed 仓库消除了逐对象成员查询，复用经过认证的软件包事实，并用有界组提交提升载荷。正式
交付的二进制与发布流水线也统一收敛到 SOW 实际支持的仓库工作流。

## Plain：一遍完成包体处理

默认无签名 `sow create` 路径通过 `--jobs` 控制并行度，每个 RPM 或 DEB 只做一次哈希与解析，
随后直接利用保留的检查结果渲染元数据。发布前只做最后一次软件包集合与文件 `stat` 快照检查，
无需再次读取和哈希所有包体，也能拒绝并发输入变更。

Plain 元数据是可以重建的派生状态。实现不会创建操作日志、恢复垃圾区、回滚前镜像，也不会
重复计算包体哈希。进程中断后重新运行 `sow create`，即可从软件包目录重建元数据。

Pigsty 预处理会保留 RPM Header 中架构为 `i386`、`i486`、`i586` 或 `i686` 的软件包，
让它们继续进入仓库元数据与 `repo_complete` 校验清单；DEB `i386` 与精确匹配 Patroni 3.0.4
的过滤规则仍按预期生效。

## Managed：扩展规模，不放松完整性

成员关系表增加了按包体 SHA-256 的反向索引，Desired 与 Built Membership 通过一次有序批量
投影展开，不再为每个对象单独查询。项目基准中，包含 5,000 个对象的 Dist 列表从约 4.1 秒
缩短至 33 毫秒；50,000 个对象从超过十分钟仍未完成，缩短到约 300 毫秒。

以不可变包体 SHA-256 为键的软件包事实缓存可以随时重建。Ingest 对每个新 RPM 或 DEB 完整
认证并解析一次，保留渲染元数据所需、与具体视图无关的事实。构建时批量载入这些事实并在内存中
匹配；记录缺失或损坏时，再从经过认证的包体惰性重建。

对于未改变的 Pool，暖构建使用设备号、inode、size、mtime 与 ctime 指纹校验载荷，包体读取量
降为零。指纹漂移时执行一次权威 SHA-256 校验并修复缓存路径；`sow check` 仍负责显式的完整
密码学审计。RPM 元数据产物与 DEB 架构索引使用有界 `--jobs` 并发，Generation Manifest 与
Changeset 行批量写入，最终规范化复用已有描述符快照，不再重新扫描 Pool。

## 有界提交与可观察构建

Managed 载荷提升采用有界的单写入者组提交。每批最多处理 512 个对象或 1 GiB：先创建公开 Pool
链接并持久化各目标目录，再移除 pending 名称并持久化共享的 pending 目录。崩溃因此只会留下
可恢复的“仅 pending”“精确双链接”或“仅 Pool”状态；两个名称同时持久丢失仍是完整性错误。

Pending 载荷在私有 `0700` 目录中直接使用最终的 `0644` 权限，因此提升只涉及命名空间变更。
Pending 源保护记录对象身份，不会在整个构建期间为每个软件包持有一个描述符，描述符占用保持
有界。发布载荷时也会先持久化目标目录项，再解除源名称。

长时间构建会为渲染、载荷提升、Dist 发布、规范化与收尾阶段追加结构化
`build_progress` 事件。它们可在 `sow log` 中观察，但不会为每个阶段增加数据库 checkpoint，
因此进度记录不会让本可成功的构建失败。

## 收敛发布与运行时边界

R2 发布传输只保留 SOW 实际使用的存储原语：list、head、get 与 conditional put。远端 GC
保持只报告、不删除对象的边界。未使用的云控制、CDN、Edge Worker、迁移程序与替代运行时路径
已从活动代码树移除，正式 CLI 只依赖统一的仓库核心；默认 `go test ./...` 因而覆盖完整的活动
实现。

## 正确性与发布质量

- 本地 GC 可以安全移除 Generation 中记录的唯一大小写折叠 Pool 别名，这对大小写不敏感的
  文件系统尤其重要。路径、大小与摘要仍必须标识同一不可变对象；存在歧义或漂移时拒绝执行。
- 每个归档都包含 `LICENSE`。RPM 与 DEB 声明 Apache-2.0，并分别把许可证安装到
  `/usr/share/licenses/sow/LICENSE` 与 `/usr/share/doc/sow/copyright`。
- CI 强制执行格式化、模块整洁、vet、静态分析、死代码检查、性能测试编译、完整测试、竞态
  测试、干净交付检查与软件包快照检查。
- 集成门禁覆盖正式二进制的干净环境混合 RPM/DEB 流程、Ubuntu 22.04 上无签名 Plain APT 的
  精确安装、AlmaLinux 8/9/10 的 DNF 签名切换探针，以及固定 MinIO 环境中的 S3 条件写操作。
- 正式发布包含 macOS 与 Linux 的 amd64/arm64 归档、两个 Linux 架构的 RPM 与 DEB，以及
  `SHA256SUMS`。

## 获取发布版本

通过[下载页面](/zh/download/)获取对应平台的安装命令，或在
[GitHub Release](https://github.com/pgsty/sow/releases/tag/v0.3.0) 查看全部交付物。安装后运行
`sow version`，确认使用的是选定的二进制。

完整操作契约见 [Plain 模式](/zh/docs/feature/plain/)、[Managed 模式](/zh/docs/feature/managed/)
与[平台与集成](/zh/docs/reference/compatibility/)。
