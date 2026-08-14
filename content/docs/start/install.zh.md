---
title: "安装"
linkTitle: "安装"
description: "通过归档、RPM/DEB 安装包或源码安装 SOW，并核对二进制与文件系统要求。"
url: "/zh/docs/start/install/"
weight: 100
icon: fa-solid fa-download
---

SOW 只有一个可执行文件，不需要启用服务，也不依赖语言运行时。Release 构建目标是 Linux 与
macOS 的 `amd64`、`arm64`；Linux 另外提供 RPM 与 DEB 安装包。不支持 Windows。

在[下载页](/zh/download/)选择匹配操作系统与架构的归档或 Linux 安装包。页面同时提供每个
已发布制品、对应源码 Tag 与 `SHA256SUMS` 的链接。

## 安装归档

下载一个归档与 `SHA256SUMS`，解压前只校验对应条目：

```bash
# Linux amd64
grep 'sow_.*_linux_amd64.tar.gz$' SHA256SUMS | sha256sum -c -
tar -xzf sow_*_linux_amd64.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

macOS 选择 `darwin_amd64` 或 `darwin_arm64`，并把 `sha256sum -c -` 换成
`shasum -a 256 -c -`。没有 root 时，把二进制装到已经加入 `PATH` 的目录，例如
`~/.local/bin`。

## 安装 Linux 软件包

Linux 软件包使用 `1PGSTY` Release 后缀：

```bash
sudo rpm -Uvh ./sow-*-1PGSTY.x86_64.rpm
sudo apt install ./sow_*-1PGSTY_amd64.deb
```

只执行符合本机发行版与架构的那条命令。RPM 把 License 安装到
`/usr/share/licenses/sow/LICENSE`；DEB 把版权/协议文件安装到 `/usr/share/doc/sow/`。

## 从源码构建

Go Module 声明使用 Go 1.26.5，元数据生成不需要 C 工具链。请把 `vX.Y.Z` 替换为下载页
链接的源码 Tag：

```bash
git clone https://github.com/pgsty/sow.git
cd sow
set -euo pipefail
SOW_TAG=vX.Y.Z
git checkout "$SOW_TAG"
SOW_VERSION="${SOW_TAG#v}"
CGO_ENABLED=0 go build -trimpath \
  -ldflags="-s -w -X github.com/pgsty/sow/internal/v2cli.Version=${SOW_VERSION}" \
  -o sow ./cmd/sow
sudo install -m 0755 sow /usr/local/bin/sow
```

这组命令使用 Release 构建参数，并把所选 Tag 的产品版本写入二进制。

## 校验

```bash
sow version
sow help
```

`sow version` 输出产品版本、目标 OS/架构与构建 Go 工具链；`sow help` 列出命令树。
归档中还包含 `README.md`、`CHANGELOG.md` 与 Apache-2.0 `LICENSE`。

## 权限与可选工具

执行用户需要读取输入软件包，并能写入 Plain 目标目录或 Managed 工作区。Managed 工作区
应放在本地 POSIX 文件系统上；锁、fsync、安全路径与原子 rename 都属于正确性契约。

软件包解析与元数据渲染都在进程内完成。只有两条可选路径需要主机工具：

- RPM **包签名** 需要 `rpm` 与可用的 GPG 环境；
- `agent://` 元数据密钥需要 `gpg` 与 `gpg-agent`。

接下来可用[快速上手](/zh/docs/start/quickstart/)进入 Plain 模式，或用
[第一个工作区](/zh/docs/start/workspace/)进入 Managed 模式。
