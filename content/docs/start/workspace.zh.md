---
title: "第一个工作区"
linkTitle: "第一个工作区"
description: "创建工作区，建立 RPM/DEB Dist，添加软件包并校验公共树。"
url: "/zh/docs/start/workspace/"
weight: 300
icon: fa-solid fa-layer-group
---

Managed 模式会持久保存配置、成员关系、Generation 与审计状态。下面从空目录开始。

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
└── .sow/     # SQLite 状态、锁、staging、恢复与操作日志
```

不要编辑或对外服务 `.sow/`。`init` 是幂等操作：重复执行会校验并收敛已声明的 Repository
与 Dist，不会重置有效工作区。

默认架构族是 `x86_64` 与 `aarch64`。配置接受 `amd64`、`arm64` 别名，并规范化为上述族名。

## 创建 Repository 与两个 Dist {#2-创建-repository-与两个-dist}

```bash
sow repo new local
sow dist new el9 --format rpm
sow dist new bookworm --format deb
```

一个 Repository 拥有一棵公共 `pool/ + dists/` 树和一份私有状态数据库。每个 Dist 只有
一种格式。`dist new` 会立即生成合法空视图，客户端读取空 Dist 时得到空索引而不是 404。

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

SOW 从包本身读取身份与架构，把接受的字节存入 `local/pool/`，更新 Desired Membership，
并在返回前构建受影响的 Dist。输入路径只用于导入；后续构建使用 Managed 包池。

需要合并多次成员变更时，用 `--skip` 暂不构建，最后统一收敛：

```bash
sow add /path/to/more/*.rpm -d el9 --skip
sow build
```

Desired Membership 领先于 Built Generation 时，Repository 状态为 `dirty`，且
`ready_to_copy=false`。

## 查看与校验 {#4-查看与校验}

```bash
sow status
sow ls -d el9
sow ls -d bookworm
sow check
```

`status` 是低成本状态读取。`check` 是交付门禁：它校验配置、保留根、状态、公共文件权限、
包字节、Desired Membership、索引、签名与 Generation manifest，且不写入任何内容。
只有 clean 且所有层都通过的 Repository 才返回成功。

查看规范化配置与默认值：

```bash
sow config show --all
```

## 对外服务 Repository {#5-对外服务-repository}

公共交付单元是 `/srv/sow/local`，不是工作区根。把这个目录挂到稳定 URL 前缀；不要暴露
`sow.yml` 或 `.sow/`。

- DNF base URL：`https://repo.example.com/local/dists/el9/x86_64/`
- APT source：`deb https://repo.example.com/local bookworm main`

安全的 Nginx 与 filesystem 发布流程见[对外服务](/zh/docs/tutorial/serving/)。

{{% /steps %}}

## 选择规则

- Workspace：从当前目录向上查找，或从 `-C DIR` 开始查找。
- Repository：`-r NAME`、当前路径所属 Repository，或唯一已配置 Repository。
- Dist：`-d NAME`，可重复；只有命令能够唯一确定范围时才可省略。

存在歧义时直接报错；SOW 不会随便挑选 Repository 或 Dist。

## 下一步

- [核心概念](/zh/docs/start/concepts/)
- [搭建 YUM 仓库](/zh/docs/tutorial/yum-repo/)
- [搭建 APT 仓库](/zh/docs/tutorial/apt-repo/)
- [`sow.yml` 参考](/zh/docs/reference/config/)
