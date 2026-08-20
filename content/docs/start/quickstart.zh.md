---
title: "快速上手"
linkTitle: "快速上手"
description: "索引一个 RPM/DEB 软件包目录，对外服务，并配置客户端。"
url: "/zh/docs/start/quickstart/"
weight: 200
icon: fa-solid fa-bolt
---

Plain 模式在一个目录内生成平面仓库。它不读取 `sow.yml`，不创建工作区，也不维护数据库。

## 1. 准备目录

把 RPM 和/或 DEB 文件放在目录顶层。`sow create` 不递归扫描，也不移动或改名包文件。

```bash
mkdir -p /srv/repo
cp /path/to/packages/*.rpm /path/to/packages/*.deb /srv/repo/
```

如果某种格式不存在，请只复制你实际拥有的软件包。

## 2. 生成元数据

```bash
sow create /srv/repo
```

混合格式输出形态如下：

```console
created /srv/repo: rpm=1 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

目录会变成：

```text
/srv/repo/
├── package.rpm
├── package.deb
├── repodata/       # RPM: repomd.xml、primary、filelists、other
├── Packages        # DEB 平面索引
└── Packages.gz
```

Plain 模式不生成 DEB `Release`、`InRelease` 或 `Release.gpg`。RPM 与 DEB 元数据在一次
操作中生成；任何解析或渲染错误都会阻止新索引提交。

## 3. 对外服务

本地检查可以使用任意静态文件服务器：

```bash
cd /srv/repo
python3 -m http.server --bind 127.0.0.1 8080
```

在另一个终端检查两个协议入口：

```bash
curl --fail http://127.0.0.1:8080/repodata/repomd.xml >/dev/null
curl --fail http://127.0.0.1:8080/Packages.gz >/dev/null
```

Python 服务器只适合预览；长期服务请使用正常维护的 HTTP 服务器。

## 4. 配置客户端

把 `REPO_HOST` 换成客户端能访问的地址。

```ini {tab="dnf" group="dnf-apt" value="dnf"}
# /etc/yum.repos.d/sow-quickstart.repo
[sow-quickstart]
name=SOW Quick Start
baseurl=http://REPO_HOST:8080/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```

```text {tab="apt" value="apt"}
# /etc/apt/sources.list.d/sow-quickstart.list
deb [trusted=yes] http://REPO_HOST:8080/ ./
```

刷新索引并安装软件包：

```bash
# RPM 客户端
sudo dnf makecache
sudo dnf install PACKAGE_NAME

# DEB 客户端
sudo apt update
sudo apt install PACKAGE_NAME
```

APT source 末尾的 `./` 表示平面仓库。`[trusted=yes]` 与关闭 DNF 签名检查只适用于这个
未签名的快速示例；需要真实性保证时应使用已签名 Managed 仓库。

## 5. 更新仓库

增删包文件后重新执行同一条命令：

```bash
sow create /srv/repo
```

目录内容就是 Plain 模式的全部状态。包字节不变时，生成的元数据具有确定性，重复运行会报告
`noop=true`。

自动化场景可使用带版本的 JSON 信封：

```bash
sow create /srv/repo --json
```

## 何时使用 Managed 模式

如果目录已经恰好包含要发布的全部内容，使用 Plain。需要具名 Dist、架构视图、成员策略、
已签名元数据、Generation、审计或发布目标时，使用 [Managed 工作区](/zh/docs/start/workspace/)。

另见 [`sow create`](/zh/docs/command/create/) 与
[Plain 平面仓库](/zh/docs/feature/plain/)。
