---
title: "搭建 YUM 仓库"
linkTitle: "搭建 YUM 仓库"
description: "创建托管 RPM 仓库，配置成员策略，对外服务并接入 dnf。"
categories: [Tutorial]
tags: [yum, rpm, managed, dist]
url: "/zh/docs/tutorial/yum-repo/"
weight: 100
icon: fa-solid fa-box-open
---

本教程从零创建一个 Managed RPM 仓库。先安装 SOW、Python 3，并准备适合目标客户端的 RPM 文件。使用当前用户可创建、可写入的空目录 `/srv/sow`，或换成其他可写路径。

## 1. 创建工作区

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
```

`el9` 是这个 RPM 包集合的名称，可以按需要更改。它不改变软件包的操作系统兼容性。

## 2. 配置成员策略

编辑生成的 `sow.yml`。下面的配置按包名与架构各保留一个版本，并排除调试包与 LLVM JIT 包：

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

检查配置：

```bash
sow config check
```

策略先执行 `exclude`，再执行 `limit`。SOW 把 `noarch` 包加入每个启用的架构视图。`architectures` 中只填写 CPU 架构名。

## 3. 添加 RPM

```bash
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow check -r pigsty
```

把输入路径换成实际 RPM 目录。`add` 将接受的软件包存入包池，更新成员并构建索引。检查逐包输出：被排除的文件会单独报告，不会使整条命令失败。

公共树如下：

```text
/srv/sow/pigsty/
├── pool/...
└── dists/el9/
    ├── x86_64/repodata/...
    └── aarch64/repodata/...
```

RPM 索引通过相对路径指向 `pool/`。服务或复制完整的 `pigsty/` 目录树，客户端才能下载软件包。

## 4. HTTP 预览

在另一个终端执行以下命令，并保持运行：

```bash
python3 -m http.server --bind 127.0.0.1 --directory /srv/sow/pigsty 8080
```

预览只提供仓库根目录中的文件，并且只能从本机访问。长期运行或供其他主机访问时，按[对外服务](/zh/docs/tutorial/serving/)配置。

## 5. 配置 dnf

在运行预览的 Linux 主机上，把以下内容保存为 `/etc/yum.repos.d/pigsty.repo`。远程客户端需先发布仓库，再换成其公共地址：

```ini
# /etc/yum.repos.d/pigsty.repo
[pigsty-el9]
name=Pigsty EL9
baseurl=http://127.0.0.1:8080/dists/el9/$basearch/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```

刷新并查询仓库：

```bash
sudo dnf --disablerepo='*' --enablerepo=pigsty-el9 makecache --refresh
dnf --disablerepo='*' --enablerepo=pigsty-el9 list available
```

本例使用未签名软件包与元数据。按[仓库签名](/zh/docs/tutorial/signing/)启用验签。预览完成后，删除此源配置文件并停止 Python 服务器。

## 6. 发布或导出

使用 [`sow publish`](/zh/docs/tutorial/serving/) 发布到 filesystem 或 R2 目标。它按客户端所需的顺序上传软件包与元数据。隔离主机的手工交付步骤也见该教程。

默认 `dnf reposync` 等工具会拒绝指向根包池的父级相对路径。需要供这些工具使用时，导出一份
独立 RPM 仓库：

```bash
sow export rpm-leaf el9 x86_64 /srv/export/pigsty-el9-x86_64 -r pigsty
```

RPM Dist 必须属于当前构建快照。混合仓库先检查[导出前提](/zh/docs/command/export/)。

目标目录必须不存在或为空。导出默认复制软件包。`--hardlink` 只用于同一文件系统；导出文件与源包池共享存储，应保持只读。

## 更新仓库

```bash
sow add /path/to/new.rpm -r pigsty -d el9
sow check -r pigsty
```

`add` 会自动构建更新。配置 `limit: 1` 后，同包名、同架构的最新版本会替换此前成员。修改配置后执行 `sow build -r pigsty`。

撤下软件包时，先用 `sow rm PACKAGE_NAME -r pigsty -d el9 --check` 预览选择结果，再去掉 `--check` 执行。包名会选中其全部版本与架构；只删除一个包对象时，使用 SHA-256 引用。

已测试客户端见[平台与集成](/zh/docs/reference/compatibility/)。
