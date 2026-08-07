---
title: "兼容性"
linkTitle: "兼容性"
description: "哪些客户端消费过 SOW 仓库、二进制支持哪些平台,以及你必须遵守的约束。"
url: "/zh/docs/reference/compatibility/"
weight: 700
icon: fa-solid fa-circle-check
---

SOW 输出的是标准 rpm-md 与 Debian archive 元数据,所以问题不在于客户端"能不能"读,
而在于哪些客户端**确实被验证过**。本页给出实测矩阵、二进制支持的平台,
以及少数几条忽略了就会出问题的约束。

## 包管理器客户端

下表每一行都对 SOW 构建的仓库做过端到端验证:刷新索引、列出软件包、安装其中一个。

| 客户端 | 版本 | 结果 |
|---|---|---|
| AlmaLinux 10 `dnf` | dnf4 | `repo_gpgcheck=1` + `gpgcheck=1` 下 `makecache` 与 `install` 通过 |
| AlmaLinux 9 `dnf` | dnf4 | 同上 |
| AlmaLinux 8 `dnf` | dnf4 | 同上 |
| CentOS 7 `yum` | 3.4.3 | `makecache` 与包列表解析通过,多版本 NEVRA 排序正确 |
| Debian 13 `apt` | 3.0.3 | `update`(验签 `InRelease`、走 by-hash)与 `install` 通过 |
| Debian 12 `apt` | 2.6.1 | 同上;另外也验证了平面仓库 |
| `dnf reposync` | EL9 | 按 pool 布局完整镜像 |

RPM 测试**两道签名校验都开着**:`repo_gpgcheck=1` 验证 `repodata/repomd.xml.asc`,
`gpgcheck=1` 验证包签名。APT 侧使用 `Signed-By` 验证 `InRelease`,
HTTP 日志证实 `apt` 实际是通过 `by-hash/SHA256/` 而不是直接路径拉取索引的。

CentOS 7 的 `yum` 3.4.3 是测过的最老客户端。它早于 by-hash,也不需要 by-hash ——
RPM 侧没有等价机制,校验和命名的元数据文件起到了同样的作用。

`sow create` 构建的平面仓库,`dnf`、`yum`、`apt` 都能通过 `file://` 与 `http://` 消费。

{{% alert title="平面仓库与 APT" color="info" %}}
平面仓库没有 `Release` 文件,所以 `apt` 不会为它验签。
请把该源标记为 `[trusted=yes]`;真正需要来源认证时,请改用带元数据签名的 Managed Dist。
{{% /alert %}}

## 平台

二进制以 `CGO_ENABLED=0` 构建,没有任何运行时库依赖。

| 操作系统 | `amd64` | `arm64` |
|---|---|---|
| Linux | 支持 | 支持 |
| macOS (Darwin) | 支持 | 支持 |

不支持 Windows。SOW 依赖 POSIX 建议锁(`flock`)、硬链接和原子 `rename`,没有可移植的替代。

**在 macOS 上构建、在 Linux 上服务**是受支持的工作流。为了保证这种可移植性,
SOW 会拒绝任何在大小写不敏感比较下会碰撞的池路径,
因此在大小写敏感的 Linux 上构建的仓库,复制到默认的 macOS 文件系统上依然有效。

## 文件系统要求

**只支持本地 POSIX 文件系统。** SOW 未在 NFS 等网络文件系统上测试,也不声称支持 ——
它们不提供 SOW 事务模型所依赖的锁与持久化语义。请在本地构建,再把结果复制到任何地方。

**`pool/` 与 `dists/` 必须在同一个文件系统上。** 架构视图用硬链接投影包池,
而硬链接不能跨设备。两者不在同一文件系统时,SOW 会明确失败,而不是静默改成复制:

```text
<repo>/pool/...                                 # 规范字节
<repo>/dists/<dist>/x86_64/pool/...             # 硬链接,同一 inode
```

实践中只有在仓库目录下单独挂载卷时才会遇到这个问题。stage 目录同样放在与目标相同的
文件系统上 —— 这正是最终那次 `rename` 能够原子完成的前提。

把仓库**复制**到别处没有这个要求。不保留硬链接的工具会把每个别名复制成独立的普通文件:
对客户端功能完全一致,只是多占磁盘。想保留去重就用 `rsync --hard-links`。

## SOW 不生成哪些元数据

传统工具会产出、而 SOW 有意不产出的东西如下。对上面测过的所有客户端来说,它们都是可选的。

| 不生成 | 后果 |
|---|---|
| SQLite repodata(`primary.sqlite.bz2` 等) | 无影响。`dnf` / `yum` 使用 XML 元数据;SQLite 变体多年来一直是可选的。 |
| `modulemd` | 模块化流不在范围内。非模块化的包不受影响。 |
| zchunk 元数据 | `dnf` 退回完整元数据下载 —— 这本就是没有 zchunk 时的正常行为。 |
| `Release` 中的 `MD5Sum` 与 `SHA1` | 需要客户端接受只有 SHA256 的清单。测过的每个 `apt` 都可以。 |
| `Packages` 中的 `MD5sum` 与 `SHA1` 字段 | 同上 —— `SHA256` 存在且足够。 |
| `binary-<arch>/` 下的逐架构 `Release` 存根 | `apt` 不需要;`reprepro` 会写,SOW 不写。 |
| 源码包索引(SRPM、DSC) | 只处理二进制包。 |

把 `Release` 与 `Packages` 合起来看,一个 DEB Dist 发布的就是这些,不多不少:

```console
Acquire-By-Hash: yes
SHA256:
 95e8c59d21d69285ac788bd8ea78b0544b0a1395ae9a0e3a700ec13b420e5c39 2245 main/binary-amd64/Packages
 4d658bdf6a542999f737e5f89e3bdb504c205fb85cda76f3e4b1ef73619c5900 751 main/binary-amd64/Packages.gz
```

## by-hash 与较老的 APT

Managed DEB Dist 始终发布 `by-hash/SHA256/` 并声明 `Acquire-By-Hash: yes`。
它保证了索引更新对"刚刚取过 `Release` 的客户端"是安全的:
新索引发布的同时,旧索引仍可按摘要访问。

APT 1.2(2015 年)及以后版本会自动使用 by-hash。更老的客户端忽略这个字段,
直接拉取 `main/binary-<arch>/Packages` —— SOW 也始终写这个文件,所以它们照样能工作,
只是少了那层更新竞态保护。

`reprepro` **完全不支持** by-hash,这是迁移的一条现实理由。

## 外部工具

SOW 不调用 `createrepo_c`、`dpkg-scanpackages`、`modifyrepo_c` 或 `repo2module`。
RPM 头与 Debian control 文件在进程内解析,所有元数据也在进程内渲染。

只有两类操作会跳出二进制:

| 操作 | 需要 | 说明 |
|---|---|---|
| RPM 包签名 | `rpm` 以及可用的 GPG 环境 | Plain 的 `create --sign-with`,以及 Managed 中 `signing.rpm.packages.mode` 为 `fill` / `always` 时。签名始终发生在私有 stage 副本上。 |
| 使用 `agent://` 的元数据签名 | `gpg` 与运行中的 agent | 仅限 `agent://` 形式的 key 引用。 |

用 `file://` 或 `env://` key 做元数据签名是**进程内**完成的 ——
也就是说,一个带已签名 `InRelease` 与 `repomd.xml.asc` 的仓库,可以完全不依赖外部工具产出。

## 版本

本页的兼容性结论由以下版本产出:

```bash
sow version
```

```console
sow 0.2.0-dev darwin/arm64 go1.26.5
```

仓库输出是确定性的:固定的时间戳、固定的压缩参数与稳定排序,
使得相同输入 + 相同配置产出字节稳定的元数据。
对未变化的目录重跑 `sow create` 是 no-op,一个字节都不会重写。

## 延伸阅读

- [安装](/zh/docs/start/install/) —— 平台矩阵与源码构建
- [仓库布局](/zh/docs/reference/layout/) —— 硬链接约束的由来
- [从 createrepo_c / reprepro 迁移](/zh/docs/tutorial/migration/) —— 功能层面的对比
- [对外服务](/zh/docs/tutorial/serving/) —— `dnf` 与 `apt` 的客户端配置
