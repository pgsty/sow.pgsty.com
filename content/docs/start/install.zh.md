---
title: "安装 SOW"
linkTitle: "安装"
description: "下载预编译二进制或从源码构建,并验证安装结果。"
url: "/zh/docs/start/install/"
weight: 100
icon: fa-solid fa-download
---

SOW 以单个静态可执行文件分发。所谓安装,就是把这一个文件放到 `PATH` 上的某个位置。
没有软件包要装,没有服务要启用,在你执行第一条需要落盘的命令之前,它也不会创建任何
状态目录。

## 支持的平台

二进制以 `CGO_ENABLED=0` 构建,不依赖 libc,可在对应操作系统与 CPU 架构的任意现代内核上运行。

| 操作系统 | `amd64` | `arm64` |
|---|---|---|
| Linux | 支持 | 支持 |
| macOS(Darwin) | 支持 | 支持 |

不支持 Windows。SOW 依赖 POSIX 建议锁、硬链接与原子 `rename`,且只在本地 POSIX 文件系统上
验证过 —— NFS 之类的网络文件系统不提供它所需的锁与持久化语义。

{{% alert title="文件系统要求" color="info" %}}
在 [Managed 托管模式](/zh/docs/start/workspace/)下,架构视图由包池以硬链接投影而来,
因此同一仓库的 `pool/` 与 `dists/` 必须位于同一个文件系统。跨设备时 SOW 直接报错,
不会静默退化成复制。Plain 平面模式没有这个约束。
{{% /alert %}}

## 下载发行版本

各平台的预编译二进制发布在
[GitHub Releases 页面](https://github.com/pgsty/sow/releases)。下载与你的操作系统和架构
匹配的压缩包,解压后放到 `PATH` 上:

```bash
tar -xzf sow_*.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

如果机器上没有 root,放到 `~/.local/bin` 同样可用 —— SOW 自身的运行从不需要提权。

## 从源码构建

构建只需要 Go 工具链。克隆仓库并构建 `cmd/sow` 入口:

```bash
git clone https://github.com/pgsty/sow.git
cd sow
CGO_ENABLED=0 go build -trimpath -o sow ./cmd/sow
```

设置 `GOOS` 与 `GOARCH` 即可交叉编译;因为没有 cgo,交叉构建不需要 Go 之外的任何工具链:

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -o sow-linux-arm64 ./cmd/sow
```

## 验证安装

```bash
sow version
```

```console
sow 0.2.0-dev darwin/arm64 go1.26.5
```

这一行给出 SOW 版本、二进制针对的平台,以及构建它的 Go 工具链版本。`sow --version` 输出相同内容。

查看完整命令树:

```bash
sow help
```

每条命令都有自己的帮助页 —— `sow help create`、`sow help dist new` 等等 ——
其中列出该命令**确切**接受的参数。不在该命令参数矩阵内的 flag 会被拒绝,而不是被忽略。

## 外部依赖

生成仓库元数据的全过程不调用任何外部程序。SOW 自己解析 RPM 头与 Debian control 文件、
自己算校验和、在进程内写出 `repodata/`、`Packages` 与 `Release`。`createrepo_c`、
`dpkg-scanpackages`、`reprepro`、`modifyrepo_c` 都不会被执行。

只有两项可选能力会用到环境中的工具:

| 能力 | 需要 | 原因 |
|---|---|---|
| RPM **包体**签名 —— `sow create --sign-with`,或 Managed 的 `packages.mode` 为 `fill` / `always` | `rpm` 与可用的 GPG 环境 | 包体签名由 `rpm --addsign` 对私有 stage 副本产生 |
| 使用 `agent://<fingerprint>` 密钥引用的元数据签名 | `gpg` 与运行中的 `gpg-agent` | 私钥留在 agent 内,不进入 SOW 进程 |

使用 `file://` 或 `env://` 密钥引用的元数据签名在进程内完成,不需要外部 GPG。
完整配置见[仓库签名](/zh/docs/tutorial/signing/)。

## 下一步

- [快速上手](/zh/docs/start/quickstart/) —— 五分钟发布一个装包的目录。
- [第一个工作区](/zh/docs/start/workspace/) —— 搭建可精选、多架构的仓库。
- [核心概念](/zh/docs/start/concepts/) —— 两条路径背后的模型。
