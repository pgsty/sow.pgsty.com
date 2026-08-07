---
title: "sow config"
linkTitle: "sow config"
description: "只读校验 sow.yml，并打印任意作用域的有效配置。"
url: "/zh/docs/reference/cli/config/"
weight: 300
icon: fa-solid fa-file-code
---

`sow config` 有两个只读子命令。`config check` 是对 `sow.yml` 的全量预检——每次手工改完配置以及在
CI 里都该跑一遍。`config show` 打印 SOW 实际算出来的配置，用它确认默认值、继承的架构与规范化别名
是不是按你预期解析的。

两个子命令都不创建目录、不碰数据库、不自动修正你的文件。

## 语法

```text
sow config check [-C DIR] [--json]
sow config show [--all] [-C DIR] [-r NAME] [-d NAME]... [--json]
```

`sow help config` 会列出两者。

## sow config check

解析并校验完整的 `sow.yml`：schema 版本、名称、路径冲突、架构许可表、Dist 格式、成员策略与签名 key
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
| `--json` | 输出版本化 JSON envelope | false |
| `-h, --help` | 显示帮助 | — |

### 严格拒绝未知字段

未知键是错误，不是警告。一个拼写错误不会静默地让某条策略失效：

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": parse sow.yml: yaml: unmarshal errors:
  line 8: field bogus_field not found in type config.DistConfig
```

schema 版本被钉死：

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": config schema must be "sow/v2", got "sow/v1"
```

`check` 还会验证声明的每个签名 key 引用可解析且适用于签名——过程中绝不打印密钥材料。如果你从许可表
里删掉一个架构，而仍有 Dist 配置、Membership 或已构建代在用它，`config check` 会拒绝该配置。

## sow config show

以 YAML 打印当前选定作用域的有效配置。

```console
sow config show
schema: sow/v2
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

对比磁盘上的文件——里面只有你写的内容：

```console
cat sow.yml
schema: sow/v2
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
列表。架构一律以规范化 family（`x86_64`、`aarch64`）打印，绝不用生态别名——`amd64` 与 `arm64` 只是
同两个 family 的 DEB 写法。

### 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `--all` | 展开整个工作区的默认值与规范化架构 | 关闭 |
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 按选择规则 |
| `--json` | 输出版本化 JSON envelope | false |
| `-h, --help` | 显示帮助 | — |

### 用 -r/-d 做作用域投影

`-r` 与 `-d` 把输出收窄到选中的对象。要回答"这一个 Dist 上实际生效的策略是什么"，这是最快的方式：

```console
sow config show -r pigsty -d el9
schema: sow/v2
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

`--all` 方向相反：无论你站在哪里，它都展开整个工作区。

### 秘密永不输出

密钥材料与 passphrase 不会出现在 `config show`、JSON、操作日志或错误文本中。只显示引用形态
（`file://…`、`env://…`、`agent://…`）与 fingerprint。

## 示例

在 CI 里先校验再构建：

```bash
sow config check -C /srv/repo || exit 1
sow build -r pgsql
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
| `1` | 读取配置文件时的运行时 I/O 错误 |
| `2` | 用法错误、工作区未找到、未知字段、schema 不符，或任何校验失败 |
| `6` | 指定的仓库或 Dist 不存在 |

`config check` 把校验失败报为退出码 `2` 而不是 `6`：非法的 `sow.yml` 属于配置错误，不是被拒绝的
操作。

## 参见

- [sow.yml 配置参考](/zh/docs/reference/config/) —— 全部配置键与完整示例文件
- [成员策略](/zh/docs/feature/policy/) —— `exclude` 与 `limit` 如何求值
- [签名模型](/zh/docs/feature/signing/) —— key 引用文法与两条信任链
- [sow init](/zh/docs/reference/cli/init/) —— 收敛手写配置
- [sow check](/zh/docs/reference/cli/build/) —— 校验磁盘字节的运行时对照命令
