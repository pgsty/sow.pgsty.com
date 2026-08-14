---
title: "包引用"
linkTitle: "包引用"
description: "命令行上指代一个软件包的五种写法,以及歧义如何裁决。"
url: "/zh/docs/reference/package-ref/"
weight: 300
icon: fa-solid fa-fingerprint
---

`sow rm`、`sow show`、`sow where` 都接受一个 `PACKAGE` 参数。本页定义你能在那里写什么。
三条命令共用同一套文法,只有对 **歧义名称** 的处理不同。

这里的内容与 `sow add` 无关 —— `add` 接受的是文件系统路径,不是包引用。

## 五种形态

| 形态 | 例子 | 匹配 |
|---|---|---|
| 内容摘要 | `sha256:d06d7f23b9cf...b98b1229` | 恰好一个包对象 |
| RPM 坐标 | `rpm:pev2-0:1.23.0-1.noarch` | 恰好一个 RPM |
| DEB 坐标 | `deb:libpq5=18.3-1.pgdg12+1:amd64` | 恰好一个 DEB |
| 完整文件名 | `pev2-1.23.0-1.noarch.rpm` | 以该文件名存储的包 |
| 裸包名 | `pev2` | 该名称的全部版本与架构 |

前三种是 **精确** 引用:指名道姓,要么命中要么失败。后两种是便利写法,可能匹配多个对象。

你不需要手工拼这些字符串。`sow ls` 会直接打印每个包的摘要与坐标,可以原样粘回命令行:

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:5759c643a789631346e3ed315a696a0118f81f7cc3c65e5a4385a876983d3a18	rpm:blackbox_exporter-0:0.28.0-1.x86_64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229	rpm:pev2-0:1.23.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

### 内容摘要

```text
sha256:<64 位小写十六进制>
```

已存储包体完整字节的 SHA-256。这是 SOW 里最强的引用形式:它就是对象身份,不可能有歧义。

```bash
sow where sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229
```

```console
{"reference":"sha256:d06d7f23...b98b1229","locations":[{"repository":"pigsty","dists":["el9"],"built_dists":["el9"],"sha256":"d06d7f23...b98b1229","coordinate":"rpm:pev2-0:1.23.0-1.noarch"}]}
```

摘要必须完整且小写。**不支持** 前缀匹配,也不做大小写折叠 —— 位数不足或大写都属于用法拒绝,
不是"没找到":

```console
operation rejected: managed: operation rejected: sha256 reference requires 64 lowercase hexadecimal digits
```

注意这个摘要覆盖的是 **已存储** 的字节。如果仓库对 RPM 包体做了重签,
对象摘要与你交给 `sow add` 的那个文件的摘要就不一样了。

### RPM 坐标

```text
rpm:<name>-<epoch>:<version>-<release>.<arch>
```

完整 NEVRA,加 `rpm:` 前缀。每一段都必填,**包括 epoch** —— 包本身没有 epoch 时写 `0`。

```bash
sow where 'rpm:pev2-0:1.23.0-1.noarch'
```

在 shell 里请加引号:NEVRA 含冒号,否则可能被历史展开或路径补全改写。

前缀与 epoch 都是必需的。少任何一个,这串字符就会被当成裸名解析,从而什么都找不到:

```console
sow where 'rpm:pev2-1.23.0-1.noarch'
operation rejected: managed: operation rejected: package reference "rpm:pev2-1.23.0-1.noarch" was not found in the selected Workspace scope
```

架构那一段取自 RPM 包头:`x86_64`、`aarch64` 或 `noarch`。它 **不是** 规范族名 ——
`noarch` 包这里就写 `noarch`,尽管 SOW 内部把它归类为 neutral(中性)。

### DEB 坐标

```text
deb:<package>=<version>:<architecture>
```

Debian 身份三元组,加 `deb:` 前缀。版本是含 epoch 与 revision 的完整 Debian 版本号;
架构是生态名(`amd64`、`arm64`、`all`),不是规范族名。

```bash
sow where 'deb:libpq5=18.3-1.pgdg12+1:amd64'
```

三段都必填。`deb:libpq5=18.3-1.pgdg12+1` 不带架构,匹配不到任何东西。

### 完整文件名

包存储时的完整文件名,含扩展名:

```bash
sow where 'pev2-1.23.0-1.noarch.rpm'
sow where 'libpq5_18.3-1.pgdg12+1_amd64.deb'
```

看着目录列表操作时,这是最好敲的写法。但它 **不是身份** —— SOW 不用文件名区分包,
理论上两个不同对象可以叫同一个名字。脚本里请优先用坐标或摘要。

### 裸包名

只写二进制包名:

```bash
sow where pev2
```

它的含义取决于命令:

- **`sow rm`** 把它理解为所选 Dist 中该名称的 **全部** 版本与原生架构。这是有意设计的 ——
  下架一个包通常意味着全部下架。先用 `-c` 预览:

  ```bash
  sow rm libpq5 -d trixie -c
  ```

  ```console
  {"repository":"pigsty","desired_revision":10,"built_generation":"00000000000000000010","dirty":false,"check":true,
   "removed":[{"dist":"trixie","sha256":"310611d0...","coordinate":"deb:libpq5=18.2-1.pgdg12+1:amd64","name":"libpq5"},
              {"dist":"trixie","sha256":"4b526223...","coordinate":"deb:libpq5=18.3-1.pgdg12+1:amd64","name":"libpq5"},
              {"dist":"trixie","sha256":"cadeb929...","coordinate":"deb:libpq5=18.3-1.pgdg12+1:arm64","name":"libpq5"}], ...}
  ```

- **`sow show` 与 `sow where`** 要求它唯一命中。这两条命令描述的是单个包,
  名称匹配多个时会连同候选列表一起拒绝:

  ```console
  operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1.pgdg12+1:amd64 sha256:310611d0fea1ce82644f48d90d485c60738b21e52ab5a60e1de43875bdfef601, deb:libpq5=18.3-1.pgdg12+1:amd64 sha256:4b5262231787caf1f367f5c8705a8a03d3176c31a15e6096946d50514db128be, deb:libpq5=18.3-1.pgdg12+1:arm64 sha256:cadeb9294901ac5ae6228bd3471c444cc288d9894af0dd0730909596d9dfcefb
  ```

  每个候选都同时给出坐标与摘要,所以修正方式就是把其中一条粘回命令行。

## 哪些写法不成立

不带 `rpm:` 前缀的 NEVRA 看起来像坐标,实际会被当作裸名解析,
而裸名里不含 epoch 和架构:

```console
sow rm 'pev2-0:1.23.0-1.noarch' -d el9 -c
operation rejected: managed: operation rejected: package reference not found: package reference "pev2-0:1.23.0-1.noarch" matches no Desired Membership
```

另外,这里没有 glob、没有正则、没有版本区间,也没有 `--all` 参数。
如果你想按模式 **筛选** 一批包,那是 `sow.yml` 里的[成员策略](/zh/docs/reference/config/),
不是命令行选择器。命令行永远只用来指代 **已经存在** 的包。

## 作用域

引用总是在某个作用域内解析,而作用域由常规的选择参数决定,与引用写法无关:

| 命令 | 默认作用域 | 收窄方式 |
|---|---|---|
| `sow rm` | 所选仓库的所选 Dist | `-r`、`-d`(存在多个时必填) |
| `sow show` | 所选仓库 | `-r`、`-d` |
| `sow where` | 工作区内全部仓库 | `-r`、`-d` |

`sow where` 是那条"广搜"命令 —— 当你知道某个包在某处、但不知道在哪个仓库时用它。
`sow show` 则是在一个仓库内把一个对象的细节全部展开。

两条命令没找到时的措辞也不同,可以据此判断自己跑的是哪一条:

```console
# rm —— 引用本身解析成功,但所选 Dist 里没有对应成员
operation rejected: ... package reference "nosuchpkg" matches no Desired Membership

# show / where —— 搜索范围内根本不存在
operation rejected: ... package reference "nosuchpkg" was not found in the selected Workspace scope
```

## 坐标与身份

上面的坐标形态是包的 **逻辑身份**。SOW 强制约束:一个仓库内,一个坐标最多对应一个内容对象。
用已存在的坐标加入一个 **不同** 的文件是硬冲突 —— SOW 不会悄悄挑一个赢家,也没有 `--replace`。

因此,两个只有签名不同的包仍然会冲突,因为它们坐标相同。如果你真的要重签发布,
请提高 release 号;如果只是把同一个输入再加一次,SOW 会识别出来并报告 `reused`。

## 延伸阅读

- [`sow rm`](/zh/docs/command/rm/) —— 移除、预览与批量语义
- [`sow ls`](/zh/docs/command/ls/)、[`show`](/zh/docs/command/show/) 与 [`where`](/zh/docs/command/where/) —— 三条查询命令
- [退出码](/zh/docs/reference/exit-codes/) —— `6` 同时覆盖"无匹配"与"歧义"
