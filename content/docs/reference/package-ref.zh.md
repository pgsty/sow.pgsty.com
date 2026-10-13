---
title: "包引用"
linkTitle: "包引用"
description: "按摘要、坐标、文件名或包名选择软件包，并解决匹配歧义。"
categories: [Reference]
tags: [cli, rpm, deb]
url: "/zh/docs/reference/package-ref/"
weight: 300
icon: fa-solid fa-fingerprint
---

`rm`、`show` 和 `where` 接受包引用，`add` 接受文件或目录路径。
先用 `sow ls` 查到包坐标或 SHA-256，再传给其他命令。

```bash
sow ls -r demo -d el9
sow show 'rpm:example-0:1.0-1.x86_64' -r demo
```

<span id="五种形态"></span>
<span id="内容摘要"></span>
<span id="rpm-坐标"></span>
<span id="deb-坐标"></span>
<span id="完整文件名"></span>
<span id="哪些写法不成立"></span>

## 支持的形式

| 形式 | 语法 | 匹配对象 |
|---|---|---|
| SHA-256 | `sha256:<64 位小写十六进制数字>` | 已存储的包字节 |
| RPM 坐标 | `rpm:<name>-<epoch>:<version>-<release>.<arch>` | 包含 epoch 的完整 RPM 身份 |
| DEB 坐标 | `deb:<name>=<version>:<arch>` | 完整 DEB 身份 |
| 文件名 | `example-1.0-1.x86_64.rpm` | 已存储的包文件名 |
| 裸包名 | `example` | 二进制包名 |

SHA-256 必须完整且小写。缩写或大写摘要会被拒绝，退出码为 `6`。
摘要对应已存储字节；Managed RPM 签名可能使它与输入文件摘要不同。

RPM 坐标始终包含 epoch，包没有 epoch 时用 `0`。带 `rpm:` 前缀的引用按完整存储坐标匹配。
匹配时必须提供坐标的全部字段。

DEB 坐标包含完整 Debian 版本（含 epoch、revision）与原生架构。
DEB 使用 `amd64`、`arm64` 或 `all`；RPM 使用 `x86_64`、`aarch64` 或 `noarch`。
这些值来自包本身，不是配置别名。

```bash
sow where 'rpm:example-0:1.0-1.noarch'
sow where 'deb:example=2:1.0-1:amd64'
```

文件名方便输入，但不一定唯一。脚本优先使用坐标或完整摘要。
包引用不支持路径、通配符、正则表达式或版本范围。

<span id="裸包名"></span>

## 包名匹配与歧义

| 命令 | 裸包名匹配多个版本或架构时 |
|---|---|
| `rm` | 移除所选 Dist 中的全部匹配成员 |
| `show` | 拒绝歧义引用并列出候选 |
| `where` | 要求唯一包身份，并返回该身份在各仓库中的位置 |

按包名移除前可先预览：

```bash
sow rm example -r demo -d el9 --check
```

`show` 或 `where` 遇到歧义时，从候选列表选择坐标或摘要。
多个仓库保存相同格式、坐标和 SHA-256 时，`where` 可以返回多个仓库位置。
仓库中的版本或字节不同时，使用 `-r` 或更精确的引用。

其他引用形式在单个仓库中必须确定一个对象。匹配不到或存在歧义时，退出码为 `6`。

<span id="作用域"></span>

## 搜索范围

`rm` 和 `where` 搜索期望成员。不带 `-d` 时，`show` 搜索全部已记录包对象，
包括已退出 Dist 的包；带 `-d` 时，只搜索所选 Dist 的期望成员。未记录的文件不参与查询。

| 命令 | 默认范围 | 选择方式 |
|---|---|---|
| `rm` | 一个仓库中所选 Dist 的成员 | `-r`；可重复的 `-d`，或推断出的 Dist |
| `show` | 所选仓库的全部已记录包对象 | `-r`；`-d` 限定为所选 Dist 的期望成员 |
| `where` | 工作区全部仓库 | 可选 `-r`、`-d` |

`rm` 无法推断 Dist 且仓库中有多个 Dist 时，需要指定 `-d`。
不带 `-r` 的 `where -d NAME` 搜索包含该 Dist 名称的仓库。
所请求的 Dist 名称在所有仓库中都不存在时，命令报错。

<span id="坐标与身份"></span>

## 坐标冲突

一个仓库内，一个坐标最多对应一个内容对象。已有坐标下加入不同包时，SOW 拒绝覆盖。
仅改变签名也会改变完整字节身份。

启用 RPM 包签名时，坐标、排除签名头后的包体摘要和签名策略匹配，就可以复用已有签名对象。
其他情况下，改变字节应使用新的发行版本和文件名。详见[签名](/zh/docs/feature/signing/)。

命令选项见 [`rm`](/zh/docs/command/rm/)、[`show`](/zh/docs/command/show/)和
[`where`](/zh/docs/command/where/)。

<span id="延伸阅读"></span>
