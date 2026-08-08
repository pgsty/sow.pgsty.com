---
title: "下载与安装"
linkTitle: "下载"
description: "获取 SOW 二进制：Release 资产、源码构建与 Release 构建目标。"
url: "/zh/download/"
weight: 20
icon: fa-solid fa-download
---

SOW 是一个自包含可执行文件。使用 Archive 安装就是把该文件放进 `PATH`；没有服务要启用，
在命令真正需要状态前也不会创建状态目录。Linux 还可以使用 Release 中的 RPM/DEB 包常规安装。

## 预编译二进制

SOW v0.2.0 的 GitHub Release 当前仍是 **Draft**。其中四个 Linux/macOS 归档、
`1PGSTY` Linux RPM/DEB 包与 `SHA256SUMS` 尚不可公开下载。在操作者把它发布到
[Releases 页面](https://github.com/pgsty/sow/releases)之前,请按下文从源码构建。
公开后,自动下载前仍要确认 Release 条目中
确实存在匹配的归档与校验和,再下载对应归档并解压到位:

v0.2.0 不发布 Docker 或其他容器镜像。

```bash
tar -xzf sow_*.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

没有 root 时可以安装到 `~/.local/bin`。SOW 不需要特权守护进程。执行用户必须能读写
Workspace 或 Plain 目标目录及发布目标，并能读取输入包、解析签名引用。

## Release 构建目标

Release Pipeline 以 `CGO_ENABLED=0` 构建，不需要另装 cgo 工具链或语言运行时；二进制仍会使用
操作系统标准 ABI 与 Framework。Release 资产的构建目标如下：

| 操作系统 | `amd64` | `arm64` | 说明 |
|---|---|---|---|
| Linux | 构建 | 构建 | 主要目标平台 |
| macOS(Darwin) | 构建 | 构建 | Intel 与 Apple Silicon |
| Windows | — | — | 不支持 |

不支持 Windows 是有意为之:SOW 依赖 POSIX 建议锁与原子 `rename`。
同样的原因,请把仓库放在本地 POSIX 文件系统上 —— NFS 等网络文件系统无法提供它
所依赖的锁与持久化语义。

## 源码构建

唯一的构建依赖是 Go 工具链,项目要求 **Go 1.26.5** 或更高版本。

```bash
git clone https://github.com/pgsty/sow.git
cd sow
CGO_ENABLED=0 go build -trimpath -o sow ./cmd/sow
```

因为没有 cgo,交叉编译不需要除 Go 之外的任何工具链:

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

这行输出依次是 SOW 版本、二进制的目标平台,以及构建它的 Go 工具链版本。
`sow --version` 输出同一行内容,`sow help` 则列出完整命令树。

## 你不需要安装的东西

生成仓库元数据的全过程不会调用外部程序:SOW 自己解析 RPM 头与 Debian control 文件,
自己算校验和,在进程内写出 `repodata/`、`Packages` 与 `Release` —— 从不调用
`createrepo_c`、`dpkg-scanpackages`、`reprepro` 或 `modifyrepo_c`。

只有两个可选功能会用到环境中的外部工具:RPM **包签名**需要 `rpm` 与可用的 GPG 环境,
`agent://` 形式的密钥引用需要正在运行的 `gpg-agent`。其余能力(包括 `file://`
与 `env://` 的元数据签名)都在二进制内部完成。细节见[安装](/zh/docs/start/install/)。

## 下一步

- [快速上手](/zh/docs/start/quickstart/) —— 五分钟把一个装包的目录变成可服务的仓库。
- [第一个工作区](/zh/docs/start/workspace/) —— 搭一个可筛选、多架构的托管仓库。
- [兼容性](/zh/docs/reference/compatibility/) —— 当前自动化证据及其边界。
