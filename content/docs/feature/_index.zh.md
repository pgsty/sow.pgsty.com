---
title: "功能"
linkTitle: "功能"
description: "选择仓库模式，了解包策略、签名、发布与审计功能。"
categories: [Feature]
tags: [plain, managed, policy, signing]
url: "/zh/docs/feature/"
aliases:
  - "/docs/feature/overview/"
weight: 300
icon: fa-solid fa-cubes
---

SOW 用两种模式创建仓库索引。可以随时重建的包目录使用 Plain；
需要持续更新、策略、签名和发布的仓库使用 Managed。

<span id="能力矩阵"></span>

## 功能对照

| 功能 | Plain | Managed |
|---|---|---|
| RPM 与 DEB 索引 | 一个目录，可包含任一种或两种格式 | 一个仓库，分别使用不同 Dist |
| 持久化成员与构建快照 | — | 支持 |
| 分架构视图 | — | 支持，包含架构无关包 |
| 包排除 | `--pigsty` 使用固定清理规则 | 按 Dist 配置 |
| 版本数量限制 | — | 按 Dist 配置 |
| 元数据签名 | — | RPM 和 DEB |
| RPM 包签名 | `--sign-with` | `never`、`fill`、`always` |
| 中断恢复 | 重新运行 `create` | 操作记录和发布尝试 |
| 操作日志与 JSONL 导出 | — | 支持 |
| 发布目标 | — | Filesystem 与 R2 |

SOW 自行解析包并生成索引，无需 `createrepo_c`、`dpkg-scanpackages` 或 `reprepro`。
RPM 包签名使用主机上的 `rpm` 和 GPG 环境；元数据密钥引用解析为 GPG 密钥标识时，也需要 `gpg`。

<span id="仓库格式"></span>

## 生成格式

| 格式 | Plain | Managed 增加的内容 |
|---|---|---|
| RPM | `primary`、`filelists`、`other` XML 和 `repomd.xml` | 架构视图，可选 `repomd.xml.asc` |
| DEB | `Packages`、`Packages.gz` | `Release`、by-hash 索引，可选 `InRelease`、`Release.gpg` |

RPM XML 使用 gzip 压缩。SOW 不生成 SQLite rpm-md、zchunk、modulemd 或源码包索引。
生成结果由你配置的 HTTP 服务或对象存储对外提供。
客户端细节见[平台与集成](/zh/docs/reference/compatibility/)。

<span id="按问题阅读"></span>

## 按任务阅读

| 任务 | 文档 |
|---|---|
| 在现有包旁生成索引 | [Plain 仓库](/zh/docs/feature/plain/) |
| 管理持续的包更新 | [Managed 工作区](/zh/docs/feature/managed/) |
| 在不同 Dist 视图间共用包字节 | [包池与视图](/zh/docs/feature/views/) |
| 排除软件包或保留最新版本 | [成员策略](/zh/docs/feature/policy/) |
| 为包与索引签名 | [签名](/zh/docs/feature/signing/) |
| 中断后继续执行 | [事务与恢复](/zh/docs/feature/transactions/) |
| 查看状态、验证输出与读取历史 | [可观测与审计](/zh/docs/feature/audit/) |
