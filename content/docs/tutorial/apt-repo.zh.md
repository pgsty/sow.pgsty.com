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

本教程从零创建一个 Managed DEB 仓库。你需要一个可写目录，以及一个或多个
DEB 文件。

## 1. 创建工作区

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new trixie --format deb -r pigsty
```

Dist 名称会成为 APT Suite。它由你定义；SOW 不会根据 `trixie` 推断发行版语义。

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
sow config show --all
```

配置中保存规范架构名，渲染时使用 Debian 生态名称：`x86_64` 对应 `amd64`，`aarch64`
对应 `arm64`；中立架构 `all` 包会进入两个视图。

## 3. 添加 DEB

```bash
sow add /path/to/packages/*.deb -r pigsty -d trixie
sow status -r pigsty
sow check -r pigsty
```

接纳的包体只保存一次。公共树如下：

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

`pool/` 下的路径按规范化源码包名分组；`Packages` 中的 `Filename` 相对 Archive Root；
SOW 会写入 SHA-256 by-hash 副本，并在 `Release` 中声明。

## 4. HTTP 预览

本地预览可以直接使用：

```bash
cd /srv/sow
python3 -m http.server --bind 127.0.0.1 8080
```

检查协议入口：

```bash
curl --fail http://127.0.0.1:8080/pigsty/dists/trixie/Release >/dev/null
curl --fail http://127.0.0.1:8080/pigsty/dists/trixie/main/binary-amd64/Packages.gz >/dev/null
```

长期服务应使用持续维护的 HTTP Server，并完整暴露 `pigsty/` 树。

## 5. 配置 APT

将 `REPO_HOST` 替换为客户端可访问的地址。未签名测试仓库可使用显式信任的 deb822 配置：

```ini
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: http://REPO_HOST:8080/pigsty
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

`Trusted: yes` 会关闭真实性校验，只适合受控测试。签名仓库应删除该行并配置 Keyring：

```ini
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/pigsty-archive-keyring.gpg
```

打开 `Signed-By` 前，请先完成[仓库签名](/zh/docs/tutorial/signing/)。

## 6. 安全发布

交付前必须通过深度校验：

```bash
sow check -r pigsty
```

向已配置的 filesystem 或 R2 目标交付时，使用 [`sow publish`](/zh/docs/tutorial/serving/)。
如果使用其他传输方式，应把完整仓库复制到离线 staging，再原子切换上线。不要逐文件更新在线
`dists/` 树，否则客户端可能同时看到不同 Generation 的元数据与包体。

## 更新仓库

```bash
sow add /path/to/new.deb -r pigsty -d trixie
sow rm PACKAGE_NAME -r pigsty -d trixie
sow build -r pigsty
sow check -r pigsty
```

策略或签名配置变化后用 `build` 收敛；发布门禁是 `check`，不能只看 `status`。

自动化客户端与平台覆盖见[平台与集成](/zh/docs/reference/compatibility/)。
