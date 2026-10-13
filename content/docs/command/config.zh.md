---
title: "sow config"
linkTitle: "config"
description: "校验 sow.yml 并查看生效配置。"
categories: [Command]
tags: [cli, config]
url: "/zh/docs/command/config/"
aliases: ["/docs/reference/cli/config/"]
weight: 300
icon: fa-solid fa-file-code
---

修改 `sow.yml` 后，运行 `sow config check`。它检查配置、签名引用及配置与既有仓库状态是否兼容。使用 `sow config show` 查看默认值与继承设置展开后的配置。两个命令都只读。

## 语法

```text
sow config check [-C DIR] [--json]
sow config show [--all] [-C DIR] [-r NAME] [-d NAME]... [--json]
```

## sow config check

解析并校验完整的 `sow.yml`：schema 版本、名称、路径冲突、架构许可表、Dist 格式、成员策略与签名密钥
引用。它会回报解析到的工作区以及校验了多少对象。

```console
sow config check
configuration valid: /srv/repo repositories=1 dists=2
```

```console
sow config check --json
{"schema":"sow.cli/v1","command":"config check","ok":true,"repository":null,"operation":null,"result":{"workspace":"/srv/repo","repositories":1,"dists":2},"errors":[]}
```

### 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `--json` | 输出 JSON | false |
| `-h, --help` | 显示帮助 | — |

### 严格拒绝未知字段

未知配置键会产生配置错误：

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": parse sow.yml: yaml: unmarshal errors:
  line 8: field bogus_field not found in type config.DistConfig
```

使用 `schema: sow/v3`：

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": config schema must be "sow/v3", got "invalid"
```

`config check` 还会验证签名密钥是否可用且适用于签名。从工作区架构列表移除某个架构前，先移除 Dist 配置、成员和已构建状态对该架构的使用。

## sow config show

以 YAML 输出所选范围内的生效配置。

```console
sow config show
schema: sow/v3
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    protected: false
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
      trixie:
        format: deb
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

对比原始配置文件：

```console
cat sow.yml
schema: sow/v3
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
```

`show` 补上了 `protected: false`、每个 Dist 继承来的 `architectures`、`limit: 0` 与空的 `exclude`
列表。架构以 `x86_64` 和 `aarch64` 表示；它们在 DEB 中分别写作 `amd64` 和 `arm64`。

### 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `--all` | 展开整个工作区的默认值与规范化架构 | 关闭 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 按选择规则 |
| `--json` | 输出 JSON | false |
| `-h, --help` | 显示帮助 | — |

### 用 -r/-d 选择配置范围 {#用--r-d-做作用域投影}

使用 `-r` 与 `-d` 查看指定 Dist 的实际配置：

```console
sow config show -r pigsty -d el9
schema: sow/v3
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    protected: false
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

不带 `--all` 时，按一般规则选择仓库。如果发现起点位于某个 Dist 内，默认只显示该 Dist，除非显式传入 `-d`；否则显示所选仓库的全部 Dist。`--all` 显示整个工作区，并忽略 `-r` 与 `-d`。

### 签名引用 {#秘密永不输出}

输出包含密钥引用和解析后的指纹，不包含私钥内容或口令。

## 示例

在 CI 里先校验再构建：

```bash
sow config check -C /srv/repo || exit 1
sow build -C /srv/repo -r pgsql
```

比较两个 Dist 的有效策略：

```bash
sow config show -r pgsql -d el9 > /tmp/el9.yml
sow config show -r pgsql -d el9-beta > /tmp/beta.yml
diff -u /tmp/el9.yml /tmp/beta.yml
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 配置合法，或输出成功打印 |
| `1` | 运行时错误或密钥解析失败 |
| `2` | 用法或发现错误、YAML 无效、未知字段或不支持的 schema |
| `5` | 既有状态、受控路径或恢复记录不一致 |
| `6` | 所选对象不存在、签名配置不可用，或配置与既有状态不兼容 |

`config check` 同时检查 YAML 文件及其与已有仓库状态的兼容性。

## 参见

- [sow.yml 配置参考](/zh/docs/reference/config/) —— 全部配置键与完整示例文件
- [成员策略](/zh/docs/feature/policy/) —— `exclude` 与 `limit` 如何求值
- [签名模型](/zh/docs/feature/signing/) —— 密钥引用文法与两条信任链
- [sow init](/zh/docs/command/init/) —— 创建手写配置中声明的对象
- [sow check](/zh/docs/command/check/) —— 检查包文件、索引与私有状态
