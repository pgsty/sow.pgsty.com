---
title: "功能"
linkTitle: "功能"
description: "Plain/Managed 仓库生成、包池、策略、签名、事务、发布与审计。"
categories: [Feature]
tags: [plain, managed, policy, signing]
url: "/zh/docs/feature/"
aliases:
  - "/docs/feature/overview/"
weight: 300
icon: fa-solid fa-cubes
---

SOW 提供两条相互隔离的运行路径。Plain 模式无状态地重建一个目录；Managed 模式在工作区中
持续记录软件包成员关系与不可变仓库 Generation。两者都不会暗中接管对方的状态。

## 能力矩阵

| 能力 | Plain | Managed |
|---|---:|---:|
| RPM 与 DEB 元数据 | 是 | 是 |
| RPM + DEB 混合操作 | 同一目录 | 同一 Repository、不同 Dist |
| 持久成员关系与 Generation | 否 | 是 |
| 分架构视图与中性包投影 | 否 | 是 |
| `exclude` 与版本 `limit` 策略 | 否 | 是 |
| 元数据签名 | 否 | RPM 与 DEB |
| RPM 包签名 | `--sign-with` | `never`、`fill`、`always` |
| 事务日志与恢复 | 重新运行 `create` | Workspace、Repository、发布 |
| 可查询 Operation Log 与 JSONL 导出 | 否 | 是 |
| 发布目标 | 否 | filesystem 与 R2 |

SOW 在进程内解析软件包并渲染元数据，不调用 `createrepo_c`、`dpkg-scanpackages`、
`reprepro` 或 `modifyrepo_c`。RPM 包签名是例外：它会改写包体，因此需要主机上的 `rpm`
命令与 GPG 环境。

## 仓库格式

| 表面 | RPM/YUM | DEB/APT |
|---|---|---|
| 包事实来源 | RPM header | DEB control archive |
| 身份 | NEVRA + 确切字节 SHA-256 | `name=version:arch` + 确切字节 SHA-256 |
| 索引 | `primary`、`filelists`、`other`、`repomd.xml` | `Packages`、`Packages.gz`、`Release` |
| 中性架构 | `noarch` | `all` |
| 不可变索引路径 | 校验和命名 rpm-md | `by-hash/SHA256` |
| Managed 元数据签名 | `repomd.xml.asc` | `InRelease`、`Release.gpg` |

SOW 有意不生成 SQLite rpm-md、zchunk、modulemd、源码包索引与 MD5/SHA1 DEB manifest。
它负责构建仓库文件，不提供 HTTP 服务或 CDN。

## 按问题阅读

| 问题 | 页面 |
|---|---|
| `sow create` 写什么、替代什么？ | [Plain 平面仓库](/zh/docs/feature/plain/) |
| Workspace、Repository、Dist 与私有状态如何关联？ | [Managed 工作区](/zh/docs/feature/managed/) |
| 一个包池如何供给多个纯元数据视图？ | [包池与元数据视图](/zh/docs/feature/views/) |
| 为什么软件包被排除或限量？ | [成员策略](/zh/docs/feature/policy/) |
| 哪把密钥签哪个对象？ | [签名模型](/zh/docs/feature/signing/) |
| 中断后会发生什么？ | [事务与恢复](/zh/docs/feature/transactions/) |
| 如何查看、校验并审计仓库？ | [可观测与审计](/zh/docs/feature/audit/) |

Release 目标、文件系统要求、客户端与 Provider 见[平台与集成](/zh/docs/reference/compatibility/)。
