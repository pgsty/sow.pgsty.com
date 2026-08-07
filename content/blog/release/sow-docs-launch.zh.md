---
title: "SOW 0.2:文档站上线"
linkTitle: "SOW 0.2 文档站上线"
date: 2026-08-04
author: "冯若航"
description: "SOW 文档站上线:双仓库引擎、实测客户端兼容矩阵,以及四大板块的完整文档。"
categories: [release]
tags: [发布, sow]
weight: 10
url: "/zh/blog/release/sow-docs-launch/"
---

**发布日期:** 2026-08-04 · **版本:** `sow 0.2.0-dev`

SOW 是 [Pigsty](https://pigsty.cc) 出品的自包含软件仓库管理器:一个静态 Go 二进制,
在 Linux 与 macOS 上创建并维护 APT(DEB)与 YUM(RPM)软件仓库,而且整件事都由它
自己完成 —— 从不调用 `createrepo_c`、`dpkg-scanpackages`、`reprepro` 或
`modifyrepo_c`。没有常驻服务,没有数据库,也没有需要一并安装的东西。名字取自那个动词:
把软件包播进仓库,仓库自己长起来。

## 双引擎,一个二进制

`sow create` 是平面路径。把它指向一个已经放着 `.rpm` / `.deb` 的普通目录,它就地写出
索引 —— RPM 出 `repodata/`,DEB 出 `Packages` 与 `Packages.gz`;如果目录里两种包都有,
两套索引就都在同一个目录里。无工作区、无配置文件、无状态。相同输入产出字节级一致的
结果,跑第二遍是幂等 noop。

Managed 托管路径面向你要长期维护的仓库。工作区(Workspace)装仓库(Repository),
仓库装 Dist,Dist 是单一格式下的具名成员集合。包体在 Debian 风格的 `pool/` 里只存一份,
每个架构视图都是对包池的硬链接投影,而不是第二份拷贝。成员集由 `add` / `rm` 维护,
`build` 把它变成对外发布的一代(Generation)。两者之间是一个显式的 dirty 状态,
所以你随时知道磁盘上的东西和你要的东西是否一致。写操作先落 journal,机器在 `add`
中途挂掉,下一条写命令会先完成恢复,而不是留下一棵写了一半的树。

## 兼容性是实测出来的

文档里的兼容矩阵是跑出来的,不是声称的。SOW 产出的仓库已经被这些客户端端到端消费过:
AlmaLinux 8 / 9 / 10 的 `dnf`(`gpgcheck=1` 与 `repo_gpgcheck=1` 同时开启)、
CentOS 7 的 `yum` 3.4.3(多版本 NEVRA 解析正确)、Debian 12 的 `apt` 2.6.1 与
Debian 13 的 `apt` 3.0.3(`InRelease` 验签 + `by-hash` 取索引)。EL9 上的
`dnf reposync` 能按 pool 布局完整镜像。平面仓库通过 `file://` 与 `http://` 都可消费。
值得一提的是 SOW 会输出 `Acquire-By-Hash: yes` —— 这是 reprepro 根本不支持的能力。

## 文档写了什么

站点分四个板块。[上手指南](/zh/docs/start/)负责安装二进制、五分钟发布一个仓库,
并把心智模型讲清楚。[教程](/zh/docs/tutorial/)是端到端实战:YUM 与 APT 仓库、
GPG 签名、用 Nginx 对外服务,以及从 createrepo_c / reprepro 迁移。
[功能](/zh/docs/feature/)讲原理:包池与架构视图、成员策略、两条签名信任链、
事务与崩溃恢复、审计账本。[参考](/zh/docs/reference/)是速查层:全部命令、
完整 `sow.yml` schema、包引用文法、退出码、仓库布局、JSON 输出与兼容矩阵。

范围是刻意收窄的,非目标也是写明的而不是挂起的:SOW 不造包,不做远端发布 / CDN /
对象存储上传,不支持多机多写,也不生成 modulemd、sqlite repodata、zchunk 或源码包索引。

从[快速上手](/zh/docs/start/quickstart/)开始,或者直接去[下载页](/zh/download/)取一个二进制。
