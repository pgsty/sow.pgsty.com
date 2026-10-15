---
title: "成员策略"
linkTitle: "成员策略"
description: "配置包排除与版本数量限制，读取策略结果，恢复已移除成员。"
categories: [Feature]
tags: [policy, managed]
url: "/zh/docs/feature/policy/"
weight: 500
icon: fa-solid fa-filter
---

<span id="两条规则与它们的顺序" data-td-print-local></span>

用 Dist 策略排除不需要的包，并限制索引中的版本数量。在 `sow.yml` 中配置
`exclude` 和 `limit`：

```yaml
dists:
  el9:
    format: rpm
    limit: 2
    exclude:
      - kind: [debuginfo, debugsource, llvmjit]
```

SOW 先执行 `exclude`，再执行 `limit`。`add`、`rm` 和 `build` 都会对所选 Dist 的完整候选
成员集合应用策略。编辑策略后，先运行 `sow config check`，再运行 `sow build`，
使现有成员符合新规则。

<span id="exclude" data-td-print-local></span>

## 排除软件包

每条规则包含一个或多个字段。规则内的所有字段都要匹配；一个字段内，任一模式匹配即可。
任一规则匹配时，该包被排除。

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

此配置在所有架构上排除列出的包类型，同时排除名称以 `test-` 开头或以
`-experimental` 结尾的 `aarch64` 包。

| 字段 | 匹配的包属性 |
|---|---|
| `name` | 二进制包名 |
| `source` | 规范化的源码包名 |
| `arch` | `x86_64`、`aarch64` 或 `neutral` |
| `kind` | 下表中的包类型 |
| `format` | `rpm` 或 `deb` |

模式区分大小写，支持精确字符串和 shell 通配符 `*`、`?`、`[...]`，不支持正则表达式、
版本比较或取反。空规则、空模式、首尾有空白的模式、同字段重复模式和非法通配符都是配置错误。

SOW 根据二进制包名确定 `kind`：

| 格式 | 包名后缀 | `kind` |
|---|---|---|
| RPM | `-debuginfo` | `debuginfo` |
| RPM | `-debugsource` | `debugsource` |
| RPM | `-llvmjit` | `llvmjit` |
| DEB | `-dbgsym` | `dbgsym` |
| DEB | `-dbg` | `dbg` |
| 任意 | 没有匹配后缀 | `main` |

用 `sow show PACKAGE --json` 查看计算出的类型。模式值不会按此表校验：
`kind: [debug]` 是合法配置，但不会匹配任何包类型。

<span id="limit" data-td-print-local></span>

## 限制版本数量

`limit` 按二进制包名和规范架构族分组。架构无关包（`noarch` 或 `all`）单独成组。

| 值 | 结果 |
|---|---|
| `0` | 保留所有版本，默认值 |
| 正整数 `N` | 每组保留最新的 `N` 个版本 |
| 负数 | 配置错误 |

RPM 使用 epoch-version-release 排序，DEB 使用 Debian 版本排序，不按普通字符串排序。

`limit: 2` 时，向已有版本 1、2 的 Dist 加入版本 3，会在同一次操作中移除版本 1 的成员关系。
即使包名相同，`x86_64` 包与 `noarch` 包也属于不同分组。

<span id="策略作用于完整候选集" data-td-print-local></span>

## 读取策略结果

输入包被所有选中 Dist 排除时，整体状态为 `excluded`。各 Dist 的结果中，
`excluded` 表示命中排除规则，`limited` 表示超过版本数量限制。
策略排除不计为输入失败，也不会因此使命令失败。

同一个包可以被一个 Dist 接受、被另一个排除。没有 Dist 接受新包时，
SOW 不会为它保存一个无成员关系的包对象。

<span id="放宽策略永远不会复活任何东西" data-td-print-local></span>

## 恢复已移除的版本

放宽策略不会恢复旧成员。提高 `limit`、删除排除规则或移除最新版本，只会改变当前及后续
候选包的处理结果。要恢复某个版本，请重新加入其包文件：

```bash
sow add ./archive/example-1.0-1.x86_64.rpm -r demo -d el9
```

策略移除的是成员关系，不是包字节。已构建或保留的构建快照可能仍引用该包，使其继续留在包池。
用 [`sow gc`](/zh/docs/command/gc/) 回收无引用对象；对已发布目标使用 `sow gc TARGET`。

<span id="预览一次决策" data-td-print-local></span>

## 预览移除结果

```bash
sow rm example -r demo -d el9 --check
```

预览只报告成员移除和预期文件变化，不写入状态。把文件列表视为完整计划前，请检查 JSON 中
的 `prediction_complete`。`--check` 不能与 `--skip`、`--timeout` 或 `--no-wait` 同用。

完整配置见[配置参考](/zh/docs/reference/config/)，输入结果见
[`sow add`](/zh/docs/command/add/)。

<span id="继续阅读" data-td-print-local></span>
