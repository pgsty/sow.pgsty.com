---
title: "安装"
linkTitle: "安装"
description: "通过归档、RPM/DEB 安装包或源码安装 SOW，并核对二进制与文件系统要求。"
categories: [Start]
tags: [install, rpm, deb]
url: "/zh/docs/start/install/"
weight: 100
icon: fa-solid fa-download
---

SOW 是一个可执行文件，不依赖守护进程、数据库服务或语言运行时。发布归档支持 Linux 与 macOS 的 `amd64`、`arm64` 架构。Linux 另有 RPM 与 DEB 安装包。

从 [下载页](/zh/download/) 选择 SOW 0.6.0 制品。
将所选制品与 `SHA256SUMS` 下载到独立的下载目录。

## 安装归档

以 Linux amd64 为例，先校验归档，再解压并安装：

```bash
set -euo pipefail
grep '  sow_0.6.0_linux_amd64.tar.gz$' SHA256SUMS | sha256sum -c -
tar -xzf sow_0.6.0_linux_amd64.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

macOS 选择 `darwin_amd64` 或 `darwin_arm64`，替换上述归档名称，并使用 `shasum -a 256 -c -` 校验。

没有 root 权限时，安装到用户目录：

```bash
mkdir -p "$HOME/.local/bin"
install -m 0755 sow "$HOME/.local/bin/sow"
export PATH="$HOME/.local/bin:$PATH"
```

把 `export PATH` 这一行加入 shell 配置文件，让新终端也能找到 SOW。

## 安装 Linux 软件包

先用 `SHA256SUMS` 中对应的条目校验下载的软件包，再执行适合本机发行版的命令：

```bash
# RPM，x86_64
sudo rpm -Uvh ./sow-0.6.0-1PGSTY.x86_64.rpm

# Debian 或 Ubuntu，amd64
sudo apt install ./sow_0.6.0-1PGSTY_amd64.deb
```

ARM64 主机使用以 `.aarch64.rpm` 或 `_arm64.deb` 结尾的软件包。安装后的可执行文件位于 `/usr/bin/sow`。

## 从源码构建

安装 Go 1.27.2 或更新版本，以及 Git。构建使用 `CGO_ENABLED=0`，不需要 C 编译器。

```bash
set -euo pipefail
git clone --branch v0.6.0 https://github.com/pgsty/sow.git
cd sow
SOW_BUILD_DIR="$(mktemp -d)"
CGO_ENABLED=0 go build -trimpath \
  -ldflags='-s -w -X github.com/pgsty/sow/internal/v2cli.Version=0.6.0' \
  -o "$SOW_BUILD_DIR/sow" ./cmd/sow
sudo install -m 0755 "$SOW_BUILD_DIR/sow" /usr/local/bin/sow
```

<span id="校验" data-td-print-local></span>

## 验证安装

```bash
sow version
sow help
```

`version` 显示产品版本、目标操作系统与架构，以及 Go 工具链版本。`help` 列出命令；用 `sow help COMMAND` 查看某条命令的参数。

<span id="升级-03-managed-workspace" data-td-print-local></span>

## 升级到 0.6.0 {#升级到-060}

SOW 0.6.0 保持数据库 schema v13、配置 schema `sow/v3` 与公开目录布局不变。
已使用 0.5.0 的工作区无需迁移数据库。

1. 停止工作区的全部写入任务。
2. 用保留硬链接的工具备份完整工作区，例如 `rsync -aH` 或 `tar`。
3. 安装 SOW 0.6.0。
4. 对 `sow.yml` 中每个仓库执行构建与检查：

```bash
sow version
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

把 `REPOSITORY` 换成配置中的仓库名。已是最新状态的仓库会报告空操作。
没有变化的构建保留原构建快照编号与元数据时间戳。
新的构建会记录一个发布时间，并在恢复时复用。

### 从 0.3 或 0.4 升级 {#从-04-升级到-05}

这些工作区需要在首次构建前迁移。备份工作区并安装 0.6.0 后，执行：

```bash
sow repo migrate REPOSITORY -C /srv/sow
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

对每个仓库重复执行。迁移更新数据库，重建应用当前的 RPM 验签与 APT 元数据规则。
需要回退到使用旧 schema 的版本时，恢复备份。
详情见 [`sow repo migrate`](/zh/docs/command/repo/#sow-repo-migrate) 与 [0.6.0 发布说明](/zh/blog/release/sow-v0.6.0/)。

## 升级 Plain 仓库

Plain 模式没有数据库需要迁移。更换现有 YUM 仓库的生成工具前，按[迁移现有 YUM 仓库](/zh/docs/tutorial/yum-migration/)操作。`--metadata-timestamp` 的默认值仍为 `0`。根据仓库发布历史设置时间戳，才能让带缓存的 YUM 客户端接受新索引。

<span id="权限与可选工具" data-td-print-local></span>

## 存储与可选工具

执行 SOW 的用户需要读取输入软件包，并能写入仓库目录。Managed 工作区应放在支持文件锁、`fsync` 与原子重命名的本地 POSIX 文件系统上。

软件包解析与元数据生成由 SOW 完成。可选签名功能需要以下主机工具：

| 签名方式 | 所需工具 |
|---|---|
| 使用 OpenPGP 密钥文件或密钥内容签署元数据 | 无 |
| 使用 GPG 密钥标识签署元数据 | `gpg` 与 `gpg-agent` |
| RPM 软件包签名 | `rpm` 及可用的 GPG 签名环境 |

接下来用[快速上手](/zh/docs/start/quickstart/)进入 Plain 模式，或用[第一个工作区](/zh/docs/start/workspace/)进入 Managed 模式。
