---
title: "sow show"
linkTitle: "show"
description: "查看一个软件包的存储位置与成员关系。"
categories: [Command]
tags: [cli, managed, signing]
url: "/zh/docs/command/show/"
weight: 900
icon: fa-solid fa-file-lines
---

`sow show` 查看所选仓库中的一个软件包。文本输出包含包信息、存储位置与成员关系。需要完整的软件包记录时，加上 `--json`。

## 语法

```text
sow show PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择仓库 | [选择规则](/zh/docs/command/#repository-选择) |
| `-d, --dist NAME` | 将候选项收窄到指定 Dist；可重复 | 整个仓库 |
| `--json` | 输出 JSON | false |

## 包引用

`PACKAGE` 可使用 `sha256:<hex>` 内容哈希、规范的 `rpm:<NEVRA>` 或
`deb:<name>=<version>:<arch>` 坐标、完整包文件名或裸二进制包名。完整格式见
[包引用](/zh/docs/reference/package-ref/)。

裸包名必须在所选范围内唯一。`sow rm foo` 会移除所有匹配版本，而 `sow show foo` 只允许返回
一个对象；有歧义时会列出候选项：

```console
sow show libpq5 -r pgsql -d trixie
operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1:amd64 sha256:fa84dc64..., deb:libpq5=18.3-1:amd64 sha256:491992c5..., deb:libpq5=18.3-1:arm64 sha256:3a2f7ef7...
```

从错误信息或 [`sow ls`](/zh/docs/command/ls/) 复制精确坐标/SHA-256 后重试。

## 输出

不带 `--json` 时，`show` 输出包信息、存储路径，以及期望与已构建状态中的位置：

```console
sow show centos-release-6-0.el6.centos.5.x86_64.rpm -r demo -d el9
package repository=demo coordinate="centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16 format=rpm architecture=x86_64 size=19776 storage=pool
pool=pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
dists=el9 built_dists=el9
```

加上 `--json` 后，`result.package` 会返回完整软件包记录，包括下列规范化字段。

| 字段 | 含义 |
|---|---|
| `canonical_arch` | `x86_64`、`aarch64`，或 RPM `noarch` / DEB `all` 对应的 `neutral` |
| `kind` | 策略分类：`main`、`debuginfo`、`debugsource`、`llvmjit`、`dbgsym`、`dbg` |
| `source` | 标准化源码包名 |
| `payload_sha256` | RPM 不含签名部分的摘要，用于判断是否可以复用包文件 |
| `signature_key` | 包内签名的密钥 ID（如有） |
| `storage` | 构建前为 `pending`，进入仓库树后为 `pool` |
| `dists` / `built_dists` | 期望与当前已构建状态中的位置 |

不带 `-d` 时，查找范围包括当前没有成员关系的已存储对象。带 `-d` 时，候选包必须属于所选 Dist 的期望成员。返回的 `dists` 与 `built_dists` 列表覆盖整个仓库。

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 已输出一个软件包对象 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误、未发现工作区或隐式仓库选择有歧义 |
| `5` | 仓库状态库不可读或不一致 |
| `6` | 显式范围未配置，或引用没有匹配/匹配多个对象 |

## 参见

- [`sow ls`](/zh/docs/command/ls/) —— 从 Dist 成员关系获取精确包引用
- [`sow where`](/zh/docs/command/where/) —— 跨仓库搜索
- [`sow rm`](/zh/docs/command/rm/) —— 移除匹配的期望成员
- [JSON 输出](/zh/docs/reference/json/) —— 完整结果结构
