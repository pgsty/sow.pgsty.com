---
title: "安装 SOW"
linkTitle: "安装"
description: "下载预编译二进制或从源码构建,并验证安装结果。"
url: "/zh/docs/start/install/"
weight: 100
icon: fa-solid fa-download
---

SOW 以单个自包含可执行文件分发。Archive 安装就是把它放到 `PATH`；Linux 也可使用 Release
中的 RPM/DEB 包常规安装。没有服务要启用，在命令真正需要状态前也不会创建状态目录。

## Release 构建目标

Release Pipeline 以 `CGO_ENABLED=0` 构建，不需要另装 cgo 工具链或语言运行时；二进制仍会使用
操作系统标准 ABI 与 Framework。Release 资产的构建目标如下：

| 操作系统 | `amd64` | `arm64` |
|---|---|---|
| Linux | 构建 | 构建 |
| macOS(Darwin) | 构建 | 构建 |

不支持 Windows。SOW 依赖 POSIX 建议锁与原子 `rename`,且只在本地 POSIX 文件系统上
验证过 —— NFS 之类的网络文件系统不提供它所需的锁与持久化语义。

{{% alert title="文件系统要求" color="info" %}}
请在本地 POSIX 文件系统上构建 [Managed 工作区](/zh/docs/start/workspace/),以保证锁、
fsync 与原子 rename 契约。已提交的公共 `pool/ + dists/` 树没有视图级硬链接 alias,
可以普通复制或发布。
{{% /alert %}}

## 下载发行版本

SOW v0.2.0 的 GitHub Release 当前仍是 **Draft**。其中四个 Linux/macOS 归档、
`1PGSTY` Linux RPM/DEB 包与 `SHA256SUMS` 尚不可公开下载。在操作者把它发布到
[Releases 页面](https://github.com/pgsty/sow/releases)之前,请按下文从源码构建。
公开后,自动下载前仍要确认 Release 条目中
确实存在匹配的归档与校验和,再把解压出的二进制放到 `PATH` 上:

v0.2.0 不发布 Docker 或其他容器镜像。

```bash
tar -xzf sow_*.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

没有 root 时可以安装到 `~/.local/bin`。SOW 不需要特权守护进程。执行用户必须能读写
Workspace 或 Plain 目标目录及发布目标，并能读取输入包、解析签名引用。

## 从源码构建

构建需要 Go 1.26.5 或更高版本。克隆仓库并构建 `cmd/sow` 入口:

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
sow 0.2.0 darwin/arm64 go1.26.5
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
