---
title: "SOW v0.2.0:单包体仓库"
linkTitle: "SOW v0.2.0"
date: 2026-08-08
author: "冯若航"
description: "SOW v0.2.0 确立单包体布局、显式发布目标、保留、GC 与 RPM 兼容导出。"
categories: [release]
tags: [发布, sow]
weight: 10
url: "/zh/blog/release/sow-docs-launch/"
---

**发布日期:** 2026-08-08 · **版本:** `sow 0.2.0`

SOW 是 [Pigsty](https://pigsty.cc) 出品的自包含软件仓库管理器。一个静态 Go 二进制
即可在 Linux 与 macOS 上创建维护 APT(DEB)与 YUM(RPM)仓库,无需调用
`createrepo_c`、`dpkg-scanpackages` 或 `reprepro`。

## v0.2.0 布局

Managed 仓库现在只有一个规范包体属主。每个包体只在 `pool/` 下出现一次;`dists/` 只含
APT/RPM 元数据视图。rpm-md 通过计算出的相对 href 访问根包池,APT 使用相对 archive 根的
`Filename`。

这取代了视图级硬链接 C2 原型。该原型从未成为公共产品 Release。公共版本历史是 v0.1.0
之后直接到 v0.2.0;`sow.cli/v1` 与 `sow/v3` 之类名称是 Wire/Schema 标识,不是产品版本。

默认 `dnf reposync` 会拒绝规范布局的父级相对 href。v0.2.0 保留单包体仓库作为权威来源,
并提供显式兼容路径:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

## 发布与生命周期

Managed 工作区可以定义 `filesystem` 与 S3 兼容 `r2` 目标,再用 `sow publish TARGET`
发布已验证 Generation。尝试可恢复;提交前可显式 abandon,提交后恢复只能前滚。

`sow retain` 创建或移除显式保留代根。本地 `sow gc` 只回收所有安全根都不可达的包体。
目标 GC 按 Provider 区分:filesystem 只有经过宽限期与缺失检查才条件式删除;R2 有意只生成
报告,绝不删除对象。

## 验证边界

客户端矩阵覆盖 AlmaLinux 8/9/10 DNF、CentOS 7 YUM 与 Debian 12/13 APT。
Integration workflow 还用真实 APT/DNF 客户端与固定版本 MinIO 验证 S3 兼容发布。
Provider 集成测试不等于某个公共 R2 账户或 CDN 已配置完成;托管部署仍需单独检查。

公开的 v0.2.0 Release 包含 Linux/macOS 的 amd64/arm64 archive、Linux RPM/DEB 包与
`SHA256SUMS`。SOW 不构建仓库包体、不发布容器镜像、不协调多写者、不充当 CDN,
也不生成 modulemd、SQLite repodata、zchunk 或源码包索引。

从[快速上手](/zh/docs/start/quickstart/)开始,查看[设计演进](/zh/docs/design/evolution/),
或直接使用[命令行参考](/zh/docs/reference/cli/)。
