---
title: "搭建 YUM 仓库"
linkTitle: "搭建 YUM 仓库"
description: "创建托管 RPM 仓库，配置成员策略，对外服务并接入 dnf。"
url: "/zh/docs/tutorial/yum-repo/"
weight: 100
icon: fa-solid fa-box-open
---

本教程从零创建一个 Managed RPM 仓库。你需要 SOW 0.2.0、一个可写目录，以及一个或多个
RPM 文件。

## 1. 创建工作区

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
```

Dist 名称由你定义。SOW 不会根据 `el9` 推断操作系统版本。

## 2. 配置成员策略

编辑生成的 `sow.yml`。下面的配置按包名与架构各保留一个版本，并排除调试包：

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  pigsty:
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]
targets: {}
```

手工修改配置后，先校验再写仓库状态：

```bash
sow config check
sow config show --all
```

策略先执行 `exclude`，再执行 `limit`。`noarch` 包会投影到每个启用的架构视图，不能写进
`architectures`。

## 3. 添加 RPM

```bash
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow status -r pigsty
sow check -r pigsty
```

`add` 解析包头，将每个接纳的包只保存一次，更新 Desired 成员关系并落成新 Generation。
被策略排除的输入会逐项报告，但不算命令失败。

公共树如下：

```text
/srv/sow/pigsty/
├── pool/...
└── dists/el9/
    ├── x86_64/repodata/...
    └── aarch64/repodata/...
```

rpm-md 的 `location href` 通过相对路径访问根目录下的 `pool/`。不要只复制某个架构目录；
它不是独立仓库。

## 4. HTTP 预览

本地预览可以直接使用：

```bash
cd /srv/sow
python3 -m http.server --bind 127.0.0.1 8080
```

在另一个终端检查入口：

```bash
curl --fail http://127.0.0.1:8080/pigsty/dists/el9/x86_64/repodata/repomd.xml >/dev/null
```

长期服务应使用持续维护的 HTTP Server。它必须完整暴露 `pigsty/` 树，确保客户端解析后落到
`pigsty/pool/` 的软件包 URL 可访问。

## 5. 配置 dnf

将 `REPO_HOST` 替换为客户端可访问的地址：

```ini
# /etc/yum.repos.d/pigsty.repo
[pigsty-el9]
name=Pigsty EL9
baseurl=http://REPO_HOST:8080/pigsty/dists/el9/$basearch/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```

刷新并查询仓库：

```bash
sudo dnf clean metadata
sudo dnf makecache --refresh
dnf --disablerepo='*' --enablerepo=pigsty-el9 list available
```

这里有意使用未签名配置。只有完成[仓库签名](/zh/docs/tutorial/signing/)后，才应打开客户端验签。

## 6. 发布或导出

交付前必须通过深度校验：

```bash
sow check -r pigsty
```

向已配置的 filesystem 或 R2 目标交付时，使用 [`sow publish`](/zh/docs/tutorial/serving/)。
只有先复制到离线 staging、再原子切换上线时，才适合整根复制；不要对在线仓库做无序原地同步。

默认 `dnf reposync` 等工具会拒绝指向根包池的父级相对路径。遇到这种消费者时，导出一份
自包含 RPM Leaf：

```bash
sow export rpm-leaf el9 x86_64 /srv/export/pigsty-el9-x86_64 -r pigsty
```

目标目录必须不存在或为空。默认会复制包体；`--hardlink` 只适用于同一文件系统、可信且只读的
显式优化场景。

## 更新仓库

```bash
sow add /path/to/new.rpm -r pigsty -d el9
sow rm PACKAGE_NAME -r pigsty -d el9
sow build -r pigsty
sow check -r pigsty
```

`add` 与 `rm` 修改 Desired 成员关系；策略或签名配置变化后用 `build` 收敛；发布门禁是
`check`，不能只看 `status`。

当前测试矩阵究竟证明了哪些客户端行为，请看[兼容性](/zh/docs/reference/compatibility/)。
