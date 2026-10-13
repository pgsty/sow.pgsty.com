---
title: "第一个工作区"
linkTitle: "第一个工作区"
description: "创建工作区，组织 RPM 与 DEB 软件包，并检查仓库。"
categories: [Start]
tags: [managed, repository, dist, generation]
url: "/zh/docs/start/workspace/"
weight: 300
icon: fa-solid fa-layer-group
---

本例创建一个 Managed 仓库，包含两个具名软件包集合，称为 Dist：
`el9` 存放 RPM，`bookworm` 存放 DEB。使用可写的空目录 `/srv/sow`，或换成其他路径。

{{% steps %}}

## 初始化工作区 {#1-初始化工作区}

```bash
sow init /srv/sow
cd /srv/sow
```

`init` 创建：

```text
/srv/sow/
├── sow.yml   # 配置；schema: sow/v3
└── .sow/     # SOW 管理的私有状态
```

需要调整配置时，编辑 `sow.yml`。私有目录 `.sow/` 由 SOW 管理。
重复执行 `init` 不会重置已有软件包或状态。

## 创建仓库与两个 Dist {#2-创建-repository-与两个-dist}

```bash
sow repo new local
sow dist new el9 --format rpm
sow dist new bookworm --format deb
```

每个 Dist 只有一种包格式。`dist new` 默认创建 `x86_64` 与 `aarch64` 的空索引。
两个 Dist 共用仓库的 `pool/` 目录。

此时公共布局为：

```text
/srv/sow/local/
├── pool/
└── dists/
    ├── el9/
    │   ├── x86_64/repodata/
    │   └── aarch64/repodata/
    └── bookworm/
        ├── Release
        └── main/
            ├── binary-amd64/{Packages,Packages.gz,by-hash/}
            └── binary-arm64/{Packages,Packages.gz,by-hash/}
```

## 添加软件包 {#3-添加软件包}

显式选择目标 Dist：

```bash
sow add /path/to/packages/*.rpm -d el9
sow add /path/to/packages/*.deb -d bookworm
```

把输入路径换成实际软件包文件。SOW 读取包身份与架构，将接受的文件存入 `local/pool/`，更新成员并构建受影响的 Dist。后续构建使用包池，SOW 不再依赖原始输入文件。

## 查看与校验 {#4-查看与校验}

```bash
sow status
sow ls -d el9
sow ls -d bookworm
sow check
```

`ls` 列出各 Dist 中的软件包。`status` 应显示 `clean` 与 `ready_to_copy=true`。
`check` 成功表示文件与记录的构建结果一致。

## 对外提供仓库 {#5-对外服务-repository}

发布完整的 `/srv/sow/local` 目录，让客户端能同时访问索引与软件包。工作区配置和 `.sow/` 保留在服务器根目录之外。

按[对外服务](/zh/docs/tutorial/serving/)配置 Nginx 发布。[YUM](/zh/docs/tutorial/yum-repo/) 与 [APT](/zh/docs/tutorial/apt-repo/) 教程提供客户端配置，包括未签名仓库所需的信任设置。

{{% /steps %}}

## 批量更新

以后要连续添加多批软件包时，给 `add` 加上 `--skip`，最后构建一次：

```bash
sow add /path/to/more/*.rpm -d el9 --skip
sow build
```

有待构建的成员变更时，`sow status` 显示 `dirty` 与 `ready_to_copy=false`。


## 选择规则

上例从当前目录找到工作区，并选择其中唯一的仓库。
在其他目录运行时，加上 `-C /srv/sow`；工作区内有多个仓库时，加上 `-r local`。
使用 `-d NAME` 选择 Dist，可重复指定多个。完整的发现规则与默认值见[选择规则](/zh/docs/command/#repository-选择)。

## 下一步

- [核心概念](/zh/docs/start/concepts/)
- [搭建 YUM 仓库](/zh/docs/tutorial/yum-repo/)
- [搭建 APT 仓库](/zh/docs/tutorial/apt-repo/)
- [`sow.yml` 参考](/zh/docs/reference/config/)
