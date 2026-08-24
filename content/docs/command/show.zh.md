---
title: "sow show"
linkTitle: "show"
description: "查看一个 Package Object 的身份、标准化事实、存储、签名与成员关系。"
categories: [Command]
tags: [cli, managed, signing]
url: "/zh/docs/command/show/"
weight: 900
icon: fa-solid fa-file-lines
---

`sow show` 在所选 Repository 中解析一个包引用，并打印完整 Package Object。该命令只读，
不获取写锁。

## 语法

```text
sow show PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择 Repository | [选择规则](/zh/docs/command/#repository-选择) |
| `-d, --dist NAME` | 将候选项收窄到指定 Dist；可重复 | 整个 Repository |
| `--json` | 将结果包装进 `sow.cli/v1` Envelope | false |

## 包引用

`PACKAGE` 可使用 `sha256:<hex>` 内容身份、规范的 `rpm:<NEVRA>` 或
`deb:<name>=<version>:<arch>` 坐标、完整包文件名或裸二进制包名。精确文法见
[包引用](/zh/docs/reference/package-ref/)。

裸包名必须在所选范围内唯一。`sow rm foo` 会移除所有匹配版本，而 `sow show foo` 只允许返回
一个对象；有歧义时会列出候选项：

```console
sow show libpq5 -r pgsql -d trixie
operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1:amd64 sha256:fa84dc64..., deb:libpq5=18.3-1:amd64 sha256:491992c5..., deb:libpq5=18.3-1:arm64 sha256:3a2f7ef7...
```

从错误信息或 [`sow ls`](/zh/docs/command/ls/) 复制精确坐标/SHA-256 后重试。

## 输出

不带 `--json` 时，`show` 以紧凑的人类可读格式输出身份、存储路径与 Desired/Built 位置：

```console
sow show centos-release-6-0.el6.centos.5.x86_64.rpm -r demo -d el9
package repository=demo coordinate="centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16 format=rpm architecture=x86_64 size=19776 storage=pool
pool=pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
dists=el9 built_dists=el9
```

加上 `--json` 后，标准 Envelope 的 `result` 会返回完整 Package Object，包括下列规范化字段。

| 字段 | 含义 |
|---|---|
| `canonical_arch` | `x86_64`、`aarch64`，或 RPM `noarch` / DEB `all` 对应的 `neutral` |
| `kind` | 策略分类：`main`、`debuginfo`、`debugsource`、`llvmjit`、`dbgsym`、`dbg` |
| `source` | 标准化源码包名 |
| `payload_sha256` | RPM 去签名摘要，用于保证重签名幂等 |
| `signature_key` | 包内签名的 Key ID（如有） |
| `storage` | 构建前为 `pending`，进入仓库树后为 `pool` |
| `dists` / `built_dists` | Desired 与当前 Built Membership |

`-d` 只收窄候选解析范围，不改变包身份。

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 已输出一个 Package Object |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误、未发现工作区或隐式 Repository 选择有歧义 |
| `5` | Repository 状态库不可读或不一致 |
| `6` | 显式范围未配置，或引用没有匹配/匹配多个对象 |

## 参见

- [`sow ls`](/zh/docs/command/ls/) —— 从 Dist Membership 获取精确身份
- [`sow where`](/zh/docs/command/where/) —— 跨 Repository 搜索
- [`sow rm`](/zh/docs/command/rm/) —— 移除匹配的 Desired Membership
- [JSON 输出](/zh/docs/reference/json/) —— 完整结果结构
