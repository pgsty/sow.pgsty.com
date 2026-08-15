---
title: "sow where"
linkTitle: "where"
description: "在工作区的 Repository 与 Dist 中定位一个 Package Object。"
url: "/zh/docs/command/where/"
weight: 1000
icon: fa-solid fa-location-dot
---

`sow where` 用于回答工作区中哪些 Dist 仍包含某个 Package Object。它默认搜索全部 Repository，
只读且不获取写锁。

## 语法

```text
sow where PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 将搜索限制到一个 Repository | 全部 Repository |
| `-d, --dist NAME` | 将搜索限制到指定 Dist；可重复 | 全部 Dist |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

## 引用解析

`PACKAGE` 与 [`sow show`](/zh/docs/command/show/) 使用相同文法：SHA-256、规范 RPM/DEB 坐标、
完整文件名或裸包名。

解析范围是完整的所选工作区范围。裸包名必须标识唯一 Package Object；即使同名对象位于不同
Repository，也会产生歧义。使用 `-r`/`-d` 收窄范围，或提供精确坐标/SHA-256。

## 输出

不带 `--json` 时，`where` 输出命令专用 JSON：

```console
sow where epel-release
{"reference":"epel-release","locations":[{"repository":"pigsty","dists":["el9"],"built_dists":["el9"],"sha256":"d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab","coordinate":"rpm:epel-release-0:7-5.noarch"}]}
```

每个位置同时给出 Desired `dists` 与当前 `built_dists`，可用于确认已移除或已替换版本是否仍对
客户端可见。

加上 `--json` 后，同一对象位于 `result` 下。引用不存在属于明确拒绝，而不是空成功：

```console
sow where nosuchpkg
operation rejected: managed: operation rejected: package reference "nosuchpkg" was not found in the selected Workspace scope
```

## 示例

列出仍在提供某个精确版本的全部位置：

```bash
sow where 'rpm:patroni-0:3.0.4-1.noarch' --json |
  jq -r '.result.locations[] | "\(.repository)/\(.dists | join(","))"'
```

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 已输出一个解析后的 Package Object 及其位置 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误或未发现工作区 |
| `5` | 某个 Repository 状态库不可读或不一致 |
| `6` | 显式 Repository/Dist 未配置，或引用没有匹配/在所选范围内有歧义 |

## 参见

- [`sow show`](/zh/docs/command/show/) —— 查看解析后的 Package Object
- [`sow ls`](/zh/docs/command/ls/) —— 列出一个 Dist 集合
- [包引用](/zh/docs/reference/package-ref/) —— 精确文法与歧义规则
