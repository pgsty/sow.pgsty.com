---
title: "搭建 APT 仓库"
linkTitle: "搭建 APT 仓库"
description: "创建带 by-hash 索引的托管 DEB 仓库，并配置 APT 客户端。"
categories: [Tutorial]
tags: [apt, deb, managed, dist]
url: "/zh/docs/tutorial/apt-repo/"
weight: 200
icon: fa-solid fa-cube
---

本教程从零创建一个 Managed DEB 仓库。先安装 SOW、Python 3，并准备适合目标客户端的 DEB 文件。使用当前用户可创建、可写入的空目录 `/srv/sow`，或换成其他可写路径。

## 1. 创建工作区

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new trixie --format deb -r pigsty
```

Dist 名称 `trixie` 对应客户端配置中的 `Suites`，可以按需要更改。它不改变软件包的发行版兼容性。

## 2. 配置成员策略

如果需要过滤或限制版本，编辑生成的 `sow.yml`：

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  pigsty:
    dists:
      trixie:
        format: deb
        limit: 1
        exclude:
          - kind: [dbgsym, dbg]
targets: {}
```

然后校验：

```bash
sow config check
```

配置中的 `x86_64`、`aarch64` 分别生成 Debian 的 `amd64`、`arm64` 索引。
架构无关的 `all` 包进入两个视图。

## 3. 添加 DEB

```bash
sow add /path/to/packages/*.deb -r pigsty -d trixie
sow check -r pigsty
```

把输入路径换成实际 DEB 目录。`add` 将接受的软件包保存一次，并构建索引。公共目录树如下：

```text
/srv/sow/pigsty/
├── pool/...
└── dists/trixie/
    ├── Release
    └── main/
        ├── binary-amd64/
        │   ├── Packages
        │   ├── Packages.gz
        │   └── by-hash/SHA256/...
        └── binary-arm64/...
```

`Packages` 中的 `Filename` 相对于仓库根目录。保留完整目录树，客户端才能找到软件包。SOW 生成 `by-hash` 索引，供 APT 按内容哈希获取元数据。

## 4. HTTP 预览

在另一个终端执行以下命令，并保持运行：

```bash
python3 -m http.server --bind 127.0.0.1 --directory /srv/sow/pigsty 8080
```

预览只提供仓库根目录中的文件，并且只能从本机访问。长期运行或供其他主机访问时，按[对外服务](/zh/docs/tutorial/serving/)配置。

## 5. 配置 APT

在运行预览的 Linux 主机上，把以下内容保存为 `/etc/apt/sources.list.d/pigsty.sources`。ARM64 客户端将 `Architectures` 改为 `arm64`。远程客户端需先发布仓库，再换成其公共地址：

```ini
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: http://127.0.0.1:8080
Suites: trixie
Components: main
Architectures: amd64
Trusted: yes
```

刷新并查询：

```bash
sudo apt update
apt-cache policy
```

输出中应出现 `trixie/main` 的软件包来源。`Trusted: yes` 用于本例的未签名仓库。
需要签名时，按[仓库签名](/zh/docs/tutorial/signing/)生成签名、安装公钥并配置 `Signed-By`。
预览完成后，删除测试源配置文件并停止 Python 服务器。

<span id="6-安全发布" data-td-print-local></span>

## 6. 发布仓库

使用 [`sow publish`](/zh/docs/tutorial/serving/) 发布到 filesystem 或 R2 目标。它先上传软件包与索引，再更新 `Release` 及其签名。隔离主机的手工交付步骤也见该教程。

## 更新仓库

```bash
sow add /path/to/new.deb -r pigsty -d trixie
sow check -r pigsty
```

`add` 会自动构建更新。配置 `limit: 1` 后，同包名、同架构的最新版本会替换此前成员。修改配置后执行 `sow build -r pigsty`。

撤下软件包时，先用 `sow rm PACKAGE_NAME -r pigsty -d trixie --check` 预览选择结果，再去掉 `--check` 执行。包名会选中其全部版本与架构；只删除一个包对象时，使用 SHA-256 引用。

已测试客户端见[平台与集成](/zh/docs/reference/compatibility/)。
