---
title: 冯若航
linkTitle: Vonng
description: SOW 与 Pigsty 的作者；PostgreSQL 基础设施、软件交付，以及夹在两者中间的那些工具。
---

冯若航（[@Vonng](https://github.com/Vonng)）编写 **SOW**，以及它为之构建软件仓库的
PostgreSQL 发行版 [Pigsty](https://pigsty.cc/)。

SOW 起于交付问题，而不是打包问题。Pigsty 要在 Enterprise Linux、Debian 与 Ubuntu 上分发
数百个 RPM 与 DEB 软件包；而「此刻仓库里到底有什么、是谁放进去的」，诚实的答案只是一份目录
列表加一段 shell 历史。把成员关系、不可变 Generation、签名与发布都变成显式状态，这个问题
才有了工具可以直接回答的答案；一次仓库重建，也从「一夜之间冒出来的一批文件」变成了可审计的
发布边界。

- [pigsty.cc](https://pigsty.cc/) — SOW 为之构建软件仓库的 PostgreSQL 发行版
- [GitHub 上的 @Vonng](https://github.com/Vonng) — 这些项目背后的仓库
- [vonng.com](https://vonng.com/) — 长文
