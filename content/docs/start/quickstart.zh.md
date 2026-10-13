---
title: "快速上手"
linkTitle: "快速上手"
description: "索引一个 RPM/DEB 软件包目录，对外服务，并配置客户端。"
categories: [Start]
tags: [plain, rpm, deb, cli]
url: "/zh/docs/start/quickstart/"
weight: 200
icon: fa-solid fa-bolt
search_keywords: [快速上手, 入门, sow create, 平面仓库, 软件源, RPM, DEB]
search_boost: 1.6
---

Plain 模式为一个软件包目录生成仓库，不需要工作区或配置文件。准备 SOW、用于预览的 Python 3，以及至少一个 RPM 或 DEB 文件。

{{% steps %}}

## 准备目录 {#1-准备目录}

创建可写目录。将下例输入路径换成实际文件，只执行已有格式对应的复制命令：

```bash
mkdir -p "$HOME/sow-quickstart"
cp /path/to/example.rpm "$HOME/sow-quickstart/"
cp /path/to/example.deb "$HOME/sow-quickstart/"
```

把包放在目录顶层；`sow create` 不扫描子目录。

## 生成元数据 {#2-生成元数据}

```bash
sow create "$HOME/sow-quickstart"
```

目录中有一个 RPM 和一个 DEB 时，输出包含：

```text
rpm=1 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

原始软件包旁会新增索引：

```text
sow-quickstart/
├── example.rpm
├── example.deb
├── repodata/       # RPM 索引与元数据
├── Packages        # DEB 平面索引
└── Packages.gz
```

SOW 只为实际存在的格式生成索引。Plain 模式不生成 APT `Release`、`InRelease` 或 `Release.gpg` 文件，也不改变软件包名称与路径。

## 启动本地服务器 {#3-对外服务}

在另一个终端执行以下命令，并保持运行：

```bash
python3 -m http.server --bind 127.0.0.1 --directory "$HOME/sow-quickstart" 8080
```

如果本机没有 APT 或 DNF 客户端，按已添加的格式检查 HTTP 入口：

```bash
# RPM
curl --fail http://127.0.0.1:8080/repodata/repomd.xml >/dev/null

# DEB
curl --fail http://127.0.0.1:8080/Packages.gz >/dev/null
```

此服务器只能从本机访问。要供其他客户端访问或长期运行，请按[对外服务](/zh/docs/tutorial/serving/)配置。

## 配置本机客户端 {#4-配置客户端}

如果预览服务器运行在 Linux 上，为本机包管理器创建源配置文件。下面使用未签名元数据，并关闭客户端签名检查。需要签名元数据时，使用 [Managed 工作区](/zh/docs/start/workspace/)与[签名教程](/zh/docs/tutorial/signing/)。

{{< tabs group="package-manager" default="dnf" label="选择包管理器" >}}
{{< tab label="DNF / YUM" value="dnf" >}}
把以下内容保存为 `/etc/yum.repos.d/sow-quickstart.repo`：

```ini {copy="all"}
[sow-quickstart]
name=SOW Quick Start
baseurl=http://127.0.0.1:8080/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```

刷新索引并安装其中一个软件包：

```bash {copy="all"}
sudo dnf --disablerepo='*' --enablerepo=sow-quickstart makecache
sudo dnf install PACKAGE_NAME
```
{{< /tab >}}
{{< tab label="APT" value="apt" >}}
把以下内容保存为 `/etc/apt/sources.list.d/sow-quickstart.list`：

```text {copy="all"}
deb [trusted=yes] http://127.0.0.1:8080/ ./
```

末尾的 `./` 选择平面仓库。刷新索引并安装其中一个软件包：

```bash {copy="all"}
sudo apt update
sudo apt install PACKAGE_NAME
```
{{< /tab >}}
{{< /tabs >}}

把 `PACKAGE_NAME` 换成包内元数据中的名称，而不是文件名。macOS 用户可以完成上述 HTTP 检查；软件包安装需在兼容的 Linux 客户端上执行。

## 更新仓库 {#5-更新仓库}

添加或删除软件包文件后，重新生成索引：

```bash
sow create "$HOME/sow-quickstart"
```

包文件与参数不变时，生成的元数据也不变，重复运行会报告 `noop=true`。

替换其他 YUM 元数据生成工具时，按[迁移现有 YUM 仓库](/zh/docs/tutorial/yum-migration/)保留客户端缓存所需的时间戳。

{{% /steps %}}

预览完成后，用 `Ctrl+C` 停止服务器，并从客户端删除本例的源配置文件。软件包目录可以保留，以后继续使用。

<span id="何时使用-managed-模式"></span>

## 下一步

需要具名 Dist、架构视图、版本限制、元数据签名与发布目标时，使用 [Managed 工作区](/zh/docs/start/workspace/)。全部 Plain 参数见 [`sow create`](/zh/docs/command/create/)。
